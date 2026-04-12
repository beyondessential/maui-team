# Maui Team — Shared AI Context

This file is imported by all Maui repositories via the `.maui/` submodule. It provides team-wide context and conventions. Repo-specific rules go in the repo's own `AGENT.md`, below the import line.

## How to use in a repo

1. Add the `.maui` submodule:
   ```bash
   git submodule add https://github.com/beyondessential/maui-team .maui
   ```

2. Create `AGENT.md` at the repo root. Import this file first, then add the relevant standards and repo-specific context:
   ```
   @./.maui/knowledge/AGENT.base.md
   @./.maui/knowledge/standards/git-conventions.md
   @./.maui/knowledge/standards/dbt-conventions.md
   ```
   Only import the standards relevant to the repo — don't import all of them.

   Repos that use dbt (`data-lake`, `data-staging`, `tamanu-source-dbt`, `tamanu-dbt-*`) should also import:
   ```
   @./.maui/knowledge/standards/metadata.md
   @./.maui/knowledge/standards/agent-patterns.md
   ```

   Repos that model program registries as cohorts (`tamanu-dbt-*` with program registry data) should also import:
   ```
   @./.maui/knowledge/standards/cohort-conventions.md
   ```

3. Create a local AI context file (add to `.gitignore` — it is not committed) that points to `AGENT.md`. The filename depends on the tool:
   - **Claude Code**: `CLAUDE.md` containing `@./AGENT.md`
   - **Cursor**: `.cursorrules` containing `@./AGENT.md` (or use Cursor's project rules)
   - **Other tools**: consult the tool's documentation for how to set a project-level context file

   `AGENT.md` is the committed, tool-agnostic entry point. Local config files are per-developer and never committed.

---

## Maui team context

Maui is a data engineering team building and maintaining data pipelines and analytics infrastructure for Tamanu (electronic health records) and Tupaia (data visualisation platform). The stack is primarily Python, Dagster, and dbt.

Repositories:
- `data-lake` — Dagster orchestration; Tamanu analytics; other pipelines (FluTracking, NIWA)
- `data-staging` — Standard Tupaia reporting models for Tamanu data (merging into `tamanu-source-dbt`)
- `tamanu-source-dbt` — Mono-repo for Tamanu and Tupaia reporting; source of base models for `data-staging`
- `tamanu-dbt-*` — Deployment-specific Tamanu dbt models
- `fsm-data-migration` — Migration from FSM EHR to Tamanu
- `datatools` — CLI commands for data tasks in Tamanu/Tupaia

---

## Language and writing style

- **Australian English** throughout all code, documentation, comments, and configuration
- Be concise — prefer a clear short statement over a lengthy justification
- In comments and docstrings: say what something does, not what is obvious

---

## Git conventions

See `@./.maui/knowledge/standards/git-conventions.md` for full details.

Summary:
- Branch naming: `feature/`, `fix/`, `chore/`, `refactor/`, `docs/`
- Commit messages: imperative mood, conventional commit format
- PRs: clear description, testing notes, request review before merging
- Main branch is protected; never commit directly to `main`

---

## Code review

This repo uses Claude Code review via GHA. See `.maui/REVIEW.md` (or a repo-local `REVIEW.md`) for review criteria. Claude runs automatically on PR open/reopen; re-trigger with `/review` comment.

Claude Code review is a required status check. A human reviewer approval is also required before merging.
