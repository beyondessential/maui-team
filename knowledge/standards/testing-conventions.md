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
  - name: base_patients
    columns:
      - name: patient_id
        tests:
          - not_null
          - unique
      - name: date_of_birth
        tests:
          - not_null
```

Apply to all primary keys at minimum.

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
| Null checks, uniqueness, accepted values, relationships | Generic test |
| Multi-column constraints, business logic, complex filters | Singular test |
| Cross-model referential integrity | Relationship generic test |

### Pre-commit

```bash
dbt test --profiles-dir config
```

Run against affected models before committing model changes.
