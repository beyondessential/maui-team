# Tamanu dbt Conventions

Conventions for dbt projects that model data from Tamanu (electronic health
records). General dbt conventions live in `dbt-conventions.md`; this file covers
the Tamanu-specific patterns layered on top.

## Version branches

Maui manages multiple Tamanu deployments running different versions. Long-running
version branches in Tamanu-bound repositories are named by `<major>.<minor>`:

```
main      ← latest (e.g. 2.50.x)
2.49      ← maintained for deployments on 2.49
2.48      ← maintained for deployments on 2.48
```

- Cut short-lived work branches from the relevant version branch when targeting
  a specific deployed version; cut from `main` for forward-only work
- Backport fixes to older version branches via cherry-pick or a separate PR
  against the version branch
- See `release-conventions.md` for how version branches map to release tags and
  `git-conventions.md` for the general branching rules

## `data_staging` package

External package at `dbt_packages/data_staging/` — not editable in consuming repos. Changes require a new package release in `beyondessential/data-staging`.

> **Merger note.** The `data-staging` package is in the process of being merged into
> `tamanu-source-dbt` (see `../AGENT.base.md` repo list). Until the merge lands, treat
> `data_staging` as the canonical home for shared base/staging models; after the merge,
> equivalent models live under `tamanu-source-dbt/models/` and the package import goes
> away. Standards in this file describe the pre-merge layout.

## Source naming

- **`source('tamanu', 'table')`** — direct queries against Tamanu raw tables; works across all targets (`tamanu_nr`, `clone`, `demo`, etc.)
- **`source(target.name, 'table')`** — used internally by `data_staging` staging models only; do not use in project models

## Localised model overrides

Each instance may define localised versions of `data_staging` dimension models with a country-code suffix (e.g. `dim_patient_nr`, `dim_location_ki`). Always use the localised version when one exists — never `ref()` a package model directly if a `_{cc}` suffixed override is present in `models/dimension/`.

## `fct__` vs `dim__patient_program_registrations`

- `fct__patient_program_registrations` — one row per registration event (counts, dates)
- `dim__patient_program_registrations` — SCD2 history of registration state (point-in-time status)

## SCD2 dim conventions

- `valid_to` is never NULL — current records use `{{ var("default_end_datetime") }}` as the sentinel
- Select current record: `valid_to = '{{ var("default_end_datetime") }}'::timestamp`
- Always filter `registration_status = 'active'` when joining for active patients

## JOIN types for mapping tables

Tupaia mapping tables (`facility_mapping`, subdivision tables) are incomplete — always use LEFT JOIN with a COALESCE fallback.

Tamanu FK columns are often nullable — verify against the model/migration in `../tamanu` before picking INNER vs LEFT JOIN, or rows silently drop (e.g. `patient_program_registration_conditions.program_registry_condition_id` is nullable while `program_registry_condition_category_id` is NOT NULL).

## Timezone handling

Clinical/domain datetimes flow through bases and `ds__` as timestamps untouched — no `at time zone`, no `to_user_selected_timezone()` wrap at those layers. The `to_user_selected_timezone()` macro is applied **only** in the report layer (`to_char({{ to_user_selected_timezone('field') }}, var("date_format"))`), where it respects the viewer's `:timezone` session variable and defaults to `var("timezone")` when unset (so the deployment TZ stays the practical default). Audit metadata (`created_at`, `updated_at`, `deleted_at`) is the only exception: those columns are `timestamp with timezone`, and the base models present them in deployment-local wall-clock time via `at time zone '{{ var("timezone") }}'`.

## Deduplication with `DISTINCT ON`

- `ORDER BY ... ASC` = keeps the earliest record
- `ORDER BY ... DESC` = keeps the latest record

## Recurring mart patterns

**Tupaia mapping** (use instance-appropriate fallback values):
```sql
COALESCE(s.tupaia_subdivision_id, CONCAT('{CC}_sdUnknown_d', p.division)) AS subdivision_id,
COALESCE(f.tupaia_facility_id, '{CC}_fUnknown_sdUnknown_dUnknown') AS tupaia_facility_id
```

**Age category join:**
```sql
JOIN {{ ref('age_in_years_category_{instance}') }} c
    ON c.age_in_years_key = {{ age_in_years_key('date_column', 'p.date_of_birth') }}
```

**Monthly census scaffold** (point-in-time patient counts):
```sql
FROM dim_model
CROSS JOIN reporting_months rm
WHERE valid_from::DATE <= rm.end_of_month
  AND valid_to::DATE >= rm.end_of_month
```

## Narrower-window parallel intermediates

Tamanu reports run against the production schema as **views over the
compiled bundle** ([data-architecture/decisions.md](../architecture/data-architecture/decisions.md)
D5/D9) — every report query re-evaluates the full upstream chain at run time.
For reports that aggregate over the full reporting history (multi-year
indicator panels for DHIS2 export, registry summaries, etc.), the view chain
can run for tens of seconds against the production DB.

