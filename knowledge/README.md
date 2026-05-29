# knowledge/

Shared AI assistant context for the Maui team. Imported into individual repos via the `.maui/` submodule (see [`AGENT.base.md`](AGENT.base.md) for the import pattern).

## What goes where

| Directory | Question it answers | Document shape | Typical status |
|---|---|---|---|
| [`architecture/`](architecture/) | Where are we going? Why is the system shaped this way? | Decisions, trade-offs, open questions | Often `draft` or `review` |
| [`standards/`](standards/) | What should I do? | Rules, patterns, examples | `approved` and stable |
| [`runbooks/`](runbooks/) | How do I do X? | Step-by-step procedures | `approved` once procedure is settled |

Match the question to the directory:
- Implementing something? → start in `standards/`
- Trying to understand the design? → start in `architecture/`
- Executing a specific task? → start in `runbooks/`

## Files at this level

- [`AGENT.base.md`](AGENT.base.md) — base AI context imported by every Maui repo. Repo-specific rules extend it in the repo's own `AGENT.md`.
- [`glossary.md`](glossary.md) — terminology (Tamanu, Tupaia, OMOP, layer prefixes, the three `data-lake`s, …). Lift definitions from here when an unfamiliar term appears in any other doc.

## What's currently in each directory

### [`architecture/`](architecture/)

- [`data-architecture.md`](architecture/data-architecture.md) — entry point for the data architecture (status: `review`). The detail lives in the [`data-architecture/`](architecture/data-architecture/) subdirectory: decisions, production-promotion mechanics, Phase 0, open questions, consequences, developer quick reference
- `north-star.svg` — the architecture diagram referenced from `data-architecture.md`

### [`standards/`](standards/)

- [`dbt-conventions.md`](standards/dbt-conventions.md) — dbt model layers, materialisation rules, env-aware switch, `bases/`-only rule
- [`dbt-metadata.md`](standards/dbt-metadata.md) — required `meta:` block fields on dbt models (owner, domain, tier, classification)
- [`tamanu-dbt-conventions.md`](standards/tamanu-dbt-conventions.md) — Tamanu-specific dbt patterns: version branches, `data_staging` package, source naming, recurring patterns
- [`derived-elements-conventions.md`](standards/derived-elements-conventions.md) — `der__` layer (cohorts, eras, episodes), OMOP-lite columns, registry consolidation
- [`sql-conventions.md`](standards/sql-conventions.md) — SQL formatting, casing, aliasing
- [`python-conventions.md`](standards/python-conventions.md) — Python conventions ruff doesn't enforce
- [`dagster-conventions.md`](standards/dagster-conventions.md) — Dagster asset and pipeline patterns
- [`testing-conventions.md`](standards/testing-conventions.md) — test type selection, naming, AC linkage
- [`git-conventions.md`](standards/git-conventions.md) — branch naming, commit messages, merge strategy
- [`linear-conventions.md`](standards/linear-conventions.md) — Linear issue tracking conventions
- [`release-conventions.md`](standards/release-conventions.md) — versioning and release process
- [`sdd-conventions.md`](standards/sdd-conventions.md) — spec-driven development conventions (the canonical SDD reference; the skill is the authoring tool)
- [`parallel-agents.md`](standards/parallel-agents.md) — when and how to use parallel sub-agents

### [`runbooks/`](runbooks/)

- [`onboarding-checklist.md`](runbooks/onboarding-checklist.md) — first-week setup for new team members
- [`environment-and-credentials.md`](runbooks/environment-and-credentials.md) — how to obtain credentials for Maui repos
- [`tamanu-dbt-setup.md`](runbooks/tamanu-dbt-setup.md) — set up a `tamanu-dbt-<deployment>` project
- [`new-report.md`](runbooks/new-report.md) — add a new Tamanu report (with production-bundle context)
- [`new-derived-element.md`](runbooks/new-derived-element.md) — add a new derived element (cohort initially; eras/episodes follow)
- [`macro-change-impact.md`](runbooks/macro-change-impact.md) — assess and roll out a macro change across models
- [`refactoring-guide.md`](runbooks/refactoring-guide.md) — phased refactoring playbook across all Maui repositories

## Contributing

- **Adding a standard** — new file in [`standards/`](standards/). Keep rules concise and actionable; these are read by AI assistants, not browsing humans.
- **Adding an architecture doc** — new file in [`architecture/`](architecture/) with a status header (`draft` / `review` / `approved`). Sibling diagrams (e.g. `.svg`) live alongside.
- **Adding a runbook** — new file in [`runbooks/`](runbooks/) using clear numbered steps; include prerequisites and verification steps.
- **Adding a glossary term** — append to [`glossary.md`](glossary.md) in the right section; keep definitions short.

Australian English throughout. Prefer short, direct rules over lengthy explanations. Repo-specific content extends these files in the repo's own `AGENT.md` rather than being added here.

CI validates internal markdown links and the `@./.maui/...` example imports in
the README and runbooks (see [`../.github/workflows/link-check.yml`](../.github/workflows/link-check.yml) and
[`../.github/workflows/imports-check.yml`](../.github/workflows/imports-check.yml)).
Run `python scripts/check_agent_imports.py` locally before pushing if you've
renamed files referenced from import examples.
