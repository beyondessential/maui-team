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
   @./.maui/knowledge/standards/sdd-conventions.md
   @./.maui/knowledge/standards/dbt-conventions.md
   ```
   `sdd-conventions.md` applies to every Maui repo (we use SDD universally) — import it by default. Otherwise only import the standards relevant to the repo — don't import all of them.

   Repos that use dbt (`data-lake`, `data-staging`, `tamanu-source-dbt`, `tamanu-dbt-*`) should also import:
   ```
   @./.maui/knowledge/standards/dbt-metadata.md
   @./.maui/knowledge/standards/parallel-agents.md
   ```

   Repos that model program registries as cohorts (`tamanu-dbt-*` with program registry data) should also import:
   ```
   @./.maui/knowledge/standards/derived-elements-conventions.md
   ```

   Repos that consume or contribute to the canonical clinical model (`tamanu-source-dbt`, `tamanu-dbt-*`, `data-staging`, `data-lake`) should also import architectural context so agents ground decisions in the team's data architecture, not just the conventions that flow from it:
   ```
   @./.maui/knowledge/architecture/data-architecture.md
   ```
   Architecture docs at `review` status are imported as **non-binding context** — agents should treat them as the team's working direction, not yet as rules. Conventions in `standards/` carry the operative rules; the architecture explains the rationale and direction. Status `draft` docs are not imported by anyone; status `approved` docs are imported as rules in the same way as standards.

   See [`knowledge/README.md`](README.md) for what each directory contains.

3. Create a local AI context file (add to `.gitignore` — it is not committed) that points to `AGENT.md`. The filename depends on the tool:
   - **Claude Code**: `CLAUDE.md` containing `@./AGENT.md`
   - **Cursor**: `.cursorrules` containing `@./AGENT.md` (or use Cursor's project rules)
   - **Other tools**: consult the tool's documentation for how to set a project-level context file

   `AGENT.md` is the committed, tool-agnostic entry point. Local config files are per-developer and never committed.

---

## Maui team context

Maui is a data engineering team building and maintaining data pipelines and analytics infrastructure for Tamanu (electronic health records) and Tupaia (data visualisation platform). The stack is primarily Python, Dagster, and dbt.

Repositories:
- `data-lake` — Dagster orchestration; Tamanu analytics; other pipelines (FluTracking, NIWA). Rename to `bes-data-pipelines` is in flight but pending dependency updates, so the repo and references are still `data-lake` for now
- `data-staging` — Standard Tupaia reporting models for Tamanu data (merging into `tamanu-source-dbt`)
- `tamanu-source-dbt` — Mono-repo for Tamanu and Tupaia reporting; absorbing `data-staging` (the merge is in flight)
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

## Opening PRs

When composing a PR body (via `gh pr create --body`, the API, or any other
flow that supplies a body), follow the structure in the repo's
`.github/pull_request_template.md` (Summary, Linear / spec, Test plan,
Risk / rollback, Checklist). The template only auto-populates when no body
is supplied; agents that write their own body bypass it unless explicitly
told to follow it.

---

## Spec-driven development

For any non-trivial new dbt model (`ref__` / `lkp__` / `can__` / `der__` /
`metric__` / `ds__`), Dagster pipeline, data extract, migration, or dashboard:

1. **Write the spec.** Spec lives at `<repo>/specs/<artefact-type>/<spec-name>.md`.
   Start from a template in `.maui/skills/maui-spec-driven-development/assets/templates/`.
2. **Each `BL-XXX` clause is one declarative sentence.** No embedded rationale,
   no file:line references, no code-line hand-holding. A 40% length reduction
   on first review is normal.
3. **Anchor code to clauses.** At each implementation site add a `# BL-XXX:`
   (or `-- BL-XXX:`) comment naming the clause it fulfils. Tests prefix the
   AC: `test_ac_001_<descriptor>` for pytest, `ac_001_<descriptor>` for dbt.
4. **Spec and code land in the same PR.** Before merging, squash in-branch
   change-log rows to one merge-dated entry; delete (don't annotate) any
   resolved `DV-XXX` / `OQ-XXX` rows. The trunk spec is a contract, not a
   history book.
5. **Lifecycle.** New specs start `Status: draft`, bump to `review` when
   opening the PR, `implemented` when ACs all pass.

Skip specs for trivial bugfixes, hotfixes, or throwaway exploration.

Full convention set: `@./.maui/knowledge/standards/sdd-conventions.md`.
Authoring guide and templates: `.maui/skills/maui-spec-driven-development/`.

---

## Code review

This repo uses Claude Code review via GHA. See `.maui/REVIEW.md` (or a repo-local `REVIEW.md`) for review criteria. Claude runs automatically on PR open/reopen; re-trigger with `/review` comment.

Claude Code review is a required status check. A human reviewer approval is also required before merging.
