# SQL Conventions

Applies to all SQL across Maui repositories. For dbt-specific rules (model layers, testing, documentation), see `dbt-conventions.md`.

Formatting, keyword casing, and aliasing are enforced by SQLFluff — see `.sqlfluff` at the repo root. The rules below cover what SQLFluff cannot enforce.

## Identifiers

Lowercase `snake_case`. Descriptive — avoid abbreviations unless universally understood.

## Joins

- `join` is treated as `inner join` — both are acceptable
- Avoid implicit cross joins (comma-separated tables in `from`)
- Handle fan-out explicitly when joining one-to-many

Note: `ambiguous.join` is excluded from the SQLFluff config, so cross join detection is not automated.

## NULL handling

- `is null` / `is not null` — never `= null`
- Be explicit about null behaviour in aggregations and comparisons

## Ordering

- Use `order by` only where the output order is meaningful to the consumer
- Be explicit about `asc` / `desc`
