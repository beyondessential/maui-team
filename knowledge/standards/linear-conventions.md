# Linear Conventions

How the Maui team uses Linear for issue tracking. Brief; extend in repo `AGENT.md` if
a repo has project-specific Linear conventions.

## Workspace and team

- **Workspace:** `beyondessential`
- **Team prefix:** `BES`
- **Project key in URLs:** `BES-NNN` (e.g. `BES-1234`)

Issue IDs are referenced as `BES-NNN` in spec identity blocks, PR titles, and
branch names.

## Issue lifecycle

Use the workflow Linear ships with; the team conventions sit on top:

- **Triage** — new issues land here from intake (Slack, partner, on-call)
- **Backlog** — accepted but not yet scheduled
- **Todo** — scheduled, ready to pick up
- **In Progress** — actively being worked on
- **In Review** — PR open, awaiting review
- **Done** — merged and verified
- **Cancelled** — won't fix

Move issues forward as work progresses. Don't leave issues stuck in **In Review**
after the PR merges — close them or mark **Done**.

## Required fields when opening an issue

- **Title** — concrete and verb-led ("Add `der__cohort_diabetes` to tamanu-dbt-fj",
  not "diabetes cohort")
- **Description** — context, requirements, links. If the issue warrants a spec,
  note "spec to follow at `<repo>/specs/<artefact-type>/<spec-name>.md`" once the
  spec exists.
- **Assignee** — required once the issue moves out of **Triage**
- **Labels** — at least one of `data`, `tamanu`, `tupaia`, `infra`, `docs`,
  `migration` (extend as needed)
- **Project** — link to the Maui project if it's team work; leave blank for ad-hoc
  partner requests

Estimates and cycle assignment are optional; the data lead manages them at the
project level.

## Linking issues to PRs and specs

- **PR title** — include the Linear ID at the end:
  `feat(reports): add diabetes line-list report (BES-1234)`
- **PR body** — Linear auto-links from `BES-NNN` mentions; no manual URL needed
- **Branch name** — include the Linear ID in `kebab-case`:
  `feat/bes-1234-diabetes-line-list`
- **Spec identity block** — every spec template has a **Linear issue** field;
  populate it with the issue's URL

When a spec gets created, paste the spec path back into the Linear issue's
description so reviewers can navigate from issue → spec → code in one step.

## Triage rotation

The data lead runs triage weekly. Untriaged issues older than five working days are
escalated.

## What gets a Linear issue

- New models, pipelines, extracts, migrations, dashboards
- Bug fixes that warrant tracking (not trivial typo fixes)
- Architecture decisions and Phase 0 deliverables (each deliverable in
  [`../architecture/data-architecture.md`](../architecture/data-architecture.md)
  § Phase 0 should have a Linear issue)
- Externally-requested work (from partners, country focal points, programme leads)

Don't open Linear issues for:
- Speculative ideas with no clear owner
- Minor documentation typo fixes (just open a PR)
- Conversations that resolve themselves in a single team-channel thread

## See also

- [`git-conventions.md`](git-conventions.md) — branch naming and commit messages
- [`sdd-conventions.md`](sdd-conventions.md) — when an issue warrants a spec
