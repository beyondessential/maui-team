# Derived Elements Conventions

Conventions for the `der__` layer — OMOP's "Standardized Derived Elements" category.
Derived elements are computed analytic constructs (cohorts, eras, episodes) built on top
of `can__` (canonical clinical events) and joined to `ref__` / `lkp__` for facility-
scoped definitions and analytic groupings.

See `../architecture/data-architecture.md` (D2) for where `der__` sits in the layer
taxonomy and `dbt-conventions.md` § Model layers for the full per-layer reference.

> **Naming and registry transitions.** Two transitions are in flight that affect how
> this file reads against existing code:
> 1. **`coh__<program>` → `der__cohort_<program>`** — new cohort models use the `der__`
>    prefix; existing `coh__` models migrate when touched. See § Legacy `coh__` reference
>    at the end of this file.
> 2. **`cohort_definitions.csv` → `metric_definitions.csv`** — Phase 0 plans to
>    consolidate the cohort registry into the unified `metric_definitions.csv` so that
>    cohorts, eras, episodes, and metrics share one catalogue. See § Registry below for
>    the destination shape and the transition rules.

---

## What `der__` is and isn't

| Layer | Holds | Examples |
|---|---|---|
| `can__` | Canonical clinical events in OMOP-lite shape — facts about what happened to a patient | `can__person`, `can__visit_occurrence`, `can__condition_occurrence`, `can__measurement`, `can__drug_exposure`, `can__observation` |
| `der__` | Computed analytic constructs derived from `can__` — cohorts, eras, episodes | `der__cohort_<program>`, `der__condition_era`, `der__drug_era`, `der__episode_<name>` |

`can__` answers "what happened?"; `der__` answers "what *kind of pattern* did the
clinical events form?"

A common point of confusion: `can__person` is **not** a derived element. The person
table is OMOP's Standardized Clinical Data category. Cohorts about people are derived
elements; the person table itself is canonical.

---

## Derived element types

### Cohorts (`der__cohort_<program>`)

A set of patients who meet some clinical or programmatic inclusion criteria over a
defined time window, with explicit entry and exit dates. Cohorts answer questions like
"which patients are in the NCD programme?" or "which patients were enrolled in the HIV
care cascade in 2024?".

Use a cohort when a Program Registry requires:
- Fixed-window retention analysis (e.g. 6-month, 12-month cohorts)
- Incidence or prevalence tracking over time
- Survival or loss-to-follow-up (LTFU) analysis
- Standardised indicator sets (DHIS2, PEPFAR)

For a simple current-state registry view with no temporal analysis, a `ds__` dataset
suffices — no derived element needed.

### Eras (`der__condition_era`, `der__drug_era`) — future pattern

OMOP's eras combine successive clinical events of the same kind into continuous spans:

- `der__condition_era` — combined condition occurrences into chronic-care episodes
  (e.g. "hypertension from 2020-03 to present, continuous")
- `der__drug_era` — combined drug exposures into continuous treatment periods (e.g.
  "metformin 500mg from 2023-01 to 2024-06, no gaps over 30 days")
- `der__dose_era` — combined drug exposures at a specific dose

Eras are a future pattern in the BES stack — added when the analytic question requires
continuous-period reasoning rather than discrete events. Inputs come from `can__`
(`can__condition_occurrence`, `can__drug_exposure`).

### Episodes (`der__episode_<name>`) — future pattern

OMOP episodes capture clinically meaningful sequences of related events spanning
multiple domains (e.g. a pregnancy episode spans condition occurrences, measurements,
visits, and drug exposures). Episodes are a future pattern; add them when an analytic
question requires multi-domain temporal grouping.

---

## Materialisation

`der__` follows the env-aware materialisation pattern in `dbt-conventions.md`:
- `view` in the production compiled bundle (`reporting_*` target)
- `view` or `incremental` on the replica (`analytics_*` target), depending on size

Apply the `{{ config(materialized = ('view' if target.name.startswith('reporting_')
else 'incremental'), ...) }}` switch when the model sits in a Tamanu report chain. For
replica-only derived elements consumed by Tupaia via Data Tables, choose the
materialisation that suits the query budget directly.

---

## Registry

### Destination state — unified `metric_definitions.csv`

