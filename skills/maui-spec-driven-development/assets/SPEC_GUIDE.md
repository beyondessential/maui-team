# Spec-Driven Development Guide

How the Maui team uses spec-driven development (SDD) for data work.

## Why SDD

Data work has a specific failure mode: requirements drift between conversation, code, and stakeholder expectation. Stakeholders ask for "the report"; engineers infer; results disagree; trust erodes. Specs anchor the conversation by making the rules explicit, numbered, and traceable into code.

## What we spec

Anything that warrants design effort:

- dbt models (datasets, cohorts, reports)
- Dagster pipelines
- Data extracts (one-off and recurring)
- Data migrations
- Tupaia dashboards

We don't spec trivial fixes, hotfixes, or exploratory analysis.

## Where specs live

| Artefact | Location |
|---|---|
| Templates | `assets/templates/` |
| This guide | `assets/SPEC_GUIDE.md` |
| Populated specs | `<repo>/specs/<artefact-type>/<spec-name>.md` |

A spec lives with the code it describes. Templates and this guide are distributed via the `.maui` submodule and are relative to this skill's directory.

## Lifecycle

| Status | Means |
|---|---|
| `draft` | Author is writing |
| `review` | Open for team feedback |
| `approved` | Signed off; implementation can start |
| `implemented` | Code matches spec; all acceptance criteria pass |
| `deprecated` | Spec retired |

Bumping status is a team convention, not a tool. Update the status line in the spec's identity block as it progresses. We may add a PR check later — for now, the team agrees by review.

## Spec anchoring

Every business logic rule in a spec has a numbered ID (`BL-001`, `BL-002`…). Implementing code references the ID in a comment:

```sql
-- BL-001: Exclude soft-deleted records (see specs/dbt-model/patients_dataset.md)
where deleted_at is null
```

Tests reference the same IDs. A reader can grep one ID and find rule, code, and test in a single search.

**The pointer is one-way: code → spec.** Specs should not cite code by file path and line number. Line numbers rot on every unrelated edit; the rot is silent (no static check catches it) and induces spec-side churn on every refactor that moves a function. If a spec rule needs to reference code at all, use a symbol name (e.g. `run_postgres_copy_import`, `_commit_batch`) — stable across line moves and still grep-navigable. In practice, a tight BL clause rarely needs a code reference at all: the spec describes behaviour, the code implements it, and the `# BL-XXX:` comment provides the navigation trail.

## ID conventions

| Prefix | Use |
|---|---|
| `BL-XXX` | Business logic clause |
| `AC-XXX` | Acceptance criterion (testable check) |
| `OQ-XXX` | Open question |
| `DV-XXX` | Divergence between current code and ideal spec (retrospective specs) |
| `DQ-XXX` | Data quality check (migration specs) |

Number from 001 within each prefix per spec. Don't reuse IDs across specs.

## Acceptance criteria

Each spec lists numbered acceptance criteria that map to BL clauses. Each AC is implemented as a dbt test, Great Expectations expectation, or other verifiable check. A spec moves to `implemented` when all ACs pass.

## Authoring a spec

1. Pick the right template from this skill's `assets/templates/` directory (distributed via the `.maui` submodule).
2. Copy it into your repo: `<your-repo>/specs/<artefact-type>/<spec-name>.md`.
3. Fill in the identity block, then work top-down.
4. Mark unknowns as `[TBD: <question>]` rather than guessing. Promote each TBD to an `OQ-XXX` before review.
5. Number every distinct rule as `BL-XXX` from the start — don't renumber later.
6. Open a PR with status `draft` or `review`.

## Reviewing a spec

Reviewers should focus on:

- Is the purpose clear and grounded in a concrete user need?
- Are the inputs and outputs specified at the right level of detail?
- Is each `BL` clause atomic, testable, and unambiguous?
- Does each `AC` map to an implementable test?
- Are open questions captured rather than glossed over?

## Tightening

A `BL` / `DQ` clause should compress to one declarative sentence. If a clause runs to three or more sentences, cut these patterns:

- **Embedded rationale** ("because X, so Y") — move to `DV` or Change log.
- **Duplicated cross-references** — one link is enough.
- **Restated invariants** — anchor in one clause; the other refers back.
- **Multi-clause parentheticals** — split or drop.
- **Code-line hand-holding** — drop entirely. Specs don't cite code by line number (see *Spec anchoring*); the `# BL-XXX:` comment in the code is the trail.

A 40% length reduction with no normative loss is normal on a first pass.

## Before merging

Specs accrete on a feature branch (multiple change-log entries, `DV-XXX` items that get resolved mid-branch, `OQ-XXX` items that get answered before approval). Before merging to the trunk, **collapse the resolved entries rather than mark them resolved**:

- `DV-XXX` items resolved on this branch → **delete the row** rather than strike-through or mark "Resolved YYYY-MM-DD". From the trunk's perspective the divergence never existed.
- `OQ-XXX` items closed on this branch → same treatment. Delete the row.
- Multiple change-log entries from the branch's iteration → squash into one entry dated at merge time. The trunk's change log records *what landed*, not how the branch got there.
- Identity-block `Created` / `Last updated` dates → align with the merge date if the spec is landing as one record.

The principle: the trunk's spec is a contract, not a history book. Commit history captures *how we got here*; the spec captures *what we agreed to*. Resolved divergences and answered open questions are tracked in git, not in the spec.

This applies even for retrospective specs landing alongside their first implementation — the `DV-XXX` items that were resolved as part of bringing the spec and code into alignment shouldn't ship as historical record in the merged spec.

## Retrospective specs

When documenting existing code, write the spec to describe the *ideal* state. Where current code diverges, capture each divergence as a `DV-XXX` work item. Each divergence becomes follow-up work to bring code in line with spec — never edit the spec to match buggy code.

## See also

- `templates/dbt-model.md`
- `templates/dagster-pipeline.md`
- `templates/data-extract.md`
- `templates/data-migration.md`
- `templates/tupaia-dashboard.md`
