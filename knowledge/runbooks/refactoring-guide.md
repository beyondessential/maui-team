# Refactoring Guide

Covers `tamanu-source-dbt`, `data-staging`, `data-lake` (→ `bes-data-pipelines`).

## Goals

| Goal | Means |
|---|---|
| Reduce maintenance | Cut duplication, hardcoded values, layer violations |
| Improve scalability | Right-size materialisations, dedupe across countries, partition |
| Improve quality | Coverage minimums, eliminate silent data loss, doc all models |

## Phases

Run in order; each phase assumes the previous is clean.

```
1. Enforcement      automated, low risk
2. Structure        layer violations, naming, materialisations
3. Testing          coverage uplift
4. Scalability      incremental, partitioning, macro consolidation
5. Architecture     ds__ registries → der__cohort_; dim__ → ref__/can__
```

Phase 5 reflects the architecture transition
([D2, D7](../architecture/data-architecture/decisions.md)). New work uses new
prefixes; existing models migrate when touched.

---

## Phase 1 — Enforcement

Baseline checks; fix before any structural work.

### Formatting + tests

```bash
sqlfluff fix .
dbt test --profiles-dir config
python scripts/validate_report_configs.py
python scripts/check_translations.py
```

### Hardcoded format strings

```bash
grep -rn "YYYY\|%Y-%m-%d\|DD/MM" models/ --include="*.sql"
```

Replace with `{{ var("date_format") }}` etc. from `dbt_project.yml`.

### Hardcoded translations

```bash
grep -rn "'Active'\|'Inactive'\|'Male'\|'Female'" models/ --include="*.sql"
```

Use the repo's translation macro (see repo `AGENT.md`).

### `source()` outside `bases/`

```bash
grep -rn "source(" models/ --include="*.sql" \
  | grep -v "models/sources\|models/logs"
```

Every downstream layer reads via `ref()` (D10).

### Floating package versions

```bash
grep -A2 "package:" packages.yml | grep -v "version:"
```

Pin specific tags; no branches.

### Missing `meta:` blocks

```bash
grep -rL "meta:" models/ --include="*.yml" \
  | grep -v "sources\|surveys\|compiled"
```

See [`../standards/dbt-metadata.md`](../standards/dbt-metadata.md).

### `order by` in wrong layers

```bash
grep -rn "order by" models/ --include="*.sql" \
  | grep -v "models/reports"
```

Reports only.

---

## Phase 2 — Structure

### Layer violations

```
sources/logs
   │
 bases ──┬── ref__ ──────────┐
         ├── lkp__ ──────────┤
         ├── surveys ────────┤   (generated pivot of survey responses)
         │                   ├── can__ ── der__ ── metric__ ── ds__ ── reports
         └── facts (legacy)
```

Hard rule: only `bases/` reads `public.*` (D10).

```bash
# D10 violations
grep -rn "source(" models/ --include="*.sql" \
  | grep -v "models/sources\|models/logs\|models/bases"

# Reports reading bases directly (should go via ds__/metric__/der__/can__/facts)
grep -rn "ref('base_\|ref('logs_" models/reports/ --include="*.sql"
```

### Materialisations

| Layer | Default | Override |
|---|---|---|
| `bases/`, `lkp__`, `surveys` | `view` | Never |
| `int__` | `ephemeral` | Never |
| `ref__` | `view` | — |
| `can__`, `der__`, `metric__`, `ds__` | env-aware | Replica only — production bundle always view |
| `models/reports/` | `view` | Always |
| Replica-only `metric__` outside report chain | `incremental` / `table` | — |
| Legacy `facts` | `view` | — |

Production-bundle models must be production-safe SQL. Env-aware pattern:
[`../standards/dbt-conventions.md`](../standards/dbt-conventions.md).

```bash
# Intermediates wrongly materialised
grep -rn "materialized.*view\|materialized.*table" \
  models/intermediate/ --include="*.sql" --include="*.yml"
```

View-on-view nesting has a runtime penalty. Pull shared join logic into an
`int__` ephemeral.

### Naming

| Layer | Pattern |
|---|---|
| `bases/` | `base__<entity>` |
| `ref__` | `ref__<entity>` |
| `lkp__` | `lkp__<entity>` |
| `surveys` | `<survey_id>` (generated; never edit manually) |
| `can__` | `can__<entity>` |
| `der__` | `der__<element>` (e.g. `der__cohort_<program>`) |
| `metric__` | `metric__<id>` (matches `metric_definitions.csv`) |
| `int__` | `int__<description>` |
| `ds__` | `ds__<description>` |
| Reports | `<description>_line_list` etc. |
| Legacy `facts` | `fct__<description>` |
| Legacy `dim__` | `dim_<entity>`, soft retirement → `ref__` / `can__` |

Rename mismatches; update all downstream `ref()`s.

### Missing `.yml`

```bash
for f in models/**/*.sql; do
  base="${f%.sql}"
  [[ ! -f "${base}.yml" ]] && echo "Missing: ${base}.yml"
done
```

Generated models (`models/surveys/`, `macros/translation.sql`) exempt.

---

## Phase 3 — Testing

### Coverage baseline

`bases/` need no tests (sources carry theirs). `ds__` must have `not_null` +
`unique` on PKs:

```yaml
columns:
  - name: <primary_key>
    tests: [not_null, unique]
```

