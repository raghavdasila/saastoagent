from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path

from agent_execution_runtime import (
    AgentBuild, AgentRun, BuildLimits, ConnectionBinding, EvalCase, EvalRun,
    RecordEvent, RunStatus, WriteVerification,
)


class CorpusLocalAgentRuntimeStore:
    """Corpus-owned local persistence adapter for neutral runtime records."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._db() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS corpus_agent_builds (content_hash TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS corpus_agent_runs (run_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, updated_at TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS corpus_agent_events (run_id TEXT NOT NULL, sequence INTEGER NOT NULL, tenant_id TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(run_id, sequence));
                CREATE TABLE IF NOT EXISTS corpus_agent_eval_cases (case_id TEXT PRIMARY KEY, build_hash TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS corpus_agent_eval_runs (eval_run_id TEXT PRIMARY KEY, build_hash TEXT NOT NULL, payload TEXT NOT NULL);
            """)

    def _db(self):
        return sqlite3.connect(self.path, timeout=30)

    def save_build(self, value: AgentBuild) -> None:
        with self._lock, self._db() as db:
            existing = db.execute("SELECT payload FROM corpus_agent_builds WHERE content_hash=?", (value.content_hash,)).fetchone()
            payload = _dump(value)
            if existing is not None and existing[0] != payload:
                raise ValueError("corpus_runtime_build_hash_collision")
            db.execute("INSERT OR IGNORE INTO corpus_agent_builds VALUES(?,?)", (value.content_hash, payload))

    def get_build(self, content_hash: str) -> AgentBuild:
        with self._lock, self._db() as db:
            row = db.execute("SELECT payload FROM corpus_agent_builds WHERE content_hash=?", (content_hash,)).fetchone()
        if row is None:
            raise KeyError("build_not_found")
        value = json.loads(row[0])
        return AgentBuild(
            **{key: value[key] for key in ("build_id", "version", "name", "instructions", "model", "model_digest", "source_path", "source_hash", "schema_version")},
            allowed_operations=tuple(value["allowed_operations"]),
            preauthorized_write_operations=tuple(value["preauthorized_write_operations"]),
            connections=tuple(ConnectionBinding(**{**item, "operation_ids": tuple(item.get("operation_ids", ()))}) for item in value["connections"]),
            write_verifications=tuple(WriteVerification(**{**item, "response_path": tuple(item["response_path"])}) for item in value.get("write_verifications", ())),
            limits=BuildLimits(**value["limits"]),
        )

    def create_run(self, value: AgentRun) -> None:
        with self._lock, self._db() as db:
            db.execute("INSERT INTO corpus_agent_runs VALUES(?,?,?,?)", (value.run_id, value.tenant_id, value.updated_at, _dump(value)))

    def update_run(self, value: AgentRun) -> None:
        with self._lock, self._db() as db:
            cursor = db.execute("UPDATE corpus_agent_runs SET updated_at=?,payload=? WHERE run_id=? AND tenant_id=?", (value.updated_at, _dump(value), value.run_id, value.tenant_id))
            if cursor.rowcount != 1:
                raise KeyError("run_not_found")

    def append_event(self, run_id: str, value: RecordEvent) -> None:
        with self._lock, self._db() as db:
            tenant = db.execute("SELECT tenant_id FROM corpus_agent_runs WHERE run_id=?", (run_id,)).fetchone()
            if tenant is None:
                raise KeyError("run_not_found")
            db.execute("INSERT INTO corpus_agent_events VALUES(?,?,?,?)", (run_id, value.sequence, tenant[0], _dump(value)))

    def get_run(self, tenant_id: str, run_id: str) -> AgentRun:
        with self._lock, self._db() as db:
            row = db.execute("SELECT payload FROM corpus_agent_runs WHERE run_id=? AND tenant_id=?", (run_id, tenant_id)).fetchone()
        if row is None:
            raise KeyError("run_not_found")
        value = json.loads(row[0])
        value["status"] = RunStatus(value["status"])
        return AgentRun(**value)

    def events(self, tenant_id: str, run_id: str) -> tuple[RecordEvent, ...]:
        with self._lock, self._db() as db:
            rows = db.execute("SELECT payload FROM corpus_agent_events WHERE run_id=? AND tenant_id=? ORDER BY sequence", (run_id, tenant_id)).fetchall()
        return tuple(RecordEvent(**json.loads(row[0])) for row in rows)

    def list_runs(self, tenant_id: str) -> tuple[AgentRun, ...]:
        with self._lock, self._db() as db:
            rows = db.execute("SELECT payload FROM corpus_agent_runs WHERE tenant_id=? ORDER BY updated_at DESC", (tenant_id,)).fetchall()
        return tuple(AgentRun(**{**value, "status": RunStatus(value["status"])}) for value in (json.loads(row[0]) for row in rows))

    def save_case(self, value: EvalCase) -> None:
        with self._lock, self._db() as db:
            db.execute("INSERT INTO corpus_agent_eval_cases VALUES(?,?,?)", (value.case_id, value.build_hash, _dump(value)))

    def get_case(self, case_id: str) -> EvalCase:
        with self._lock, self._db() as db:
            row = db.execute("SELECT payload FROM corpus_agent_eval_cases WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            raise KeyError("case_not_found")
        value = json.loads(row[0])
        for name in ("expected_operations", "forbidden_operations", "required_response_fields"):
            value[name] = tuple(value[name])
        return EvalCase(**value)

    def save_eval_run(self, value: EvalRun) -> None:
        with self._lock, self._db() as db:
            db.execute("INSERT INTO corpus_agent_eval_runs VALUES(?,?,?)", (value.eval_run_id, value.build_hash, _dump(value)))

    def eval_runs(self, build_hash: str) -> tuple[EvalRun, ...]:
        with self._lock, self._db() as db:
            rows = db.execute("SELECT payload FROM corpus_agent_eval_runs WHERE build_hash=? ORDER BY eval_run_id", (build_hash,)).fetchall()
        return tuple(EvalRun(**{**value, "reasons": tuple(value["reasons"])}) for value in (json.loads(row[0]) for row in rows))


def _dump(value) -> str:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"))


def _plain(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {item.name: _plain(getattr(value, item.name)) for item in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


__all__ = ["CorpusLocalAgentRuntimeStore"]
