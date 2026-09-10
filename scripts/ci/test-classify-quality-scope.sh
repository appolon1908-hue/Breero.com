#!/usr/bin/env bash
set -euo pipefail

classifier="$(dirname "$0")/classify-quality-scope.sh"

assert_scope() {
  local name="$1" expected="$2"
  shift 2
  local actual
  actual="$(printf '%s\n' "$@" | "$classifier")"
  [[ "$actual" == "$expected" ]] || {
    printf 'scenario %s failed\nexpected:\n%s\nactual:\n%s\n' "$name" "$expected" "$actual" >&2
    exit 1
  }
}

assert_scope backend-only $'backend=true\nfrontend=true\nbootstrap=false' apps/api/app/main.py
assert_scope frontend-only $'backend=false\nfrontend=true\nbootstrap=false' apps/web/app/page.tsx
assert_scope backend-and-frontend $'backend=true\nfrontend=true\nbootstrap=false' apps/api/app/main.py apps/web/app/page.tsx
assert_scope workflow-only $'backend=false\nfrontend=false\nbootstrap=false' .github/workflows/quality.yml
assert_scope documentation-only $'backend=false\nfrontend=false\nbootstrap=false' docs/runbook.md

test_cross_boundary_rename() {
  local fixture base head actual expected
  fixture="$(mktemp -d)"
  trap 'rm -rf "$fixture"' RETURN

  git -C "$fixture" init -q
  git -C "$fixture" config user.name quality-scope-test
  git -C "$fixture" config user.email quality-scope-test@example.invalid
  mkdir -p "$fixture/apps/api" "$fixture/docs"
  printf 'runtime\n' >"$fixture/apps/api/module.py"
  git -C "$fixture" add apps/api/module.py
  git -C "$fixture" commit -qm baseline
  base="$(git -C "$fixture" rev-parse HEAD)"

  git -C "$fixture" mv apps/api/module.py docs/module.py
  git -C "$fixture" commit -qm cross-boundary-rename
  head="$(git -C "$fixture" rev-parse HEAD)"

  actual="$(git -C "$fixture" diff --no-renames --name-only "$base" "$head" | "$classifier")"
  expected=$'backend=true\nfrontend=true\nbootstrap=false'
  [[ "$actual" == "$expected" ]] || {
    printf 'scenario cross-boundary-rename failed\nexpected:\n%s\nactual:\n%s\n' "$expected" "$actual" >&2
    exit 1
  }
}

test_cross_boundary_rename

echo 'QUALITY_SCOPE_SCENARIOS=PASS'
