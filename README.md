# maui-team

Central repository for shared AI assistant knowledge and reusable GitHub Actions workflows across Maui team repositories.

## Structure

```
maui-team/
├── REVIEW.md                       # Maui team Claude Code review reference
├── AGENT.md                        # AI context for this repo
├── .sqlfluff                       # Canonical SQLFluff config (dbt) — symlink from consuming repos
├── .sqlfluff-raw                   # Canonical SQLFluff config (raw SQL) — symlink from consuming repos
├── ruff.toml                       # Base ruff config — extended by consuming repos
├── .github/workflows/              # Reusable GHA workflows
└── knowledge/
    ├── AGENT.base.md               # Base AI context imported by all Maui repos
    └── standards/                  # Coding and tooling conventions
```

## Setting up a new repo

**1. Add the submodule:**

```bash
git submodule add https://github.com/beyondessential/maui-team .maui
```

**2. Create `AGENT.md`** — import the base, add relevant standards, and add repo-specific context:

```markdown
@./.maui/knowledge/AGENT.base.md
@./.maui/knowledge/standards/git-conventions.md
@./.maui/knowledge/standards/dbt-conventions.md
@./.maui/knowledge/standards/tamanu-conventions.md

## Repository: <repo-name>

<brief description and any repo-specific rules>
```

Choose standards based on the repo type:

| Repo type | Standards |
|-----------|-----------|
| `tamanu-dbt-*`, `data-staging` | git, sql, dbt, tamanu |
| `tamanu-source-dbt`, `data-lake` | git, sql, dbt, tamanu, dagster (data-lake only) |
| `datatools` | git, python, testing |

**3. Create `.github/workflows/claude-code-review.yml`:**

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, reopened]
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

**4. Set up linter configs** by symlinking to the canonical configs in `.maui/`:

*dbt repos* — symlink `.sqlfluff` at the project root (or subdirectory):
```bash
HASH=$(printf '%s' '.maui/.sqlfluff' | git hash-object -w --stdin)
git update-index --add --cacheinfo "120000,$HASH,.sqlfluff"
printf '%s' '.maui/.sqlfluff' > .sqlfluff
```

*Python repos only* — create `ruff.toml` extending the base:
```toml
extend = ".maui/ruff.toml"
```

*Repos with raw (non-dbt) SQL* — symlink `.sqlfluff-raw` → `.maui/.sqlfluff-raw` using the same approach.

**5. Add `CLAUDE.md` to `.gitignore`.** Each developer creates their own `CLAUDE.md` locally (not committed) containing just:

```
@./AGENT.md
```

This is optional — only needed by developers using Claude Code.

**To update the submodule to latest:**

```bash
git submodule update --remote .maui
```

## Code review reference (REVIEW.md)

`REVIEW.md` at the root of this repo is the Maui team baseline. Individual repos can override it by placing their own `REVIEW.md` at their root — a full replacement, so copy and extend as needed. The workflow uses a repo-local `REVIEW.md` if present, otherwise falls back to `.maui/REVIEW.md`.
