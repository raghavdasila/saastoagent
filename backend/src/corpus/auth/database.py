from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import event
from alembic.runtime.migration import MigrationContext
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base, User


class TransactionalUserDatabase(SQLAlchemyUserDatabase[User, Any]):
    """FastAPI Users adapter whose transaction belongs to the Corpus unit of work."""

    async def create(self, create_dict: dict[str, Any]) -> User:
        user = self.user_table(**create_dict)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, update_dict: dict[str, Any]) -> User:
        for key, value in update_dict.items():
            setattr(user, key, value)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()


class AuthDatabase:
    def __init__(self, url: str) -> None:
        self.url = url
        self.engine: AsyncEngine = create_async_engine(url)
        if url.startswith("sqlite"):
            event.listen(self.engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
        self._sessions = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    def session(self) -> AsyncSession:
        return self._sessions()

    @asynccontextmanager
    async def user_database(
        self,
        session: AsyncSession,
    ) -> AsyncIterator[TransactionalUserDatabase]:
        yield TransactionalUserDatabase(session, User)

    async def create_schema_for_tests(self) -> None:
        """Test-only schema creation; product startup never calls this."""

        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def verify_revision(self, expected_revision: str) -> None:
        async with self.engine.connect() as connection:
            current = await connection.run_sync(
                lambda sync_connection: MigrationContext.configure(
                    sync_connection
                ).get_current_revision()
            )
        if current != expected_revision:
            raise MigrationRevisionError(
                f"Corpus auth database revision is {current!r}; expected "
                f"{expected_revision!r}. Run the explicit auth migration command."
            )

    async def close(self) -> None:
        await self.engine.dispose()


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class MigrationRevisionError(RuntimeError):
    pass


__all__ = [
    "AuthDatabase",
    "MigrationRevisionError",
    "TransactionalUserDatabase",
]
