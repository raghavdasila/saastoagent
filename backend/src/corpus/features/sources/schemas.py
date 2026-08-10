from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from routedeck_core.contracts.operations import OperationSource


class RetrySourceArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=16, max_length=16)


class GraphStageArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=16, max_length=16)
    revision_id: str = Field(min_length=16, max_length=16)
    stage_id: str = Field(min_length=1, max_length=64)


class ProposeContractRevisionArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    revision_id: str | None = Field(default=None, min_length=16, max_length=16)

    @model_validator(mode="after")
    def exact_or_current(self) -> "ProposeContractRevisionArguments":
        if (self.source_id is None) != (self.revision_id is None):
            raise ValueError("Source and revision must be supplied together.")
        return self


class ApproveContractRevisionArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_ref: str = Field(min_length=1, max_length=128)


class TestApiConnectionArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    source_revision_id: str | None = Field(default=None, min_length=16, max_length=16)
    connection_profile_id: str | None = Field(default=None, min_length=16, max_length=16)
    operation_id: str = Field(pattern=r"^GetProduct(?:Types|Tags)$")

    @model_validator(mode="after")
    def exact_or_current(self) -> "TestApiConnectionArguments":
        supplied = (
            self.source_id,
            self.source_revision_id,
            self.connection_profile_id,
        )
        if any(value is not None for value in supplied) and not all(
            value is not None for value in supplied
        ):
            raise ValueError("Source, revision, and profile must be supplied together.")
        return self


class ExecuteRoutedApiArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(min_length=16, max_length=16)


class SaveApiOperationCurationArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str | None = Field(default=None, min_length=16, max_length=16)
    source_revision_id: str | None = Field(default=None, min_length=16, max_length=16)
    inventory_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    included_operation_ids: tuple[str, ...] = Field(max_length=5_000)
    excluded_operation_ids: tuple[str, ...] | None = Field(default=None, max_length=5_000)
    expected_current_curation_id: str | None = Field(
        default=None, min_length=16, max_length=16
    )

    @model_validator(mode="after")
    def exact_or_current(self) -> "SaveApiOperationCurationArguments":
        exact_identity = (
            self.source_id,
            self.source_revision_id,
            self.inventory_fingerprint,
        )
        if any(value is not None for value in exact_identity):
            if not all(value is not None for value in exact_identity) or (
                self.excluded_operation_ids is None
            ):
                raise ValueError(
                    "Exact curation requires Source, revision, fingerprint, and exclusions."
                )
        elif self.expected_current_curation_id is not None:
            raise ValueError(
                "Current curation resolves its comparison identity on the server."
            )
        if not self.included_operation_ids:
            raise ValueError("At least one operation must be included.")
        return self


def save_api_operation_curation_arguments(
    arguments: Mapping[str, Any],
    source: OperationSource,
) -> SaveApiOperationCurationArguments:
    values = dict(arguments)
    if source is OperationSource.AGENT:
        # Owner, Source, revision, fingerprint, CAS, and the exhaustive
        # complement are server-owned for model-selected curation. The model
        # supplies only the user's explicit inclusion decision; Corpus resolves
        # the exact current inventory and classifies every other item excluded.
        values = {
            key: values[key]
            for key in ("included_operation_ids",)
            if key in values
        }
    return SaveApiOperationCurationArguments.model_validate(values)


__all__ = [
    "ApproveContractRevisionArguments",
    "GraphStageArguments",
    "ExecuteRoutedApiArguments",
    "ProposeContractRevisionArguments",
    "RetrySourceArguments",
    "SaveApiOperationCurationArguments",
    "save_api_operation_curation_arguments",
    "TestApiConnectionArguments",
]
