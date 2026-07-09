from __future__ import annotations

from routedeck_core import RouteDeckOperationPolicy

from backend.services.corpus.manifest import ACTION_TARGETS


class CorpusOperationPolicy(RouteDeckOperationPolicy):
    """Maps Corpus app actions into generic RouteDeck operations."""

    def __init__(self) -> None:
        super().__init__(
            target_nodes_by_action=ACTION_TARGETS,
            review_action_ids=[
                "execution.plan",
                "execution.provide_input",
                "approval.approve",
                "approval.reject",
                "knowledge.generate",
                "memory.save",
                "learning.approve",
                "learning.reject",
                "qa.run",
            ],
            safety_class_by_category={
                "execution": "write_external",
                "deployment": "draft",
                "feedback": "draft",
                "learning": "draft",
                "auth": "credential",
            },
        )
