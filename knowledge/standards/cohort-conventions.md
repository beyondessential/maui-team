# Cohort Conventions

Conventions for modelling Tamanu Program Registries as OMOP-inspired cohorts. Uses the
`coh__` semantic layer described in `dbt-conventions.md`.

## When to use this pattern

Use cohort modelling when a Program Registry requires:
- Fixed-window retention analysis (e.g. 6-month, 12-month cohorts)
- Incidence or prevalence tracking over time
- Survival or loss-to-follow-up (LTFU) analysis
- Standardised indicator sets (DHIS2, PEPFAR)

For a simple current-state registry view with no temporal analysis, a `ds__` dataset suffices.

## Broader OMOP vision

Cohort modelling is the first application of the `coh__` semantic layer. The same pattern
extends to other OMOP clinical domains as the stack matures:

| OMOP domain | Tamanu source | Future model |
|-------------|--------------|--------------|
| Person | `patients` + `patient_additional_data` | `coh__person` |
| Visit occurrence | `encounters` | `coh__encounters` |
| Condition occurrence | diagnoses, registry conditions | `coh__conditions` |
| Measurement | survey lab/vital results | `coh__measurements` |
| Drug exposure | prescriptions | `coh__drug_exposures` |
| Cohort | program registries | `coh__<program>` |

Each domain model carries OMOP concept shadow columns via `map__omop_<domain>` seeds, forming
a complete AI-queryable clinical semantic layer.

---

## Layer structure and naming

| Model | Materialisation | Purpose |
|-------|----------------|---------|
| `coh__<name>_registry` | `view` | Wide-format patient registry — conditions pivot, exit data; cohort denominator and ad-hoc lookup |
| `int__<name>_cohort_<period>_patients` | `ephemeral` | Patient × reporting-month scaffold with cohort membership logic |
| `int__<name>_cohort_<period>_<measurement>` | `ephemeral` | Per-measurement-type window (one model per type) |
| `coh__<name>` | `view` | OMOP-aligned membership + demographics; AI primary query target |
| `coh__<name>_observations` | `view` | Clinical measurements linked to cohort members |

`<period>` uses compact notation: `6m`, `12m`, `24m`.

---

## Cohort definition registry

BES maintains a central data dictionary of cohort definitions in `tamanu-source-dbt` as a seed:
`seeds/cohort_definitions.csv`. This is the authoritative source of `cohort_definition_id`
values across all deployments.

Seed schema:

| Column | Description |
|--------|-------------|
| `cohort_definition_id` | Unique integer ID — assigned sequentially; never reused |
| `cohort_name` | Short machine-readable name (e.g. `ncd_registry`) |
| `description` | Human-readable description of the cohort program |
| `omop_concept_id` | OMOP concept ID for the clinical domain (SNOMED preferred) |
| `vocabulary_id` | Vocabulary source (e.g. `SNOMED`) |

**Before building a new cohort**, check whether the program already has an entry. If not,
open a PR to `tamanu-source-dbt` to register it first. The deployment-specific `coh__` model
must reference the assigned `cohort_definition_id` from this registry — never assign one locally.

---

## OMOP-lite required columns

All `coh__<name>` models must include these four columns:

| Column | Type | Source |
|--------|------|--------|
| `cohort_definition_id` | integer | From `tamanu-source-dbt` cohort definition registry — see above |
| `subject_id` | uuid | `patients.id` — no hashing needed for internal use |
| `cohort_start_date` | date | Deployment-specific — see below |
| `cohort_end_date` | date | Deployment-specific — see below |

### `cohort_start_date` — deployment-specific

Declare in the repo `AGENT.md` which source is used:
- Registry `datetime` field on `patient_program_registrations`, OR
- A specific intake/enrolment survey form field (state form ID and field name)
- Some deployments prefer survey date when present, falling back to registry date

### `cohort_end_date` — deployment-specific

Declare in the repo `AGENT.md`. Apply in priority order (use first available):
1. Exit date from a dedicated exit survey form
2. Date the patient's `registration_status` became inactive on the registry
3. Date of death (from `patients` or relevant encounter)
4. 180 days after last recorded encounter (censoring sentinel)
5. `NULL` — patient remains in open cohort

The `new-cohort.md` runbook requires the agent to confirm these sources with the user before building.

---

## Registry model (`coh__<name>_registry`)

One row per active program registration. Serves as the cohort denominator and source for
the patient selection intermediate.

**Conditions pivot** — use `MAX(CASE WHEN ... THEN datetime END)` to produce one column per
condition. `NULL` means the condition has not been recorded:

```sql
with conditions as (
    select
        split_part(patient_program_registration_id, ';', 1) as patient_id,
        max(case when program_registry_condition_id = 'prCondition-X' then datetime end) as condition_x,
        max(case when program_registry_condition_id = 'prCondition-Y' then datetime end) as condition_y
    from {{ ref('patient_program_registration_conditions') }}
    where split_part(patient_program_registration_id, ';', 2) = '<programRegistry-id>'
    group by patient_id
)
```

