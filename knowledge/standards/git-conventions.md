# Git Conventions

## Branch naming

```
<type>/<short-description>
```

Types: `feature`, `fix`, `hotfix`, `chore`, `refactor`, `docs`

- `hotfix` — urgent fix for a production deployment, typically targeting a version branch

Examples: `feature/patient-report`, `fix/translation-bug`, `hotfix/missing-translation`, `chore/update-dependencies`

## Version branches

Maui manages multiple deployments running different versions. Long-running version branches are named by `<major>.<minor>`:

```
main      ← latest (e.g. 2.50.x)
2.49      ← maintained for deployments on 2.49
2.48      ← maintained for deployments on 2.48
```

- Cut short-lived work branches from the relevant version branch, not from `main`
- Use `fix/` for normal fixes; `hotfix/` when the fix is urgent and targets a specific deployed version
- Backport fixes to older version branches via cherry-pick or a separate PR against the version branch

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
- Merge commit for version branches where commit history is meaningful
- Never force-push to `main` or version branches
- Rebase onto the target branch before merging if the branch is behind

## Protected branches

- `main` and all version branches (e.g. `2.49`, `2.48`) are protected
- Required checks must pass before merging
- At least one human reviewer approval required
