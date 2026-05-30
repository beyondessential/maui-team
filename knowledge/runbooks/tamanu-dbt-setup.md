# Tamanu dbt project setup

Set up a new `tamanu-dbt-<deployment>` (or fresh clone of one). Architecture:
[`../architecture/data-architecture.md`](../architecture/data-architecture.md).
Conventions: [`../standards/dbt-conventions.md`](../standards/dbt-conventions.md).

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Git with submodule support
- PostgreSQL access to the Tamanu replica (ask the data lead)

## Steps

### 1. Clone + env

```bash
git clone <repository-url>
cd <project-directory>
uv sync
```

### 2. `.env`

```bash
cp .env.example .env
# Fill in DB credentials (ask the data lead)
```

### 3. dbt deps

```bash
dbt deps
dbt debug
```

### 4. Customise

- `pyproject.toml` — `name` (`tamanu-dbt-fj`), `version` (Tamanu version)
- `dbt_project.yml` — `name` and `profile` matching `pyproject.toml`
- `config/profiles.yml` — profile name + `target` (`dev` / `staging` / `prod`)
- `packages.yml` — `revision` pinned to Tamanu version (`2.32.0`); never a branch
- `README.md` — replace boilerplate with deployment-specific title/description

**`AGENT.md`** at repo root:

```
@./.maui/knowledge/AGENT.base.md
@./.maui/knowledge/standards/git-conventions.md
@./.maui/knowledge/standards/sql-conventions.md
@./.maui/knowledge/standards/dbt-conventions.md
@./.maui/knowledge/standards/tamanu-dbt-conventions.md
@./.maui/knowledge/standards/dbt-metadata.md

---

## Repository: <repo-name>

<Brief description.>
```

**`CLAUDE.md`** (gitignored, per-developer):

```
@./AGENT.md
```

**`.github/workflows/publish-artifacts.yml`:**

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

Required: `META_CERT`, `META_KEY`, `META_URL`. AWS via OIDC — IAM role
`arn:aws:iam::491618206332:role/gha-s3-tamanu-translations` must trust the repo.
See [`../../.github/workflows/README.md`](../../.github/workflows/README.md).

### 5. Generate survey models

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/generate_survey_models.py
```

### 6. Build reporting assets

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/build_reporting_assets.py
```

Cleans deps, runs models, generates docs + compiled SQL + reports list.

### 7. Build + serve

```bash
dbt run
dbt docs generate
dbt docs serve
```

## Available scripts

From `tamanu-source-dbt`:

- `generate_survey_models.py`
- `list_tamanu_reports.py`
- `build_reporting_assets.py`

Invoke via `uv run python dbt_packages/tamanu_source_dbt/scripts/<name>.py`.

## Project structure

Layer table: [`../standards/dbt-conventions.md`](../standards/dbt-conventions.md)
§ Model layers. Typical organisation by layer prefix (`bases/`, `ref__`, `lkp__`,
`surveys/`, `can__`, `der__`, `metric__`, `int__`, `ds__`, `reports/`); older
deployments may also have legacy `facts/` / `dim__` / `datasets/`.

## Workflow

1. Create models in the right layer directory
2. `dbt run --select <model_name>`
3. Document in sibling `.yml`; `meta:` per
   [`../standards/dbt-metadata.md`](../standards/dbt-metadata.md)
4. `dbt docs generate`
5. Commit per [`../standards/git-conventions.md`](../standards/git-conventions.md)

## Troubleshooting

- **Connection error** — check `.env` vars; ask the data lead if creds are stale
- **Package install failed** — internet / GitHub access
- **Compilation error** — SQL syntax or `ref()` / `source()` dependencies

Help: [dbt docs](https://docs.getdbt.com/), the `tamanu-source-dbt` package, or
the team lead for DB access.
