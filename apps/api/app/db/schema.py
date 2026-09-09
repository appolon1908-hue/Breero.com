from functools import lru_cache
from pathlib import Path

from alembic.script import ScriptDirectory

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


@lru_cache
def expected_schema_revision() -> str:
    """Return the single Alembic head this build of the API expects.

    Readiness compares ``alembic_version`` against this value, so it must track the
    migrations that shipped in the image rather than a constant somebody remembers to
    bump. Resolving it from the script directory keeps the two in step by construction.

    Raises ``RuntimeError`` rather than degrading: an API that cannot tell whether its
    schema is current must not be able to report itself ready.
    """
    if not MIGRATIONS_DIR.is_dir():
        raise RuntimeError(f"migration script directory is missing at {MIGRATIONS_DIR}")
    heads = ScriptDirectory(str(MIGRATIONS_DIR)).get_heads()
    if len(heads) != 1:
        raise RuntimeError(
            "expected exactly one Alembic head, found: " + (", ".join(sorted(heads)) or "none")
        )
    return heads[0]
