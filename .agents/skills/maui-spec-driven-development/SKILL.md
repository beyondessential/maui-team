---
name: maui-spec-driven-development
description: Create spec-driven development (SDD) docs for Maui team data work — dbt models, Dagster pipelines, data extracts, data migrations, and Tupaia dashboards. Use this skill whenever the user wants to write a spec, design doc, requirements doc, or technical specification for any data task; whenever they ask to document an existing model, pipeline, or extract; whenever they reference a Linear issue and want to scope it before coding; or whenever they mention "spec", "design", "SDD", "requirements", "data contract", or "acceptance criteria" in the context of pipelines, models, dashboards, extracts, or migrations. Trigger this proactively at the start of any Maui data task that warrants up-front design — even if the user does not say the word "spec". The skill produces docs anchored by numbered business-logic clauses (BL-001, BL-002…) that downstream code references in comments, so every line of code traces back to a spec clause.
---

# Spec-Driven Development for Maui Data Tasks

This skill produces spec docs for Maui team data work. Specs are the source of truth — code, tests, and documentation derive from them. When code and spec disagree, the spec is correct and the code is wrong.

The skill produces two kinds of artefact:

1. **Team-facing guide and templates** — placed once in `maui-team/knowledge/specs/` so the whole team can use them.
2. **Populated specs** — placed in each consuming repo under `<repo>/specs/<artefact-type>/<spec-name>.md`, alongside the code they describe.

Templates live centrally in `maui-team`. Populated specs live with the code.

## Core SDD principles

1. **Spec before code.** Every model, pipeline, extract, migration, or dashboard worth designing starts with a spec.
2. **Numbered clauses anchor everything.** Business logic is enumerated as `BL-001`, `BL-002`… Code comments reference these IDs. Tests assert these IDs. A reader can grep one ID and find rule, implementation, and test in one search.
3. **The spec describes the ideal state.** When documenting existing code, write the spec to describe what the code *should* do. Where current code diverges, capture each divergence as a `DV-XXX` work item. Never edit the spec to match buggy code.
4. **Status is conventional, not enforced.** Lifecycle: `draft → review → approved → implemented → deprecated`. The team moves a spec forward by agreement, not by tooling.
5. **Open questions are first-class.** Capture unknowns explicitly with owner and due date. Don't bury them in TODOs.

## When to use this skill

- Starting a new data task (Tamanu report, Tupaia dashboard, dataset model, migration, extract, Dagster pipeline)
- Documenting an existing model or pipeline retrospectively
- Scoping a Linear issue before implementation
- Setting up SDD in a repo that does not have it yet

**Do not** use this skill for trivial bugfixes, hotfixes, or throwaway exploratory analyses. Specs are for work that warrants design effort.

## Entry modes

Identify the mode early — it determines how you gather context.

### Mode A — Existing repo (retrospective)
The user points at a model, pipeline, or extract that already exists. Inspect the code to draft a spec describing the *ideal* state. Flag any divergence between current code and ideal as a `DV-XXX` work item.

Steps:
1. Read the relevant files. For Maui repos, prefer the `ask-a-dev` skill / `github-repo-rag` MCP server over manual exploration.
2. Identify artefact type → select template.
3. Populate the spec from observed behaviour, prompting the user for purpose and business context that aren't captured in code.
4. Capture divergences from ideal in the `Divergence` section.

### Mode B — Linear issue (forward)
The user references a Linear issue. Pull the issue, extract requirements, draft a forward-looking spec.

Steps:
1. Use `linear:get_issue` to fetch the issue (the tool needs to be loaded via `tool_search` first).
2. Identify artefact type from issue content. If unclear, ask.
3. Populate the spec from the issue plus user clarification.
4. Add the spec path back to the Linear issue (offer to do this; ask before posting).

### Mode C — Conversation (greenfield)
The user describes a new task in chat. Interview them to build the spec.

Steps:
1. Identify artefact type.
2. Walk through the template section by section, asking targeted questions.
3. Don't ask everything at once — work through purpose, then inputs, then logic, then outputs. One section per turn is usually right.

## Artefact types and templates

| User says… | Artefact type | Template |
|---|---|---|
| dbt model, dataset, cohort, base/fact/dim model | dbt model | `assets/templates/dbt-model.md` |
| Tamanu report (the report-tier dbt model) | dbt model (report layer) | `assets/templates/dbt-model.md` |
| Dagster pipeline / job / asset, orchestration | Dagster pipeline | `assets/templates/dagster-pipeline.md` |
| Data extract, ad-hoc query, data dump | Data extract | `assets/templates/data-extract.md` |
| Data migration, FSM migration, EHR migration | Data migration | `assets/templates/data-migration.md` |
| Tupaia dashboard, map overlay, indicator | Tupaia dashboard | `assets/templates/tupaia-dashboard.md` |

