# Spec-Driven Development (SDD) Conventions

How the Maui team uses spec-driven development for data work. This file is the
canonical reference for the conventions; the `maui-spec-driven-development` skill
(distributed via `.maui/skills/`) is the authoring tool that produces specs
following these conventions.

## When to write a spec

Spec anything that warrants design effort and would benefit from a written contract
between author, reviewer, and future maintainer:

- New `ref__`, `lkp__`, `can__`, `der__`, `metric__`, or `ds__` models
- New Tamanu reports involving non-trivial business logic
- New Dagster pipelines
- Data extracts (one-off and recurring)
- Data migrations
- New Tupaia dashboards and map overlays

**Do not** write specs for:
- Trivial bug fixes
- Hotfixes (time-to-fix outweighs spec value)
- Throwaway exploration (notebooks, scratch SQL)
- One-off ad-hoc queries

The test: would a teammate reading the code in six months know *why* it does what it
does? If yes, no spec. If no, write a spec.

## Where specs live

| Artefact | Location |
|---|---|
| Spec templates | `.maui/skills/maui-spec-driven-development/assets/templates/` |
| The authoring guide | `.maui/skills/maui-spec-driven-development/assets/SPEC_GUIDE.md` |
| Populated specs | `<repo>/specs/<artefact-type>/<spec-name>.md` |

Templates and the guide are distributed via the `.maui` submodule. Populated specs
live in the consuming repo, alongside the code they describe.

## Lifecycle

| Status | Means |
|---|---|
| `draft` | Author is writing; not yet ready for feedback |
| `review` | Open for team feedback |
| `approved` | Team has signed off; implementation can start |
| `implemented` | Code matches spec; all acceptance criteria pass |
| `deprecated` | Spec retired; kept for history |

Status is a team convention, not a tool enforcement. Bump the status line in the
spec's identity block as it progresses. A future PR check may gate merge on spec
status; not in place yet.

## ID conventions

Every distinct rule, criterion, question, or divergence in a spec has a numbered ID
with a prefix:

| Prefix | Use |
|---|---|
| `BL-NNN` | Business logic clause |
| `AC-NNN` | Acceptance criterion (a testable check) |
| `OQ-NNN` | Open question (with owner + due date) |
| `DV-NNN` | Divergence between current code and ideal spec (retrospective specs only) |
| `DQ-NNN` | Data quality check (migration specs) |

Number from 001 within each prefix per spec. **Never reuse IDs.** If a clause is
deleted, renumber later clauses only if the spec is still in `draft`; in
`review` / `approved` / `implemented`, retire the ID and don't reuse it.

## Spec anchoring — the code → spec pointer

Implementing code references the BL/DQ ID in a comment:

```sql
-- BL-001: Exclude soft-deleted records (see specs/dbt-model/patients_dataset.md)
where deleted_at is null
```

```python
# BL-003: Skip rows where patient consent was withdrawn
df = df[df['consent_withdrawn'].isna()]
```

Tests reference the same IDs:

```yaml
- name: ac_001_no_soft_deleted   # asserts BL-001
  test: <generic or singular test>
```

A reader can grep one ID and find: spec clause, implementing code, asserting test.

**The pointer is one-way: code → spec.** Specs do **not** cite code by file path
and line number. Line numbers rot on every unrelated edit; the rot is silent (no
static check catches it). If a spec rule needs to reference code at all, use a
symbol name (e.g. `run_postgres_copy_import`) — stable across line moves and still
grep-navigable.

In practice, a tight BL clause rarely needs a code reference: the spec describes
behaviour, the code implements it, and the `BL-NNN` comment provides navigation.

## Authoring a spec

1. Pick the artefact type and copy the template from
   `.maui/skills/maui-spec-driven-development/assets/templates/` to
   `<repo>/specs/<artefact-type>/<spec-name>.md`
2. Fill in the identity block (Name, Type, Status, Owner, Linear issue, Created,
   Last updated, …)
3. Work top to bottom. Mark unknowns as `[TBD: <question>]` rather than guessing
4. Number every distinct rule as `BL-001`, `BL-002`… from the start — do not
   renumber later
5. Promote each `[TBD]` to an `OQ-XXX` row with owner + due date before moving the
   spec from `draft` to `review`
6. Open a PR with status `draft` or `review`

## Reviewing a spec

Reviewer checklist:

- Is the purpose clear and grounded in a concrete user need?
- Are inputs and outputs specified at the right level of detail?
- Is each `BL` clause atomic, testable, and unambiguous?
- Does each `AC` map to an implementable test?
- Are open questions captured rather than glossed over?
- For retrospective specs (Mode A): are divergences from the ideal explicitly
  listed as `DV-XXX` items rather than the spec being edited to match buggy code?

## Tightening clauses

A `BL` / `DQ` clause should compress to one declarative sentence. If a clause runs
to three or more sentences, cut these patterns:

- **Embedded rationale** ("because X, so Y") — move to `DV` or Change log
- **Duplicated cross-references** — one link is enough
- **Restated invariants** — anchor in one clause; the other refers back
- **Multi-clause parentheticals** — split or drop
- **Code-line hand-holding** — drop entirely

A 40% length reduction with no normative loss is normal on a first pass.

## Before merging

Specs accrete on a feature branch (multiple change-log entries, `DV-XXX` items that
get resolved mid-branch, `OQ-XXX` items that get answered before approval). Before
merging to the trunk, **collapse the resolved entries rather than mark them
resolved**:

- `DV-XXX` items resolved on this branch → **delete the row**, not strike-through.
  From the trunk's perspective the divergence never existed
- `OQ-XXX` items closed on this branch → same treatment. Delete the row
- Multiple change-log entries from the branch → squash into one entry dated at
  merge time
- Identity-block `Created` / `Last updated` dates → align with the merge date if
  the spec is landing as one record

Principle: the trunk's spec is a contract, not a history book. Commit history
captures *how we got here*; the spec captures *what we agreed to*.

## Retrospective specs (Mode A)

When documenting existing code:
- Write the spec to describe the *ideal* state
- Where current code diverges, capture each divergence as a `DV-XXX` work item
- Each divergence becomes follow-up work to bring code into spec
- **Never edit the spec to match buggy code.**

## Code review hooks

Reviewers flag PRs that:

- Introduce new non-trivial logic without `BL-XXX` spec-anchor comments when a spec
  exists for that area — **🟡 Suggestion**
- Carry `BL-XXX` references that don't match any clause in the corresponding spec
  — **🟡 Suggestion**
- Introduce a new model, pipeline, or extract without an accompanying spec —
  **🟡 Suggestion** (suggest creating one)
- Directly contradict a spec clause they reference (e.g. `-- BL-003: Exclude
  deleted` but the `where` clause does the opposite) — **🔴 Blocker**

See [`../../REVIEW.md`](../../REVIEW.md) § Spec-driven development for the review
rubric.

## See also

- [`linear-conventions.md`](linear-conventions.md) — issue references in spec
  identity blocks
- [`git-conventions.md`](git-conventions.md) — branch naming for spec PRs
- The `maui-spec-driven-development` skill's `SPEC_GUIDE.md` for authoring details
- The skill's `references/sdd-principles.md` for background on SDD theory
