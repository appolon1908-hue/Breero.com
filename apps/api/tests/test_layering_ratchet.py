import importlib.util
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_layering", API_ROOT / "scripts" / "check_layering.py"
)
assert _spec and _spec.loader
check_layering = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_layering)


def _violations(tmp_path: Path, source: str) -> list[tuple[str, str]]:
    """Classify one synthetic router module, ignoring the reported path."""
    module = tmp_path / "router.py"
    module.write_text(source, encoding="utf-8")
    original_root = check_layering.API_ROOT
    check_layering.API_ROOT = tmp_path
    try:
        found = check_layering._violations_for(module)
    finally:
        check_layering.API_ROOT = original_root
    return [(rule, imported) for _, rule, imported in found]


def test_async_session_annotation_is_not_a_violation(tmp_path) -> None:
    # Every router needs AsyncSession to annotate Depends(get_db).
    assert _violations(tmp_path, "from sqlalchemy.ext.asyncio import AsyncSession\n") == []


def test_sqlalchemy_exc_is_not_a_violation(tmp_path) -> None:
    # Translating an IntegrityError into an HTTP response is the router's job.
    assert _violations(tmp_path, "from sqlalchemy.exc import IntegrityError\n") == []


def test_query_constructors_are_a_violation(tmp_path) -> None:
    assert _violations(tmp_path, "from sqlalchemy import select\n") == [
        ("sqlalchemy-query", "sqlalchemy")
    ]


def test_sqlalchemy_sql_is_a_violation(tmp_path) -> None:
    assert _violations(tmp_path, "from sqlalchemy.sql import Select\n") == [
        ("sqlalchemy-query", "sqlalchemy.sql")
    ]


def test_orm_model_import_is_a_violation(tmp_path) -> None:
    assert _violations(tmp_path, "from app.domains.jobs.models import Job\n") == [
        ("orm-model", "app.domains.jobs.models")
    ]


def test_auth_models_are_exempt(tmp_path) -> None:
    # current_user resolves to a User entity, so guarded routers must name the type.
    assert _violations(tmp_path, "from app.domains.auth.models import User\n") == []


def test_schemas_and_services_are_not_violations(tmp_path) -> None:
    source = (
        "from app.domains.jobs.service import JobService\n"
        "from app.domains.jobs.schemas import JobRead\n"
    )
    assert _violations(tmp_path, source) == []


def test_baseline_matches_the_tree() -> None:
    # Same assertion CI makes, so a local pytest run surfaces drift too.
    current = check_layering.collect()
    baseline = check_layering.read_baseline()
    assert current - baseline == set(), "new router layering violations"
    assert baseline - current == set(), "stale baseline entries; run --update"
