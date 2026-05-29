# Maui Team Central Repository

This repo provides shared AI assistant knowledge and reusable GHA workflows for all Maui team repositories.

## Structure

- [`REVIEW.md`](REVIEW.md) — Claude Code review reference. Team baseline; individual repos can override with their own copy.
- [`AGENT.md`](AGENT.md) — this file. AI context for working on this repo itself.
- [`README.md`](README.md) — public-facing setup guide for new repos.
- [`.editorconfig`](.editorconfig), [`.markdownlint.jsonc`](.markdownlint.jsonc) — editor and lint config.
- [`.sqlfluff`](.sqlfluff), [`.sqlfluff-raw`](.sqlfluff-raw), [`ruff.toml`](ruff.toml) — canonical linter configs; consuming repos symlink or extend these.
- [`.github/workflows/`](.github/workflows/) — reusable GHA workflows consumed via `uses:` in other repos, plus this repo's own CI (link check, imports check).
- [`.github/pull_request_template.md`](.github/pull_request_template.md) — PR body template for this repo and reference for consumers.
- [`scripts/`](scripts/) — utility scripts (e.g. `check_agent_imports.py`).
- [`skills/`](skills/) — shared Claude Code skills (currently `maui-spec-driven-development`); consumer repos symlink `.claude/skills` here.
- [`knowledge/`](knowledge/) — see [`knowledge/README.md`](knowledge/README.md) for the index:
  - [`AGENT.base.md`](knowledge/AGENT.base.md) — base AI context imported by every Maui repo via the `.maui/` submodule
  - [`glossary.md`](knowledge/glossary.md) — terminology reference
  - [`architecture/`](knowledge/architecture/) — strategic/architectural docs (north star, decisions, phase 0, open questions)
  - [`standards/`](knowledge/standards/) — coding and tooling conventions (dbt, dbt-metadata, sql, python, dagster, testing, git, linear, release, sdd, tamanu-dbt, derived-elements, parallel-agents)
  - [`runbooks/`](knowledge/runbooks/) — step-by-step operational guides (onboarding, env + credentials, dbt setup, new-report, new-derived-element, macro-change, refactoring)

## Contributing

### Adding or updating runbooks
Add or edit files in `knowledge/runbooks/`. Runbooks cover setup/onboarding procedures and operational tasks (e.g. deployments, migrations, incident response). Use clear numbered steps; include prerequisites and verification steps where relevant. Runbooks may be followed by humans or AI agents.

### Adding or updating standards
Edit the relevant file in `knowledge/standards/`. Keep rules concise and actionable — these are read by AI assistants, not humans browsing docs.

### Adding an architecture doc
New strategic/architectural docs go in `knowledge/architecture/`. Carry a status header (`draft` / `review` / `approved`). Multi-section architectures may split into a subdirectory (see `knowledge/architecture/data-architecture/` for the pattern).

### Adding a glossary term
Append to `knowledge/glossary.md` in the appropriate section; keep definitions short and lift from existing canonical sources where possible.

### Setting up a new repo
See [`README.md`](README.md) for the full setup steps (submodule, AGENT.md, workflow, CLAUDE.md gitignore).

### Adding a reusable workflow
Add a `.yml` file to `.github/workflows/` with `on: workflow_call`. Document inputs and secrets in [`.github/workflows/README.md`](.github/workflows/README.md).

### Editing a skill
Skills live in [`skills/`](skills/) and are distributed to consumer repos via the `.maui/` submodule. Consumer repos symlink `.claude/skills` → `.maui/skills`.

## CI

This repo has its own CI:

- **`link-check.yml`** — validates internal markdown links resolve. Runs on PRs touching `.md` files.
- **`imports-check.yml`** — validates `@./.maui/<path>` example imports in README, AGENT.base, and runbooks point at real files. Runs `scripts/check_agent_imports.py`.

Run the imports check locally before pushing if you've renamed files referenced from import examples:

```bash
python scripts/check_agent_imports.py
```

## Refactoring

See [`knowledge/runbooks/refactoring-guide.md`](knowledge/runbooks/refactoring-guide.md) for the phased refactoring playbook covering all Maui-managed repositories.

### Knowledge file conventions
- Australian English throughout
- Use headings to structure sections clearly
- Prefer short, direct rules over lengthy explanations
- Where rules are repo-specific, note "extend in repo `AGENT.md`" rather than adding project-specific content here
- Cross-references between knowledge files use relative paths; CI catches broken links
