from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


EVALSET_FACTORY_SCHEMA_VERSION = 1

QUERY_CATEGORIES = (
    "exact_spec_reference",
    "paraphrase",
    "non_exact_wording",
    "low_lexical_overlap",
    "typo_or_noisy",
    "verbose_or_indirect",
    "negation_or_exclusion",
    "context_followup",
    "pronoun_or_reference",
    "correction_or_changed_constraint",
    "ambiguous_conflicting_intents",
    "ask_param",
    "independent_multi_intent",
    "dependent_multi_hop",
    "no_tool_target_isolation",
    "no_tool_global_catalog",
    "abstain_insufficient_evidence",
)

ALLOWED_DECISIONS = {
    "ROUTE",
    "ASK_DISAMBIGUATE",
    "ASK_PARAM",
    "NO_TOOL",
    "ABSTAIN",
}

ALLOWED_TRUTH_BASES = {
    "endpoint",
    "endpoint_plus_context",
    "endpoint_required_inputs",
    "endpoint_alternatives",
    "endpoint_sequence",
    "target_catalog_absence",
    "registry_catalog_absence",
    "insufficient_evidence",
}


class ContextStrategy(str, Enum):
    MINIMAL = "minimal"
    ENDPOINT_NEIGHBORHOOD = "endpoint_neighborhood"
    FULL_ENDPOINT = "full_endpoint"


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_duration_ns: int = 0
    load_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    eval_duration_ns: int = 0

    def __post_init__(self) -> None:
        for name in (
            "prompt_tokens",
            "completion_tokens",
            "total_duration_ns",
            "load_duration_ns",
            "prompt_eval_duration_ns",
            "eval_duration_ns",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "total_duration_ns": self.total_duration_ns,
            "load_duration_ns": self.load_duration_ns,
            "prompt_eval_duration_ns": self.prompt_eval_duration_ns,
            "eval_duration_ns": self.eval_duration_ns,
        }


@dataclass(frozen=True)
class Recipe:
    category: str
    description: str
    expected_decision: str
    truth_basis: str
    generation_rules: tuple[str, ...]
    deterministic_validators: tuple[str, ...]
    semantic_review_dimensions: tuple[str, ...]
    difficulty_pressures: tuple[str, ...]
    context_requirements: tuple[str, ...]
    prompt_version: int = 1

    def __post_init__(self) -> None:
        if self.category not in QUERY_CATEGORIES:
            raise ValueError(f"Unsupported evalset factory category: {self.category!r}")
        if self.expected_decision not in ALLOWED_DECISIONS:
            raise ValueError(f"Unsupported ToolRouter decision: {self.expected_decision!r}")
        if self.truth_basis not in ALLOWED_TRUTH_BASES:
            raise ValueError(f"Unsupported truth basis: {self.truth_basis!r}")
        if self.prompt_version <= 0:
            raise ValueError("prompt_version must be positive")
        if not self.generation_rules:
            raise ValueError(f"Recipe {self.category!r} requires generation rules")
        if not self.deterministic_validators:
            raise ValueError(f"Recipe {self.category!r} requires deterministic validators")
        if not self.semantic_review_dimensions:
            raise ValueError(f"Recipe {self.category!r} requires semantic review dimensions")
        if self.expected_decision == "NO_TOOL" and self.truth_basis not in {
            "target_catalog_absence",
            "registry_catalog_absence",
        }:
            raise ValueError("NO_TOOL recipes require explicit catalog-absence truth")
        forbidden_no_tool_evidence = {"retrieval_score", "score_margin", "ranking_margin"}
        if self.expected_decision == "NO_TOOL" and forbidden_no_tool_evidence.intersection(
            self.deterministic_validators
        ):
            raise ValueError("NO_TOOL cannot be inferred from retrieval scores or margins")


@dataclass(frozen=True)
class RecipePack:
    schema_version: int
    pack_id: str
    recipes: tuple[Recipe, ...]

    def __post_init__(self) -> None:
        if self.schema_version != EVALSET_FACTORY_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported recipe schema version {self.schema_version}; "
                f"expected {EVALSET_FACTORY_SCHEMA_VERSION}"
            )
        if not self.pack_id.strip():
            raise ValueError("Recipe pack requires a non-empty pack_id")
        categories = [recipe.category for recipe in self.recipes]
        duplicates = sorted({category for category in categories if categories.count(category) > 1})
        if duplicates:
            raise ValueError(f"Duplicate recipe categories: {duplicates}")
        missing = sorted(set(QUERY_CATEGORIES) - set(categories))
        extra = sorted(set(categories) - set(QUERY_CATEGORIES))
        if missing or extra:
            raise ValueError(f"Recipe pack category mismatch; missing={missing}, extra={extra}")

    def by_category(self, category: str) -> Recipe:
        for recipe in self.recipes:
            if recipe.category == category:
                return recipe
        raise KeyError(category)


