# Agent Patterns

Guidance for effective agentic workflows in Maui repositories. These patterns apply across
all dbt, Python, and Dagster repos and are tool-agnostic — follow them whether working with
Claude Code, Cursor, Codex, or any other AI coding assistant.

---

## When to use parallel agents

Spawn parallel sub-agents when tasks are **independent** and can proceed simultaneously.

Good candidates:
- Exploring multiple model layers at once (bases, datasets, reports)
- Running independent verification checks (linting, config validation, translation checks)
- Impact analysis across a large codebase before making changes
- Cross-repo checks (e.g. does a deployment repo already handle an edge case?)

## When not to parallise

- Sequential tasks where each step depends on the result of the previous one
- Single-file changes with clear, bounded scope
- Tasks where full context must accumulate before the next decision

---

## Parallel exploration pattern

When the scope of a change is uncertain, explore multiple areas simultaneously rather
than sequentially:

```
Agent A → search models/bases/ for pattern X
Agent B → search models/datasets/ for pattern X
Agent C → search models/reports/ for pattern X
```

Synthesise all results before writing any code. This avoids discovering halfway through
that many more files need updating.

## Verification pattern

After making changes, run independent checks in parallel rather than one at a time:

```
Agent A → sqlfluff lint .
Agent B → python scripts/validate_report_configs.py
Agent C → python scripts/check_translations.py
```

Only proceed to commit when all checks pass.

## Context discipline

When delegating to a sub-agent, pass only what it needs — not the full session history.
A focused prompt with specific file paths or search patterns returns faster, more relevant
results than a broad exploration request.

Good: "Search `models/reports/sql/standard/` for files using a hardcoded `at time zone`
expression rather than the `to_user_selected_timezone` macro — return file paths only."

Avoid: "Look through the whole codebase and tell me everything about timezone handling."

---

## Runbooks

For common multi-step workflows, follow the runbooks in `knowledge/runbooks/`. Runbooks
are structured so either a human or an AI agent can execute them step by step, with
explicit checkpoints and verification steps.

Available runbooks:
- `new-report.md` — adding a standard + sensitive report pair
- `macro-change-impact.md` — assessing and rolling out a macro to existing models
- `tamanu-dbt-setup.md` — setting up a new deployment repo
- `new-cohort.md` — building a program registry cohort using the OMOP-inspired semantic layer