```bash
grep -rL "not_null\|unique" models/datasets/ --include="*.yml"
```

### Range/conditional tests

`dbt_utils` tests on numeric/date fields. Patterns:
[`../standards/testing-conventions.md`](../standards/testing-conventions.md).
Priorities: age/measurement (`accepted_range`), no-future dates
(`expression_is_true`), conditional not-null for hierarchical IDs.

### Fan-out detection

```bash
grep -B5 -A10 "join" models/ --include="*.sql" \
  | grep -v "left join\|inner join\|cross join"
```

Every join needs explicit dedup, aggregation, or a one-to-one comment.

### Unit tests

Add for: window functions in cohort membership, `CASE` producing classifications,
models with past correctness bugs. Place in `data-tests/unit_tests/<model>.yml`.

### NULL handling

```bash
grep -rn "= null\|!= null" models/ --include="*.sql"
```

Use `is null` / `is not null`.

---

## Phase 4 — Scalability

### Incremental

Candidates: event-grain facts with monotonic timestamps; replicated logs.

```sql
{{ config(materialized='incremental', unique_key='id') }}

select ... from {{ source(...) }}
{% if is_incremental() %}
  where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

Confirm source has reliable `updated_at`; add a lookback window if late-arriving
records matter.

### Macro consolidation

```bash
grep -rn "where.*deleted_at is null\|where.*test_patient" models/ --include="*.sql" \
  | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20
```

Candidates: encounter/patient filter blocks, shared Tamanu+Tupaia aggregation
logic (shared-pivot rule), repeated `DISTINCT ON` exit-survey patterns.

### Dagster partitioning

`data-lake` modules: `bes`, `flutracking`, `msupply`, `nauru`, `niwa`, `senaite`,
`tamanu_backup`, `tamanu_datasets`, `tamanu_meta`, `tupaia`, `uptimerobot`,
`vesalius`, `who_icd`.

Audit for: assets loading full tables on every run with a natural time
partition; sensors without `minimum_interval_seconds`; schedules missing the
`_schedule` suffix.

```bash
grep -rn "def.*sensor\|@sensor" dagster/ --include="*.py" -l \
  | xargs grep -L "minimum_interval_seconds"
```

Patterns: [`../standards/dagster-conventions.md`](../standards/dagster-conventions.md).

### Cross-country dedup (`data-lake`)

Country projects: `dbt/tamanu_{country}/` for `dl`, `fj`, `ki`, `nr`, `pw`,
`to`, `tv`, `ws`.

**Known inconsistencies to fix first:**

1. `tamanu_fj` uses `models/mart/`; others use `models/dataset/`. Standardise on
   `models/dataset/`.
2. Intermediate prefix inconsistent — convention is `int__`. Scan:
   ```bash
   grep -rn "ref('itm__\|ref('int_[^_]" dbt/ --include="*.sql"
   ```
3. `tamanu_nr` has `r__`-prefixed models with no equivalent elsewhere. Reclassify
   as `reports` or `datasets`.

**Find duplicates:**

```bash
for country in fj ki nr pw tv ws; do
  find dbt/tamanu_${country}/models -name "ds__*.sql" \
    | sed "s/dbt\/tamanu_${country}\/models\///;s/_${country}\.sql$/.sql/;s/\.sql$//"
done | sort | uniq -c | sort -rn | awk '$1 >= 3'
```

Specific duplicate inventory rots quickly — tracked in the Linear consolidation
epic. Re-run the command before each dedup pass.

**When to consolidate:** move to `data-staging` when a model appears in 3+
country projects and differences are only country suffix, deployment IDs, or
survey form IDs. Keep separate when logic reflects genuine country-specific
clinical workflows.

---

## Phase 5 — Architecture migration

Two parallel migrations from [D2, D7](../architecture/data-architecture/decisions.md).

### 5a — `ds__` registries → `der__cohort_<program>`

Migrate existing `ds__` registry models to `der__` when:
- Program registry needs temporal analysis (incidence, LTFU, retention)
- The model serves both Tamanu and Tupaia outputs

Steps (full pattern:
[`../standards/derived-elements-conventions.md`](../standards/derived-elements-conventions.md)):

1. Check `tamanu-source-dbt/seeds/cohort_definitions.csv`; register if absent
   (Phase 0 consolidation into `metric_definitions.csv` tracked separately)
2. Build `der__cohort_<program>_registry` from the existing `ds__` registry's
   conditions pivot and exit CTE
3. Build `int__<n>_cohort_<period>_patients`
4. Build `der__cohort_<program>` with OMOP-lite columns
5. Update consumers (line-list reports, Tupaia aggregations)
6. Deprecate the `ds__` model — don't delete until all downstream refs update

### 5b — `dim__` → `ref__` / `can__`

Soft retirement. New work splits:

- Health-system entities (care site, location, provider) → `ref__` reading from `bases/`
- Patient and clinical-event entities → `can__`

Migrate opportunistically when touching a model; don't delete `dim__` until all
refs point at the new layer.

---

## Repo update checklist

After a refactoring pass, update the repo's `AGENT.md`:

- [ ] New `dbt_project.yml` variables
- [ ] New macros + intended use
- [ ] Materialisation overrides
- [ ] Incremental models (unique key + lookback)
- [ ] Cohort configuration (start/end date sources, `map__omop_*` seeds)
- [ ] Pre-commit additions

---

## Quick reference

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
