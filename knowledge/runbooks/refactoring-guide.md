# Refactoring Guide

Covers all Maui-managed repositories: `tamanu-source-dbt`, `data-staging`, `data-lake`
(dbt models and Dagster assets). Use this guide when planning or executing refactoring work
across any of these layers.

---

## Goals

| Goal | What it means in practice |
|---|---|
| **Reduce maintenance** | Eliminate duplication, hardcoded values, and layer violations that require multi-file changes for a single logical change |
| **Improve scalability** | Right-size materialisations, consolidate cross-country duplication, partition large assets |
| **Improve quality** | Enforce test coverage minimums, eliminate silent data loss patterns, document all models |

---

## Phased approach

Work through phases in order. Each phase has lower risk and higher payoff than the next, and
later phases assume the earlier ones are complete.

```
Phase 1 — Enforcement   (automated, low risk)
Phase 2 — Structure     (layer violations, naming, materialisations)
Phase 3 — Testing       (coverage uplift)
Phase 4 — Scalability   (incremental, partitioning, macro consolidation)
Phase 5 — Cohort migration  (ds__ → coh__ for registry models)
```

---

## Phase 1 — Standards enforcement

Run these checks across all repos. Fix before any structural work — they are the baseline.

### SQL and dbt formatting

```bash
sqlfluff fix .
dbt test --profiles-dir config
python scripts/validate_report_configs.py
python scripts/check_translations.py
```

Flag as blocker if any of these fail on `main`.

### Hardcoded format strings

Search for inline date format strings:

```bash
grep -rn "YYYY\|%Y-%m-%d\|DD/MM" models/ --include="*.sql"
```

Replace with project variables defined in `dbt_project.yml`:

```sql
-- Before
to_char(encounter_date, 'DD/MM/YYYY')

-- After
to_char(encounter_date, {{ var("date_format") }})
```

### Hardcoded translations

Search for hardcoded user-facing labels:

```bash
grep -rn "'Active'\|'Inactive'\|'Male'\|'Female'" models/ --include="*.sql"
```

Replace with the repo's translation macro. Check `AGENT.md` for the macro name and prefix
conventions.

### Raw source references bypassing base models

Scan for `source()` calls outside `models/sources/` and `models/logs/`:

```bash
grep -rn "source(" models/ --include="*.sql" \
  | grep -v "models/sources\|models/logs"
```

Every reference downstream of sources must go through a base model using `ref()`.

### Floating package versions

Check `packages.yml` in each repo:

```bash
grep -A2 "package:" packages.yml | grep -v "version:"
```

All packages must pin a specific git tag or version string — no branch references.

### Missing meta blocks

```bash
grep -rL "meta:" models/ --include="*.yml" \
  | grep -v "sources\|surveys\|compiled"
```

All non-generated model YAML files must include a `meta:` block. See `metadata.md` for
valid field values.

### `order by` in wrong layers

```bash
grep -rn "order by" models/ --include="*.sql" \
  | grep -v "models/reports"
```

`order by` is only permitted in report models. Remove from all other layers.

---

## Phase 2 — Structure

### Layer violations

Verify model lineage respects the defined stack:

```
sources/logs → bases → [int__] → surveys/facts/coh__ → [int__] → datasets → [int__] → reports
```

Check for models that skip layers (e.g. a dataset joining directly to a source, or a report
joining to a base). Use `ref()` graph traversal or dbt lineage tools.

Common violations to search for:

```bash
# Datasets referencing sources directly
grep -rn "source(" models/datasets/ --include="*.sql"

# Reports referencing bases directly (should go through facts/datasets)
grep -rn "ref('base_\|ref('logs_" models/reports/ --include="*.sql"
```

### Materialisations audit

Review every non-ephemeral model and verify its materialisation is justified:

| Layer | Expected default | Override allowed when |
|---|---|---|
| `bases` | `view` | Never — bases are always views |
| `int__` | `ephemeral` | Never — intermediates are always ephemeral |
| `facts`, `surveys`, `coh__` | `view` | — |
| `datasets` | `view` | Frequently queried by Tupaia — use `table` |
| Reports (Tupaia aggregation) | `table` | — |
| Reports (Tamanu line-list) | `view` | — |

Search for intermediates incorrectly materialised as views or tables:

```bash
grep -rn "materialized.*view\|materialized.*table" \
  models/intermediate/ --include="*.sql" --include="*.yml"
```

View-on-view nesting (a view selecting from another view) carries a runtime penalty. If a
dataset queries several views joined together, consider whether the shared join logic should
become an `ephemeral` intermediate.

### Naming consistency

Run a naming audit against the conventions in `dbt-conventions.md`:

