# dbt Model Spec: `<model_name>`

## Identity

| Field | Value |
|---|---|
| **Name** | `<model_name>` (e.g. `der__cohort_nutrition_registry`) |
| **Type** | dbt model |
| **Layer** | `[base \| ref \| lkp \| can \| der \| metric \| int \| ds \| report \| fct (legacy) \| dim (legacy) \| coh (legacy)]` |
| **Materialisation** | `[view \| table \| incremental \| ephemeral]` |
| **Status** | `draft` |
| **Owner** | `@<github_handle>` |
| **Linear issue** | [MAUI-XXX](url) |
| **Repo** | `<repo-name>` |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

## Purpose

**Why does this model exist?** (1–3 sentences)

**Who consumes it?** (downstream models, reports, dashboards, end users)

**Business context:** (programme, country, clinical question being answered)

## Grain

**One row per:** _e.g. one row per patient per encounter per measurement._

State explicitly. The grain definition is the most common source of model bugs.

## Inputs

### Upstream models / sources

| Reference | Why we need it |
|---|---|
| `{{ ref('can__person') }}` | Person demographics (OMOP-shaped) |
| `{{ ref('der__cohort_<name>') }}` | Cohort definition |

### Required input columns

For each upstream, list the columns this model depends on. Helps with impact analysis when upstreams change.

| Upstream | Columns used |
|---|---|
| `can__person` | `person_id`, `birth_date`, `gender_concept_id` |
| `der__cohort_<name>` | `subject_id`, `cohort_id`, `cohort_start_date`, `cohort_end_date` |

### Freshness expectations

How recent must input data be for this model to produce valid output? e.g. `bases refreshed within 24 hours`.

## Output schema

| Column | Type | Description | Tests |
|---|---|---|---|
| `patient_id` | uuid | PK | `not_null`, `unique` |
| `encounter_date` | date | Date of encounter | `not_null` |
| ... | | | |

## Business logic

Each rule has an ID. Reference these IDs in implementing code (`-- BL-001:`).

- **BL-001:** Exclude soft-deleted records (`deleted_at is null` on bases).
- **BL-002:** Restrict to patients with active programme registration on the encounter date.
- **BL-003:** _<add edge cases, null handling, dedup strategy, fan-out handling, time-zone handling — each as its own BL>_

## Acceptance criteria

Each criterion implements one or more BL clauses and is realised as a dbt test or Great Expectations expectation.

| ID | Criterion | Implements | Test type |
|---|---|---|---|
| AC-001 | No rows where `deleted_at is not null` | BL-001 | dbt singular test |
| AC-002 | All `patient_id` values appear in `base__patients` | BL-002 | dbt `relationships` |
| ... | | | |

## Lineage

```
upstream                              this model                  downstream
can__person       ──┐
der__cohort_<name> ──┼──►  ds__<name>_encounters   ──►  <name>_line_list (report)
                                                         └►  Tupaia: <dashboard_name>
```

## Open questions

| ID | Question | Owner | Due |
|---|---|---|---|
| OQ-001 | _e.g. should withdrawn-consent patients appear in line-lists with masked PII or be excluded?_ | @<owner> | YYYY-MM-DD |

## Divergence from current code

_Mode A (retrospective specs) only. Each divergence is follow-up work to bring code in line with spec._

| ID | Divergence | Resolution |
|---|---|---|
| DV-001 | _e.g. current `int__<name>_pivot` does not exclude test patients_ | _Add `test_patient_id is null` filter_ |
| DV-002 | _e.g. existing model uses legacy `coh__<name>` prefix_ | _Rename to `der__cohort_<name>` next time the model is touched (D2 in-flight)_ |

## Change log

| Date | Author | Change |
|---|---|---|
| YYYY-MM-DD | @<owner> | Initial draft |
