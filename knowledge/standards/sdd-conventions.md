# SDD Conventions

Canonical reference for Maui's spec-driven development. The
`maui-spec-driven-development` skill (`.maui/skills/`) is the authoring tool.

## When to spec

Spec: new `ref__` / `lkp__` / `can__` / `der__` / `metric__` / `ds__` models,
Tamanu reports with non-trivial logic, Dagster pipelines, data extracts,
migrations, Tupaia dashboards.

Skip: trivial fixes, hotfixes, throwaway exploration.

Test: would a teammate in six months know *why* the code does what it does? If
yes, no spec. If no, spec it.

## Locations

| Artefact | Location |
|---|---|
| Templates | `.maui/skills/maui-spec-driven-development/assets/templates/` |
| Authoring guide | `.maui/skills/maui-spec-driven-development/assets/SPEC_GUIDE.md` |
| Populated specs | `<repo>/specs/<artefact-type>/<spec-name>.md` |

## Lifecycle

`draft` → `review` → `approved` → `implemented` → `deprecated`. Bump the
identity-block status as work progresses. Convention, not enforced.

## ID prefixes

| Prefix | Use |
|---|---|
| `BL-NNN` | Business logic clause |
| `AC-NNN` | Acceptance criterion (testable) |
| `OQ-NNN` | Open question (owner + due) |
| `DV-NNN` | Divergence from ideal (Mode A only) |
| `DQ-NNN` | Data quality check (migrations) |

Number from 001 per prefix per spec. Never reuse IDs. Renumber only in `draft`.

## Spec anchoring

Code references the BL/DQ ID; tests do too:

```sql
-- BL-001: Exclude soft-deleted records
where deleted_at is null
```

```yaml
- name: ac_001_no_soft_deleted   # asserts BL-001
```

Grep one ID → spec clause, code, test.

**One-way pointer (code → spec).** Specs never cite code by file/line — line
numbers rot silently. Use a symbol name if a code reference is genuinely needed;
otherwise let the `BL-NNN` comment carry the navigation.

## Reviewer checklist

- Purpose clear, grounded in a concrete need?
- Inputs/outputs at the right level?
- Each BL atomic, testable, unambiguous?
- Each AC maps to a runnable test?
- Open questions captured (not buried)?
- Mode A: divergences listed as `DV-XXX`, spec not edited to match buggy code?

## Tightening BL / DQ clauses

One declarative sentence. Cut: embedded rationale, duplicated cross-refs,
restated invariants, multi-clause parentheticals, code-line hand-holding.
40% length reduction with no normative loss is normal on a first pass.

## Before merging

Collapse, don't annotate. Resolved `DV-XXX` / `OQ-XXX` items → **delete the row**.
Multiple change-log entries → squash to one at merge time. The trunk spec is a
contract, not a history book.

## Mode A (retrospective specs)

Spec the *ideal* state. Capture every divergence as `DV-XXX`. Never edit the spec
to match buggy code.

## Review hooks

| Issue | Severity |
|---|---|
| New non-trivial logic missing `BL-XXX` anchors when a spec exists | 🟡 Suggestion |
| `BL-XXX` reference doesn't match any spec clause | 🟡 Suggestion |
| New model/pipeline/extract with no spec | 🟡 Suggestion |
| Code contradicts a spec clause it references | 🔴 Blocker |

Full rubric: [`../../REVIEW.md`](../../REVIEW.md) § Spec-driven development.

## See also

- [`linear-conventions.md`](linear-conventions.md) — issue refs in identity blocks
- The skill's `SPEC_GUIDE.md` — authoring details
- The skill's `references/sdd-principles.md` — background
