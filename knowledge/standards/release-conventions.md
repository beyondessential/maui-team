# Release Conventions

How Maui repos cut releases. Branch rules: [`git-conventions.md`](git-conventions.md).

## Versioning

Semver `<major>.<minor>.<patch>`.

- **`tamanu-source-dbt`** — tracks upstream Tamanu major/minor; patch is BES-side
- **`tamanu-dbt-<deployment>`** — same, optional `-<deployment>` suffix when
  deployment carries divergent fixes (`2.49.3-fj`)
- **`data-lake`** (→ `bes-data-pipelines`) — independent semver
- **`fsm-data-migration`** — date- or milestone-based; semver not required

## Version branches

`<major>.<minor>` (`2.49`, `2.48`). `main` carries the latest in-development
version. Backport via cherry-pick or a separate PR. Rules:
[`git-conventions.md`](git-conventions.md).

## Cutting a release

1. CI green (`dbt-tests`, `claude-code-review`, `python-ci` — whichever apply)
2. Bump version in `pyproject.toml` / `dbt_project.yml` / `packages.yml`. dbt
   projects: pin matching `tamanu-source-dbt` version
3. Add changelog entry (see below)
4. Open release PR: `chore(release): vX.Y.Z`; body = changelog excerpt
5. Merge after review
6. GitHub Release: tag `vX.Y.Z`, target the release commit, body = changelog
   excerpt. Publish — triggers `publish-artifacts.yml` for dbt repos

`publish-artifacts.yml` handles S3 + meta-server. Never manually upload bundles.

## Release notes

`CHANGELOG.md` at each repo's root,
[Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [2.49.3] — 2026-06-12

### Added
- `der__cohort_diabetes` for fj deployment (MAUI-1234)

### Changed
- Updated `metric__hypertension_controlled` threshold (MAUI-1240)

### Fixed
- Timezone bug in `encounter_summary_line_list` (MAUI-1247)

### Deprecated
- `dim_patient_summary` — use `ds__patient_summary`. Remove in 2.50.x
```

Sections: Added / Changed / Fixed / Deprecated / Removed / Security. Use what
applies. Every entry references its Linear issue.

## What goes where

- **Patch** — bug fixes, doc updates, no schema changes for consumers
- **Minor** — additive schema changes; consumers can adopt or ignore
- **Major** — bound to a Tamanu major; may carry breaking changes

`Deprecated` flags removal one minor version ahead. Never remove without a
deprecation cycle.

## Cross-repo coordination

When `tamanu-source-dbt` affects deployment repos:

1. Cut `tamanu-source-dbt` release first
2. PR each `tamanu-dbt-<deployment>` to bump pinned version
3. Tag deployment releases after PRs merge
4. Post rollout plan + dates in the team channel

Breaking changes: at least one minor-version lead time before requiring update.

## See also

- [`git-conventions.md`](git-conventions.md)
- [`linear-conventions.md`](linear-conventions.md)
- [`../../.github/workflows/README.md`](../../.github/workflows/README.md)