**Exit CTE** — use `DISTINCT ON` to get the most recent exit survey per patient:

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

**Registry filter**:
```sql
where ppr.program_registry_id = '<programRegistry-id>'
```

---

## Cohort patient selection (`int__<name>_cohort_<period>_patients`)

Generates a patient × reporting-month scaffold then filters to cohort members.

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
    r.registration_date,
    ...
from reporting_months rm
cross join {{ ref('coh__<name>_registry') }} r
-- registration month = window start (e.g. 9 months ago for a 6-month cohort)
where date_trunc('month', r.registration_date::date) = (rm.month - interval '9 months')::date
-- patient must be active at the evaluation point (6 months post-registration = 3 months ago)
  and (r.exit_recorded_date is null
       or r.exit_recorded_date::date >= (rm.month - interval '3 months')::date)
```

---

## Measurement window models (`int__<name>_cohort_<period>_<measurement>`)

One model per measurement type. Document the window bounds and control thresholds in a comment.

```sql
-- BP measurements in 3–9 month post-registration window
-- Control threshold: <140/90 for hypertension, <130/90 for diabetes
select
    to_char(rm.month, 'YYYY-MM') as yearmonth,
    patient_id,
    max(case when systolic < 140 and diastolic < 90 then 1 else 0 end) as bp_controlled
from ...
where encounter_date between (registration_date + interval '3 months')
                         and (registration_date + interval '9 months')
group by yearmonth, patient_id
```

---

## OMOP concept shadow columns

Concept ID columns go in `coh__` models only — never in base models. Base models remain lean.

Pattern — include local value and concept ID as siblings:

```sql
p.sex,
s.concept_id    as sex_concept_id,       -- OMOP concept: 8507=Male, 8532=Female (Gender vocabulary)
p.ethnicity_id,
e.concept_id    as ethnicity_concept_id  -- OMOP concept from map__omop_ethnicity
```

### `map__omop_<domain>` seeds

All local → OMOP mappings live in `map__omop_<domain>` seeds. `coh__` models join to these;
they never embed mapping logic inline.

| Tier | Scope | Repo |
|------|-------|------|
| Universal | Same across all Tamanu instances (e.g. sex) | `tamanu-source-dbt` |
| Deployment-specific | Local ref data, condition codes | `tamanu-dbt-*` |

Standard seed schema:

| Column | Description |
|--------|-------------|
| `local_code` | Tamanu value (reference data ID or coded value) |
| `local_name` | Human-readable local label |
| `concept_id` | OMOP concept ID (from OHDSI Athena) |
| `concept_name` | OMOP standard concept name |
| `vocabulary_id` | Vocabulary source (e.g. `SNOMED`, `LOINC`, `RxNorm`, `Gender`) |

Look up concept IDs at [OHDSI Athena](https://athena.ohdsi.org/). Document vocabulary source
in the seed's `.yml`.

Only add concept columns when the concept ID is actively used in a model or report — never
speculatively.

### Repo `AGENT.md` must declare available mappings

Under "Cohort configuration", list which `map__omop_*` seeds exist and which domains they cover.
An agent building a new `coh__` model must check this list before adding concept columns.

---

## Observation period (for LTFU and incidence)

For incidence rates and loss-to-follow-up analysis, create `int__<name>_observation_period`
(ephemeral) defining the denominator:

```sql
select
    patient_id,
    min(first_event_date)                                    as observation_period_start,
    coalesce(exit_recorded_date, max(last_event_date))       as observation_period_end
from ...
group by patient_id, exit_recorded_date
```

---

## Shared-pivot rule

All reports — line-list and aggregation — must source from `coh__` — never define
cohort membership logic independently in each output layer.

```
coh__<name> (view)
  ├── Tamanu line-list report (view)    →  SELECT * FROM coh__<name> WHERE ...
  ├── Tamanu aggregation report (view)  →  SELECT yearmonth, COUNT(*) FROM coh__<name> GROUP BY yearmonth
  └── Tupaia aggregation model (table)  →  same aggregation logic; Tupaia applies its own filters
```

Where Tamanu and Tupaia aggregation outputs share the same logic, define it in a macro and
call it from both models.

---

## Transition note

Existing models using `ds__` prefix remain valid. `tamanu-dbt-msf-syria` is the reference
implementation using the prior convention — new cohort models use `coh__`.

Reference files in `tamanu-dbt-msf-syria`:
- `models/datasets/ds__ncd_registry.sql` — conditions pivot + exit CTE pattern
- `models/intermediate/int__ncd_cohort_6m_patients.sql` — patient selection pattern
- `models/datasets/ds__ncd_cohort_6m.sql` — final cohort dataset
