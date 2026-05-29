# Runbook: Adding a New Derived Element

Builds a program registry cohort in the `der__` derived-elements layer
(`der__cohort_<program>`). Steps in order; steps marked **[parallel]** can be
delegated to separate agents running simultaneously.

This runbook is the procedural guide. The canonical SQL patterns
(conditions pivot, exit CTE, patient-selection scaffold, measurement windows,
OMOP-lite columns, registry rules) live in
[`../standards/derived-elements-conventions.md`](../standards/derived-elements-conventions.md).
This file points at the right sections rather than duplicating them.

Currently covers the cohort case. Eras and episodes follow the same shape;
extend this runbook in place when you build the first non-cohort derived element.

Applies to `tamanu-dbt-*` repos.

---

## Step 0 — Gather deployment-specific configuration

**The agent must ask the user these questions before writing any code.**

1. What is the `program_registry_id` for this programme? (e.g.
   `programRegistry-ncdregistry`)
2. What condition IDs (`program_registry_condition_id`) are relevant, and what
   local name should each column use?
3. **Entry date source** — `cohort_start_date` per the cases in
   [`derived-elements-conventions.md` § `cohort_start_date`](../standards/derived-elements-conventions.md#cohort_start_date--deployment-specific).
   Which case applies?
4. **Exit date source** — `cohort_end_date` per the cases in
   [`derived-elements-conventions.md` § `cohort_end_date`](../standards/derived-elements-conventions.md#cohort_end_date--deployment-specific).
   Which case applies (priority order)?
5. What cohort window is needed? (e.g. 6-month, 12-month)
6. What measurement types need tracking? (e.g. BP, HbA1c, weight) — list each
   with its survey form, field IDs, and control thresholds.
7. Which `map__omop_*` seeds exist in this repo? (check repo `AGENT.md` under
   "Cohort configuration", or search `seeds/` for `map__omop_` files)

Document the answers in the repo's `AGENT.md` under a **"Cohort configuration"**
section before proceeding. Create the section if it doesn't exist.

**Register the cohort in the central registry.**

See [`derived-elements-conventions.md` § Registry](../standards/derived-elements-conventions.md#registry)
for the current operative state (`cohort_definitions.csv` with integer
`cohort_definition_id`) and the destination state (unified
`metric_definitions.csv` with text `cohort_id`). The runbook applies the
transition rule: open a PR to `tamanu-source-dbt` to add a row to
`cohort_definitions.csv` *and* pick a text `cohort_id` matching the model suffix
(e.g. `cohort_ncd` for `der__cohort_ncd`). Both IDs co-exist on the new model
until consolidation lands.

---

## Prerequisites

- `dbt deps` run; database connection configured
- Step 0 answers documented in the repo's `AGENT.md`
- `program_registry_id` and condition IDs verified queryable:
  ```sql
  select distinct program_registry_id from patient_program_registrations;

  select distinct program_registry_condition_id
  from patient_program_registration_conditions
  where split_part(patient_program_registration_id, ';', 2) = '<programRegistry-id>';
  ```

---

## Steps

### 1. Build `der__cohort_<name>_registry` **[can start immediately]**

Create `models/derived/der__cohort_<name>_registry.sql` — env-aware
materialisation (`view` on the replica is the typical choice; see
[`dbt-conventions.md` § Environment-aware materialisation](../standards/dbt-conventions.md#environment-aware-materialisation-targetname-switch)).

Follow the registry-model pattern in
[`derived-elements-conventions.md` § Registry model](../standards/derived-elements-conventions.md#registry-model-der__cohort_name_registry):
conditions pivot CTE, exit CTE, registry filter. Read upstream via
`ref('base__...')` or `ref('can__...')` — never via `source()` (D10).

Create matching `.yml` — document all columns.

### 2. Build cohort patient selection **[after step 1]**

Create `models/derived/int__<name>_cohort_<period>_patients.sql` — `ephemeral`.

Follow the pattern in
[`derived-elements-conventions.md` § Cohort patient selection](../standards/derived-elements-conventions.md#cohort-patient-selection-int__name_cohort_period_patients):
reporting-months scaffold, `CROSS JOIN` to the registry, registration-month
filter, active-at-evaluation filter.

Create matching `.yml`.

### 3. Build measurement window models **[parallel, after step 1]**

For each measurement type from Step 0, create one ephemeral intermediate at
`models/derived/int__<name>_cohort_<period>_<measurement>.sql`.

Follow the pattern in
[`derived-elements-conventions.md` § Measurement window models](../standards/derived-elements-conventions.md#measurement-window-models-int__name_cohort_period_measurement):
filter to the measurement window, apply control thresholds, group by
`yearmonth, patient_id`.

Document window bounds and thresholds in a comment at the top of each file.

Create matching `.yml` for each.

### 4. Build `der__cohort_<name>` **[after steps 2 and 3]**

Create `models/derived/der__cohort_<name>.sql` — env-aware materialisation.

Must include the OMOP-lite columns per
[`derived-elements-conventions.md` § OMOP-lite required columns](../standards/derived-elements-conventions.md#omop-lite-required-columns):
`cohort_id` (text), `cohort_definition_id` (integer), `subject_id`,
`cohort_start_date`, `cohort_end_date`.

Add demographics and concept shadow columns where applicable (check the repo's
`AGENT.md` for available `map__omop_*` seeds).

Create matching `.yml` — document all OMOP columns; state both `cohort_id` and
`cohort_definition_id` values in the model description.

### 5. Build `der__cohort_<name>_observations` **[after steps 2 and 3]**

Create `models/derived/der__cohort_<name>_observations.sql` — env-aware
materialisation. Join `int__<name>_cohort_<period>_patients` to each measurement
intermediate; one row per patient per reporting period, linked by `patient_id` +
`yearmonth`.

Create matching `.yml` — document measurement columns including control
thresholds.

### 6. Add report and aggregation outputs **[parallel, after steps 4 and 5]**

**Tamanu line-list report** (if needed):
- Create a report view in `models/reports/` sourcing from
  `{{ ref('der__cohort_<name>') }}`
- Follow [`new-report.md`](new-report.md) for translations, timezone macros, and
  config

**Tamanu aggregation report** (if needed):
- `view`-materialised model sourcing from `{{ ref('der__cohort_<name>') }}`
- Aggregate by `yearmonth`, facility, or other dimensions in the report; filter
  in the report, not in the cohort model
- Never redefine cohort membership — always source from the `der__` model
  (shared-pivot rule)

**Tupaia aggregation / Data Table** (if needed):
- Preferred: the `der__cohort_<name>` model itself is the Tupaia Data Table —
  Tupaia reads it directly and applies its own filters
- If a separate pre-aggregated table is needed for performance, materialise on
  the replica only (`analytics_*` target); keep it out of the production bundle
- If the aggregation matches a Tamanu aggregation report, extract a shared macro

The shared-pivot rule (never redefine cohort logic) is non-negotiable; see
[`derived-elements-conventions.md` § Shared-pivot rule](../standards/derived-elements-conventions.md#shared-pivot-rule).

---

### 7. Validate **[parallel checks]**

```bash
sqlfluff fix models/derived/

dbt test --profiles-dir config \
  --select der__cohort_<name> der__cohort_<name>_registry der__cohort_<name>_observations

grep -r "cohort_definition_id\|cohort_id" models/derived/*.yml
```

---

## Checklist before opening a PR

- [ ] `der__cohort_<name>_registry` created with conditions pivot and exit CTE
- [ ] `int__<name>_cohort_<period>_patients` created (ephemeral)
- [ ] One `int__<name>_cohort_<period>_<measurement>` per measurement type
      (ephemeral)
- [ ] `der__cohort_<name>` created with all OMOP-lite columns (`cohort_id`,
      `cohort_definition_id`, `subject_id`, `cohort_start_date`,
      `cohort_end_date`)
- [ ] `der__cohort_<name>_observations` created
- [ ] All models have `.yml` documentation; OMOP columns documented; both
      `cohort_id` and `cohort_definition_id` values stated in model description
- [ ] Repo `AGENT.md` updated with cohort configuration (entry/exit date
      sources, programme ID)
- [ ] Tamanu report and/or Tupaia Data Table added (if required)
- [ ] All downstream consumers (`ref()`) source from `der__cohort_<name>` — not
      from bespoke re-derivations
- [ ] `cohort_definition_id` registered in
      `tamanu-source-dbt/seeds/cohort_definitions.csv` and matches exactly
- [ ] `cohort_id` text value matches the model suffix
- [ ] No reads from `public.*` outside `bases/` (D10)
- [ ] `sqlfluff fix` applied
- [ ] `dbt test` passes
- [ ] Spec added if the cohort warrants one (see
      [`../standards/sdd-conventions.md`](../standards/sdd-conventions.md))
