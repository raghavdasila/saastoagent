from __future__ import annotations

from pathlib import Path

from agent_delivery_runtime.domain import DeploymentMode, SessionPurpose
from agent_delivery_runtime.store import DeliveryStore


class CorpusLocalDeliveryStore(DeliveryStore):
    """Corpus-owned durable store using the shared v0.2 deployment-mode schema.

    The import is deliberately one-way and idempotent. Existing v0.1 Corpus
    Delivery identities are copied into neutral Delivery targets without
    rewriting or deleting the retained legacy tables.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(path.resolve())
        self._import_corpus_v01_delivery()

    def _import_corpus_v01_delivery(self) -> None:
        with self._connect() as db:
            tables = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            required = {
                "corpus_delivery_channels",
                "corpus_delivery_deployments",
                "corpus_delivery_activations",
                "corpus_delivery_sessions",
                "corpus_delivery_interactions",
            }
            if not required.issubset(tables):
                return
            db.execute(
                """INSERT OR IGNORE INTO channels
                   (channel_id, name, slug, enabled, created_at)
                   SELECT channel_id, name, slug, enabled, created_at
                   FROM corpus_delivery_channels"""
            )
            db.execute(
                """INSERT OR IGNORE INTO deployment_targets_v2
                   (target_id, mode, owner_scope, channel_id, name, created_at)
                   SELECT channel_id, ?, 'channel:' || channel_id, channel_id, name, created_at
                   FROM corpus_delivery_channels""",
                (DeploymentMode.DELIVERY.value,),
            )
            db.execute(
                """INSERT OR IGNORE INTO deployment_revisions_v2
                   (deployment_id, target_id, mode, request_key, bundle_json, status,
                    requested_at, completed_at, failure_code, failure_message, proof_json)
                   SELECT deployment_id, channel_id, ?, NULL, bundle_json, status,
                          requested_at, completed_at, failure_code, failure_message, proof_json
                   FROM corpus_delivery_deployments""",
                (DeploymentMode.DELIVERY.value,),
            )
            db.execute(
                """INSERT OR IGNORE INTO activations_v2
                   (activation_id, target_id, deployment_id, reason, activated_at)
                   SELECT activation_id, channel_id, deployment_id, reason, activated_at
                   FROM corpus_delivery_activations"""
            )
            db.execute(
                """INSERT OR IGNORE INTO agent_sessions_v2
                   (session_id, target_id, activation_id, deployment_id, runtime_session_id,
                    created_at, mode, purpose, owner_scope)
                   SELECT session_id, channel_id, activation_id, deployment_id,
                          runtime_session_id, created_at, ?, ?, NULL
                   FROM corpus_delivery_sessions""",
                (
                    DeploymentMode.DELIVERY.value,
                    SessionPurpose.DELIVERED_CONVERSATION.value,
                ),
            )
            db.execute(
                """INSERT OR IGNORE INTO agent_interactions_v2
                   (interaction_id, session_id, deployment_id, input_summary, output_summary,
                    status, started_at, completed_at, trace_json, mode, purpose)
                   SELECT interaction_id, session_id, deployment_id, input_summary,
                          output_summary, status, started_at, completed_at, trace_json, ?, ?
                   FROM corpus_delivery_interactions""",
                (
                    DeploymentMode.DELIVERY.value,
                    SessionPurpose.DELIVERED_CONVERSATION.value,
                ),
            )


__all__ = ["CorpusLocalDeliveryStore"]
