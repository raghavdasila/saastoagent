from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict
from pathlib import Path

from agent_delivery_runtime.domain import (
    Activation,
    DeployableAgentBundle,
    DeploymentRevision,
    DeploymentStatus,
    InteractionRecord,
    PublicSession,
    WebChannel,
)


class CorpusLocalDeliveryStore:
    """Corpus-owned durable provider for the neutral delivery store port."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS corpus_delivery_channels (
                  channel_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                  slug TEXT NOT NULL UNIQUE, enabled INTEGER NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corpus_delivery_deployments (
                  deployment_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL,
                  bundle_json TEXT NOT NULL, status TEXT NOT NULL,
                  requested_at TEXT NOT NULL, completed_at TEXT,
                  failure_code TEXT, failure_message TEXT, proof_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corpus_delivery_activations (
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  activation_id TEXT NOT NULL UNIQUE, channel_id TEXT NOT NULL,
                  deployment_id TEXT NOT NULL, reason TEXT NOT NULL,
                  activated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corpus_delivery_sessions (
                  session_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL,
                  activation_id TEXT NOT NULL, deployment_id TEXT NOT NULL,
                  runtime_session_id TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corpus_delivery_interactions (
                  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                  interaction_id TEXT NOT NULL UNIQUE, session_id TEXT NOT NULL,
                  deployment_id TEXT NOT NULL, input_summary TEXT NOT NULL,
                  output_summary TEXT NOT NULL, status TEXT NOT NULL,
                  started_at TEXT NOT NULL, completed_at TEXT NOT NULL,
                  trace_json TEXT NOT NULL
                );
            """)

    def _db(self):
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def create_channel(self, value: WebChannel) -> None:
        with self._lock, self._db() as db:
            db.execute(
                "INSERT INTO corpus_delivery_channels VALUES (?,?,?,?,?)",
                (value.channel_id, value.name, value.slug, int(value.enabled), value.created_at),
            )

    def list_channels(self) -> list[WebChannel]:
        with self._lock, self._db() as db:
            rows = db.execute("SELECT * FROM corpus_delivery_channels ORDER BY created_at").fetchall()
        return [self._channel(row) for row in rows]

    def channel(self, *, channel_id=None, slug=None):
        field, value = ("channel_id", channel_id) if channel_id is not None else ("slug", slug)
        with self._lock, self._db() as db:
            row = db.execute(f"SELECT * FROM corpus_delivery_channels WHERE {field}=?", (value,)).fetchone()
        return self._channel(row) if row else None

    def set_channel_enabled(self, channel_id: str, enabled: bool) -> None:
        with self._lock, self._db() as db:
            result = db.execute(
                "UPDATE corpus_delivery_channels SET enabled=? WHERE channel_id=?",
                (int(enabled), channel_id),
            )
            if result.rowcount != 1:
                raise KeyError("channel_not_found")

    def save_deployment(self, value: DeploymentRevision) -> None:
        with self._lock, self._db() as db:
            db.execute(
                "INSERT INTO corpus_delivery_deployments VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    value.deployment_id, value.channel_id,
                    json.dumps(asdict(value.bundle), sort_keys=True, separators=(",", ":")),
                    value.status.value, value.requested_at, value.completed_at,
                    value.failure_code, value.failure_message,
                    json.dumps(value.proof, sort_keys=True, separators=(",", ":")),
                ),
            )

    def update_deployment(self, value: DeploymentRevision) -> None:
        with self._lock, self._db() as db:
            result = db.execute(
                "UPDATE corpus_delivery_deployments SET status=?,completed_at=?,failure_code=?,failure_message=?,proof_json=? WHERE deployment_id=?",
                (
                    value.status.value, value.completed_at, value.failure_code,
                    value.failure_message,
                    json.dumps(value.proof, sort_keys=True, separators=(",", ":")),
                    value.deployment_id,
                ),
            )
            if result.rowcount != 1:
                raise KeyError("deployment_not_found")

    def claim_deployment(self, deployment_id: str):
        with self._lock, self._db() as db:
            result = db.execute(
                "UPDATE corpus_delivery_deployments SET status=? WHERE deployment_id=? AND status=?",
                (DeploymentStatus.VERIFYING.value, deployment_id, DeploymentStatus.QUEUED.value),
            )
            if result.rowcount != 1:
                return None
            row = db.execute(
                "SELECT * FROM corpus_delivery_deployments WHERE deployment_id=?",
                (deployment_id,),
            ).fetchone()
        return self._deployment(row)

    def finalize_ready(self, value: DeploymentRevision, activation: Activation) -> bool:
        with self._lock, self._db() as db:
            result = db.execute(
                "UPDATE corpus_delivery_deployments SET status=?,completed_at=?,failure_code=NULL,failure_message=NULL,proof_json=? WHERE deployment_id=? AND status=?",
                (
                    DeploymentStatus.READY.value, value.completed_at,
                    json.dumps(value.proof, sort_keys=True, separators=(",", ":")),
                    value.deployment_id, DeploymentStatus.VERIFYING.value,
                ),
            )
            if result.rowcount != 1:
                return False
            newer = db.execute(
                "SELECT COUNT(*) FROM corpus_delivery_deployments WHERE channel_id=? AND requested_at>? AND status IN (?,?,?)",
                (
                    value.channel_id, value.requested_at, DeploymentStatus.QUEUED.value,
                    DeploymentStatus.VERIFYING.value, DeploymentStatus.READY.value,
                ),
            ).fetchone()[0]
            if newer:
                return False
            self._insert_activation(db, activation)
            return True

    def deployment(self, deployment_id: str):
        with self._lock, self._db() as db:
            row = db.execute(
                "SELECT * FROM corpus_delivery_deployments WHERE deployment_id=?",
                (deployment_id,),
            ).fetchone()
        return self._deployment(row) if row else None

    def deployments_for_channel(self, channel_id: str):
        with self._lock, self._db() as db:
            rows = db.execute(
                "SELECT * FROM corpus_delivery_deployments WHERE channel_id=? ORDER BY requested_at DESC",
                (channel_id,),
            ).fetchall()
        return [self._deployment(row) for row in rows]

    def activate(self, value: Activation) -> None:
        with self._lock, self._db() as db:
            self._insert_activation(db, value)

    def _insert_activation(self, db, value: Activation) -> None:
        db.execute(
            "INSERT INTO corpus_delivery_activations(activation_id,channel_id,deployment_id,reason,activated_at) VALUES (?,?,?,?,?)",
            (value.activation_id, value.channel_id, value.deployment_id, value.reason, value.activated_at),
        )

    def current_activation(self, channel_id: str):
        with self._lock, self._db() as db:
            row = db.execute(
                "SELECT activation_id,channel_id,deployment_id,reason,activated_at FROM corpus_delivery_activations WHERE channel_id=? ORDER BY sequence DESC LIMIT 1",
                (channel_id,),
            ).fetchone()
        return Activation(**dict(row)) if row else None

    def save_session(self, value: PublicSession) -> None:
        with self._lock, self._db() as db:
            db.execute(
                "INSERT INTO corpus_delivery_sessions VALUES (?,?,?,?,?,?)",
                tuple(asdict(value).values()),
            )

    def session(self, session_id: str):
        with self._lock, self._db() as db:
            row = db.execute(
                "SELECT * FROM corpus_delivery_sessions WHERE session_id=?", (session_id,)
            ).fetchone()
        return PublicSession(**dict(row)) if row else None

    def save_interaction(self, value: InteractionRecord) -> None:
        with self._lock, self._db() as db:
            db.execute(
                "INSERT INTO corpus_delivery_interactions(interaction_id,session_id,deployment_id,input_summary,output_summary,status,started_at,completed_at,trace_json) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    value.interaction_id, value.session_id, value.deployment_id,
                    value.input_summary, value.output_summary, value.status,
                    value.started_at, value.completed_at,
                    json.dumps(value.trace, sort_keys=True, separators=(",", ":")),
                ),
            )

    def interactions(self, interaction_id=None):
        where, parameters = (" WHERE interaction_id=?", (interaction_id,)) if interaction_id else ("", ())
        with self._lock, self._db() as db:
            rows = db.execute(
                "SELECT * FROM corpus_delivery_interactions" + where + " ORDER BY sequence DESC",
                parameters,
            ).fetchall()
        return [self._interaction(row) for row in rows]

    def session_interactions(self, session_id: str, after=None):
        with self._lock, self._db() as db:
            if after is None:
                rows = db.execute(
                    "SELECT * FROM corpus_delivery_interactions WHERE session_id=? ORDER BY sequence",
                    (session_id,),
                ).fetchall()
            else:
                cursor = db.execute(
                    "SELECT sequence FROM corpus_delivery_interactions WHERE session_id=? AND interaction_id=?",
                    (session_id, after),
                ).fetchone()
                if cursor is None:
                    return []
                rows = db.execute(
                    "SELECT * FROM corpus_delivery_interactions WHERE session_id=? AND sequence>? ORDER BY sequence",
                    (session_id, cursor[0]),
                ).fetchall()
        return [self._interaction(row) for row in rows]

    @staticmethod
    def _channel(row):
        value = dict(row)
        value["enabled"] = bool(value["enabled"])
        return WebChannel(**value)

    @staticmethod
    def _deployment(row):
        value = dict(row)
        bundle = DeployableAgentBundle(**json.loads(value.pop("bundle_json")))
        proof = json.loads(value.pop("proof_json"))
        value["status"] = DeploymentStatus(value["status"])
        return DeploymentRevision(bundle=bundle, proof=proof, **value)

    @staticmethod
    def _interaction(row):
        value = dict(row)
        value.pop("sequence")
        value["trace"] = json.loads(value.pop("trace_json"))
        return InteractionRecord(**value)


__all__ = ["CorpusLocalDeliveryStore"]
