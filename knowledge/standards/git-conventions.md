# Git Conventions

## Branch naming

```
<type>/<short-description>
```

Types: `feature`, `fix`, `chore`, `refactor`, `docs`

Examples: `feature/patient-report`, `fix/translation-bug`, `chore/update-dependencies`

## Commit messages

Format: imperative mood, conventional commit style

```
<type>(<scope>): <short description>
```

- Start with a verb: "Add", "Fix", "Remove", "Update", "Refactor"
- Keep the subject line under 72 characters
- No full stop at the end of the subject line
- Use the body for context if the change is non-obvious

Examples:
```
feat(reports): add patient encounter summary report
fix(translations): correct missing label for encounter date
chore: update dbt-utils to 1.3.3
```

## Pull requests

- Title: conventional commit format (Claude Code will update if vague)
- Description: what changed, why, and what was tested
- Include testing commands or steps relevant to the change
- Request review before merging — do not self-merge without approval
- Keep PRs focused; avoid bundling unrelated changes

## Merge strategy

- Squash merge preferred for feature branches (clean history)
- Merge commit for long-running branches where commit history is meaningful
- Never force-push to `main`
- Rebase onto `main` before merging if the branch is behind

## Protected branches

- `main` is protected in all repos
- Required checks must pass before merging
- At least one human reviewer approval required
