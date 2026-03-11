# Tamanu dbt Conventions

Conventions for dbt projects that model data from Tamanu (electronic health records).

## `data_staging` package

External package at `dbt_packages/data_staging/` — not editable in consuming repos. Changes require a new package release in `beyondessential/data-staging`.

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

## Data table meta

Mart models exposed as data tables require:

```yaml
meta:
  create_data_table: true
  data_table_permission_groups:
    - Group Name
```

Columns use `data_table_filter: yearmonth|array|date` and `data_table_metric: sum`.
