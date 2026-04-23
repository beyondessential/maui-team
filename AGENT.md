# Maui Team Central Repository

This repo provides shared AI assistant knowledge and reusable GHA workflows for all Maui team repositories.

## Structure

- `REVIEW.md` — Claude Code review reference. Team baseline; individual repos can override with their own copy.
- `AGENT.md` — this file. AI context for working on this repo itself.
- `.github/workflows/` — reusable GHA workflows consumed via `uses:` in other repos.
- `knowledge/AGENT.base.md` — base AI context imported by all Maui repos via the `.maui/` submodule.
- `knowledge/runbooks/` — step-by-step operational guides.
- `knowledge/standards/` — coding and tooling conventions (git, Python, SQL, dbt, Dagster, testing).

## Contributing

### Adding or updating runbooks
Add or edit files in `knowledge/runbooks/`. Runbooks cover setup/onboarding procedures and operational tasks (e.g. deployments, migrations, incident response). Use clear numbered steps; include prerequisites and verification steps where relevant. Runbooks may be followed by humans or AI agents.

### Adding or updating standards
Edit the relevant file in `knowledge/standards/`. Keep rules concise and actionable — these are read by AI assistants, not humans browsing docs.

### Setting up a new repo
See `README.md` for the full setup steps (submodule, AGENT.md, workflow, CLAUDE.md gitignore).

### Adding a reusable workflow
Add a `.yml` file to `.github/workflows/` with `on: workflow_call`. Document inputs and secrets in `.github/workflows/README.md`.

## Refactoring

See `knowledge/runbooks/refactoring-guide.md` for the phased refactoring playbook covering all Maui-managed repositories.

### Knowledge file conventions
- Australian English throughout
- Use headings to structure sections clearly
- Prefer short, direct rules over lengthy explanations
- Where rules are repo-specific, note "extend in repo `AGENT.md`" rather than adding project-specific content here