The standard mitigation is a **narrower-window parallel intermediate**: a
sibling model of the all-time intermediate that filters to (typically) the
past 3 reporting months, paired with a sibling report that consumes only the
narrow-window chain. Routine monthly export runs hit the narrow chain
(sub-second); ad-hoc historical pulls hit the all-time chain (slow but rare).

This is **not a stopgap** for the architecture's incremental-materialisation
direction ([decisions.md](../architecture/data-architecture/decisions.md) D5):
replica-side incremental materialisation helps Tupaia consumers and ad-hoc
analytics, but the production view chain still re-evaluates at query time by
design (live data, no staleness). Narrower-window intermediates are the
production-side answer and stay relevant alongside any future incremental
work on the replica.

### Implementation pattern — collapse main + `_past3m` onto a macro

Without care, each indicator ends up with two parallel SQL files that drift
out of sync as bugs and edge cases land in only one. Use a single body macro
per indicator under `macros/<deployment>_reporting/`, parameterised by a
`window` argument, with thin model files calling it:

```
macros/<deployment>_reporting/
  _helpers.sql                            # window-start, ref-suffix helpers
  cohort_<program>_patients.sql           # one body macro per indicator
  indicators_consultations.sql
  ...

models/intermediate/
  int__<...>_patients.sql                 # {{ <name>(window='all_time') }}
  int__<...>_patients_past3m.sql          # {{ <name>(window='past3m') }}
```

The model files are vestigial — dbt needs them in the manifest for
ref-graph resolution, but the SQL lives in the macro.

**Shared helpers.** Three helpers handle the differing fragments so each body
macro only branches on `{% if window == 'past3m' %}` in one place:

```jinja
{% macro <deployment>_reporting_months_start(window) %}
{%- if window == 'past3m' -%}
date_trunc('month', {{ get_current_date() }} - interval '3 months')::date
{%- else -%}
'{{ var("start_date") }}'::date
{%- endif -%}
{% endmacro %}

{% macro <deployment>_past3m_lower_bound() %}
date_trunc('month', {{ get_current_date() }} - interval '3 months')::date
{% endmacro %}

{% macro <deployment>_ref_suffix(window) %}
{%- if window == 'past3m' -%}_past3m{%- endif -%}
{% endmacro %}
```

**Switching upstream refs.** When a paired intermediate depends on another
paired intermediate (e.g. `with_measurements` reads `patients`), the body
macro composes the upstream ref using `<deployment>_ref_suffix(window)`:

```jinja
from {{ ref('int__<name>_patients' ~ suffix) }} cp
```

This keeps the all-time chain self-consistent and the past3m chain
self-consistent — `int__X_past3m` only references other `_past3m`
intermediates, all-time only references all-time.

**When a pair diverges semantically.** If the main and past3m variants
genuinely have different upstream layers (e.g. main rewired to consume
`der__`, past3m still on `int__`), they can't share a macro. Document the
divergence in the affected spec and either rewire past3m to match, or accept
the gap as a stable divergence rather than dragging both back into one
template. Reviewer signal: if more than one or two pairs diverge, the
production-side perf strategy may need rethinking.

Reference implementation: `tamanu-dbt-msf-syria/macros/ncd_reporting/` (10
collapsed pairs spanning cohort selection, indicator aggregation, and
measurement joins). Spec:
`tamanu-dbt-msf-syria/specs/dbt-model/ncd-indicators-migration.md`.

## `logs.changes` window functions

When using window functions against `logs.changes`, always order by:

```sql
order by c.logged_at, c.record_updated_at, c.id
```

- `logged_at` — server-side transaction timestamp; authoritative and immune to device clock skew
- `record_updated_at` — tiebreaker for rows sharing the same `logged_at` (e.g. batch sync in one transaction); reflects device-side change time
- `id` — final tiebreaker for deterministic results when both timestamps are identical

Do not order by `logged_at, c.id` alone — `id` is a random UUID and does not preserve insertion order.

## Data table meta

Mart models exposed as data tables require:

```yaml
meta:
  create_data_table: true
  data_table_permission_groups:
    - Group Name
```

Columns use `data_table_filter: yearmonth|array|date` and `data_table_metric: sum`.

## Translation prefixes

Translation string IDs in `report_translations_*.csv` follow a concept-prefix convention. The `report.reporting.` namespace is added automatically by `translate_label()` — only the concept portion appears in calls and CSV keys.

| Source of the label | Prefix | Example key |
|---------------------|--------|-------------|
| Field bound to a specific Tamanu survey | `survey<SurveyID>` | `surveyPatientVitalsHeight`, `surveyHIVVisitARTRegimen` |
| Generic concept not tied to one survey | bare concept | `vitalSign`, `encounterId`, `patientName` |

`<SurveyID>` matches the Tamanu survey ID (camelCase, as it appears in `surveys.id`). The trailing portion is the field name in camelCase.

Keep rows in `report_translations_*.csv` sorted alphabetically by `stringId` (header row first). Append-only ordering produces noisy diffs and hides duplicates; the generation script tolerates any order, so the on-disk file is the only thing that needs to stay sorted.
