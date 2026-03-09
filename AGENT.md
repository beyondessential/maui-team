# Maui Team Central Repository

This repo provides shared AI assistant knowledge and reusable GHA workflows for all Maui team repositories.

## Structure

- `REVIEW.md` — Claude Code review reference. Team baseline; individual repos can override with their own copy.
- `AGENT.md` — this file. AI context for working on this repo itself.
- `.github/workflows/` — reusable GHA workflows consumed via `uses:` in other repos.
- `knowledge/AGENT.base.md` — base AI context imported by all Maui repos via the `.maui/` submodule.
- `knowledge/standards/` — coding and tooling conventions (git, Python, SQL, dbt, Dagster, testing).
- `knowledge/prompts/` — reusable prompt templates for common tasks.
- `knowledge/architecture/` — Maui data platform architecture documentation.
- `knowledge/runbooks/` — operational guides for known failure scenarios.

## Contributing

### Adding or updating standards
Edit the relevant file in `knowledge/standards/`. Keep rules concise and actionable — these are read by AI assistants, not humans browsing docs.

### Adding a reusable workflow
Add a `.yml` file to `.github/workflows/` with `on: workflow_call`. Document inputs and secrets in `.github/workflows/README.md`.

### Knowledge file conventions
- Australian English throughout
- Use headings to structure sections clearly
- Prefer short, direct rules over lengthy explanations
- Where rules are repo-specific, note "extend in repo `AGENT.md`" rather than adding project-specific content here
