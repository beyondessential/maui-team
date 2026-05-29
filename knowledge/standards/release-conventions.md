# Release Conventions

How Maui repositories cut releases and how downstream consumers track versions.
For branch naming, see [`git-conventions.md`](git-conventions.md).

## Versioning

Maui repositories follow semantic versioning aligned with the Tamanu release the
artefact targets:

```
<major>.<minor>.<patch>
```

- **`tamanu-source-dbt`** — versions track upstream Tamanu releases. Major and
  minor follow Tamanu's major/minor; patch tracks BES-side patches against that
  Tamanu version.
- **`tamanu-dbt-<deployment>`** — same convention, optionally with a deployment
  suffix in the tag (e.g. `2.49.3-fj`) when the deployment carries divergent fixes.
- **`data-lake`** (rename to `bes-data-pipelines` in flight) — independent semver
  since it's not bound to a Tamanu release.
- **`fsm-data-migration`** — date-based or milestone-based per the migration plan;
  semver not required.

## Version branches

Long-running version branches are named `<major>.<minor>` (`2.49`, `2.48`). See
[`git-conventions.md`](git-conventions.md) § Version branches for the branching
rules.

`main` always carries the latest in-development version. Backports to older
version branches go via cherry-pick or a separate PR targeting the branch.

## Cutting a release

1. **Confirm CI is green** on the branch you're releasing from. `dbt-tests`,
   `claude-code-review`, `python-ci` — whichever apply to the repo.
2. **Update `pyproject.toml` / `dbt_project.yml` / `packages.yml`** to the new
   version. For dbt projects, ensure `packages.yml` pins the matching
   `tamanu-source-dbt` version (or matching internal package versions).
3. **Update the changelog** — add an entry under the new version in `CHANGELOG.md`
   (or the repo's equivalent). See § Release notes below.
4. **Open a release PR** with title `chore(release): vX.Y.Z`. Body should include
   the changelog excerpt for this release.
5. **Merge** once reviewed.
6. **Tag and publish** via GitHub Releases:
   - Tag: `vX.Y.Z` (lowercase `v` prefix)
   - Target: the release commit on `main` or the version branch
   - Title: `vX.Y.Z`
   - Body: the changelog excerpt
   - Publish — this triggers `publish-artifacts.yml` for dbt repos

The `publish-artifacts.yml` workflow (see
[`../../.github/workflows/README.md`](../../.github/workflows/README.md)) handles
S3 upload and meta-server registration automatically; do not manually upload
compiled bundles.

## Release notes

Release notes live in `CHANGELOG.md` at each repo's root, following the
[Keep a Changelog](https://keepachangelog.com/) shape:

```markdown
## [2.49.3] — 2026-06-12

### Added
- `der__cohort_diabetes` for fj deployment (BES-1234)

### Changed
- Updated `metric__hypertension_controlled` to use the new threshold (BES-1240)

### Fixed
- Fixed timezone bug in `encounter_summary_line_list` (BES-1247)

### Deprecated
- `coh__ncd` — use `der__cohort_ncd` instead. Remove in 2.50.x
```

Sections: **Added**, **Changed**, **Fixed**, **Deprecated**, **Removed**,
**Security**. Use the ones that apply; omit empty sections.

Each entry should reference the Linear issue that drove the change.

## What goes in a release

- **Patch (`X.Y.Z+1`)** — bug fixes, minor improvements, doc updates, no schema
  changes downstream consumers need to plan for
- **Minor (`X.Y+1.0`)** — additive schema changes, new models, new metrics, new
  reports; downstream consumers can adopt or ignore
- **Major (`X+1.0.0`)** — bound to a Tamanu major release; may carry breaking
  schema changes. Downstream consumers must plan migration

`Deprecated` entries should signal removal a full minor version ahead — never
remove without a deprecation cycle.

## Coordinating across repos

When a `tamanu-source-dbt` release affects deployment repos:

1. Cut the `tamanu-source-dbt` release first
2. Open coordinating PRs in each affected `tamanu-dbt-<deployment>` updating the
   pinned `tamanu-source-dbt` version in `packages.yml`
3. Tag deployment releases once all the deployment PRs are merged
4. Notify the team channel with the rollout plan and dates

For breaking changes, give deployment repos at least one minor-version lead time
before requiring the update.

## See also

- [`git-conventions.md`](git-conventions.md) — version branches, backporting
- [`linear-conventions.md`](linear-conventions.md) — issue references
- [`../../.github/workflows/README.md`](../../.github/workflows/README.md) —
  `publish-artifacts.yml` details
