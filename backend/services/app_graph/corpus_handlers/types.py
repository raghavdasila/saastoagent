from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import User
from backend.core.schemas import AppGraphState, EntryGraphMessage
from backend.services.app_graph.corpus_context import CorpusContextQueries
from routedeck_core import RouteDeckActionResult


CorpusActionResult: TypeAlias = RouteDeckActionResult[AppGraphState, EntryGraphMessage]


@dataclass(slots=True)
class CorpusActionContext:
    user: User | None
    db: AsyncSession
    queries: CorpusContextQueries
