# Runbook: Tamanu dbt project set-up

How to set up a new `tamanu-dbt-<deployment>` project from scratch, or a fresh clone
of an existing one. For the broader architecture context, see
`../architecture/data-architecture.md`. For the layer taxonomy and conventions, see
`../standards/dbt-conventions.md`.

## Prerequisites

1. [uv](https://docs.astral.sh/uv/) installed
2. PostgreSQL access to the Tamanu replica (see
   `environment-and-credentials.md` for how to request credentials)
3. Git, with submodule support

## Installation steps

### 1. Clone and set up the environment

```bash
git clone <repository-url>
cd <project-directory>
uv sync
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with the database credentials from your team lead
# (see environment-and-credentials.md if you don't have them)
```

### 3. Install dbt dependencies

```bash
dbt deps
dbt debug   # verifies the connection
```

### 4. Project customisation

Update the following files for the new deployment:

#### `pyproject.toml`
- `name` — project name (e.g. `tamanu-dbt-fj`)
- `version` — match the deployed Tamanu version

#### `dbt_project.yml`
- `name` — must match `pyproject.toml`
- `profile` — must match `pyproject.toml`

#### `config/profiles.yml`
- Profile name — match `dbt_project.yml`
- `target` — environment name (e.g. `dev`, `staging`, `prod`)

#### `packages.yml`
- `revision` — pin to the deployed Tamanu version (e.g. `2.32.0`); never use a branch
  reference. See `../standards/dbt-conventions.md` § Package management.

#### `README.md`
- Update title and description for the deployment (project name, country/region,
  Tamanu instance). Remove the template boilerplate.

#### `AGENT.md`
Create `AGENT.md` at the repo root, importing the standards relevant to a
`tamanu-dbt-<deployment>` repo:

```
@./.maui/knowledge/AGENT.base.md
@./.maui/knowledge/standards/git-conventions.md
@./.maui/knowledge/standards/sql-conventions.md
@./.maui/knowledge/standards/dbt-conventions.md
@./.maui/knowledge/standards/tamanu-dbt-conventions.md
@./.maui/knowledge/standards/dbt-metadata.md

---

## Repository: <repo-name>

<Brief description of the deployment.>
```

#### `CLAUDE.md`
Create `CLAUDE.md` at the repo root (gitignored — per-developer, not committed):

```
@./AGENT.md
```

#### `.github/workflows/publish-artifacts.yml`
Create `.github/workflows/publish-artifacts.yml` calling the reusable workflow on
release:

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

Required secrets and repository variables: `META_CERT`, `META_KEY`, `META_URL`. AWS
credentials are obtained via OIDC — the IAM role
`arn:aws:iam::491618206332:role/gha-s3-tamanu-translations` must trust the calling
repository.

See `../../.github/workflows/README.md` for the full workflow reference and
`environment-and-credentials.md` for how to obtain the secrets.

### 5. Generate survey models

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/generate_survey_models.py
```

### 6. Build reporting assets

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/build_reporting_assets.py
```

This script cleans dbt deps, runs models against the configured target, generates
docs, compiles models, and creates the reporting schema SQL files plus the project
reports list.

### 7. Build and serve docs

```bash
dbt run
dbt docs generate
dbt docs serve
```

## Available scripts

From the `tamanu-source-dbt` package:

- `uv run python dbt_packages/tamanu_source_dbt/scripts/generate_survey_models.py`
- `uv run python dbt_packages/tamanu_source_dbt/scripts/list_tamanu_reports.py`
- `uv run python dbt_packages/tamanu_source_dbt/scripts/build_reporting_assets.py`

## Project structure

See `../standards/dbt-conventions.md` § Model layers for the canonical layer table.
Deployment repos typically organise `models/` by layer prefix (`bases/`, `ref__`,
`lkp__`, `can__`, `der__`, `metric__`, `int__`, `ds__`, `reports/`); legacy domain
directories (`facts/`, `surveys/`, `dim__`/`datasets/`) may also be present in older
deployments.

## Development workflow

1. Create models in the appropriate directory (see layer table referenced above)
2. Test models with `dbt run --select <model_name>`
3. Document models in sibling `.yml` files; populate the `meta:` block per
   `../standards/dbt-metadata.md`
4. Generate docs with `dbt docs generate`
5. Commit per `../standards/git-conventions.md`

## Troubleshooting

### Common issues

1. **Connection error** — verify `.env` variables; cross-check against
   `environment-and-credentials.md`
2. **Package installation failed** — check internet access and GitHub credentials
3. **Model compilation error** — verify SQL syntax and `ref()` / `source()` dependencies

### Getting help

- [dbt documentation](https://docs.getdbt.com/)
- The `tamanu-source-dbt` package docs
- Team lead for database access issues
