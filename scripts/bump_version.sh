#!/usr/bin/env bash
#
# Cut a new release for Suad AI.
#
#   Usage:
#     ./scripts/bump_version.sh 0.1.1
#     ./scripts/bump_version.sh 0.2.0 --no-push
#     ./scripts/bump_version.sh --dry-run 0.1.1
#
# What it does:
#   1. Validates the version against Semantic Versioning (MAJOR.MINOR.PATCH,
#      optional -prerelease suffix).
#   2. Requires a clean working tree.
#   3. Requires HEAD to be up to date with the remote 'origin/main'.
#   4. Bumps the version in every place that stores it:
#        - pyproject.toml
#        - backend/app/__init__.py
#        - frontend/package.json
#   5. Commits the change as  "chore: release v<version>"
#   6. Creates an annotated tag  v<version>
#   7. Pushes the commit and the tag (unless --no-push).
#
# Update CHANGELOG.md yourself BEFORE running this script: the release commit
# only touches version fields, never the changelog body.

set -euo pipefail

push="yes"
dry_run="no"
version=""

for arg in "$@"; do
  case "$arg" in
    --no-push) push="no" ;;
    --dry-run) dry_run="yes" ;;
    *) version="$arg" ;;
  esac
done

if [[ -z "$version" ]]; then
  echo "usage: $0 <MAJOR.MINOR.PATCH> [--no-push] [--dry-run]" >&2
  echo "example: $0 0.1.1" >&2
  exit 1
fi

# Normalize an optional leading "v": v0.1.1 -> 0.1.1
version="${version#v}"

if ! [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo "error: '$version' is not valid Semantic Versioning (expected X.Y.Z or X.Y.Z-rc.1)" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "error: working tree is not clean — commit or stash your changes first." >&2
  exit 1
fi

if [[ "$push" == "yes" && "$dry_run" == "no" ]]; then
  git fetch origin --quiet
  behind="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
  if [[ "$behind" != "0" ]]; then
    echo "error: local main is $behind commit(s) behind origin/main — pull/rebase first." >&2
    exit 1
  fi
fi

if [[ -e "pyproject.toml" ]]; then
  sed -i "s/^version = \"[^\"]*\"/version = \"$version\"/" pyproject.toml
fi
sed -i "s/^__version__ = \"[^\"]*\"/__version__ = \"$version\"/" backend/app/__init__.py
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$version\"/" frontend/package.json

echo "Version -> $version"

if [[ "$dry_run" == "yes" ]]; then
  echo "dry-run: reverting version bumps"
  git checkout -- pyproject.toml backend/app/__init__.py frontend/package.json
  exit 0
fi

git add pyproject.toml backend/app/__init__.py frontend/package.json
git commit -m "chore: release v$version"
git tag -a "v$version" -m "Suad AI v$version"

if [[ "$push" == "yes" ]]; then
  git push origin main
  git push origin "v$version"
  echo "released and pushed: v$version"
else
  echo "released locally: v$version (not pushed)"
fi