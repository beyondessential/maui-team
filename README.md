# maui-team

Central repository for shared AI assistant knowledge and reusable GitHub Actions workflows across Maui team repositories.

## Repositories

| Repository | Purpose |
|------------|---------|
| `data-lake` | Dagster orchestration; Tamanu analytics via dbt/Tupaia reporting; other data pipelines (FluTracking, NIWA) |
| `data-staging` | Standard models for Tupaia reporting of Tamanu data (merging into `tamanu-source-dbt`) |
| `tamanu-source-dbt` | Mono-repo for Tamanu and Tupaia reporting; includes base models used by `data-staging` |
| `tamanu-dbt-*` | Deployment-specific Tamanu dbt models |
| `fsm-data-migration` | Migration from FSM EHR to Tamanu |
| `datatools` | CLI commands for data tasks in Tamanu/Tupaia |

## Structure

```
maui-team/
├── REVIEW.md                       # Maui team Claude Code review reference
├── AGENT.md                        # AI context for this repo
├── .github/workflows/              # Reusable GHA workflows
└── knowledge/
    ├── AGENT.base.md               # Base AI context imported by all Maui repos
    ├── standards/                  # Coding and tooling conventions
```

## Using the knowledge base (git submodule)

Add this repo as a submodule at `.maui/` in any Maui repository:

```bash
git submodule add https://github.com/<org>/maui-team .maui
git submodule update --init
```

In the consuming repo's `AGENT.md`, import the shared base:

```markdown
@./.maui/knowledge/AGENT.base.md
```

Then add repo-specific context below the import.

To update to the latest version:

```bash
git submodule update --remote .maui
```

## Using reusable workflows

In any Maui repo, create `.github/workflows/code-review.yml`:

```yaml
name: Code Review

on:
  pull_request:
    types: [opened, reopened]
  issue_comment:
    types: [created]

jobs:
  review:
    uses: <org>/maui-team/.github/workflows/claude-code-review.yml@main
    secrets: inherit
```

The workflow uses a repo-local `REVIEW.md` if present, otherwise falls back to `.maui/REVIEW.md`.

## Code review reference (REVIEW.md)

`REVIEW.md` at the root of this repo is the Maui team baseline. Individual repos can override it by placing their own `REVIEW.md` at their root — a full replacement, so copy and extend as needed.
