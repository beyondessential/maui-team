# Refactoring Guide

Covers all Maui-managed repositories: `tamanu-source-dbt`, `data-staging`, `data-lake`
(dbt models and Dagster assets — to be renamed to `bes-data-pipelines`; rename pending
dependency updates). Use this guide when planning or executing refactoring work
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
Phase 5 — Architecture migration  (ds__ registries → der__cohort_<program>; dim__ → ref__/can__)
```

Phase 5 reflects the in-flight architecture transition described in
`../architecture/data-architecture.md` (D2, D7). New work uses the new prefixes;
existing models migrate as they are touched.

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

All non-generated model YAML files must include a `meta:` block. See `../standards/dbt-metadata.md` for
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

Verify model lineage respects the defined stack (see `dbt-conventions.md` for the full
layer table):

```
sources/logs
   │
 bases ──┬── ref__ ──────────┐
         ├── lkp__ ──────────┤
         │                   ├── can__ ── der__ ── metric__ ── ds__ ── reports
         └── surveys, facts (legacy, in active use)
```

`int__` ephemerals may sit between any two layers. The hard rule (D10) is that
**only `bases/` reads `public.*`** — every other layer reads via `ref()`.

Check for models that skip layers or bypass `bases/`. Use `ref()` graph traversal or
dbt lineage tools.

Common violations to search for:

```bash
# Any model outside bases/ reading public.* via source() — violates D10
grep -rn "source(" models/ --include="*.sql" \
  | grep -v "models/sources\|models/logs\|models/bases"

# Reports reading bases directly (should pass through ds__, metric__, der__, can__, or facts)
grep -rn "ref('base_\|ref('logs_" models/reports/ --include="*.sql"
```

### Materialisations audit

Review every non-ephemeral model and verify its materialisation is justified. The new
taxonomy is env-aware (replica vs production bundle) — see
`dbt-conventions.md` § Environment-aware materialisation for the `target.name` pattern.

| Layer | Expected default | Override allowed when |
|---|---|---|
| `bases/` | `view` | Never — bases are always views |
| `lkp__` | `view` | Never — lookups are always views over seeds |
| `int__` | `ephemeral` | Never — intermediates are always ephemeral |
| `ref__` | `view` | — |
| `can__`, `der__`, `metric__`, `ds__` | env-aware: `view` in `reporting_*` bundle, `view` / `incremental` / `table` on `analytics_*` replica | Override permitted on replica targets only; production bundle is always a view |
| `models/reports/` (Tamanu) | `view` | Always — production bundle |
| Tupaia-only `metric__` outside the report chain | `incremental` or `table` on replica | — |
| `facts`, `surveys`, `coh__` (legacy) | `view` | — |

Models in the transitive closure of `models/reports/` ship to production via the
compiled bundle and must be production-safe SQL (no Python models, valid against
production schema, tractable as a runtime view). Replica-only models can use heavier
materialisations.

Search for intermediates incorrectly materialised as views or tables:

```bash
grep -rn "materialized.*view\|materialized.*table" \
  models/intermediate/ --include="*.sql" --include="*.yml"
```

View-on-view nesting (a view selecting from another view) carries a runtime penalty. If a
`ds__` or `metric__` queries several views joined together, consider whether the shared join
logic should become an `ephemeral` `int__` intermediate.

### Naming consistency

Run a naming audit against the conventions in `dbt-conventions.md`:

| Layer | Expected pattern | Check |
|---|---|---|
| `bases/` | `base__<entity>` | `grep -rn "^  - name:" models/bases/` |
| `ref__` | `ref__<entity>` | — |
| `lkp__` | `lkp__<entity>` | — |
| `can__` | `can__<entity>` | — |
| `der__` | `der__<element>` (e.g. `der__cohort_<program>`) | — |
| `metric__` | `metric__<id>` (snake-case, matches `metric_definitions.csv`) | — |
| `int__` | `int__<description>` | `grep -rn "^  - name:" models/intermediate/` |
| `ds__` | `ds__<description>` | — |
| Reports | `<description>_line_list` (and similar suffixes) | — |
| `facts` (legacy) | `fct__<description>` | `grep -rn "^  - name:" models/facts/` |
| `coh__` (legacy, renaming) | `coh__<program>` → `der__cohort_<program>` | new cohorts use `der__`; existing models migrate when touched |
| `dim__` (legacy, soft retirement) | `dim_<entity>` | new work uses `ref__` / `can__` |

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

The specific known-duplicate inventory used to live here but rots quickly. It now
lives in the Linear consolidation epic (see project board). Use the command above to
generate a fresh inventory before each dedup pass; treat any result that appears in
3+ country projects as a consolidation candidate.

**When to consolidate vs keep separate:**

Move to `data-staging` when the model appears in three or more country projects and the only
differences are: country suffix in the model name, deployment-specific facility/location IDs,
or survey form IDs (all of which can be variables or seeds). Keep in the country project when
the logic reflects genuinely country-specific clinical workflows or local reference data
structures that are unlikely to generalise.

---

## Phase 5 — Architecture migration

Two migrations run in parallel under Phase 5, both following from
`../architecture/data-architecture.md` (D2, D7).

### 5a — `ds__` registries → `der__cohort_<program>`

Existing `ds__` registry models should be migrated to the `der__` derived-elements layer
when:
- The program registry requires temporal analysis (incidence, LTFU, retention)
- The model is used as a shared base for both Tamanu and Tupaia outputs

See `derived-elements-conventions.md` for the full migration pattern. Steps:

1. Check whether the program already has a `cohort_definition_id` in
   `tamanu-source-dbt/seeds/cohort_definitions.csv`. Register it if not.
   (Phase 0 plans to consolidate this seed into the unified `metric_definitions.csv`
   registry — track that change separately.)
2. Build `der__cohort_<program>_registry` from the existing conditions pivot and exit
   CTE patterns. (New work uses `der__cohort_*`; existing `coh__*` models keep their
   prefix until they're touched again.)
3. Build `int__<n>_cohort_<period>_patients` for the patient selection scaffold.
4. Build `der__cohort_<program>` with the four required OMOP-lite columns.
5. Update Tamanu line-list and Tupaia outputs to source from `der__cohort_<program>`.
6. Deprecate the `ds__` model — do not delete until all downstream refs are updated.

Reference implementation: `tamanu-dbt-msf-syria` models listed in
`../standards/derived-elements-conventions.md` § Legacy `coh__` reference (the
`tamanu-dbt-msf-syria` files still carry the legacy prefix; the conventions doc
includes the migration steps).

### 5b — `dim__` → `ref__` / `can__` (soft retirement)

The `dim__` layer (e.g. `dim_patient`, `dim_location`, `dim_model`) is on the soft
retirement path. New work splits the responsibilities:

- Health-system entities (care site, location, provider) → `ref__` reading from
  `bases/` and applying OMOP column naming
- Patient and clinical-event entities → `can__` (`can__person`,
  `can__visit_occurrence`, …)

Existing `dim__` models stay in place until their downstream consumers are updated.
Migrate opportunistically when touching a model; don't delete `dim__` until all refs
point at the new layer.

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