| Layer | Expected pattern | Check |
|---|---|---|
| `facts` | `fct__<description>` | `grep -rn "^  - name:" models/facts/` |
| `int__` | `int__<description>` | `grep -rn "^  - name:" models/intermediate/` |
| `datasets` | `ds__<description>` | — |
| `coh__` | `coh__<description>` | — |
| Reports | `<description>_line_list` | — |

Flag any model whose file name does not match the expected prefix for its layer. Rename and
update all downstream `ref()` calls.

### Missing YAML documentation files

```bash
for f in models/**/*.sql; do
  base="${f%.sql}"
  [[ ! -f "${base}.yml" ]] && echo "Missing: ${base}.yml"
done
```

Every non-generated model requires a `.yml` file with at minimum a short description and
primary-key tests. Generated models (`models/surveys/`, `macros/translation.sql`) are exempt.

---

## Phase 3 — Testing uplift

### Minimum coverage baseline

Base models require no tests — they are thin cosmetic projections over source models, which
carry their own tests. Adding duplicate tests here creates noise without adding safety.

Dataset models must have at minimum:

```yaml
columns:
  - name: <primary_key>
    tests:
      - not_null
      - unique
```

Find dataset models missing PK tests:

```bash
grep -rL "not_null\|unique" models/datasets/ --include="*.yml"
```

### Range and conditional tests

Apply `dbt_utils` tests to numeric and date fields. See `testing-conventions.md` for
patterns. Prioritise:

- Age and measurement fields (`accepted_range`)
- Date fields that must not be in the future (`expression_is_true`)
- Conditional not-null for hierarchical IDs (child set implies parent set)

### Fan-out detection

Search for joins where a one-to-many relationship is not explicitly handled:

```bash
grep -B5 -A10 "join" models/ --include="*.sql" \
  | grep -v "left join\|inner join\|cross join"
```

Every join must have explicit deduplication or fan-out handling (e.g. `DISTINCT ON`,
aggregation, or a comment stating the join is known to be one-to-one).

### Unit tests for complex logic

Add dbt unit tests (see `testing-conventions.md`) for:
- Window functions in cohort membership logic
- `CASE` expressions producing status or classification columns
- Any model that has had a correctness bug in the past

Place unit test YAML files in `data-tests/unit_tests/<model_name>.yml`.

### NULL handling review

Scan for potential silent NULL mismatches:

```bash
grep -rn "= null\|!= null" models/ --include="*.sql"
```

All null comparisons must use `is null` / `is not null`.

---

## Phase 4 — Scalability

### Incremental models

Identify large, append-only models that are currently materialised as tables and would
benefit from incremental loading. Candidates:

- Event-grain fact tables with a monotonically increasing timestamp
- Log models replicated from Tamanu

Incremental model pattern:

```sql
{{ config(materialized='incremental', unique_key='id') }}

select ...
from {{ source(...) }}

{% if is_incremental() %}
  where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

Before converting, confirm the source table has a reliable `updated_at` column and that
late-arriving records are not a concern (or add a lookback window).

### Macro consolidation

Find duplicated SQL logic across models that should be extracted into macros:

```bash
# Look for repeated CTE patterns (e.g. the same filter block in multiple files)
grep -rn "where.*deleted_at is null\|where.*test_patient" models/ --include="*.sql" \
  | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

Candidate macros to create or extend:
- Common encounter/patient filter blocks
- Shared aggregation logic used in both Tamanu and Tupaia outputs (extract into a macro,
  call from both — see shared-pivot rule in `dbt-conventions.md`)
- Repeated `DISTINCT ON` exit survey patterns

### Dagster partitioning

Dagster assets in `data-lake` are organised into domain modules: `bes`, `flutracking`,
`msupply`, `nauru`, `niwa`, `senaite`, `tamanu_backup`, `tamanu_datasets`, `tamanu_meta`,
`tupaia`, `uptimerobot`, `vesalius`, `who_icd`.

Review each module for:

1. Assets loading full tables on every run that have a natural time partition — prioritise
   `tamanu_datasets` (per-country Tamanu replication) and `flutracking` (time-series ILI data,
   which already has `ili_partitions.py`).
2. Assets without `minimum_interval_seconds` on their sensors — check
   `tamanu_datasets/assets/sling_assets.py` and any custom sensors in `nauru/` and `vesalius/`.
3. Schedules named without the `_schedule` suffix convention (see `dagster-conventions.md`).

```bash
# Find sensors without minimum_interval_seconds
grep -rn "def.*sensor\|@sensor" dagster/ --include="*.py" -l \
  | xargs grep -L "minimum_interval_seconds"
```

See `dagster-conventions.md` for partitioned asset patterns. For `tamanu_datasets`, the
per-country replication YAMLs (`replication_{country}.yml`) define stream-level config —
partitioning should be applied at the asset level in `sling_assets.py`, not in the YAML.

### Cross-country deduplication (data-lake)

