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
