from __future__ import annotations

import hashlib
import os
import re
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from .models import (
    PreparedSource,
    ContractRevisionProposalRecord,
    ContractRevisionProposalState,
    SourceRecord,
    SourceRevisionRecord,
    SourceState,
    SourceView,
    utc_now,
)


class SourceRepositoryError(RuntimeError):
    pass


class SourceNotFound(SourceRepositoryError):
    pass


class SourceNotReady(SourceRepositoryError):
    pass


class ContractRevisionConflict(SourceRepositoryError):
    pass


class LocalSourceRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def begin_source(
        self,
        *,
        owner_key: str,
        connector_key: str,
        display_name: str,
        original_filename: str,
        content: bytes,
        description_filename: str | None = None,
        description_content: bytes | None = None,
    ) -> PreparedSource:
        if not owner_key.strip() or not connector_key.strip() or not display_name.strip():
            raise ValueError("Owner, connector, and source display name are required.")
        if Path(original_filename).name != original_filename or any(
            separator in original_filename for separator in ("/", "\\")
        ):
            raise ValueError("Source input must use a plain filename.")
        # 96 bits keeps owner-facing IDs opaque and collision-resistant while
        # leaving room for nested connector artifacts on Windows.
        source_id = secrets.token_urlsafe(12)
        revision_id = secrets.token_urlsafe(12)
        now = utc_now()
        source = SourceRecord(
            source_id=source_id,
            owner_key=owner_key,
            connector_key=connector_key,
            display_name=display_name.strip(),
            current_revision_id=revision_id,
            created_at=now,
            updated_at=now,
        )
        revision = SourceRevisionRecord(
            revision_id=revision_id,
            source_id=source_id,
            original_filename=original_filename,
            content_sha256=hashlib.sha256(content).hexdigest(),
            description_filename=description_filename,
            description_sha256=(
                hashlib.sha256(description_content).hexdigest()
                if description_content is not None
                else None
            ),
            state=SourceState.QUEUED,
            created_at=now,
            updated_at=now,
        )
        source_dir = self._source_dir(owner_key, source_id)
        revision_dir = source_dir / "r" / revision_id
        input_path = revision_dir / "i" / original_filename
        artifact_dir = revision_dir / "a"
        if source_dir.exists():
            raise SourceRepositoryError(
                f"The generated source ID already exists: {source_id}"
            )
        input_path.parent.mkdir(parents=True, exist_ok=False)
        artifact_dir.mkdir(parents=True, exist_ok=False)
        _write_bytes_atomic(source_dir / ".source-mutation.lock", b"\0")
        _write_bytes_atomic(input_path, content)
        if description_filename is not None and description_content is not None:
            _write_bytes_atomic(
                revision_dir / "i" / description_filename,
                description_content,
            )
        _write_model_atomic(revision_dir / "revision.json", revision)
        # The owner inventory discovers a Source through source.json. Publish
        # that pointer only after its exact current revision is durable.
        _write_model_atomic(source_dir / "source.json", source)
        return PreparedSource(
            source=source,
            revision=revision,
            input_path=input_path,
            artifact_dir=artifact_dir,
        )

    def attach_job(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        job_id: str,
    ) -> SourceView:
        if not job_id.strip():
            raise ValueError("Source job ID cannot be empty.")
        return self._replace_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            updates={"job_id": job_id, "updated_at": utc_now()},
        )

    def mark_running(
        self, *, owner_key: str, source_id: str, revision_id: str
    ) -> SourceView:
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            from_states={SourceState.QUEUED},
            state=SourceState.RUNNING,
            summary={},
            failure_code=None,
            failure_message=None,
        )

    def mark_queued_for_retry(
        self, *, owner_key: str, source_id: str, revision_id: str
    ) -> SourceView:
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            from_states={SourceState.FAILED},
            state=SourceState.QUEUED,
            summary={},
            failure_code=None,
            failure_message=None,
        )

    def list(self, *, owner_key: str) -> tuple[SourceView, ...]:
        owner_dir = self._owner_dir(owner_key)
        if not owner_dir.is_dir():
            return ()
        values: list[SourceView] = []
        for manifest in owner_dir.glob("*/source.json"):
            with _exclusive_source_lock(manifest.parent / ".source-mutation.lock"):
                if not manifest.is_file():
                    continue
                source = self._read_source(manifest)
                if source.owner_key != owner_key:
                    raise SourceRepositoryError(
                        f"Source owner metadata disagrees at {manifest}"
                    )
                values.append(self._view(source))
        return tuple(
            sorted(values, key=lambda value: (value.created_at, value.source_id))
        )

    def get(self, *, owner_key: str, source_id: str) -> SourceView:
        manifest = self._source_dir(owner_key, source_id) / "source.json"
        if not manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(manifest.parent / ".source-mutation.lock"):
            return self._get_unlocked(
                owner_key=owner_key, source_id=source_id, manifest=manifest
            )

    def _get_unlocked(
        self, *, owner_key: str, source_id: str, manifest: Path | None = None
    ) -> SourceView:
        manifest = manifest or self._source_dir(owner_key, source_id) / "source.json"
        if not manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        source = self._read_source(manifest)
        if source.owner_key != owner_key:
            raise SourceNotFound("The requested source does not exist.")
        return self._view(source)

    def get_revision(
        self, *, owner_key: str, source_id: str, revision_id: str
    ) -> SourceView:
        source_dir = self._source_dir(owner_key, source_id)
        if not (source_dir / "source.json").is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_dir / ".source-mutation.lock"):
            source = self._owned_source(owner_key=owner_key, source_id=source_id)
            revision = self._read_revision(
                self._revision_dir(owner_key, source_id, revision_id) / "revision.json"
            )
            if revision.source_id != source_id:
                raise SourceNotFound("The requested source revision does not exist.")
            return SourceView(
                source_id=source.source_id,
                connector_key=source.connector_key,
                display_name=source.display_name,
                created_at=source.created_at,
                updated_at=source.updated_at,
                revision=revision,
            )

    @contextmanager
    def locked_revision(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str | None = None,
        require_current: bool = False,
    ):
        """Yield one exact owner-scoped revision and its directory under the Source lock."""
        source_dir = self._source_dir(owner_key, source_id)
        manifest = source_dir / "source.json"
        if not manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_dir / ".source-mutation.lock"):
            source = self._owned_source(owner_key=owner_key, source_id=source_id)
            selected_revision_id = revision_id or source.current_revision_id
            if require_current and source.current_revision_id != selected_revision_id:
                raise SourceNotReady(
                    "The selected source revision is no longer current."
                )
            revision_dir = self._revision_dir(
                owner_key, source_id, selected_revision_id
            )
            revision = self._read_revision(revision_dir / "revision.json")
            if revision.source_id != source_id:
                raise SourceNotFound("The requested source revision does not exist.")
            yield (
                SourceView(
                    source_id=source.source_id,
                    connector_key=source.connector_key,
                    display_name=source.display_name,
                    created_at=source.created_at,
                    updated_at=source.updated_at,
                    revision=revision,
                ),
                revision_dir,
            )

    def owner_route_plan_index_path(self, *, owner_key: str, plan_id: str) -> Path:
        """Return one owner-scoped opaque-plan index path without scanning Sources."""
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", plan_id):
            raise SourceNotFound("The requested route plan does not exist.")
        return self._owner_dir(owner_key) / "api-route-plans" / f"{plan_id}.json"

    def create_contract_revision_proposal(
        self,
        *,
        owner_key: str,
        proposal: ContractRevisionProposalRecord,
        candidate_bytes: bytes,
    ) -> ContractRevisionProposalRecord:
        source_dir = self._source_dir(owner_key, proposal.source_id)
        if not (source_dir / "source.json").is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(
            source_dir / ".source-mutation.lock"
        ):
            return self._create_contract_revision_proposal_locked(
                owner_key=owner_key,
                proposal=proposal,
                candidate_bytes=candidate_bytes,
            )

    def _create_contract_revision_proposal_locked(
        self,
        *,
        owner_key: str,
        proposal: ContractRevisionProposalRecord,
        candidate_bytes: bytes,
    ) -> ContractRevisionProposalRecord:
        source_path = self._source_dir(owner_key, proposal.source_id) / "source.json"
        source = self._owned_source(owner_key=owner_key, source_id=proposal.source_id)
        if source.current_revision_id != proposal.parent_revision_id:
            raise ContractRevisionConflict(
                "The Source changed before this contract proposal could be saved."
            )
        if any(
            item.parent_revision_id == proposal.parent_revision_id
            and item.final_canonical_sha256 == proposal.final_canonical_sha256
            for item in source.contract_revision_proposals
        ):
            raise ContractRevisionConflict(
                "This exact contract revision was already proposed for the Source."
            )
        proposal_dir = self._proposal_dir(
            owner_key, proposal.source_id, proposal.proposal_id
        )
        if proposal_dir.exists():
            raise ContractRevisionConflict("The contract proposal already exists.")
        candidate_path = proposal_dir / self._candidate_filename(
            proposal.final_canonical_sha256
        )
        _write_bytes_atomic(candidate_path, candidate_bytes)
        updated = source.model_copy(
            update={
                "updated_at": proposal.proposed_at,
                "contract_revision_proposals": (
                    *source.contract_revision_proposals,
                    proposal,
                ),
            }
        )
        try:
            _write_model_atomic(source_path, updated)
        except Exception:
            # Candidate bytes are not product-visible until the source manifest
            # records their immutable proposal identity.
            candidate_path.unlink(missing_ok=True)
            try:
                proposal_dir.rmdir()
            except OSError:
                pass
            raise
        return proposal

    def list_contract_revision_proposals(
        self, *, owner_key: str, source_id: str
    ) -> tuple[ContractRevisionProposalRecord, ...]:
        source_dir = self._source_dir(owner_key, source_id)
        if not (source_dir / "source.json").is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_dir / ".source-mutation.lock"):
            return self._owned_source(
                owner_key=owner_key, source_id=source_id
            ).contract_revision_proposals

    def get_contract_revision_proposal(
        self, *, owner_key: str, source_id: str, proposal_id: str
    ) -> ContractRevisionProposalRecord:
        source_dir = self._source_dir(owner_key, source_id)
        if not (source_dir / "source.json").is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_dir / ".source-mutation.lock"):
            source = self._owned_source(owner_key=owner_key, source_id=source_id)
            matches = tuple(
                item
                for item in source.contract_revision_proposals
                if item.proposal_id == proposal_id
            )
            if len(matches) != 1:
                raise SourceNotFound("The requested contract proposal does not exist.")
            return matches[0]

    def approve_contract_revision(
        self,
        *,
        owner_key: str,
        source_id: str,
        proposal_id: str,
        revision_id: str,
        approved_by_owner_id: str,
        approved_at: datetime,
        summary: dict[str, object],
    ) -> SourceView:
        source_dir = self._source_dir(owner_key, source_id)
        if not (source_dir / "source.json").is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(
            source_dir / ".source-mutation.lock"
        ):
            return self._approve_contract_revision_locked(
                owner_key=owner_key,
                source_id=source_id,
                proposal_id=proposal_id,
                revision_id=revision_id,
                approved_by_owner_id=approved_by_owner_id,
                approved_at=approved_at,
                summary=summary,
            )

    def _approve_contract_revision_locked(
        self,
        *,
        owner_key: str,
        source_id: str,
        proposal_id: str,
        revision_id: str,
        approved_by_owner_id: str,
        approved_at: datetime,
        summary: dict[str, object],
    ) -> SourceView:
        source_path = self._source_dir(owner_key, source_id) / "source.json"
        source = self._owned_source(owner_key=owner_key, source_id=source_id)
        proposals = list(source.contract_revision_proposals)
        matches = [
            (index, item)
            for index, item in enumerate(proposals)
            if item.proposal_id == proposal_id
        ]
        if len(matches) != 1:
            raise SourceNotFound("The requested contract proposal does not exist.")
        index, proposal = matches[0]
        if proposal.state is not ContractRevisionProposalState.PENDING:
            raise ContractRevisionConflict("The contract proposal is no longer pending.")
        if source.current_revision_id != proposal.parent_revision_id:
            raise ContractRevisionConflict(
                "The Source changed after this contract proposal was created."
            )
        candidate_path = self._proposal_dir(
            owner_key, source_id, proposal_id
        ) / self._candidate_filename(proposal.final_canonical_sha256)
        try:
            candidate_bytes = candidate_path.read_bytes()
        except OSError as error:
            raise SourceRepositoryError(
                "The reviewed contract candidate is unavailable."
            ) from error
        if hashlib.sha256(candidate_bytes).hexdigest() != proposal.final_canonical_sha256:
            raise ContractRevisionConflict(
                "The reviewed contract candidate no longer matches its recorded hash."
            )
        revision_dir = self._revision_dir(owner_key, source_id, revision_id)
        if revision_dir.exists():
            raise ContractRevisionConflict("The new Source revision already exists.")
        filename = self._candidate_filename(proposal.final_canonical_sha256)
        input_path = revision_dir / "i" / filename
        artifact_dir = revision_dir / "a"
        input_path.parent.mkdir(parents=True, exist_ok=False)
        artifact_dir.mkdir(parents=True, exist_ok=False)
        _write_bytes_atomic(input_path, candidate_bytes)
        revision = SourceRevisionRecord(
            revision_id=revision_id,
            source_id=source_id,
            original_filename=filename,
            content_sha256=proposal.final_canonical_sha256,
            state=SourceState.READY,
            created_at=approved_at,
            updated_at=approved_at,
            summary=dict(summary),
            parent_revision_id=proposal.parent_revision_id,
            artifact_revision_id=proposal.parent_revision_id,
        )
        _write_model_atomic(revision_dir / "revision.json", revision)
        proposals[index] = proposal.model_copy(
            update={
                "state": ContractRevisionProposalState.APPROVED,
                "approved_by_owner_id": approved_by_owner_id,
                "approved_at": approved_at,
                "approved_revision_id": revision_id,
            }
        )
        updated_source = source.model_copy(
            update={
                "current_revision_id": revision_id,
                "updated_at": approved_at,
                "contract_revision_proposals": tuple(proposals),
            }
        )
        # The single manifest replacement commits both proposal approval and
        # the new current pointer. A failure leaves the prior revision current.
        _write_model_atomic(source_path, updated_source)
        return SourceView(
            source_id=updated_source.source_id,
            connector_key=updated_source.connector_key,
            display_name=updated_source.display_name,
            created_at=updated_source.created_at,
            updated_at=updated_source.updated_at,
            revision=revision,
        )

    def artifact_dir(self, *, owner_key: str, source_id: str) -> Path:
        view = self.get(owner_key=owner_key, source_id=source_id)
        return self.artifact_dir_exact(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=view.revision.revision_id,
        )

    def artifact_dir_exact(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
    ) -> Path:
        view = self.get_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        )
        artifact_revision_id = (
            view.revision.artifact_revision_id or view.revision.revision_id
        )
        return (
            self._source_dir(owner_key, source_id)
            / "r"
            / artifact_revision_id
            / "a"
        )

    def revision_dir(self, *, owner_key: str, source_id: str) -> Path:
        view = self.get(owner_key=owner_key, source_id=source_id)
        return (
            self._source_dir(owner_key, source_id)
            / "r"
            / view.revision.revision_id
        )

    def input_path(self, *, owner_key: str, source_id: str) -> Path:
        view = self.get(owner_key=owner_key, source_id=source_id)
        return (
            self._source_dir(owner_key, source_id)
            / "r"
            / view.revision.revision_id
            / "i"
            / view.revision.original_filename
        )

    def mark_ready(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        summary: dict[str, object],
    ) -> SourceView:
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            from_states={SourceState.RUNNING},
            state=SourceState.READY,
            summary=summary,
            failure_code=None,
            failure_message=None,
        )

    def mark_failed(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        failure_code: str,
        failure_message: str,
    ) -> SourceView:
        if not failure_code.strip() or not failure_message.strip():
            raise ValueError("Failed source revisions require a code and message.")
        return self._transition(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
            from_states={SourceState.QUEUED, SourceState.RUNNING},
            state=SourceState.FAILED,
            summary={},
            failure_code=failure_code,
            failure_message=failure_message,
        )

    def _transition(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        from_states: set[SourceState],
        state: SourceState,
        summary: dict[str, object],
        failure_code: str | None,
        failure_message: str | None,
    ) -> SourceView:
        source_manifest = self._source_dir(owner_key, source_id) / "source.json"
        if not source_manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_manifest.parent / ".source-mutation.lock"):
            source_view = self._get_unlocked(
                owner_key=owner_key, source_id=source_id, manifest=source_manifest
            )
            if source_view.revision.revision_id != revision_id:
                raise SourceNotFound("The requested source revision does not exist.")
            if source_view.revision.state not in from_states:
                raise SourceRepositoryError(
                    "The source revision cannot make the requested state transition."
                )
            now = utc_now()
            updated_revision = source_view.revision.model_copy(
                update={
                    "state": state,
                    "updated_at": now,
                    "summary": dict(summary),
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                }
            )
            source = self._read_source(source_manifest).model_copy(
                update={"updated_at": now}
            )
            revision_manifest = (
                source_manifest.parent / "r" / revision_id / "revision.json"
            )
            _write_model_atomic(revision_manifest, updated_revision)
            _write_model_atomic(source_manifest, source)
            return SourceView(
                source_id=source.source_id,
                connector_key=source.connector_key,
                display_name=source.display_name,
                created_at=source.created_at,
                updated_at=source.updated_at,
                revision=updated_revision,
            )

    def _replace_revision(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        updates: dict[str, object],
    ) -> SourceView:
        source_manifest = self._source_dir(owner_key, source_id) / "source.json"
        if not source_manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        with _exclusive_source_lock(source_manifest.parent / ".source-mutation.lock"):
            source_view = self._get_unlocked(
                owner_key=owner_key, source_id=source_id, manifest=source_manifest
            )
            if source_view.revision.revision_id != revision_id:
                raise SourceNotFound("The requested source revision does not exist.")
            updated_revision = source_view.revision.model_copy(update=updates)
            source = self._read_source(source_manifest).model_copy(
                update={"updated_at": updated_revision.updated_at}
            )
            _write_model_atomic(
                source_manifest.parent / "r" / revision_id / "revision.json",
                updated_revision,
            )
            _write_model_atomic(source_manifest, source)
            return SourceView(
                source_id=source.source_id,
                connector_key=source.connector_key,
                display_name=source.display_name,
                created_at=source.created_at,
                updated_at=source.updated_at,
                revision=updated_revision,
            )

    def _view(self, source: SourceRecord) -> SourceView:
        revision_path = (
            self._source_dir(source.owner_key, source.source_id)
            / "r"
            / source.current_revision_id
            / "revision.json"
        )
        if not revision_path.is_file():
            raise SourceRepositoryError(
                f"The current source revision is missing: {revision_path}"
            )
        revision = self._read_revision(revision_path)
        return SourceView(
            source_id=source.source_id,
            connector_key=source.connector_key,
            display_name=source.display_name,
            created_at=source.created_at,
            updated_at=source.updated_at,
            revision=revision,
        )

    def _owned_source(self, *, owner_key: str, source_id: str) -> SourceRecord:
        manifest = self._source_dir(owner_key, source_id) / "source.json"
        if not manifest.is_file():
            raise SourceNotFound("The requested source does not exist.")
        source = self._read_source(manifest)
        if source.owner_key != owner_key:
            raise SourceNotFound("The requested source does not exist.")
        return source

    def _read_revision(self, path: Path) -> SourceRevisionRecord:
        if not path.is_file():
            raise SourceNotFound("The requested source revision does not exist.")
        try:
            return SourceRevisionRecord.model_validate_json(
                path.read_text(encoding="utf-8")
            )
        except (OSError, ValidationError) as error:
            raise SourceRepositoryError(
                f"The source revision metadata is invalid: {error}"
            ) from error

    def _read_source(self, path: Path) -> SourceRecord:
        try:
            return SourceRecord.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError) as error:
            raise SourceRepositoryError(
                f"The source metadata is invalid: {error}"
            ) from error

    def _owner_dir(self, owner_key: str) -> Path:
        if not owner_key.strip():
            raise ValueError("Owner key cannot be empty.")
        opaque = hashlib.sha256(owner_key.encode("utf-8")).hexdigest()[:16]
        return self.root / opaque

    def _source_dir(self, owner_key: str, source_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", source_id):
            raise SourceNotFound("The requested source does not exist.")
        return self._owner_dir(owner_key) / source_id

    def _revision_dir(
        self, owner_key: str, source_id: str, revision_id: str
    ) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", revision_id):
            raise SourceNotFound("The requested source revision does not exist.")
        return self._source_dir(owner_key, source_id) / "r" / revision_id

    def _proposal_dir(
        self, owner_key: str, source_id: str, proposal_id: str
    ) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{16}", proposal_id):
            raise SourceNotFound("The requested contract proposal does not exist.")
        return self._source_dir(owner_key, source_id) / "contract-revisions" / proposal_id

    @staticmethod
    def _candidate_filename(final_hash: str) -> str:
        return f"effective-{final_hash[:12]}.json"


def _write_model_atomic(path: Path, model) -> None:
    _write_text_atomic(path, model.model_dump_json(indent=2))


def _write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_bytes_atomic(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(value)
    temporary.replace(path)


_SOURCE_LOCKS_GUARD = threading.Lock()
_SOURCE_LOCKS: dict[Path, threading.RLock] = {}


@contextmanager
def _exclusive_source_lock(path: Path):
    """Serialize one Source manifest mutation across threads and processes."""
    resolved = path.resolve()
    with _SOURCE_LOCKS_GUARD:
        local_lock = _SOURCE_LOCKS.setdefault(resolved, threading.RLock())
    with local_lock:
        with resolved.open("a+b") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            _lock_file(handle)
            try:
                yield
            finally:
                _unlock_file(handle)


if os.name == "nt":
    import msvcrt

    def _lock_file(handle) -> None:
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(handle) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_file(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _unlock_file(handle) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = [
    "ContractRevisionConflict",
    "LocalSourceRepository",
    "SourceNotFound",
    "SourceNotReady",
    "SourceRepositoryError",
]
