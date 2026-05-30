# Derived Elements Conventions

Conventions for the `der__` layer — OMOP's "Standardized Derived Elements".
Built on `can__`, joined to `ref__` / `lkp__`. See
[D2](../architecture/data-architecture/decisions.md) and
[`dbt-conventions.md`](dbt-conventions.md) for the layer taxonomy.

> **Transition in flight:** `cohort_definitions.csv` → unified
> `metric_definitions.csv`. See § Registry.

## What `der__` is and isn't

| Layer | Holds |
|---|---|
| `can__` | Canonical clinical events — `can__person`, `can__visit_occurrence`, `can__condition_occurrence`, `can__measurement`, `can__drug_exposure`, `can__observation` |
| `der__` | Computed analytic constructs — `der__cohort_<program>`, `der__condition_era`, `der__drug_era`, `der__episode_<name>` |

`can__` = "what happened?"; `der__` = "what *pattern* did the events form?".
`can__person` is canonical, not derived.

## Element types

### Cohorts (`der__cohort_<program>`)

Patients meeting clinical/programmatic criteria over a defined window, with
entry and exit dates. Use when a Program Registry needs fixed-window retention,
incidence/prevalence, survival/LTFU, or standardised indicator sets
(DHIS2, PEPFAR). For a current-state view with no temporal analysis, use `ds__`.

### Eras (`der__condition_era`, `der__drug_era`) — future

