from __future__ import annotations

import json
import hashlib
import re
from dataclasses import replace
from pathlib import Path
from collections.abc import Callable, Mapping
from typing import Any

import ollama

from .contracts import (
    EvalsetRequest,
    EvalsetResult,
    IngestRequest,
    IngestResult,
    ManagedParameter,
    RankedEndpoint,
    RetrievalRequest,
    RetrievalResult,
    RetrievalStep,
)
from .engine.evalset_factory_contracts import (
    ContextStrategy,
    load_recipe_pack,
)
from .engine.evalset_factory_experiment import (
    EvalsetFactoryExperiment,
    ExperimentConfig,
    ExperimentInputs,
)
from .engine.evalset_factory_export import build_export, write_export
from .engine.evalset_factory_generation import OllamaGenerationClient
from .engine.evalset_factory_validation import OllamaSemanticReviewClient
from .engine.ladder_llm import stable_hash
from .engine.openapi_loader import load_openapi_specs, write_normalized_bundle
from .engine.openapi_loader import read_normalized_bundle
from .openai_responses import (
    OpenAIResponsesTransport,
    resolve_openai_model_digest,
)
from .engine.semantic_grag_router import SemanticGRAGRouter
from .engine.semantic_graph import build_semantic_graph
from .engine.semantic_graph_retrieval import (
    EmbeddingProvider,
    SemanticGraphIndex,
    SentenceTransformerEmbeddingProvider,
)
from .errors import (
    ToolRouterArtifactError,
    ToolRouterDependencyError,
    ToolRouterInputError,
)
from .serialization import (
    read_index,
    subset_index,
    write_embeddings,
    write_graph,
    write_json_atomic,
)
from .settings import ToolRouterSettings


