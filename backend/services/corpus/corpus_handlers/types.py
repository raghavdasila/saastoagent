from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import User
from backend.core.schemas import CorpusGraphState, EntryGraphMessage
from backend.services.corpus.corpus_context import CorpusContextQueries
from routedeck_core import RouteDeckActionResult


CorpusActionResult: TypeAlias = RouteDeckActionResult[CorpusGraphState, EntryGraphMessage]


@dataclass(slots=True)
class CorpusActionContext:
    user: User | None
    db: AsyncSession
    queries: CorpusContextQueries
