# Code Review Reference

Maui team baseline for Claude Code reviews. Individual repos can override by placing their own `REVIEW.md` at their root (full replacement — copy and extend as needed).

---

## Review checklist

**Correctness**
- Logic errors, off-by-one errors, incorrect assumptions
- Edge cases not handled (nulls, empty inputs, out-of-range values)
- Data type mismatches or implicit conversions

**Security** — BLOCK and request immediate changes if any of the following are found:
- Hardcoded credentials, API keys, passwords, or tokens
- Committed `.env` or secrets files
- PII exposed in code, examples, or logs
- Unmasked secrets in log statements

**Data integrity**
- Transformations that could silently drop or duplicate records
- Joins without explicit handling of fan-out or null keys
- Filtering logic that may exclude valid records

**Code quality**
- Unclear naming (variables, functions, models)
- Duplicated logic that should be abstracted
- Missing documentation where it would aid understanding

**Tests**
- New logic without corresponding tests
- Tests that don't assert meaningful outcomes

**Dependencies and configuration**
- Newly introduced dependencies without justification
- Undocumented configuration or environment assumptions

---

## Severity guidance

| Level | When to use |
|-------|-------------|
| 🔴 **Blocker** | Security issues (see above), data correctness bugs, broken functionality |
| 🟡 **Suggestion** | Missing tests, unclear naming, undocumented assumptions |
| 🔵 **Nit** | Minor wording or style not covered by linters |

Default to **Suggestion** when unsure. Reserve **Blocker** for issues that risk data loss, security exposure, or broken behaviour.

---

## What NOT to flag

- Style issues already enforced by a linter (SQLFluff, ruff, etc.)
- Naming that differs from preference but is clear and consistent within the file
- Refactoring opportunities outside the PR scope
- Hypothetical edge cases with no realistic path to occurring

---

## PR title

If the title is vague or auto-generated, update it to conventional commit format:

```
<type>(<scope>): <short description>
```

Types: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`

```bash
gh pr edit <number> --title 'improved title here'
```

---

## Summary comment format

Keep the sticky summary brief:
- Overall verdict: ✅ approved or ⚠️ issues found
- Count of blockers / suggestions / nits
- Regression testing checklist (commands only, no explanation)

All specific feedback goes in inline comments — do not repeat details in the summary.

---

## Inline comments

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments \
  --method POST \
  --field body='your comment' \
  --field commit_id='<sha>' \
  --field path='relative/file/path' \
  --field line=<line_number> \
  --field side='RIGHT'
```
