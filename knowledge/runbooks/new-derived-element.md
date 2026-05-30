# Adding a New Derived Element

Builds a `der__cohort_<program>` model. Currently cohort-only; extend in place
for eras/episodes when needed. Applies to `tamanu-dbt-*` repos.

Canonical patterns live in
[`../standards/derived-elements-conventions.md`](../standards/derived-elements-conventions.md);
this runbook is the procedural guide.

`[parallel]` steps can be delegated to separate agents.

---

## Step 0 — Gather config (ask the user first)

1. `program_registry_id` (e.g. `programRegistry-ncdregistry`)
2. Relevant `program_registry_condition_id`s + local column names
3. `cohort_start_date` source — see [§ `cohort_start_date`](../standards/derived-elements-conventions.md#cohort_start_date--deployment-specific)
4. `cohort_end_date` source + priority — see [§ `cohort_end_date`](../standards/derived-elements-conventions.md#cohort_end_date--deployment-specific)
5. Cohort window (`6m`, `12m`, …)
6. Measurement types + control thresholds
7. Available `map__omop_*` seeds (check repo `AGENT.md`)

Document answers under "Cohort configuration" in the repo `AGENT.md`.

## Step 0a — Register the cohort upstream *(separate PR, in `tamanu-source-dbt`)*

Cohort registration is a cross-repo step. **Open and merge this PR before
starting the deployment-side work** — the deployment models reference IDs that
must exist in the upstream seed.

1. Open a PR to **`tamanu-source-dbt`** adding a row to
   `seeds/cohort_definitions.csv`:
   - Assign the next available integer `cohort_definition_id`
   - Pick a text `cohort_id` matching the model suffix (`cohort_ncd` for
     `der__cohort_ncd`). Both IDs co-exist until registry consolidation lands
2. Wait for the PR to merge and a `tamanu-source-dbt` release to publish (or
   bump the package ref in the deployment repo's `packages.yml` to a commit
   that includes the seed row)
3. Then proceed with Step 1 below in the deployment repo

See [§ Registry](../standards/derived-elements-conventions.md#registry).

---

## Prerequisites

- `dbt deps` run; DB connection configured
- Step 0 answers in `AGENT.md`
- Verify queryability:
  ```sql
  select distinct program_registry_id from patient_program_registrations;
  select distinct program_registry_condition_id
  from patient_program_registration_conditions
  where split_part(patient_program_registration_id, ';', 2) = '<programRegistry-id>';
  ```

---

## Steps

### 1. `der__cohort_<name>_registry` `[parallel]`

`models/derived/der__cohort_<name>_registry.sql` — env-aware (typically `view`
on replica). Pattern: [§ Registry model](../standards/derived-elements-conventions.md#registry-model--patterns).
Read upstream via `ref('base__...')` / `ref('can__...')` only — never
`source()` (D10). Add `.yml`.

### 2. `int__<name>_cohort_<period>_patients` *(after 1)*

`models/derived/int__<name>_cohort_<period>_patients.sql` — `ephemeral`.
Pattern: [§ Patient selection](../standards/derived-elements-conventions.md#patient-selection--pattern).
Add `.yml`.

### 3. Measurement windows `[parallel, after 1]`

One per measurement type at `models/derived/int__<name>_cohort_<period>_<measurement>.sql`
— `ephemeral`. Pattern:
[§ Measurement window](../standards/derived-elements-conventions.md#measurement-window--pattern).
Header comment with window bounds + thresholds. Add `.yml`.

### 4. `der__cohort_<name>` *(after 2 and 3)*

`models/derived/der__cohort_<name>.sql` — env-aware. Must include OMOP-lite
columns: `cohort_id`, `cohort_definition_id`, `subject_id`, `cohort_start_date`,
`cohort_end_date` (see
[§ OMOP-lite required columns](../standards/derived-elements-conventions.md#omop-lite-required-columns)).
Add demographics + concept shadow columns where `map__omop_*` seeds exist.
`.yml` states both ID values.

### 5. `der__cohort_<name>_observations` *(after 2 and 3)*

`models/derived/der__cohort_<name>_observations.sql` — env-aware. Joins the
patient-selection intermediate to each measurement intermediate; one row per
patient × yearmonth. Add `.yml` (document thresholds).

### 6. Outputs `[parallel, after 4 and 5]`

**Tamanu line-list report**: report view sourcing
`{{ ref('der__cohort_<name>') }}`; follow [`new-report.md`](new-report.md).

**Tamanu aggregation report**: `view` sourcing `{{ ref('der__cohort_<name>') }}`;
aggregate + filter in the report, not the cohort model.

**Tupaia Data Table**: preferred path is `der__cohort_<name>` *is* the Data
Table — Tupaia reads it directly. If pre-aggregation needed for performance,
materialise on `analytics_*` only (out of production bundle).

Never redefine cohort membership downstream — shared-pivot rule
([§ Shared-pivot](../standards/derived-elements-conventions.md#shared-pivot-rule)).

### 7. Validate `[parallel]`

```bash
sqlfluff fix models/derived/
dbt test --profiles-dir config \
  --select der__cohort_<name> der__cohort_<name>_registry der__cohort_<name>_observations
grep -r "cohort_definition_id\|cohort_id" models/derived/*.yml
```

---

## PR checklist

- [ ] `der__cohort_<name>_registry` with conditions pivot + exit CTE
- [ ] `int__<name>_cohort_<period>_patients` (ephemeral)
- [ ] One `int__<name>_cohort_<period>_<measurement>` per measurement (ephemeral)
- [ ] `der__cohort_<name>` with all OMOP-lite columns
- [ ] `der__cohort_<name>_observations`
- [ ] All `.yml`s present; both `cohort_id` and `cohort_definition_id` in model
      descriptions
- [ ] Repo `AGENT.md` updated with cohort config
- [ ] Tamanu report and/or Tupaia Data Table if required
- [ ] All downstream `ref()`s use `der__cohort_<name>` — no re-derivation
- [ ] `cohort_definition_id` registered in `cohort_definitions.csv`, matches
- [ ] `cohort_id` matches model suffix
- [ ] No `public.*` reads outside `bases/` (D10)
- [ ] `sqlfluff fix` applied; `dbt test` passes
- [ ] Spec added if warranted ([`sdd-conventions.md`](../standards/sdd-conventions.md))
