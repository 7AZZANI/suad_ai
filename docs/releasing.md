# Releasing & versioning

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
`MAJOR.MINOR.PATCH`.

The whole repository (backend + frontend) is versioned as **one unit** — a
single tag covers both. When you bump, all three version fields move together:

- `pyproject.toml`
- `backend/app/__init__.py` (`__version__`)
- `frontend/package.json`

Tag naming: an annotated tag `vMAJOR.MINOR.PATCH` (e.g. `v0.1.1`).

## When to bump what

| Change type | Examples | Bump |
|---|---|---|
| **Fix** | bug fixes, docs, housekeeping | `PATCH` → `0.1.0 → 0.1.1` |
| **Feature** | new adapter, new tool, new recipe, new UI page | `MINOR` → `0.1.0 → 0.2.0` |
| **Breaking** | config/env renames, API changes, auth replacement | `MAJOR` → `0.1.0 → 1.0.0` |

Pre-releases/RCs use a suffix, e.g. `1.0.0-rc.1`.

## Workflow

1. **Update `CHANGELOG.md`** — move finished work from *Unreleased* into a new
   `## [X.Y.Z] — <date>` section.
2. **Cut the release:**

   ```bash
   make release v=0.1.1
   ```

   This runs `scripts/bump_version.sh`, which:
   - fails if the working tree is dirty or `main` is behind `origin/main`;
   - bumps all three version fields;
   - commits as `chore: release v0.1.1`;
   - creates an annotated tag `v0.1.1`;
   - pushes the commit and the tag.

   The Make target always pushes. To skip the push (or do a dry run), use the
   script directly:

   ```bash
   ./scripts/bump_version.sh 0.1.1 --no-push     # commit + tag only
   ./scripts/bump_version.sh 0.1.1 --dry-run     # show what would change
   ```

3. **Create a GitHub Release** — on
   [Releases → Draft a new release](https://github.com/7AZZANI/suad_ai/releases/new),
   pick tag `v0.1.1`, title it `v0.1.1`, and paste the CHANGELOG section for
   that version.

## Post-release sanity checks

- `make test && make lint` are green on the tagged commit.
- `curl -s localhost:8000/api/setup/summary` (or `/` root info) reports the new
  version.
- The tag exists on the remote: `git ls-remote --tags origin`.