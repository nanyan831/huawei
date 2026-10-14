from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, inspect, text

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine

# Import models so SQLAlchemy registers them before create_all.
from app.models import audit_log  # noqa: F401
from app.models import evidence  # noqa: F401
from app.models import history_review_run  # noqa: F401
from app.models import exhibit  # noqa: F401
from app.models import review_run  # noqa: F401
from app.models import visitor_state  # noqa: F401


def init_db(*, schema_mode: str | None = None, database_engine: Engine | None = None) -> None:
    mode = schema_mode or settings.schema_mode
    target = database_engine or engine
    if mode == "auto_create":
        Base.metadata.create_all(bind=target)
    elif mode == "migrated":
        _require_current_migration(target)
    else:
        raise ValueError("HISTORYGUIDE_SCHEMA_MODE must be auto_create or migrated.")


def _require_current_migration(database_engine: Engine) -> None:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    expected_head = ScriptDirectory.from_config(config).get_current_head()
    with database_engine.connect() as connection:
        if "alembic_version" not in inspect(connection).get_table_names():
            raise RuntimeError("Migrated schema mode requires an Alembic version table.")
        revision = connection.execute(text("select version_num from alembic_version")).scalar_one_or_none()
        if revision != expected_head:
            raise RuntimeError(
                f"Database revision {revision or '<empty>'} does not match expected {expected_head}."
            )
        differences = compare_metadata(
            MigrationContext.configure(connection, opts={"compare_type": True}), Base.metadata
        )
        if differences:
            raise RuntimeError("Database schema differs from the migrated application models.")
