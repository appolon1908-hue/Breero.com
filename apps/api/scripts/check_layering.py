#!/usr/bin/env python
"""Ratchet the HTTP layer towards `router -> service -> repository`.

`docs/architecture/system.md` requires routers to delegate persistence to a service
and its repository. Import Linter (`.importlinter`) guards the coarse structure, but
it squashes external packages, so it cannot tell `sqlalchemy.ext.asyncio` -- the
`AsyncSession` annotation every router legitimately needs for `Depends(get_db)` --
apart from the query constructors that belong in a repository. This checker draws
that line, and freezes the modules that cross it today into a baseline.

The baseline can only shrink. A new violation fails; so does a baseline entry whose
violation has been fixed but not removed, which is what keeps the list honest.

    python scripts/check_layering.py            # verify
    python scripts/check_layering.py --update   # rewrite the baseline after a migration
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
ROUTER_DIR = API_ROOT / "app" / "api"
BASELINE = Path(__file__).resolve().parent / "layering_baseline.txt"

# `AsyncSession` is the annotation for `Depends(get_db)`; a router must name the type
# it hands to a service. `sqlalchemy.exc` lets a router translate integrity errors into
# HTTP responses. Neither builds a query, so neither is persistence logic.
ALLOWED_SQLALCHEMY_MODULES = frozenset({"sqlalchemy.ext.asyncio", "sqlalchemy.exc"})

# `current_user` resolves to a `User` ORM entity, so every guarded router must import
# it to annotate the dependency. That is forced by the auth design rather than by a
# router reaching into persistence, and unpicking it is a separate refactor.
EXEMPT_MODEL_MODULES = frozenset({"app.domains.auth.models"})


def _imported_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return modules


def _violations_for(path: Path) -> list[tuple[str, str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    relative = path.relative_to(API_ROOT).as_posix()
    found: list[tuple[str, str, str]] = []
    for module in _imported_modules(tree):
        root = module.split(".")[0]
        if root == "sqlalchemy" and module not in ALLOWED_SQLALCHEMY_MODULES:
            found.append((relative, "sqlalchemy-query", module))
        elif (
            module.startswith("app.domains.")
            and module.endswith(".models")
            and module not in EXEMPT_MODEL_MODULES
        ):
            found.append((relative, "orm-model", module))
    return found


def collect() -> set[str]:
    entries: set[str] = set()
    for path in sorted(ROUTER_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        entries.update(" ".join(item) for item in _violations_for(path))
    return entries


def read_baseline() -> set[str]:
    if not BASELINE.exists():
        return set()
    return {
        line.strip()
        for line in BASELINE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def write_baseline(entries: set[str]) -> None:
    header = (
        "# Router-purity ratchet -- see scripts/check_layering.py and\n"
        "# docs/architecture/system.md. Each line is a router that still builds its own\n"
        "# queries or reaches into an ORM model instead of delegating to a repository.\n"
        "#\n"
        "# This list may only shrink. Removing an entry is how a domain gets migrated;\n"
        "# adding one requires changing the checker, deliberately and in review.\n"
    )
    BASELINE.write_text(header + "".join(f"{entry}\n" for entry in sorted(entries)), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="rewrite the baseline")
    arguments = parser.parse_args()

    current = collect()
    if arguments.update:
        write_baseline(current)
        print(f"baseline rewritten with {len(current)} entries")
        return 0

    baseline = read_baseline()
    added = sorted(current - baseline)
    resolved = sorted(baseline - current)

    if added:
        print("New layering violations. Routers must delegate persistence to a service:")
        for entry in added:
            path, rule, module = entry.split(" ")
            reason = (
                "builds queries directly"
                if rule == "sqlalchemy-query"
                else "imports an ORM model"
            )
            print(f"  {path} {reason} ({module})")
        print("\nMove the query into the domain's repository, or call an existing service.")
    if resolved:
        print("\nBaseline entries that no longer apply. Delete these lines to lock in the fix:")
        for entry in resolved:
            print(f"  {entry}")
        print("\n  python scripts/check_layering.py --update")

    if added or resolved:
        return 1
    print(f"Router layering ratchet holding at {len(current)} known violations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
