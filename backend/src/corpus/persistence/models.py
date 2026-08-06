from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared metadata root for Corpus-owned domain modules."""


__all__ = ["Base"]