Phase 0 consolidates `cohort_definitions.csv` into `metric_definitions.csv` so that all
derived data assets — cohorts, eras, episodes, and metrics — share one introspectable
catalogue. The unified seed extends the metric registry shape (see
`../architecture/data-architecture.md` D5) with a `kind` discriminator:

| Column | Description |
|---|---|
| `metric_id` | Globally unique text identifier; snake-case. For derived elements, use the model suffix (e.g. `cohort_ncd_registry`, `condition_era_hypertension`, `episode_pregnancy`) |
| `kind` | `metric` / `cohort` / `condition_era` / `drug_era` / `dose_era` / `episode` |
| `name` | Human-readable label |
| `description` | What it is, in plain English |
| `numerator_description` | Numerator (metrics only — NULL for `der__`) |
| `denominator_description` | Denominator (metrics only — NULL for `der__`) |
| `entry_criteria` | Cohort/episode entry condition (NULL for metrics) |
| `exit_criteria` | Cohort/episode exit priority order (NULL for metrics) |
| `data_source` | Source system: `tamanu`, `msupply`, … |
| `definition_source` | External standard (e.g. `WHO_SMART_HIV`, `PEPFAR`, `OHDSI`) or `BES` |
| `definition_source_code` | External standard's own identifier; NULL for `BES` |
| `definition_rationale` | Short justification |
| `omop_concept_id` | OMOP concept ID for the cohort/element (NULL for metrics that don't have one); SNOMED preferred |
| `vocabulary_id` | Vocabulary source (`SNOMED`, `LOINC`, `RxNorm`, …) |
| `tupaia_code` | Legacy Tupaia indicator code being replaced; else NULL |
| `unit` | `count`, `percentage`, `rate_per_1000`, … (metrics only) |
| `subject_grain` | `patient`, `encounter`, `facility`, … |
| `disaggregations` | Comma-separated list of disaggregation column names (mainly metrics; cohorts may declare facility/sex breakdowns here) |
| `owner` | Team or person responsible |
| `status` | `draft` / `approved` / `deprecated` |
| `spec_path` | Path to SDD spec |

Cohort registry rows reference `omop_concept_id` for the programme's clinical domain
(e.g. SNOMED concept for "diabetes mellitus" on a diabetes-care cohort). Era and
episode rows similarly reference the domain concept their grouping is built around.

The `metric_id` column replaces the legacy integer `cohort_definition_id`. The `der__`
model carries `cohort_id` (text) as a column, sourced from the registry seed.

### Current operative state — `cohort_definitions.csv`

Until the consolidation lands, `tamanu-source-dbt/seeds/cohort_definitions.csv` remains
the authoritative source of `cohort_definition_id` integer values across all
deployments. Existing schema:

| Column | Description |
|---|---|
| `cohort_definition_id` | Unique integer ID — assigned sequentially; never reused |
| `cohort_name` | Short machine-readable name (e.g. `ncd_registry`) |
| `description` | Human-readable description of the cohort programme |
| `omop_concept_id` | OMOP concept ID for the clinical domain (SNOMED preferred) |
| `vocabulary_id` | Vocabulary source (e.g. `SNOMED`) |

**Before building a new cohort**, check whether the programme already has an entry. If
not, open a PR to `tamanu-source-dbt` to register it first. The deployment-specific
`der__cohort_<program>` (or legacy `coh__<program>`) model must reference the assigned
`cohort_definition_id` from this registry — never assign one locally.

### Transition rules

- New cohort models use the `der__cohort_<program>` prefix and carry a `cohort_id`
  text column populated with a snake-case identifier matching the model suffix
  (e.g. `der__cohort_ncd` carries `cohort_id = 'cohort_ncd'`).
- The text `cohort_id` and the legacy integer `cohort_definition_id` coexist on new
  models during the transition. Once `metric_definitions.csv` consolidation lands, the
  integer column is dropped.
- Existing `coh__` models do not need to be reissued for the registry change — they
  continue to use `cohort_definition_id` until they're touched for another reason.

---

## OMOP-lite required columns

All `der__cohort_<program>` (and legacy `coh__<program>`) models must include these
columns:

| Column | Type | Source |
|---|---|---|
| `cohort_id` | text | Matches the model suffix; snake-case (e.g. `cohort_ncd`). Sourced from registry seed |
| `cohort_definition_id` | integer | Legacy compatibility — from `cohort_definitions.csv` until consolidation lands |
| `subject_id` | uuid | `can__person.person_id` (or `patients.id` via `bases/` for legacy `coh__`) — no hashing needed for internal use |
| `cohort_start_date` | date | Deployment-specific — see below |
| `cohort_end_date` | date | Deployment-specific — see below |

For eras: required columns are `subject_id`, `condition_concept_id` (or
`drug_concept_id`), `era_start_date`, `era_end_date`, plus a `metric_id` text column
matching the model suffix.

For episodes: required columns are `subject_id`, `episode_concept_id`,
`episode_start_date`, `episode_end_date`, plus `metric_id` matching the model suffix.
Episodes additionally carry source-event references (typically as arrays of
`visit_occurrence_id` / `condition_occurrence_id` / `drug_exposure_id`) so consumers
can drill back to the underlying events.

### `cohort_start_date` — deployment-specific

Declare in the repo `AGENT.md` which source is used:
- Registry `datetime` field on `patient_program_registrations`, OR
- A specific intake/enrolment survey form field (state form ID and field name)
- Some deployments prefer survey date when present, falling back to registry date

### `cohort_end_date` — deployment-specific

Declare in the repo `AGENT.md`. Apply in priority order (use first available):
1. Exit date from a dedicated exit survey form
2. Date the patient's `registration_status` became inactive on the registry
3. Date of death (from `can__person.death_date` or relevant encounter)
4. 180 days after last recorded encounter (censoring sentinel)
5. `NULL` — patient remains in open cohort

The `new-derived-element.md` runbook requires the agent to confirm these sources with
the user before building.

---

## Cohort layer structure and naming

| Model | Materialisation | Purpose |
|---|---|---|
| `der__cohort_<name>_registry` | env-aware view | Wide-format patient registry — conditions pivot, exit data; cohort denominator and ad-hoc lookup |
| `int__<name>_cohort_<period>_patients` | `ephemeral` | Patient × reporting-month scaffold with cohort membership logic |
| `int__<name>_cohort_<period>_<measurement>` | `ephemeral` | Per-measurement-type window (one model per type) |
| `der__cohort_<name>` | env-aware view | OMOP-aligned membership + demographics; primary query target for AI and downstream models |
| `der__cohort_<name>_observations` | env-aware view | Clinical measurements linked to cohort members |

`<period>` uses compact notation: `6m`, `12m`, `24m`.

### Registry model (`der__cohort_<name>_registry`)

One row per active programme registration. Serves as the cohort denominator and source
for the patient-selection intermediate.

**Conditions pivot** — use `MAX(CASE WHEN ... THEN datetime END)` to produce one column
per condition. `NULL` means the condition has not been recorded:

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

**Exit CTE** — `DISTINCT ON` for the most recent exit survey per patient:

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

### Cohort patient selection (`int__<name>_cohort_<period>_patients`)

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
cross join {{ ref('der__cohort_<name>_registry') }} r
-- registration month = window start (e.g. 9 months ago for a 6-month cohort)
where date_trunc('month', r.registration_date::date) = (rm.month - interval '9 months')::date
-- patient must be active at the evaluation point (6 months post-registration = 3 months ago)
  and (r.exit_recorded_date is null
       or r.exit_recorded_date::date >= (rm.month - interval '3 months')::date)
```

### Measurement window models (`int__<name>_cohort_<period>_<measurement>`)

One model per measurement type. Document window bounds and control thresholds in a
comment.

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

Concept ID columns go in `can__` and `der__` models — never in `bases/`. Base models
remain lean.

Pattern — include local value and concept ID as siblings:

```sql
p.sex,
s.concept_id    as gender_concept_id,     -- OMOP concept: 8507=Male, 8532=Female (Gender vocabulary)
p.ethnicity_id,
e.concept_id    as ethnicity_concept_id   -- OMOP concept from map__omop_ethnicity
```

### `map__omop_<domain>` seeds

All local → OMOP mappings live in `map__omop_<domain>` seeds. `can__` and `der__`
models join to these; they never embed mapping logic inline.

| Tier | Scope | Repo |
|---|---|---|
| Universal | Same across all Tamanu instances (e.g. sex) | `tamanu-source-dbt` |
| Deployment-specific | Local reference data, condition codes | `tamanu-dbt-*` |

Standard seed schema:

| Column | Description |
|---|---|
| `local_code` | Tamanu value (reference data ID or coded value) |
| `local_name` | Human-readable local label |
| `concept_id` | OMOP concept ID (from OHDSI Athena) |
| `concept_name` | OMOP standard concept name |
| `vocabulary_id` | Vocabulary source (e.g. `SNOMED`, `LOINC`, `RxNorm`, `Gender`) |

Look up concept IDs at [OHDSI Athena](https://athena.ohdsi.org/). Document vocabulary
source in the seed's `.yml`.

Only add concept columns when the concept ID is actively used in a model or report —
never speculatively.

`map__omop_<domain>` is distinct from `lkp__<entity>`:
- `map__omop_*` seeds translate local Tamanu values to OMOP vocabulary concept IDs
- `lkp__` models are operational lookup tables (age bands, encounter classes, cross-
  system facility mappings) used as join targets — they're not OMOP-vocabulary maps

### Repo `AGENT.md` must declare available mappings

Under "Cohort configuration" (or "Derived-element configuration"), list which
`map__omop_*` seeds exist and which domains they cover. An agent building a new `der__`
model must check this list before adding concept columns.

---

## Observation period (for LTFU and incidence)

For incidence rates and loss-to-follow-up analysis, create
`int__<name>_observation_period` (ephemeral) defining the denominator:

```sql
select
    patient_id,
    min(first_event_date)                                    as observation_period_start,
    coalesce(exit_recorded_date, max(last_event_date))       as observation_period_end
from ...
group by patient_id, exit_recorded_date
```

Note: OMOP also defines `can__observation_period` for this purpose at the canonical
layer. Use `can__observation_period` when the spans are reusable across multiple
derived elements; use an `int__` ephemeral when the spans are bespoke to one cohort.

---

## Shared-pivot rule

All reports — Tamanu line-list, Tamanu aggregation, Tupaia dashboard — must source from
the `der__` (or legacy `coh__`) model. Never re-derive cohort membership in a
downstream output.

```
der__cohort_<name> (view)
  ├── Tamanu line-list report (view)    →  SELECT * FROM der__cohort_<name> WHERE ...
  ├── Tamanu aggregation report (view)  →  SELECT yearmonth, COUNT(*) FROM der__cohort_<name> GROUP BY yearmonth
  └── Tupaia aggregation (Data Table)   →  same aggregation logic; Tupaia applies its own filters
```

Where Tamanu and Tupaia aggregation outputs share the same logic, define it in a macro
and call it from both models.

The shared-pivot rule generalises across all `der__` types: cohorts, eras, and
episodes all serve as the construction-time guarantee that counts agree across
surfaces. Any time a downstream output needs to know "is this patient in cohort X?"
or "is this period a treatment era?", it `ref`s the `der__` model — it does not
reconstruct the logic.

---

## Legacy `coh__` reference

> **Sunset.** Delete this section once Phase 5 § 5a (cohort migration) completes —
> tracked in `../runbooks/refactoring-guide.md` § Phase 5.

The previous convention used `coh__<program>` as the cohort prefix and treated the
layer as the first application of an "OMOP-inspired semantic layer" that would later
cover clinical events as well. The architecture (D2) splits this responsibility:
clinical events live in `can__`, derived elements live in `der__`. Existing `coh__`
models remain valid until they're touched; new cohort models use `der__cohort_`.

Reference implementation using the prior `coh__` convention in `tamanu-dbt-msf-syria`:

- `models/cohort/coh__ncd_registry.sql` — conditions pivot + exit CTE pattern
- `models/intermediate/int__ncd_cohort_6m_patients.sql` — patient-selection scaffold
- `models/cohort/coh__ncd.sql` — final OMOP-lite cohort model
- `models/cohort/coh__ncd_observations.sql` — measurement-linked observations

When migrating one of these to `der__cohort_`:
1. Rename the file (e.g. `coh__ncd.sql` → `der__cohort_ncd.sql`)
2. Update all downstream `ref('coh__ncd')` calls to `ref('der__cohort_ncd')`
3. Add the text `cohort_id` column (e.g. `'cohort_ncd' as cohort_id`); keep
   `cohort_definition_id` for legacy compatibility until registry consolidation lands
4. Update the model's `.yml` description and tags accordingly
5. Note the rename in the PR description so reviewers can spot any missed `ref`s

The architecture treats this as opportunistic migration — don't batch a rename PR
across the codebase; rename one cohort family at a time when the model is being
touched for another reason.