@dataclass(frozen=True)
class FactoryCandidate:
    candidate_id: str
    target_id: str
    category: str
    query: str
    expected_decision: str
    expected_endpoint_sequence: tuple[str, ...] = ()
    allowed_alternatives: tuple[tuple[str, ...], ...] = ()
    expected_required_params: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    provided_params: Mapping[str, Any] = field(default_factory=dict)
    conversation_context: Mapping[str, Any] = field(default_factory=dict)
    truth_evidence: Mapping[str, Any] = field(default_factory=dict)
    source_endpoint_ids: tuple[str, ...] = ()
    generator_model: str = ""
    recipe_hash: str = ""
    context_strategy: ContextStrategy = ContextStrategy.ENDPOINT_NEIGHBORHOOD
    generation_usage: TokenUsage = field(default_factory=lambda: TokenUsage(0, 0))

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("Factory candidate requires a candidate_id")
        if not self.target_id.strip():
            raise ValueError("Factory candidate requires a target_id")
        if self.category not in QUERY_CATEGORIES:
            raise ValueError(f"Unsupported candidate category: {self.category!r}")
        if self.expected_decision not in ALLOWED_DECISIONS:
            raise ValueError(f"Unsupported candidate decision: {self.expected_decision!r}")
        if not self.query.strip():
            raise ValueError("Factory candidate query cannot be empty")


@dataclass(frozen=True)
class ReviewVerdict:
    candidate_id: str
    deterministic_pass: bool
    semantic_pass: bool | None
    accepted: bool
    reasons: tuple[str, ...]
    selected_endpoint_ids: tuple[str, ...] = ()
    category_fidelity: bool | None = None
    naturalness: bool | None = None
    reviewer_model: str = ""
    review_usage: TokenUsage = field(default_factory=lambda: TokenUsage(0, 0))
    review_input_hash: str = ""
    review_output_hash: str = ""

    def __post_init__(self) -> None:
        if self.accepted and not self.deterministic_pass:
            raise ValueError("A candidate cannot be accepted when deterministic validation failed")
        if self.accepted and self.semantic_pass is not True:
            raise ValueError("A candidate cannot be accepted without a positive semantic review")


def _string_tuple(value: Any, *, field_name: str, category: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Recipe {category!r} field {field_name!r} must be a list of non-empty strings")
    return tuple(item.strip() for item in value)


def _recipe_from_dict(value: Any) -> Recipe:
    if not isinstance(value, dict):
        raise ValueError("Every recipe must be a JSON object")
    category = str(value.get("category") or "")
    return Recipe(
        category=category,
        description=str(value.get("description") or "").strip(),
        expected_decision=str(value.get("expected_decision") or "").upper(),
        truth_basis=str(value.get("truth_basis") or ""),
        generation_rules=_string_tuple(value.get("generation_rules"), field_name="generation_rules", category=category),
        deterministic_validators=_string_tuple(
            value.get("deterministic_validators"),
            field_name="deterministic_validators",
            category=category,
        ),
        semantic_review_dimensions=_string_tuple(
            value.get("semantic_review_dimensions"),
            field_name="semantic_review_dimensions",
            category=category,
        ),
        difficulty_pressures=_string_tuple(
            value.get("difficulty_pressures", []),
            field_name="difficulty_pressures",
            category=category,
        ),
        context_requirements=_string_tuple(
            value.get("context_requirements", []),
            field_name="context_requirements",
            category=category,
        ),
        prompt_version=int(value.get("prompt_version", 1)),
    )


def load_recipe_pack(path: Path) -> RecipePack:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Recipe pack root must be a JSON object")
    recipes = raw.get("recipes")
    if not isinstance(recipes, list):
        raise ValueError("Recipe pack requires a recipes list")
    return RecipePack(
        schema_version=int(raw.get("schema_version", 0)),
        pack_id=str(raw.get("pack_id") or ""),
        recipes=tuple(_recipe_from_dict(value) for value in recipes),
    )