class ToolRouterAdapter:
    def __init__(
        self,
        settings: ToolRouterSettings,
        *,
        embedding_provider: EmbeddingProvider | None = None,
        generation_transport: Callable[[dict[str, Any]], Mapping[str, Any]]
        | None = None,
        review_transport: Callable[[dict[str, Any]], Mapping[str, Any]]
        | None = None,
        model_digest_resolver: Callable[[str], str] | None = None,
    ) -> None:
        self.settings = settings
        self._embedding_provider = embedding_provider
        if settings.model_provider == "openai":
            if settings.openai_api_key is None:
                raise ValueError(
                    "OPENAI_API_KEY is required for the ToolRouter OpenAI provider"
                )
            openai_transport = None
            if generation_transport is None or review_transport is None:
                openai_transport = OpenAIResponsesTransport(
                    api_key=settings.openai_api_key.get_secret_value(),
                    timeout_seconds=settings.evalset_timeout_seconds,
                    reasoning_effort=settings.openai_reasoning_effort,
                )
            self._generation_transport = generation_transport or openai_transport
            self._review_transport = review_transport or openai_transport
        else:
            self._generation_transport = generation_transport
            self._review_transport = review_transport
        self._model_digest_resolver = (
            model_digest_resolver
            or (
                resolve_openai_model_digest
                if settings.model_provider == "openai"
                else self._resolve_ollama_model_digest
            )
        )

    def ingest(self, request: IngestRequest) -> IngestResult:
        source_path = request.source_path.resolve()
        artifact_dir = request.artifact_dir.resolve()
        if not source_path.is_file():
            raise ToolRouterInputError(
                f"The API collection does not exist: {source_path}"
            )
        try:
            bundle = load_openapi_specs([source_path])
        except (OSError, TypeError, ValueError) as error:
            raise ToolRouterInputError(
                f"The API collection could not be normalized: {error}"
            ) from error
        if not bundle.endpoints:
            raise ToolRouterInputError(
                "The API collection contains no operations to index."
            )
        validation_status = _validation_status(bundle.manifest)
        if validation_status == "invalid":
            raise ToolRouterInputError(
                "The API collection is invalid before and after the declared "
                "default-value repair policy."
            )

        normalized_dir = artifact_dir / "normalized"
        graph_dir = artifact_dir / "graph"
        graph_dir.mkdir(parents=True, exist_ok=True)
        try:
            write_normalized_bundle(bundle, normalized_dir)
            trace_path = graph_dir / "graph_trace.jsonl"
            temporary_trace = trace_path.with_suffix(".jsonl.tmp")
            with temporary_trace.open("w", encoding="utf-8") as trace_handle:

                def capture_trace(event: dict[str, Any]) -> None:
                    trace_handle.write(
                        json.dumps(event, sort_keys=True, ensure_ascii=True) + "\n"
                    )

                graph = build_semantic_graph(bundle, trace_callback=capture_trace)
            temporary_trace.replace(trace_path)
        except (OSError, TypeError, ValueError, RuntimeError) as error:
            raise ToolRouterInputError(
                f"The API collection could not produce a conformant graph: {error}"
            ) from error

        provider = self._provider()
        try:
            index = SemanticGraphIndex.build(graph, provider)
        except (TypeError, ValueError, RuntimeError) as error:
            raise ToolRouterDependencyError(
                f"The semantic embedding index could not be built: {error}"
            ) from error
        write_graph(graph_dir / "semantic_graph.json", graph)
        write_embeddings(graph_dir / "embeddings.npy", index.embeddings)
        repair_count = sum(
            int(value) for value in bundle.manifest.get("repair_counts", {}).values()
        )
        manifest = {
            "schema_version": 1,
            "graph_mode": "resource_first_v1",
            "embedding_model": self.settings.embedding_model,
            "embedding_revision": self.settings.embedding_revision,
            "embedding_device": self.settings.embedding_device,
            "embedding_local_files_only": self.settings.embedding_local_files_only,
            "validation_status": validation_status,
            "repair_count": repair_count,
            "endpoint_count": len(bundle.endpoints),
            "schema_count": len(bundle.schemas),
            "security_scheme_count": len(bundle.security_schemes),
            "graph_node_count": len(graph.nodes),
            "graph_edge_count": len(graph.edges),
            "graph_card_count": len(graph.cards),
        }
        write_json_atomic(artifact_dir / "integration_manifest.json", manifest)
        return IngestResult(
            endpoint_count=manifest["endpoint_count"],
            schema_count=manifest["schema_count"],
            security_scheme_count=manifest["security_scheme_count"],
            repair_count=repair_count,
            validation_status=validation_status,
            graph_node_count=manifest["graph_node_count"],
            graph_edge_count=manifest["graph_edge_count"],
            graph_card_count=manifest["graph_card_count"],
            artifact_dir=artifact_dir,
        )

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        query = " ".join(request.query.split())
        if not query:
            raise ToolRouterInputError("A retrieval query is required.")
        if request.top_k <= 0 or request.top_k > 25:
            raise ToolRouterInputError("Retrieval top_k must be between 1 and 25.")
        managed_parameters = _managed_parameter_identities(request.managed_parameters)
        if request.trace_mode not in {"bounded", "full"}:
            raise ToolRouterInputError(
                "Retrieval trace_mode must be 'bounded' or 'full'."
            )
        graph_dir = request.artifact_dir.resolve() / "graph"
        index = read_index(
            graph_path=graph_dir / "semantic_graph.json",
            embeddings_path=graph_dir / "embeddings.npy",
            embedding_provider=self._provider(),
        )
        if request.allowed_endpoint_ids is not None:
            try:
                index = subset_index(
                    index,
                    allowed_endpoint_ids=request.allowed_endpoint_ids,
                )
            except ValueError as error:
                raise ToolRouterInputError(str(error)) from error
        index = _managed_parameter_view(index, managed_parameters)
        try:
            plan = SemanticGRAGRouter(
                index,
                trace_mode=request.trace_mode,
            ).route(
                query,
                top_k=request.top_k,
                provided_params=request.provided_params,
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            raise ToolRouterArtifactError(
                f"The persisted semantic index could not answer the query: {error}"
            ) from error
        return RetrievalResult(
            query=plan.query,
            decision_type=plan.decision_type,
            decision_reason=plan.decision_reason,
            decomposed=plan.decomposed,
            steps=tuple(
                RetrievalStep(
                    query=step.query,
                    ranked_endpoints=tuple(
                        RankedEndpoint(
                            endpoint_id=endpoint.endpoint_id,
                            score=endpoint.score,
                        )
                        for endpoint in step.ranked_endpoints
                    ),
                    trace=dict(step.trace),
                )
                for step in plan.steps
            ),
            missing_params=tuple(plan.missing_params),
            ambiguity=(dict(plan.ambiguity) if plan.ambiguity is not None else None),
            decision_evidence=dict(plan.decision_evidence),
        )

    def generate_evalset(self, request: EvalsetRequest) -> EvalsetResult:
        evalset_id = request.evalset_id.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", evalset_id):
            raise ToolRouterInputError(
                "Evalset IDs must use 1-80 letters, digits, dots, underscores, or hyphens."
            )
        if not request.categories:
            raise ToolRouterInputError("At least one evalset category is required.")
        unsupported = sorted(
            set(request.categories) - SOURCE_GROUNDED_EVALSET_CATEGORIES
        )
        if unsupported:
            raise ToolRouterInputError(
                "The source-grounded task builder does not have evidence for "
                f"these categories: {unsupported}"
            )
        if not 1 <= request.tasks_per_category <= 10:
            raise ToolRouterInputError(
                "Evalset tasks_per_category must be between 1 and 10."
            )
        if request.max_generation_attempts <= 0 or request.max_review_attempts <= 0:
            raise ToolRouterInputError(
                "Evalset generation and review attempt limits must be positive."
            )

        artifact_dir = request.artifact_dir.resolve()
        normalized_path = artifact_dir / "normalized" / "openapi_normalized.json"
        if not normalized_path.is_file():
            raise ToolRouterArtifactError(
                "The normalized OpenAPI artifact is missing for evalset generation."
            )
        try:
            bundle = read_normalized_bundle(normalized_path.parent)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ToolRouterArtifactError(
                f"The normalized OpenAPI artifact is invalid: {error}"
            ) from error
        if not bundle.endpoints:
            raise ToolRouterArtifactError(
                "The normalized OpenAPI artifact contains no endpoints."
            )
        selected_endpoint_ids = tuple(
            endpoint.id for endpoint in bundle.endpoints
        )
        if request.allowed_endpoint_ids is not None:
            allowed = tuple(request.allowed_endpoint_ids)
            if not allowed:
                raise ToolRouterInputError(
                    "At least one allowed endpoint is required for evalset generation."
                )
            if len(set(allowed)) != len(allowed):
                raise ToolRouterInputError(
                    "Allowed evalset endpoint identities must be unique."
                )
            available = {endpoint.id for endpoint in bundle.endpoints}
            unknown = sorted(set(allowed) - available)
            if unknown:
                raise ToolRouterInputError(
                    "Every allowed evalset endpoint must exist in the exact Source artifact."
                )
            selected_endpoint_ids = allowed
            allowed_set = set(allowed)
            bundle = replace(
                bundle,
                endpoints=[
                    endpoint
                    for endpoint in bundle.endpoints
                    if endpoint.id in allowed_set
                ],
            )
        normalized_hash = _sha256(normalized_path)
        target_id = f"source-{normalized_hash[:16]}"
        if request.allowed_endpoint_ids is not None:
            subset_hash = stable_hash(
                {"endpoint_ids": selected_endpoint_ids}
            )[:12]
            target_id = f"{target_id}-{subset_hash}"
        tasks = _build_source_grounded_tasks(
            target_id=target_id,
            bundle=bundle,
            categories=request.categories,
        )
        recipe_path = Path(__file__).with_name("recipes") / "v1.json"
        recipe_pack = load_recipe_pack(recipe_path)
        recipe_pack_hash = stable_hash(recipe_path.read_text(encoding="utf-8"))
        source_hashes = {
            "openapi_normalized.json": normalized_hash,
            "recipes/v1.json": _sha256(recipe_path),
        }
        if request.allowed_endpoint_ids is not None:
            source_hashes["allowed_endpoint_ids"] = stable_hash(
                selected_endpoint_ids
            )
        inputs = ExperimentInputs(
            bundles={target_id: bundle},
            tasks_by_target={target_id: tuple(tasks)},
            source_tasks_by_id={str(task["id"]): task for task in tasks},
            source_locations_by_target={target_id: "corpus_uploaded_api_collection"},
            source_hashes=source_hashes,
            bundle_hashes={
                target_id: (
                    source_hashes["openapi_normalized.json"]
                    if request.allowed_endpoint_ids is None
                    else stable_hash(
                        {
                            "normalized": source_hashes[
                                "openapi_normalized.json"
                            ],
                            "allowed_endpoint_ids": selected_endpoint_ids,
                        }
                    )
                )
            },
            reference_endpoints_by_id={
                endpoint.id: endpoint for endpoint in bundle.endpoints
            },
        )
        try:
            generator_digest = self._model_digest_resolver(
                self.settings.generator_model
            )
            reviewer_digest = self._model_digest_resolver(
                self.settings.reviewer_model
            )
        except Exception as error:
            raise ToolRouterDependencyError(
                "The configured ToolRouter model identity is unavailable for "
                f"provider {self.settings.model_provider}: {error}"
            ) from error
        if not generator_digest or not reviewer_digest:
            raise ToolRouterDependencyError(
                "The configured ToolRouter models must expose stable identities."
            )
        # User labels never become path segments. The compact stable token is
        # important because the engine's immutable cache keys are long and
        # Windows still commonly enforces the legacy path limit.
        run_dir = artifact_dir / "e" / _evalset_storage_token(evalset_id)
        cache_dir = artifact_dir / "c"
        config = ExperimentConfig(
            run_id=evalset_id,
            targets=(target_id,),
            generator_model=self.settings.generator_model,
            reviewer_model=self.settings.reviewer_model,
            require_independent_models=self.settings.model_provider != "openai",
            generator_model_digest=generator_digest,
            reviewer_model_digest=reviewer_digest,
            ollama_url=self.settings.ollama_url,
            categories=tuple(request.categories),
            context_strategies=(ContextStrategy.MINIMAL,),
            tasks_per_category=request.tasks_per_category,
            timeout_seconds=self.settings.evalset_timeout_seconds,
            max_generation_attempts=request.max_generation_attempts,
            max_review_attempts=request.max_review_attempts,
        )
        generator = OllamaGenerationClient(
            model=config.generator_model,
            model_digest=config.generator_model_digest,
            cache_dir=cache_dir,
            audit_path=run_dir / "generation_model_audit.jsonl",
            url=config.ollama_url,
            timeout_seconds=config.timeout_seconds,
            temperature=config.generation_temperature,
            seed=config.seed,
            num_ctx=config.num_ctx,
            num_predict=config.generation_num_predict,
            keep_alive=config.generation_keep_alive,
            transport=self._generation_transport,
        )
        reviewer = OllamaSemanticReviewClient(
            model=config.reviewer_model,
            model_digest=config.reviewer_model_digest,
            cache_dir=cache_dir,
            audit_path=run_dir / "review_model_audit.jsonl",
            url=config.ollama_url,
            timeout_seconds=config.timeout_seconds,
            seed=config.seed,
            num_ctx=config.num_ctx,
            num_predict=config.review_num_predict,
            keep_alive=config.review_keep_alive,
            transport=self._review_transport,
            require_independent_model=self.settings.model_provider != "openai",
        )
        try:
            summary = EvalsetFactoryExperiment(
                config=config,
                recipe_pack=recipe_pack,
                recipe_pack_hash=recipe_pack_hash,
                inputs=inputs,
                generator=generator,
                reviewer=reviewer,
                run_dir=run_dir,
            ).run()
        except (OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
            raise ToolRouterArtifactError(
                f"The evalset factory run could not be created or resumed: {error}"
            ) from error

        metrics = dict(summary["configurations"][ContextStrategy.MINIMAL.value])
        accepted_count = int(metrics.get("accepted_keys") or 0)
        expected_count = int(summary.get("expected_completion_keys") or 0)
        completed_count = int(summary.get("completed_keys") or 0)
        terminal_counts = {
            str(key): int(value)
            for key, value in dict(
                summary.get("terminal_status_counts") or {}
            ).items()
        }
        accepted_tasks: tuple[dict[str, Any], ...] = ()
        if accepted_count:
            tasks_export, export_manifest = build_export(
                run_dir=run_dir,
                strategy=ContextStrategy.MINIMAL.value,
                target_id=target_id,
            )
            write_export(
                tasks_path=run_dir / "accepted_tasks.json",
                manifest_path=run_dir / "accepted_manifest.json",
                tasks=tasks_export,
                manifest=export_manifest,
            )
            accepted_tasks = tuple(dict(task) for task in tasks_export)
        failure_statuses = {
            "generation_failed",
            "semantic_review_failed",
        }
        if accepted_count:
            status = "ready"
        elif failure_statuses.intersection(terminal_counts):
            status = "failed"
        else:
            status = "quarantined"
        return EvalsetResult(
            evalset_id=evalset_id,
            status=status,
            run_dir=run_dir,
            completed_count=completed_count,
            expected_count=expected_count,
            accepted_count=accepted_count,
            quarantined_count=max(completed_count - accepted_count, 0),
            terminal_status_counts=terminal_counts,
            offline_tokens=int(metrics.get("offline_tokens") or 0),
            generator_model=config.generator_model,
            generator_model_digest=config.generator_model_digest,
            reviewer_model=config.reviewer_model,
            reviewer_model_digest=config.reviewer_model_digest,
            accepted_tasks=accepted_tasks,
            summary=dict(summary),
        )

    def _provider(self) -> EmbeddingProvider:
        if self._embedding_provider is not None:
            return self._embedding_provider
        try:
            self._embedding_provider = SentenceTransformerEmbeddingProvider(
                self.settings.embedding_model,
                device=self.settings.embedding_device,
                batch_size=self.settings.embedding_batch_size,
                revision=self.settings.embedding_revision,
                local_files_only=self.settings.embedding_local_files_only,
            )
        except Exception as error:
            raise ToolRouterDependencyError(
                f"The configured local embedding model is unavailable: {error}"
            ) from error
        return self._embedding_provider

    def _resolve_ollama_model_digest(self, model: str) -> str:
        try:
            listing = ollama.Client(host=self.settings.ollama_url).list()
        except Exception as error:
            raise ToolRouterDependencyError(
                f"Ollama model discovery failed at {self.settings.ollama_url}: {error}"
            ) from error
        for value in listing.models:
            if value.model == model or value.model == f"{model}:latest":
                return str(value.digest or "")
        raise ToolRouterDependencyError(
            f"The required local Ollama model is not installed: {model}"
        )


def _validation_status(manifest: dict[str, Any]) -> str:
    specs = list(manifest.get("specs") or [])
    if specs and all(bool(spec.get("spec_validation", {}).get("ok")) for spec in specs):
        return "valid"
    if specs and all(
        bool(spec.get("repaired_validation", {}).get("ok")) for spec in specs
    ):
        return "repaired"
    return "invalid"


def _managed_parameter_identities(
    values: tuple[ManagedParameter, ...],
) -> tuple[tuple[str, str], ...]:
    identities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        name = value.name.strip()
        location = value.location.strip().casefold()
        if not name or location not in {"header", "path", "query", "body"}:
            raise ToolRouterInputError("Managed parameter identities are invalid.")
        identity = (location, name.casefold())
        if identity in seen:
            raise ToolRouterInputError("Managed parameter identities must be unique.")
        seen.add(identity)
        identities.append((location, name))
    return tuple(identities)


def _managed_parameter_view(
    index: SemanticGraphIndex,
    managed_parameters: tuple[tuple[str, str], ...],
) -> SemanticGraphIndex:
    if not managed_parameters:
        return index
    managed = {
        (location.casefold(), name.casefold())
        for location, name in managed_parameters
    }
    cards = []
    for card in index.cards:
        required_inputs = card.facets.get("required_inputs")
        if not isinstance(required_inputs, list):
            cards.append(card)
            continue
        filtered = [
            value
            for value in required_inputs
            if not isinstance(value, Mapping)
            or (
                str(value.get("location") or "").strip().casefold(),
                str(value.get("name") or "").strip().casefold(),
            )
            not in managed
        ]
        cards.append(
            card
            if len(filtered) == len(required_inputs)
            else replace(card, facets={**card.facets, "required_inputs": filtered})
        )
    return replace(index, cards=cards)


SOURCE_GROUNDED_EVALSET_CATEGORIES = frozenset(
    {
        "exact_spec_reference",
        "paraphrase",
        "non_exact_wording",
        "low_lexical_overlap",
        "typo_or_noisy",
        "verbose_or_indirect",
    }
)


def _build_source_grounded_tasks(
    *,
    target_id: str,
    bundle,
    categories: tuple[str, ...],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for category in categories:
        for endpoint in sorted(bundle.endpoints, key=lambda value: value.id):
            source_query = endpoint.summary or (
                f"{endpoint.operation_class} {' '.join(endpoint.resources)}"
            )
            task_id = "corpus_" + stable_hash(
                {
                    "target_id": target_id,
                    "category": category,
                    "endpoint_id": endpoint.id,
                }
            )[:20]
            tasks.append(
                {
                    "id": task_id,
                    "query": source_query,
                    "router_query": source_query,
                    "expected_decision_type": "ROUTE",
                    "expected_endpoint_sequence": [endpoint.id],
                    "allowed_alternatives": [],
                    "expected_required_params": {},
                    "provided_params": {},
                    "conversation_context": {},
                    "evalset": {
                        "schema_version": 1,
                        "query_category": category,
                        "score_scope": "corpus_source_grounded_seed",
                        "origin": "corpus_source_grounded_seed_v1",
                        "freshness": "generated_for_source_revision",
                        "authoritative_user_traffic": False,
                    },
                    "validation": {"target_id": target_id},
                }
            )
    return tasks


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evalset_storage_token(evalset_id: str) -> str:
    return hashlib.sha256(evalset_id.encode("utf-8")).hexdigest()[:20]


__all__ = ["ToolRouterAdapter"]
