# Python Conventions

Formatting, import ordering, and common errors are enforced by ruff — see `ruff.toml` at the repo root. Consuming repos extend it via:

```toml
# ruff.toml
extend = ".maui/ruff.toml"
target-version = "py312"
```

The rules below cover what ruff cannot enforce.

## Naming

| Element | Convention | Example |
|---------|-----------|---------|
| Variables / functions | `snake_case` | `get_patient_records` |
| Classes | `PascalCase` | `PatientReport` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Private members | `_leading_underscore` | `_parse_response` |
| Type aliases | `PascalCase` | `PatientId = str` |

## Type annotations

- Annotate all function signatures (parameters and return types)
- Use `from __future__ import annotations` for forward references
- Prefer `X | None` over `Optional[X]` (Python 3.10+)

## Docstrings

Use Google-style docstrings. Only add them where they aid understanding — omit on trivial functions.

## Functions and classes

- Keep functions focused on a single responsibility
- Prefer pure functions where possible
- Avoid mutable default arguments
- Document non-obvious logic with inline comments, not docstrings on trivial functions

## Error handling

- Use specific exception types, not bare `except:`
- Log errors with context before re-raising or handling
- Don't suppress exceptions silently
- **Fail loudly when a default would violate a spec rule.** If a caller omits a value and the resulting default would silently contradict a `BL-XXX` / `DQ-XXX` clause (or any documented contract), return a clear error or raise — don't fall back to the unsafe default. Convenience fallbacks that drift from the spec are foot-guns: the next operator inherits behaviour that "works" until it produces wrong data. Prefer a one-line error pointing at the missing config over a silent write of the wrong value.

## Project-specific conventions

Add repo-specific rules in the repo's `AGENT.md`.
