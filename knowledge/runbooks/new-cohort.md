# Runbook: Adding a New Cohort

Builds a program registry cohort using the OMOP-inspired `coh__` semantic layer. Follow steps
in order; steps marked **[parallel]** can be delegated to separate agents running simultaneously.

Applies to `tamanu-dbt-*` repos. See `cohort-conventions.md` for full pattern reference.

---

## Step 0 — Gather deployment-specific configuration

**The agent must ask the user these questions before writing any code.**

1. What is the `program_registry_id` for this program? (e.g. `programRegistry-ncdregistry`)
2. What condition IDs (`program_registry_condition_id`) are relevant, and what local name
   should each column use?
3. **Entry date source** — is `cohort_start_date` taken from:
   - The registry `datetime` field on `patient_program_registrations`, OR
   - A specific intake/enrolment survey form? (state the form model name and field ID)
   - Or: survey date when present, registry date as fallback?
4. **Exit date source** — is `cohort_end_date` taken from:
   - A dedicated exit survey form? (state the form model name and exit date field ID)
   - The patient's `registration_status` becoming inactive on the registry?
   - Or: exit survey preferred, inactive status as fallback?
5. What cohort window is needed? (e.g. 6-month, 12-month)
6. What measurement types need tracking? (e.g. BP, HbA1c, weight) — list each with its
   survey form, field IDs, and control thresholds.
7. Which `map__omop_*` seeds exist in this repo? (check repo `AGENT.md` under "Cohort
   configuration", or search `seeds/` for `map__omop_` files)

Document the answers in the repo's `AGENT.md` under a **"Cohort configuration"** section
before proceeding. If this section does not exist, create it.

**Check the central cohort definition registry.**

Open `tamanu-source-dbt/seeds/cohort_definitions.csv` and check whether this program already
has an entry. If it does not:
1. Open a PR to `tamanu-source-dbt` to add the new row (assign the next available integer ID)
2. Wait for that PR to merge before building the deployment-specific `coh__` models here
3. The `cohort_definition_id` used in this repo must match the registry value exactly — never
   assign one locally

---

## Prerequisites

- `dbt deps` run; database connection configured
- Answers to all Step 0 questions documented in `AGENT.md`
- `program_registry_id` and condition IDs verified as queryable in the target database:
  ```sql
  select distinct program_registry_id
  from patient_program_registrations;

  select distinct program_registry_condition_id
  from patient_program_registration_conditions
  where split_part(patient_program_registration_id, ';', 2) = '<programRegistry-id>';
  ```

---

## Steps

### 1. Build `coh__<name>_registry` **[can start immediately]**

Create `models/cohort/coh__<name>_registry.sql` — materialised as `view`.

- Conditions CTE: pivot `patient_program_registration_conditions` using
  `MAX(CASE WHEN program_registry_condition_id = '...' THEN datetime END)`
- Exit CTE: `DISTINCT ON (patient_id)` from the exit survey model, ordered by exit date desc
- Join patients, demographics, conditions, exit, and reference data
- Filter: `where ppr.program_registry_id = '<programRegistry-id>'`

Create matching `coh__<name>_registry.yml` — document all columns.

### 2. Build cohort patient selection **[after step 1]**

Create `models/cohort/int__<name>_cohort_<period>_patients.sql` — materialised as `ephemeral`.

- `generate_series` reporting months from `{{ var("start_date") }}` to current month minus 1
- `CROSS JOIN {{ ref('coh__<name>_registry') }}`
- Filter: registration month = reporting month minus cohort window
  (e.g. `- interval '9 months'` for a 6-month cohort evaluated 3 months after close)
- Filter: patient active at evaluation point (no exit or exit after evaluation date)
- Include `cohort_start_date` per the Step 0 answer

Create matching `int__<name>_cohort_<period>_patients.yml`.

### 3. Build measurement window models **[parallel with each other, after step 1]**

For each measurement type identified in Step 0, create one ephemeral intermediate:
`models/cohort/int__<name>_cohort_<period>_<measurement>.sql`

- Filter encounters/survey results to the measurement window
  (e.g. 3–9 months post-registration for a 6-month cohort)
- Apply control threshold logic as `CASE WHEN` boolean flags
- Document window bounds and control thresholds in a comment at the top of the file
- Group by `yearmonth, patient_id` — one row per patient per reporting month

Create matching `.yml` for each.

### 4. Build `coh__<name>` **[after steps 2 and 3]**

Create `models/cohort/coh__<name>.sql` — materialised as `view`.

Must include the four OMOP-lite columns:

| Column | Source |
|--------|--------|
| `cohort_definition_id` | Integer constant — assign the next available ID in this repo |
| `subject_id` | `patients.id` |
| `cohort_start_date` | Per Step 0 answer |
| `cohort_end_date` | Per Step 0 answer; apply censoring priority order |

Add demographics and concept shadow columns (if `map__omop_*` seeds exist for the relevant
domains — check repo `AGENT.md`).

Create `coh__<name>.yml` — document all four OMOP columns; state the `cohort_definition_id`
value in the model description.

### 5. Build `coh__<name>_observations` **[after steps 2 and 3]**

Create `models/cohort/coh__<name>_observations.sql` — materialised as `view`.

- Join `int__<name>_cohort_<period>_patients` to each measurement intermediate
- One row per patient per reporting period
- Linked by `patient_id` + `yearmonth`

Create matching `.yml` — document measurement columns including control thresholds.

### 6. Add report and aggregation outputs **[parallel, after steps 4 and 5]**

**Tamanu line-list report** (if needed):
- Create a report view in `models/reports/` sourcing from `{{ ref('coh__<name>') }}`
- Apply `{{ translate_label(...) }}` for user-facing column aliases
- Apply `{{ to_user_selected_timezone(...) }}` for datetime fields
- Follow the `new-report.md` runbook for config and translations

**Tupaia aggregation model** (if needed):
- Create a `table`-materialised model in `models/cohort/` or `data-staging`
- Source from `{{ ref('coh__<name>') }}` — aggregate by `yearmonth`, facility, or other dimensions
- Never redefine cohort membership logic — always source from `coh__`

---

### 7. Validate **[parallel checks]**

```bash
# Lint SQL
sqlfluff fix models/cohort/

# Run dbt tests
dbt test --profiles-dir config --select coh__<name> coh__<name>_registry coh__<name>_observations

# Check cohort_definition_id is unique across all coh__ models
grep -r "cohort_definition_id" models/cohort/*.yml
```

---

## Checklist before opening a PR

- [ ] `coh__<name>_registry` created with conditions pivot and exit CTE
- [ ] `int__<name>_cohort_<period>_patients` created (ephemeral)
- [ ] One `int__<name>_cohort_<period>_<measurement>` per measurement type (ephemeral)
- [ ] `coh__<name>` created with all four OMOP-lite columns
- [ ] `coh__<name>_observations` created
- [ ] All models have `.yml` documentation; OMOP columns documented; `cohort_definition_id`
      value stated in model description
- [ ] Repo `AGENT.md` updated with cohort configuration (entry/exit date sources, program ID)
- [ ] Tamanu report and/or Tupaia aggregation model added (if required)
- [ ] Both Tamanu report and Tupaia model source from `coh__` — not independently
- [ ] `cohort_definition_id` is registered in `tamanu-source-dbt/seeds/cohort_definitions.csv`
- [ ] `cohort_definition_id` value in this model matches the registry exactly
- [ ] `sqlfluff fix` applied
- [ ] `dbt test` passes
