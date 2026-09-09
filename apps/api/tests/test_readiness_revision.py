from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.db import schema
from app.db.schema import expected_schema_revision
from app.main import EXPECTED_SCHEMA_REVISION


def test_readiness_revision_matches_the_single_alembic_head() -> None:
    api_root = Path(__file__).resolve().parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "migrations"))
    heads = ScriptDirectory.from_config(config).get_heads()

    assert heads == [EXPECTED_SCHEMA_REVISION]


def test_readiness_revision_is_derived_not_hardcoded() -> None:
    # The readiness constant must come from the migration scripts that shipped in the
    # image. A literal would silently drift from head every time a migration lands.
    assert EXPECTED_SCHEMA_REVISION == expected_schema_revision()


def test_missing_migration_directory_fails_loudly(monkeypatch, tmp_path) -> None:
    expected_schema_revision.cache_clear()
    monkeypatch.setattr(schema, "MIGRATIONS_DIR", tmp_path / "absent")
    try:
        with pytest.raises(RuntimeError, match="migration script directory is missing"):
            expected_schema_revision()
    finally:
        expected_schema_revision.cache_clear()


def test_multiple_heads_fail_loudly(monkeypatch) -> None:
    expected_schema_revision.cache_clear()

    class TwoHeads:
        def __init__(self, _directory: str) -> None: ...

        def get_heads(self) -> list[str]:
            return ["006_auth_customer_payments", "006_finance_integrations"]

    monkeypatch.setattr(schema, "ScriptDirectory", TwoHeads)
    try:
        with pytest.raises(RuntimeError, match="exactly one Alembic head"):
            expected_schema_revision()
    finally:
        expected_schema_revision.cache_clear()
