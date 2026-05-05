from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TenantBase(DeclarativeBase):
    pass
