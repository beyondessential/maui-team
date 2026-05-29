# dbt Conventions

For SQL formatting rules (casing, aliases, formatting, joins), see `sql-conventions.md`. This file covers dbt model structure, tooling, and documentation.

## Model layers

The layer taxonomy aligns with OMOP categories where there's a fit (`ref__`, `lkp__`,
`can__`, `der__`) and adds BES-specific layers above (`metric__`, `ds__`,
`models/reports/`). See `../architecture/data-architecture.md` (D2) for rationale.

```
sources / logs
     │
   bases ──┬── ref__ ──────────┐
           ├── lkp__ ──────────┤
           │                   ├── can__ ── der__ ── metric__ ── ds__ ── reports
           └── surveys, facts (legacy, in active use)
```

`int__<description>` ephemeral models may be inserted between any two layers wherever
shared logic would otherwise be duplicated.

| Layer | Naming | Purpose | Materialisation |
|---|---|---|---|
| `sources` | declared in `sources.yml` | Raw Tamanu tables — never modified | n/a |
| `logs` | declared in `sources.yml` | Raw log/event tables — never modified | n/a |
| `bases/` | `base__<entity>` | **Only** layer allowed to read `public.*` (see D10 below). Filters deleted rows, drops internal metadata, normalises naming. Package-managed in `tamanu-source-dbt` | `view` (always) |
| `ref__` | `ref__<entity>` | OMOP health-system data wrappers (e.g. `ref__care_site`, `ref__location`, `ref__provider`) | `view` |
| `lkp__` | `lkp__<entity>` | Data-team-curated lookups — analytic groupings, cross-system mappings, standard codings. Seed-backed | `view` (always) |
| `can__` | `can__<entity>` | Canonical clinical-event facts in OMOP-lite shape (e.g. `can__person`, `can__visit_occurrence`, `can__measurement`) | env-aware (see below) |
| `der__` | `der__<element>` | Derived analytic constructs — cohorts (`der__cohort_<program>`), eras, episodes | env-aware (see below) |
| `metric__` | `metric__<id>` | Health indicators — single source of truth, shared by Tamanu reports and Tupaia. Mandatory entry in `metric_definitions.csv` | env-aware (see below) |
| `int__` | `int__<description>` | Shared intermediate logic — joins, pivots, derivations. No `order by` | `ephemeral` |
| `ds__` | `ds__<description>` | Denormalised, consumer-shaped datasets — joins across `can__`, `der__`, `metric__`. No `order by` | env-aware (see below) |
| `models/reports/` | `<description>_line_list` (and similar) | Tamanu reports — apply translations, date formatting, report configs. `order by` allowed | `view` |

### Legacy layers still in active use

> **Sunset.** Delete this table once Phase 5 (architecture migration; see
> `../runbooks/refactoring-guide.md` § Phase 5) completes — i.e. all `dim__`, `coh__`,
> `fct__`, and `surveys` models have either been migrated or formally retained as
> generated/exempt.

These predate the architecture taxonomy and are either in soft retirement or being
renamed. Treat them as the operative pattern for existing work; use the new prefixes
for new models.

| Layer | Naming | Status | Notes |
|---|---|---|---|
| `surveys` | `<survey_id>` | Active | **Generated** — never edit manually; regenerate via script. See repo `AGENT.md` for script path |
| `facts` | `fct__<description>` | Active | Event-grain alongside surveys. No `order by` |
| `dim__` | `dim_<entity>` (`dim_patient`, `dim_location`, …) | Soft retirement | New work uses `ref__` (health system) and `can__` (clinical). Existing `dim__` models remain until migrated |
| `coh__` | `coh__<program>` | Renaming to `der__cohort_<program>` per Phase 0 | New cohorts use the new prefix; existing `coh__` models remain until migrated. See `derived-elements-conventions.md` |

## Materialisations

| Type | When to use |
|------|-------------|
| `view` | Fast build, slow query — default for lightweight models |
| `table` | Slow build, fast query — use for frequently queried models |
| `incremental` | Large, append-only datasets |
| `ephemeral` | Reusable logic with no direct materialisation |

