from __future__ import annotations

from typing import Any

from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from .models import User


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


__all__ = [
    "TransactionalUserDatabase",
]