Country dbt projects live under `dbt/tamanu_{country}/` for: `dl`, `fj`, `ki`, `nr`, `pw`,
`to`, `tv`, `ws`. Each has its own `models/`, `packages.yml`, `seeds/`, and `selectors.yml`.

**Known structural inconsistencies to resolve first:**

1. `tamanu_fj` uses `models/mart/{domain}/` for datasets; all other countries use
   `models/dataset/{domain}/`. Standardise on `models/dataset/` (matches `dbt-conventions.md`
   `ds__` layer) and rename `mart/` accordingly.

2. Intermediate model prefixes are inconsistent across countries. The convention is `int__`
   (double underscore) but several countries use `itm__` or `int_` (single underscore).
   Scan and rename:
   ```bash
   grep -rn "ref('itm__\|ref('int_[^_]" dbt/ --include="*.sql"
   ```

3. `tamanu_nr` contains `r__` prefixed models (e.g. `r__tamanu_encounters_country_monthly`)
   which have no equivalent in other countries and no defined layer in `dbt-conventions.md`.
   Assess whether these should be classified as `reports` (and renamed) or `datasets`.

**Finding duplicated models across countries:**

```bash
# List dataset model names (strip country suffix) across all country projects
for country in fj ki nr pw tv ws; do
  find dbt/tamanu_${country}/models -name "ds__*.sql" \
    | sed "s/dbt\/tamanu_${country}\/models\///;s/_${country}\.sql$/.sql/;s/\.sql$//"
done | sort | uniq -c | sort -rn | awk '$1 >= 3'
```

Known duplicates confirmed in the codebase:
- `ds__encounter_medical_coding` and `ds__medical_coding` — present in `nr` and `ws` with
  near-identical structure. Consolidate into a `data-staging` macro parametrised by
  survey form ID.
- `fct_survey_medical_coding` — present in `nr` and `ws`.
- `fct_survey_patient_vitals` — present in `nr` and `ws`.
- `dim_date`, `dim_diagnosis`, `dim_location`, `dim_patient` — present in every country
  project with only the `_{country}` suffix varying. These are strong macro candidates;
  the shared dimension logic should live in `data-staging`, with country projects passing
  deployment-specific reference data as variables or seeds.

**When to consolidate vs keep separate:**

Move to `data-staging` when the model appears in three or more country projects and the only
differences are: country suffix in the model name, deployment-specific facility/location IDs,
or survey form IDs (all of which can be variables or seeds). Keep in the country project when
the logic reflects genuinely country-specific clinical workflows or local reference data
structures that are unlikely to generalise.

---

## Phase 5 — Cohort migration

Existing `ds__` registry models should be migrated to the `coh__` semantic layer when:
- The program registry requires temporal analysis (incidence, LTFU, retention)
- The model is used as a shared base for both Tamanu and Tupaia outputs

See `cohort-conventions.md` for the full migration pattern. Steps:

1. Check whether the program already has a `cohort_definition_id` in
   `tamanu-source-dbt/seeds/cohort_definitions.csv`. Register it if not.
2. Build `coh__<n>_registry` from the existing conditions pivot and exit CTE patterns.
3. Build `int__<n>_cohort_<period>_patients` for the patient selection scaffold.
4. Build `coh__<n>` with the four required OMOP-lite columns.
5. Update Tamanu line-list and Tupaia aggregation outputs to source from `coh__<n>`.
6. Deprecate the `ds__` model — do not delete until all downstream refs are updated.

Reference implementation: `tamanu-dbt-msf-syria` models listed in `cohort-conventions.md`.

---

## Repository update checklist

When completing a refactoring pass on a repo, update the repo's `AGENT.md` to reflect:

- [ ] Any new variables added to `dbt_project.yml`
- [ ] Any new macros created and their intended usage
- [ ] Materialisations changed from default
- [ ] Incremental models and their unique key / lookback window
- [ ] Cohort configuration (start/end date sources, available `map__omop_*` seeds)
- [ ] Pre-commit checklist if new validation scripts were added

---

## Quick reference — audit commands

```bash
# Phase 1
sqlfluff fix .
dbt test --profiles-dir config
grep -rn "YYYY\|%Y-%m-%d" models/ --include="*.sql"
grep -rn "source(" models/ --include="*.sql" | grep -v "models/sources\|models/logs"
grep -rn "order by" models/ --include="*.sql" | grep -v "models/reports"
grep -rL "meta:" models/ --include="*.yml" | grep -v "sources\|surveys\|compiled"

# Phase 2
grep -rn "source(" models/datasets/ --include="*.sql"
grep -rn "materialized.*view\|materialized.*table" models/intermediate/ --include="*.yml"
grep -rn "= null\|!= null" models/ --include="*.sql"

# Phase 3
grep -rL "not_null\|unique" models/datasets/ --include="*.yml"
```