OMOP eras combine successive same-domain events into continuous spans (e.g.
"hypertension from 2020-03 to present, continuous"; "metformin from 2023-01 to
2024-06, no gaps > 30 days"). Inputs from `can__condition_occurrence` /
`can__drug_exposure`. Add when continuous-period reasoning is needed.

### Episodes (`der__episode_<name>`) — future

Clinically meaningful multi-domain sequences (e.g. pregnancy spanning
conditions, measurements, visits, drugs). Add when an analytic question needs
multi-domain temporal grouping.

## Materialisation

Env-aware (see [`dbt-conventions.md`](dbt-conventions.md)): `view` in production
bundle (`reporting_*`); `view` or `incremental` on replica (`analytics_*`). For
replica-only `der__` consumed via Data Tables, pick whatever fits the query
budget.

## Registry

### Target: unified `metric_definitions.csv`

Phase 0 merges `cohort_definitions.csv` into `metric_definitions.csv` so all
derived data assets share one catalogue. Extends the metric registry
([D5](../architecture/data-architecture/decisions.md)) with a `kind` column:

| Column | Description |
|---|---|
| `metric_id` | Globally unique, snake-case (e.g. `cohort_ncd_registry`, `condition_era_hypertension`, `episode_pregnancy`) |
| `kind` | `metric` / `cohort` / `condition_era` / `drug_era` / `dose_era` / `episode` |
| `name` | Human-readable label |
| `description` | Plain English |
| `numerator_description` / `denominator_description` | Metrics only — NULL for `der__` |
| `entry_criteria` / `exit_criteria` | Cohorts/episodes only — NULL for metrics |
| `data_source` | `tamanu`, `msupply`, … |
| `definition_source` | External standard or `BES` |
| `definition_source_code` | External ID; NULL for `BES` |
| `definition_rationale` | Short |
| `omop_concept_id` | Domain concept (SNOMED preferred) |
| `vocabulary_id` | `SNOMED`, `LOINC`, `RxNorm`, … |
| `tupaia_code` | Legacy Tupaia code or NULL |
| `unit` | `count`, `percentage`, … (metrics only) |
| `subject_grain` | `patient`, `encounter`, `facility`, … |
| `disaggregations` | Comma-separated column names |
| `variant_of` | Parent `metric_id` if this row is a deployment-specific definition variant; else NULL (metrics only — see D5) |
| `owner` | Team or person |
| `status` | `draft` / `approved` / `deprecated` |
| `spec_path` | Path to SDD spec |

Text `metric_id` replaces the legacy integer `cohort_definition_id`. The `der__`
model carries `cohort_id` (text) sourced from the registry.

### Current: `cohort_definitions.csv`

Until consolidation, `tamanu-source-dbt/seeds/cohort_definitions.csv` is
authoritative:

| Column | Description |
|---|---|
| `cohort_definition_id` | Unique integer, sequential, never reused |
| `cohort_name` | Machine-readable name (e.g. `ncd_registry`) |
| `description` | Human-readable |
| `omop_concept_id` | Domain concept (SNOMED preferred) |
| `vocabulary_id` | Vocabulary source |

Before building a new cohort, check this seed. If absent, PR `tamanu-source-dbt`
to register first. Never assign an ID locally.

### Transition rule

New `der__cohort_<program>` models carry both `cohort_id` (text, matches model
suffix — e.g. `'cohort_ncd'`) and `cohort_definition_id` (integer, from seed).
Integer column drops once `metric_definitions.csv` consolidation lands.

## OMOP-lite required columns

For `der__cohort_<program>`:

| Column | Type | Source |
|---|---|---|
| `cohort_id` | text | Matches model suffix (e.g. `cohort_ncd`) |
| `cohort_definition_id` | integer | From `cohort_definitions.csv` (drops post-consolidation) |
| `subject_id` | uuid | `can__person.person_id` (or `patients.id` via `bases/` if `can__person` isn't yet built in this repo) |
| `cohort_start_date` | date | Deployment-specific — see below |
| `cohort_end_date` | date | Deployment-specific — see below |

For eras: `subject_id`, `condition_concept_id` or `drug_concept_id`,
`era_start_date`, `era_end_date`, plus text `metric_id`.

For episodes: `subject_id`, `episode_concept_id`, `episode_start_date`,
`episode_end_date`, `metric_id`, plus source-event reference arrays
(`visit_occurrence_id` / `condition_occurrence_id` / `drug_exposure_id`).

### `cohort_start_date` — deployment-specific

Declare source in repo `AGENT.md`:
- Registry `datetime` on `patient_program_registrations`, OR
- Specific intake/enrolment survey field, OR
- Survey-when-present-else-registry

### `cohort_end_date` — deployment-specific

Declare in repo `AGENT.md`. Apply in priority (first available):
1. Exit survey form
2. `registration_status` becoming inactive
3. Date of death (`can__person.death_date`)
4. 180 days after last encounter (censoring sentinel)
5. NULL — patient still in cohort

`new-derived-element.md` requires confirming these with the user before building.

## Cohort layer structure

| Model | Materialisation | Purpose |
|---|---|---|
| `der__cohort_<name>_registry` | env-aware view | Wide registry: conditions pivot, exit data |
| `int__<name>_cohort_<period>_patients` | `ephemeral` | Patient × month scaffold + membership filter |
| `int__<name>_cohort_<period>_<measurement>` | `ephemeral` | Per-measurement window |
| `der__cohort_<name>` | env-aware view | OMOP-lite cohort: membership + demographics |
| `der__cohort_<name>_observations` | env-aware view | Measurements linked to members |

`<period>` notation: `6m`, `12m`, `24m`.

### Registry model — patterns

**Conditions pivot** (one column per condition; NULL = unrecorded):

```sql
with conditions as (
    select
        split_part(patient_program_registration_id, ';', 1) as patient_id,
        max(case when program_registry_condition_id = 'prCondition-X' then datetime end) as condition_x,
        max(case when program_registry_condition_id = 'prCondition-Y' then datetime end) as condition_y
    from {{ ref('base__patient_program_registration_conditions') }}
    where split_part(patient_program_registration_id, ';', 2) = '<programRegistry-id>'
    group by patient_id
)
```

**Exit CTE** (`DISTINCT ON` for most recent per patient):

```sql
exit as (
    select distinct on (patient_id)
        patient_id,
        "<exit_date_field>"   as exit_recorded_date,
        "<exit_status_field>" as exit_status
    from {{ ref('<exit_survey_model>') }}
    order by patient_id, "<exit_date_field>" desc, end_datetime desc
)
```

Filter: `where ppr.program_registry_id = '<programRegistry-id>'`.

### Patient selection — pattern

```sql
with reporting_months as (
    select month::date
    from generate_series(
        '{{ var("start_date") }}'::date,
        date_trunc('month', {{ get_current_date() }} - interval '1 month')::date,
        '1 month'::interval
    ) month
)
select
    to_char(rm.month, 'YYYY-MM') as yearmonth,
    r.id                         as patient_id,
    r.registration_date
from reporting_months rm
cross join {{ ref('der__cohort_<name>_registry') }} r
where date_trunc('month', r.registration_date::date) = (rm.month - interval '9 months')::date
  and (r.exit_recorded_date is null
       or r.exit_recorded_date::date >= (rm.month - interval '3 months')::date)
```

(Registration month = window start; patient active at evaluation point.)

### Measurement window — pattern

One model per measurement type. Document window + thresholds in a header comment.

```sql
-- BP in 3–9 month post-registration window; control <140/90
select
    to_char(rm.month, 'YYYY-MM') as yearmonth,
    patient_id,
    max(case when systolic < 140 and diastolic < 90 then 1 else 0 end) as bp_controlled
from ...
where encounter_date between (registration_date + interval '3 months')
                         and (registration_date + interval '9 months')
group by yearmonth, patient_id
```

## OMOP concept shadow columns

Concept IDs go in `can__` and `der__`, never in `bases/`. Pattern — local value
and concept ID as siblings:

```sql
p.sex,
s.concept_id    as gender_concept_id,     -- 8507=Male, 8532=Female (Gender)
p.ethnicity_id,
e.concept_id    as ethnicity_concept_id   -- from map__omop_ethnicity
```

### `map__omop_<domain>` seeds

All local → OMOP mappings live in seeds; `can__` / `der__` join, never inline.

| Scope | Coverage | Repo |
|---|---|---|
| Universal (e.g. sex) | All deployments | `tamanu-source-dbt` |
| Deployment-specific | Local refs, condition codes | `tamanu-dbt-*` |

Schema: `local_code`, `local_name`, `concept_id`, `concept_name`, `vocabulary_id`.
Look up at [OHDSI Athena](https://athena.ohdsi.org/). Document vocabulary
source in the seed's `.yml`. Only add concept columns when actively used —
never speculatively.

`map__omop_*` ≠ `lkp__`: the former translates local codes to OMOP concepts;
the latter is operational join targets.

Repo `AGENT.md` lists which `map__omop_*` seeds exist under "Cohort
configuration".

## Observation period (LTFU and incidence)

Use `can__observation_period` when spans are reusable across multiple `der__`.
Use an `int__<name>_observation_period` ephemeral for cohort-bespoke spans:

```sql
select
    patient_id,
    min(first_event_date)                              as observation_period_start,
    coalesce(exit_recorded_date, max(last_event_date)) as observation_period_end
from ...
group by patient_id, exit_recorded_date
```

## Shared-pivot rule

Every consumer (Tamanu line-list, Tamanu aggregation, Tupaia Data Table) sources
from the `der__` model. Never re-derive cohort membership downstream.

```
der__cohort_<name>
  ├── Tamanu line-list   → SELECT * FROM der__cohort_<name> WHERE ...
  ├── Tamanu aggregation → SELECT yearmonth, COUNT(*) FROM der__cohort_<name> GROUP BY yearmonth
  └── Tupaia Data Table  → same aggregation; Tupaia applies its own filters
```

Where Tamanu and Tupaia share aggregation logic, extract a macro called from
both. Same rule applies to eras and episodes.
