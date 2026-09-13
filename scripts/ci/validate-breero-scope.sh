#!/usr/bin/env bash
set -euo pipefail

root="${1:-.}"
needle="$(printf '%s%s' 'money' 'bee')"

# Control-plane policy must name the complete protected catalog. Product
# content must remain scoped to BREERO, so exclude only policy metadata.
if grep -RIni \
  --exclude-dir=.git \
  --exclude-dir=.codestra \
  -- "$needle" "$root"; then
  echo "Cross-project product reference detected." >&2
  exit 1
fi
