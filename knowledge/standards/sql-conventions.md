# SQL Conventions

Applies to all SQL across Maui repositories. For dbt-specific rules (model layers, testing, documentation), see `dbt-conventions.md`.

## Linting

```bash
sqlfluff fix <file_or_directory>
```

Run before committing. Keyword casing and formatting are enforced by SQLFluff.

## Keywords

All SQL keywords **lowercase**: `select`, `from`, `where`, `join`, `left join`, `group by`, `order by`, etc.

## Identifiers

Lowercase `snake_case`. Descriptive — avoid abbreviations unless universally understood.

## Aliasing

- Table aliases: implicit (no `as` for table aliases)
- Column aliases: explicit (`as` required)

```sql
select
    p.patient_id,
    date_part('year', age(p.date_of_birth)) as age_years
from patients p
```

## Formatting

- One clause per line; indent column lists and conditions 4 spaces
- Commas at the start of lines

```sql
select
    patient_id
    , encounter_id
    , encounter_date
from encounters
where is_deleted = false
```

## Joins

- `join` is treated as `inner join` — both are acceptable
- Avoid implicit cross joins (comma-separated tables in `from`)
- Handle fan-out explicitly when joining one-to-many

## NULL handling

- `is null` / `is not null` — never `= null`
- Be explicit about null behaviour in aggregations and comparisons

## Ordering

- Use `order by` only where the output order is meaningful to the consumer
- Be explicit about `asc` / `desc`
