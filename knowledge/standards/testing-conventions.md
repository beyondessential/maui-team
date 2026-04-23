# Testing Conventions

## Python (pytest)

### File and function naming

- Test files: `test_<module>.py`
- Test functions: `test_<behaviour>` — describe the behaviour being tested, not the function name
- Test classes (optional): `Test<Subject>` — group related tests for a class or module

```python
# Good
def test_returns_empty_list_when_no_patients_found():
    ...

# Avoid
def test_get_patients():
    ...
```

### Structure

Use the Arrange–Act–Assert pattern:

```python
def test_filters_deleted_encounters():
    # Arrange
    encounters = [{"id": 1, "deleted_at": None}, {"id": 2, "deleted_at": "2024-01-01"}]

    # Act
    result = filter_active(encounters)

    # Assert
    assert len(result) == 1
    assert result[0]["id"] == 1
```

### Fixtures

- Define reusable test data and dependencies as fixtures in `conftest.py`
- Keep fixtures focused — one fixture per concern
- Use `scope="session"` for expensive shared resources (database connections, large datasets)

### What to test

- Unit test: pure functions, data transformations, business logic
- Integration test: database queries, API calls, file I/O (use test databases or mocks)
- Do not unit test framework internals or third-party library behaviour

### Mocking

- Mock at the boundary (external services, I/O), not internal logic
- Prefer dependency injection over patching where possible
- Use `pytest-mock` (`mocker` fixture) rather than `unittest.mock` directly

### Coverage

- New business logic should have corresponding tests
- 100% coverage is not a goal — meaningful coverage is
- Test edge cases: empty inputs, nulls, boundary values

---

## dbt

### Generic tests (schema.yml)

Use built-in generic tests for standard data quality checks:

```yaml
models:
  - name: ds__patients
    columns:
      - name: patient_id
        tests:
          - not_null
          - unique
```

Apply to all primary keys in dataset models at minimum. Base models are exempt — tests
belong on source models, not on the thin projections over them.

### Singular tests (tests/*.sql)

Use for complex business logic that can't be expressed as a generic test:

```sql
-- tests/assert_no_duplicate_encounters_per_day.sql
select patient_id, encounter_date, count(*) as cnt
from {{ ref('dataset_encounters') }}
group by 1, 2
having count(*) > 1
```

A singular test passes if it returns zero rows.

### When to use each

| Scenario | Use |
|----------|-----|
| Null checks, uniqueness, accepted values, relationships | Generic test (yml) |
| Numeric range, conditional not-null, simple expression | `dbt_utils` generic test (yml) |
| Multi-column constraints, complex business logic | Singular test (SQL file) |
| Cross-model referential integrity | `relationships` generic test (yml) |
| Window functions, complex SQL logic, transformation correctness | Unit test (yml) |

Prefer yml-based tests over singular SQL files wherever possible — they are co-located with column documentation and easier to scan.

### `dbt_utils` generic tests

`dbt_utils` is available in all Maui dbt projects. Prefer these over singular SQL for single-column checks.

Test arguments must be nested under `arguments:`. Test config (`where`, `severity`) stays at the top level.

**Numeric range** — catch data entry errors:

```yaml
- name: age
  tests:
    - dbt_utils.accepted_range:
        arguments:
          min_value: 0
          max_value: 120
          inclusive: true
```

Nulls pass `accepted_range` by default.

**Date not in future**:

```yaml
- name: event_date
  tests:
    - dbt_utils.expression_is_true:
        arguments:
          expression: "<= current_date"
```

**Conditional not-null (hierarchy integrity)** — a child ID set implies the parent must also be set:

```yaml
- name: location_group_id
  tests:
    - dbt_utils.expression_is_true:
        arguments:
          expression: "is not null"
        where: "location_id is not null"
```

**Accepted values on derived status fields** — status fields computed via `CASE` expressions:

```yaml
- name: cohort_status
  tests:
    - accepted_values:
        values: ['Active', 'N/A']
```

### Singular test patterns

Use singular SQL tests only when the logic cannot be expressed as a yml generic test — typically multi-column constraints.

**Aggregation alignment** — when multiple fields are aggregated from the same source with the same `ORDER BY`, their separator counts must match:

```sql
-- data-tests/test_<model>_aggregation_alignment.sql
-- Fails if two aggregated columns have a different number of entries.
select patient_id
from {{ ref('ds__example') }}
where
    (length(field_a) - length(replace(field_a, '; ', '')))
    != (length(field_b) - length(replace(field_b, '; ', '')))
```

**Primary key tests** — all dataset models must have `not_null` and `unique` on their primary key. Base models are exempt.

```yaml
- name: patient_id
  tests:
    - not_null
    - unique
```

### Naming

Singular test files: `test_<model>_<what_is_being_checked>.sql`

Example: `test_prescription_analysis_prescription_alignment.sql`

### Unit tests

Use dbt unit tests to verify model SQL logic with controlled fixture data — particularly window functions, complex joins, and filtering conditions that are hard to assert via data tests alone.

```yaml
# data-tests/unit_tests/<model_name>.yml
version: 2

unit_tests:
  - name: test_<model>_<what_is_being_checked>
    model: <model_name>
    given:
      - input: source('schema', 'table')
        format: csv
        rows: |
          col_a,col_b
          val1,val2
    expect:
      format: csv
      rows: |
        output_col_a,output_col_b
        expected1,expected2
```

- Place unit test YAML files in `data-tests/unit_tests/<model_name>.yml`
- Keep fixture data minimal — only rows needed to exercise the specific behaviour
- Name tests: `test_<model>_<what_is_being_checked>`

### Pre-commit

```bash
dbt test --profiles-dir config
```

Run against affected models before committing model changes.
