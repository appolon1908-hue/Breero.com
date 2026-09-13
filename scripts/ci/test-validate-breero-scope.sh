#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
validator="$repository_root/scripts/ci/validate-breero-scope.sh"
test_root="$(mktemp -d)"
trap 'rm -rf -- "$test_root"' EXIT

needle="$(printf '%s%s' 'money' 'bee')"

mkdir -p "$test_root/.codestra" "$test_root/apps"
printf '%s\n' "$needle" > "$test_root/.codestra/catalog.txt"
"$validator" "$test_root"

printf '%s\n' "$needle" > "$test_root/apps/product.txt"
if "$validator" "$test_root" >/dev/null 2>&1; then
  echo "product-scope validation accepted a cross-project product reference" >&2
  exit 1
fi

echo "BREERO scope regression scenarios passed"
