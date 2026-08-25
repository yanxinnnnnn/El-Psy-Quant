"""Alembic environment for the explicit local product database."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import URL

import el_psy_quant.persistence.artifact_index_model  # noqa: F401
import el_psy_quant.persistence.market_time_model  # noqa: F401
import el_psy_quant.persistence.paper_job_attempt_model  # noqa: F401
import el_psy_quant.persistence.paper_job_model  # noqa: F401
import el_psy_quant.persistence.paper_job_submission_key_model  # noqa: F401
import el_psy_quant.persistence.paper_account_model  # noqa: F401
import el_psy_quant.persistence.paper_execution_model  # noqa: F401
import el_psy_quant.persistence.paper_runtime_model  # noqa: F401
import el_psy_quant.persistence.portfolio_review_model  # noqa: F401
import el_psy_quant.persistence.strategy_order_model  # noqa: F401
from el_psy_quant.persistence import (
    ProductPersistenceBase,
    create_product_database_engine,
    resolve_product_database_config,
)

alembic_config = context.config
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

product_database_config = resolve_product_database_config()
database_url = URL.create(
    "sqlite", database=str(product_database_config.database_path)
).render_as_string(hide_password=False)
alembic_config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
target_metadata = ProductPersistenceBase.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the explicitly configured SQLite file."""
    connectable = create_product_database_engine(
        config=product_database_config,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