If the task does not fit any of these, ask whether it should be treated as one of the above or whether a new template is warranted.

## Workflow

### 1. Confirm setup
Check whether `maui-team/knowledge/specs/` already exists. If not, this is the first spec — offer to copy `assets/SPEC_GUIDE.md` and `assets/templates/*.md` into `maui-team` as a separate setup step before drafting the user's spec.

### 2. Identify mode and artefact type
See entry modes above.

### 3. Read the template
Use `view` to read `assets/templates/<artefact-type>.md` from this skill before drafting. Don't reproduce templates from memory — read them fresh each time.

### 4. Gather context
- Mode A: read the code (prefer `ask-a-dev` / `github-repo-rag` for Maui repos)
- Mode B: read the Linear issue
- Mode C: interview

### 5. Populate
Fill in the template top to bottom. Mark unknowns as `[TBD: <question>]` rather than guessing. Number every distinct rule as `BL-001`, `BL-002`… from the start — don't renumber later.

### 6. Place the spec
Populated specs live in the consuming repo, NOT in `maui-team`. Default location:

```
<repo>/specs/<artefact-type>/<spec-name>.md
```

Examples:
- `data-lake/specs/dagster-pipeline/tamanu_fj_replication.md`
- `tamanu-source-dbt/specs/dbt-model/coh__nutrition_registry.md`
- `fsm-data-migration/specs/data-migration/patients.md`

If the repo has no `specs/` directory, create it together with a brief `specs/README.md` pointing readers at `maui-team/knowledge/specs/SPEC_GUIDE.md`.

### 7. Cross-reference
- Confirm with the user before adding `-- BL-XXX` comments to existing code (Mode A).
- For Mode B specs, offer to attach the spec link back to the Linear issue.

## Spec-anchoring convention

Every business logic clause has an ID. Code references it. Tests assert it.

**SQL / dbt:**
```sql
-- BL-001: Exclude soft-deleted records
where deleted_at is null

-- BL-002: Restrict to encounters in the reporting facility
and encounter_facility_id = {{ var('reporting_facility_id') }}
```

**Python / Dagster:**
```python
# BL-003: Skip rows where patient consent was withdrawn
df = df[df['consent_withdrawn'].isna()]
```

**dbt tests:**
Each acceptance criterion in the spec maps to a test. Name the test to reference the AC/BL it asserts:
```yaml
- name: ac_001_no_soft_deleted   # asserts BL-001
  test: <generic or singular test>
```

A reader can grep `BL-001` once and find: spec clause, implementing code, asserting test.

## Spec lifecycle (conventional)

| Status | Means |
|---|---|
| `draft` | Author is still writing |
| `review` | Open for team feedback |
| `approved` | Team has signed off; safe to implement |
| `implemented` | Code matches spec; all ACs pass |
| `deprecated` | No longer in use; kept for history |

No tooling enforces transitions — update the status line in the identity block as the spec progresses. As the team gets used to SDD, we may add a PR check that gates merge on spec status; that's not in place yet.

## ID conventions across all spec types

| Prefix | Use |
|---|---|
| `BL-XXX` | Business logic clause (numbered rule) |
| `AC-XXX` | Acceptance criterion |
| `OQ-XXX` | Open question |
| `DV-XXX` | Divergence from current code (Mode A only) |
| `DQ-XXX` | Data quality check (used in migration specs) |

Number from 001 within each prefix per spec. Don't reuse IDs across specs.

## First-time setup in `maui-team`

When invoked for the first time and `maui-team/knowledge/specs/` doesn't exist:

1. Copy `assets/SPEC_GUIDE.md` to `maui-team/knowledge/specs/SPEC_GUIDE.md`
2. Copy `assets/templates/*.md` to `maui-team/knowledge/specs/templates/`
3. Offer to draft a small addition to `maui-team/knowledge/AGENT.base.md` referencing the new specs directory, so all repos pulling the `.maui/` submodule become aware of it.

Treat this as a separate PR from the user's first populated spec — keeps the setup change reviewable on its own.

## References

- `references/sdd-principles.md` — background on SDD theory, the Open Data Contract Standard, and why this skill diverges from it. Read this if the user asks "why are we doing it this way" or wants to ground the approach in industry practice.
