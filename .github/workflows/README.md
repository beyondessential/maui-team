# Workflows

This directory holds two kinds of workflows:

- **Reusable workflows** (`on: workflow_call`) consumed by other Maui repos via
  `uses: beyondessential/maui-team/.github/workflows/<name>.yml@main`:
  [`claude-code-review.yml`](claude-code-review.yml),
  [`dbt-tests.yml`](dbt-tests.yml),
  [`python-ci.yml`](python-ci.yml),
  [`publish-artifacts.yml`](publish-artifacts.yml).
- **This repo's own CI** (`on: pull_request` / `on: push`):
  [`link-check.yml`](link-check.yml) validates internal markdown links, and
  [`imports-check.yml`](imports-check.yml) validates that `@./.maui/<path>`
  example imports in README, AGENT.base, and runbooks resolve to real files.
  Documented at the bottom of this file.

See the [root README](../../README.md) for full new-repo setup instructions.

## claude-code-review.yml

Runs on every PR and on `/review` comments.

> ⚠️ **Auto-commit behaviour.** On pull requests, the workflow first updates the
> `.maui` submodule if it is behind `main` and **pushes a `chore: update .maui
> submodule` commit back to the PR branch as `github-actions[bot]`** before running
> the review. If you push to a PR and find an extra commit you didn't author, this is
> why. The commit only appears when the submodule was actually out of date.

After the submodule sync, the workflow runs the Claude Code review against the latest
code (using a repo-local `REVIEW.md` if present, otherwise falling back to
`.maui/REVIEW.md`).

### Secrets required

`ANTHROPIC_API_KEY` — add as a repository secret in Settings → Secrets and variables → Actions.

### Caller workflow

Create `.github/workflows/claude-code-review.yml` in the consuming repo:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, reopened, synchronize]
  issue_comment:
    types: [created]

jobs:
  claude-review:
    if: >-
      github.event_name == 'pull_request' ||
        (github.event_name == 'issue_comment' &&
        github.event.issue.pull_request != null &&
        contains(github.event.comment.body, '/review') &&
        github.event.comment.author_association != 'NONE' &&
        github.event.comment.author_association != 'FIRST_TIME_CONTRIBUTOR')
    uses: beyondessential/maui-team/.github/workflows/claude-code-review.yml@main
    secrets: inherit
```

### Re-triggering a review

Post a comment on the PR containing `/review`. Only team members (not first-time contributors) can trigger this.

### Making review a required check

In the repository's branch protection settings (Settings → Branches → Branch protection rules):
1. Enable **Require status checks to pass before merging**
2. Add `claude-review` as a required status check
3. Separately enable **Require a pull request before merging** with at least 1 required approver for human review

## dbt-tests.yml

Runs dbt data-tests against a live database. Intended for `tamanu-source-dbt` and `tamanu-dbt-*` repos.

Installs project dependencies via `uv sync`, writes a `profiles.yml` from secrets, runs `dbt deps` to install dbt packages, then runs `dbt test` to execute all data-tests. The dbt profile name is read automatically from `dbt_project.yml`.

### Secrets required

| Secret | Required | Description |
|--------|----------|-------------|
| `DBT_HOST` | Yes | Database hostname |
| `DBT_DBNAME` | Yes | Database name |
| `DBT_USER` | Yes | Database username |
| `DBT_PASSWORD` | Yes | Database password |
| `DBT_PORT` | No | Database port (defaults to 5432) |

### Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `profiles-dir` | `config` | Directory where the CI `profiles.yml` is written, relative to the project root |
| `dbt-schema` | `reporting` | Target schema for the dbt test run |

### Caller workflow

Create `.github/workflows/dbt-tests.yml` in the consuming repo:

```yaml
name: dbt Tests

on:
  pull_request:
    types: [opened, reopened, synchronize]
  push:
    branches: [main]

jobs:
  test:
    uses: beyondessential/maui-team/.github/workflows/dbt-tests.yml@main
    secrets: inherit
```

## python-ci.yml

Runs `ruff check --fix` and `ruff format` over a configurable scripts path, then runs
`pytest`. Auto-fixes from ruff are committed back to the PR branch as `style: auto-fix
and format with ruff` (same caveat as `claude-code-review.yml` — contributors may see
a commit they didn't author when ruff applies a fix).

Ruff configuration is read from the calling repo's `pyproject.toml` or `ruff.toml`,
which should extend `.maui/ruff.toml` for the shared rule set.

### Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `scripts-path` | `scripts/` | Path passed to `ruff check` / `ruff format` |

### Secrets required

None — the workflow uses the default `GITHUB_TOKEN`.

### Caller workflow

Create `.github/workflows/python-ci.yml` in the consuming repo:

```yaml
name: Python CI

on:
  pull_request:
    types: [opened, reopened, synchronize]
  push:
    branches: [main]

jobs:
  ci:
    uses: beyondessential/maui-team/.github/workflows/python-ci.yml@main
    # with:
    #   scripts-path: src/  # override if your code lives elsewhere
```

## publish-artifacts.yml

Runs on release events. Publishes all files from `compiled/v<version>/` to S3 (renaming `v<version>` → `v<M.m.x>` in filenames) and registers the canonical artifacts with the meta-server. Intended for `tamanu-source-dbt` and `tamanu-dbt-*` repos.

The deployment name is derived from the calling repository name:
- `tamanu-source-dbt` → `standard` (artifacts at `M.m.x/`)
- `tamanu-dbt-<name>` → `<name>` (artifacts at `M.m.x/<name>/`)

The `list-reports` job only runs for the `standard` deployment on its latest release.

### Secrets and variables required

- `META_CERT` — client certificate for authenticating with the meta-server
- `META_KEY` — private key for the client certificate
- `META_URL` — base URL of the meta-server (repository variable)

AWS credentials are obtained via OIDC — no static AWS secrets required. The IAM role `arn:aws:iam::491618206332:role/gha-s3-tamanu-translations` must trust the calling repository.

### Caller workflow

Create `.github/workflows/publish-artifacts.yml` in the consuming repo:

```yaml
name: Publish Artifacts

on:
  release:
    types: [published]

jobs:
  publish:
    uses: beyondessential/maui-team/.github/workflows/publish-artifacts.yml@main
    secrets: inherit
```

---

# This repo's own CI

These workflows run on this repo only and are not intended for consumer use.

## link-check.yml

Validates that internal markdown links in `knowledge/`, `README.md`, `AGENT.md`,
`REVIEW.md`, and the workflows README resolve. Runs on PRs touching `.md` files
and on pushes to `main`.

External URL behaviour is controlled by
[`.github/markdown-link-check-config.json`](../markdown-link-check-config.json) —
notably, Slab and `beyondessential/*` private-repo links are skipped (they
require auth and would fail in CI).

## imports-check.yml

Validates that `@./.maui/<path>` example imports in README, `AGENT.base.md`,
and runbooks point at real files in the repo. Catches renames that would
silently break consumer repos.

Runs [`scripts/check_agent_imports.py`](../../scripts/check_agent_imports.py).
You can also run the script locally:

```bash
python scripts/check_agent_imports.py
```
