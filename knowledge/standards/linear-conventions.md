# Linear Conventions

How the Maui team uses Linear. Extend in repo `AGENT.md` for project-specific
conventions.

- **Workspace:** `beyondessential`
- **Team prefix:** `MAUI` (issue IDs: `MAUI-NNN`)

Reference `MAUI-NNN` in spec identity blocks, PR titles, and branch names.

## Lifecycle

Triage → Backlog → Todo → In Progress → In Review → Done / Cancelled. Don't
leave issues stuck in **In Review** after the PR merges.

## Required fields

- **Title** — concrete, verb-led
- **Description** — context, requirements, links; spec path once the spec exists
- **Assignee** — once out of Triage
- **Labels** — at least one of `data`, `tamanu`, `tupaia`, `infra`, `docs`, `migration`
- **Project** — Maui project for team work; blank for ad-hoc partner requests

Estimates and cycles are optional and lead-managed.

## Linking to PRs and specs

- **PR title:** `feat(reports): add diabetes line-list report (MAUI-1234)`
- **Branch:** `feat/maui-1234-diabetes-line-list`
- **Spec identity block:** populate the Linear issue field with the URL
- **PR body:** Linear auto-links from `MAUI-NNN` mentions

When a spec is created, paste its path back into the Linear description.

## What gets an issue

Yes: new models / pipelines / extracts / migrations / dashboards, bug fixes worth
tracking, Phase 0 deliverables, externally-requested work.

No: speculative ideas, doc typo fixes (just open a PR), single-thread chats.

## Triage

Data lead runs weekly. Untriaged > 5 working days escalates.

## See also

- [`git-conventions.md`](git-conventions.md)
- [`sdd-conventions.md`](sdd-conventions.md)
