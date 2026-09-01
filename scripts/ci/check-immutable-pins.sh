#!/usr/bin/env bash
# Every third-party GitHub Action and every container image must be immutably pinned.
#
# A mutable tag is a supply-chain hole with the blast radius of the workflow that uses
# it: `actions/checkout@v4` runs whatever that tag points at today, with a token that
# can write to this repository. A retagged base image is the same problem at runtime.
#
# In-repo reusable workflows (`./.github/workflows/...`) are exempt: they resolve to
# the commit already being built, so there is nothing mutable to pin.
set -euo pipefail

failed=0

report() {
  printf '::error::%s\n' "$1" >&2
  failed=1
}

# --- GitHub Actions ---------------------------------------------------------
while IFS= read -r entry; do
  [[ -n "$entry" ]] || continue
  file="${entry%%::*}"
  ref="${entry##*::}"
  # A local reusable workflow resolves to the commit already being built.
  [[ "$ref" == ./* ]] && continue
  # A 40-character hex commit is the only acceptable pin.
  if [[ ! "$ref" =~ @[0-9a-f]{40}$ ]]; then
    report "$file uses a mutable Action reference: $ref"
  fi
done < <(
  find .github/workflows -type f -name '*.yml' 2>/dev/null |
    while IFS= read -r f; do
      grep -hoE "uses:[[:space:]]*[^[:space:]#]+" "$f" 2>/dev/null |
        sed -E 's/uses:[[:space:]]*//' |
        while IFS= read -r r; do printf '%s::%s\n' "$f" "$r"; done
    done
)

# --- Container images -------------------------------------------------------
while IFS= read -r entry; do
  [[ -n "$entry" ]] || continue
  file="${entry%%::*}"
  ref="${entry##*::}"
  # Compose interpolation (${BREERO_API_IMAGE:?...}) is resolved at deploy time from
  # a release manifest that carries the digest, and multi-stage build aliases are
  # local names rather than registry references.
  [[ "$ref" == \$* ]] && continue
  [[ "$ref" =~ ^(base|dependencies|builder|runtime)$ ]] && continue
  if [[ "$ref" != *"@sha256:"* ]]; then
    report "$file references an unpinned image: $ref"
  fi
done < <(
  find deploy .github apps -type f \( -name '*.yml' -o -name '*.yaml' -o -name 'Dockerfile*' \) 2>/dev/null |
    while IFS= read -r f; do
      grep -hoE '^[[:space:]]*(image:|FROM)[[:space:]]+[^[:space:]]+' "$f" 2>/dev/null |
        sed -E 's/^[[:space:]]*(image:|FROM)[[:space:]]+//' |
        while IFS= read -r r; do printf '%s::%s\n' "$f" "$r"; done
    done
)

if (( failed )); then
  echo "Resolve a pin with:" >&2
  echo "  git ls-remote https://github.com/<owner>/<repo> 'refs/tags/<tag>^{}'" >&2
  echo "  docker buildx imagetools inspect <image>:<tag>" >&2
  exit 1
fi

echo "IMMUTABLE_PINS=PASS"
