"""Select product features; RouteDeck owns compilation and validation."""

import json
from dataclasses import fields

from routedeck_core.app import Application, CompiledApplication, Feature, compile_app

from .features.agents.contracts import AGENTS_HOME_REF
from .features.agents.feature import create_agents_feature
from .features.designer.contracts import DESIGNER_HOME_REF
from .features.designer.feature import create_designer_feature
from .features.builder.contracts import BUILDER_HOME_REF
from .features.builder.feature import create_builder_feature
from .features.builder.policies import BUILDER_SANDBOX_POLICIES
from .features.sandbox.contracts import SANDBOX_HOME_REF
from .features.sandbox.feature import create_sandbox_feature
from .features.evaluation.contracts import EVALUATION_HOME_REF
from .features.evaluation.feature import create_evaluation_feature
from .features.channels.contracts import CHANNELS_HOME_REF
from .features.channels.feature import create_channels_feature
from .features.operations.contracts import OPERATIONS_HOME_REF
from .features.operations.feature import create_operations_feature
from .features.lounge.declarations import VERIFICATION_PENDING_REF
from .features.lounge.feature import LOUNGE_NODE, create_lounge_feature
from .features.sources.feature import SOURCES_FEATURE
from .features.sources.declarations import SOURCES_API_INTAKE_REF, SOURCES_API_REF, SOURCES_HOME_REF
from .features.workspace.contracts import HOME_REF
from .features.workspace.feature import create_workspace_feature


LOUNGE_FEATURE = create_lounge_feature(HOME_REF)
WORKSPACE_FEATURE = create_workspace_feature(
    agents_home_ref=AGENTS_HOME_REF,
    sources_home_ref=SOURCES_HOME_REF,
    verification_ref=VERIFICATION_PENDING_REF,
)
AGENTS_FEATURE = create_agents_feature(
    HOME_REF, SOURCES_HOME_REF, SOURCES_API_INTAKE_REF, SOURCES_API_REF, DESIGNER_HOME_REF, BUILDER_HOME_REF, SANDBOX_HOME_REF,
    EVALUATION_HOME_REF, CHANNELS_HOME_REF,
    OPERATIONS_HOME_REF,
)
DESIGNER_FEATURE = create_designer_feature(
    AGENTS_HOME_REF,
    BUILDER_HOME_REF,
    SOURCES_API_REF,
)
BUILDER_FEATURE = create_builder_feature(AGENTS_HOME_REF, SANDBOX_HOME_REF)
SANDBOX_FEATURE = create_sandbox_feature(AGENTS_HOME_REF, EVALUATION_HOME_REF)
BUILDER_SANDBOX_FEATURE = Feature(
    namespace="builder+sandbox",
    nodes=BUILDER_FEATURE.nodes + SANDBOX_FEATURE.nodes,
    agent_policies=BUILDER_SANDBOX_POLICIES,
    policy_refs=tuple(policy.ref for policy in BUILDER_SANDBOX_POLICIES),
)
EVALUATION_FEATURE = create_evaluation_feature(
    AGENTS_HOME_REF,
    BUILDER_HOME_REF,
    CHANNELS_HOME_REF,
)
CHANNELS_FEATURE = create_channels_feature(
    AGENTS_HOME_REF,
    BUILDER_HOME_REF,
    EVALUATION_HOME_REF,
    OPERATIONS_HOME_REF,
)
OPERATIONS_FEATURE = create_operations_feature(AGENTS_HOME_REF)


CORPUS_APP = Application(
    name="corpus",
    entry_node=LOUNGE_NODE.ref,
    features=(LOUNGE_FEATURE, WORKSPACE_FEATURE, AGENTS_FEATURE, DESIGNER_FEATURE, BUILDER_SANDBOX_FEATURE, EVALUATION_FEATURE, CHANNELS_FEATURE, OPERATIONS_FEATURE, SOURCES_FEATURE),
)


class _CorpusCompiledApplication(CompiledApplication):
    """Stabilize unordered contract collections at RouteDeck's document seam."""

    def contract_documents(self) -> dict[str, str]:
        documents = super().contract_documents()
        navgraph = json.loads(documents["compiled-navgraph.json"])
        stable_navgraph = _stable_unordered_contract_arrays(navgraph)
        documents["compiled-navgraph.json"] = (
            json.dumps(
                stable_navgraph,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n"
        )
        return documents


def _stable_unordered_contract_arrays(value):
    if isinstance(value, dict):
        return {
            key: (
                sorted(item.value if hasattr(item, "value") else item for item in item_value)
                if key == "allowed_sources" and isinstance(item_value, list)
                else _stable_unordered_contract_arrays(item_value)
            )
            for key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_stable_unordered_contract_arrays(item) for item in value]
    return value


def compile_corpus_app() -> CompiledApplication:
    compiled = compile_app(CORPUS_APP)
    return _CorpusCompiledApplication(
        **{field.name: getattr(compiled, field.name) for field in fields(compiled)}
    )


__all__ = [
    "AGENTS_FEATURE",
    "CORPUS_APP",
    "DESIGNER_FEATURE",
    "BUILDER_FEATURE",
    "BUILDER_SANDBOX_FEATURE",
    "SANDBOX_FEATURE",
    "EVALUATION_FEATURE",
    "CHANNELS_FEATURE",
    "OPERATIONS_FEATURE",
    "LOUNGE_FEATURE",
    "WORKSPACE_FEATURE",
    "compile_corpus_app",
]