### Environment-aware materialisation (`target.name` switch)

Models in the transitive closure of `models/reports/` ship to production via the
compiled SQL bundle, where they must be valid as views over the production schema. The
same model runs on the replica, where larger materialisations are fine for analytics
performance. Resolve the conflict by switching materialisation on `target.name`:

```sql
{{ config(
  materialized = ('view' if target.name.startswith('reporting_') else 'incremental'),
  unique_key = 'patient_id',
  incremental_strategy = 'merge',
) }}
```

- `reporting_*` targets compile the production bundle — the model must be
  production-safe SQL (no Python models, valid against production schema, tractable as
  a runtime view)
- `analytics_*` targets run on the replica — `incremental` or `table` materialisations
  are acceptable for performance

If the natural implementation can't be made production-safe (e.g. window functions
aggregating all encounters per patient), keep the model **out** of any Tamanu report's
chain. It can still live as a replica-only `metric__` consumed by Tupaia via Data
Tables. See `../architecture/data-architecture.md` (Production promotion path and D9).

`bases/`, `lkp__`, and `models/reports/` are always views regardless of environment.
Other layers in the new taxonomy (`ref__`, `can__`, `der__`, `metric__`, `ds__`) use
the env-aware pattern when they sit in a report chain.

## File naming

- Model SQL: `<model_name>.sql`
- Model documentation: `<model_name>.yml` (same name, same directory)
- Report configs: in `models/reports/config/<model_name>.json`
  - The `"query"` field in report configs is a placeholder (`"replace this"`) — the actual SQL is injected at compile time. This is expected and should not be flagged during review.

## Documentation

- **Mandatory** `.yml` file for all non-report models (`bases/`, `ref__`, `lkp__`,
  `can__`, `der__`, `metric__`, `ds__`, `int__`, and legacy `facts` / `surveys`)
- Document all columns — at minimum a short description
- Report models require a corresponding JSON config file
- `metric__` models additionally require a row in `metric_definitions.csv` — see
  `../architecture/data-architecture.md` (D5)

## Testing

Three kinds of tests sit alongside the models, all under whichever directory the repo's
`dbt_project.yml` configures as `test-paths` (conventionally `data-tests/`):

| Kind | File pattern | Use for |
|------|-------------|---------|
| Schema-level generic tests | inline `tests:` blocks in `<model>.yml` | column-level invariants — `not_null`, `unique`, `relationships`, `accepted_values`, or `dbt_utils.expression_is_true` for inequality / multi-column conditions on the model itself |
| Unit tests (dbt 1.8+, mocked inputs) | `unit_test__<model>.yml` | scenario coverage of transformation logic against hand-crafted inputs |
| Singular data tests (real data) | `data_test__<model>.sql` | invariants that cross-reference upstream tables or otherwise can't be expressed as a schema test |

Conventions:

- **One singular-test file per model.** Name it `data_test__<model>.sql`. Stitch multiple
  assertions together inside the file with `union all`, and tag each failure row with a
  discriminator column (e.g. `failed_ac` carrying the AC-ID from the spec) so the failing
  assertion is identifiable from the test output.
- Base models require no tests — they are thin projections over source models, which carry
  their own tests
- Dataset models must have `not_null` and `unique` tests on primary keys
- Where the repo follows SDD, name each test after the spec acceptance criterion it
  asserts (`ac_NNN_<model>_<assertion>` for schema-level tests; the `failed_ac` column
  inside the singular file otherwise). See the SDD spec format.
- Run `dbt test` before committing

## Code quality rules

- No `order by` in `bases/`, `ref__`, `lkp__`, `can__`, `der__`, `metric__`, `int__`,
  `ds__`, `surveys`, or `facts` — only in reports
