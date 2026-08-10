from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.sql.sqltypes import CHAR
from fastapi_users_db_sqlalchemy import GUID

from corpus.auth import models as _auth_models
from corpus.credentials import models as _credential_models
from corpus.features.agents import models as _agent_models
from corpus.features.designer import models as _designer_models
from corpus.features.builder import models as _builder_models
from corpus.features.sandbox import models as _sandbox_models
from corpus.features.evaluation import models as _evaluation_models
from corpus.features.channels import models as _channel_models
from corpus.features.deployment import models as _deployment_models
from corpus.jobs import models as _job_models
from corpus.persistence import Base, CorpusDatabaseSettings


config = context.config
if not config.get_main_option("sqlalchemy.url"):
    database_url = CorpusDatabaseSettings.from_env().url
    config.set_main_option(
        "sqlalchemy.url",
        database_url.replace("sqlite+aiosqlite://", "sqlite://", 1),
    )
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    del inspected_column, metadata_column
    if (
        context.dialect.name == "sqlite"
        and isinstance(inspected_type, CHAR)
        and inspected_type.length == 32
        and isinstance(metadata_type, GUID)
    ):
        return False
    return None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
