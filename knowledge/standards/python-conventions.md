# Python Conventions

## Style

- Follow PEP 8; use `ruff` for linting and formatting
- Line length: 88 characters (ruff/black default)
- Use double quotes for strings

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

## Imports

- Group: stdlib → third-party → local, separated by blank lines
- No wildcard imports (`from module import *`)
- Prefer explicit imports over importing a module and accessing attributes

## Functions and classes

- Keep functions focused on a single responsibility
- Prefer pure functions where possible
- Avoid mutable default arguments
- Document non-obvious logic with inline comments, not docstrings on trivial functions

## Error handling

- Use specific exception types, not bare `except:`
- Log errors with context before re-raising or handling
- Don't suppress exceptions silently

## Project-specific conventions

Add repo-specific rules in the repo's `AGENT.md`.