- **`bases/` is the only layer allowed to read `public.*`** (D10). Every other layer
  (`ref__`, `lkp__`, `can__`, `der__`, `metric__`, `ds__`, `models/reports/`) sources
  from `{{ ref('base__...') }}`, never `{{ source('tamanu', '...') }}`. Reading
  `public.*` outside `bases/` leaks deleted records and breaks on Tamanu version
  bumps. See `../architecture/data-architecture.md` (D10) for the full rationale.
- Before deleting a model, check downstream dependencies:
  ```bash
  grep -r "ref('<model_name>')" models/
  ```
- Use `{{ ref('model_name') }}` for all cross-model references — never hardcode schema or table names
- Use `{{ source('source_name', 'table_name') }}` for source references — and **only in `bases/`**

## Date/time formatting

Use centralised variables defined in `dbt_project.yml` — never hardcode format strings in models:

```sql
{{ var("date_format") }}
{{ var("datetime_format") }}
{{ var("time_format") }}
```

Add new format variables to `dbt_project.yml` rather than inline in models.

## Translations

Use the project's translation macro for all user-facing labels — never hardcode label strings. Check for existing translations before creating new ones.

Translation system details (macro name, CSV source, prefix conventions) are project-specific — see the repo's `AGENT.md`.

## Validation scripts

Run validation scripts before committing changes to report configs or translations. Script paths differ by repo — see the repo's `AGENT.md` for the full pre-commit checklist.

## Package management

- Pin specific version tags in `packages.yml` — never use floating references
- Run `dbt deps` after updating package versions
- Use scripts from `dbt_packages/` rather than duplicating logic locally

## Do not review

- `models/sources/` — managed externally, read-only
- `compiled/` — generated artefacts
- `models/surveys/` — regenerated by script
- Auto-generated report list files

## Pre-commit checklist

```bash
sqlfluff fix .
dbt test --profiles-dir config
# run repo-specific validation scripts (see repo AGENT.md)
```

## Project-specific conventions

Add layer-specific rules, variable usage, macro conventions, translation details, and validation script paths in the repo's `AGENT.md`.

---

## Derived elements — `der__` (in-flight rename from `coh__`)

> **Scope note.** The architecture (D2) introduces a `der__` derived-elements layer that
> generalises `coh__` (cohorts) and accommodates eras and episodes. New cohorts use
> `der__cohort_<program>`; existing `coh__<program>` models remain until migrated. The
> canonical pattern reference lives in `derived-elements-conventions.md`. This section
> captures the rules that interact with the broader dbt conventions.
>
> **Sunset.** Collapse the `coh__` references in this section into the main
> conventions once Phase 5 § 5a (cohort migration) completes.

### Shared-pivot rule

All reports — line-list and aggregation — must source from the `der__` (or legacy
`coh__`) model. Never re-derive cohort membership in a downstream output. This is the
construction-time guarantee that counts agree across Tamanu reports, Tupaia dashboards,
and any future surface.

Where Tamanu and Tupaia outputs share the same downstream aggregation logic, define it
once in a macro and call it from both models.

### Materialisation

`der__` (and legacy `coh__`) follows the env-aware materialisation pattern above — view
in the production bundle, view or incremental on the replica depending on size. Existing
`coh__` models that pre-date the env-aware pattern continue to materialise as views in
both environments until migrated.

### `map__omop_<domain>` — concept ID mappings

OMOP concept shadow columns (SNOMED, LOINC, RxNorm) go in `can__` and `der__` (or legacy
`coh__`) models only, never in base models. Mappings live in `map__omop_<domain>` seeds:

- **Universal** (same across all Tamanu deployments) — in `tamanu-source-dbt` (e.g. `map__omop_sex`)
- **Deployment-specific** (local reference data, condition codes) — in `tamanu-dbt-*` seeds

Standard seed schema: `local_code`, `local_name`, `concept_id`, `concept_name`, `vocabulary_id`.

This is distinct from `lkp__` lookups — `map__omop_*` seeds map local codes to OMOP
vocabulary concept IDs; `lkp__` models are operational lookup tables used as join targets.

See `derived-elements-conventions.md` for the full derived-element pattern.
