# Reusable Workflows

See the [root README](../../README.md) for full new-repo setup instructions.

## claude-code-review.yml

Runs Claude Code review on pull requests. Uses a repo-local `REVIEW.md` if present, otherwise falls back to `.maui/REVIEW.md`.

### Secrets required

`ANTHROPIC_API_KEY` — add as a repository secret in Settings → Secrets and variables → Actions.

### Caller workflow

Create `.github/workflows/claude-code-review.yml` in the consuming repo:

```yaml
name: Claude Code Review

on:
  pull_request:
    types: [opened, reopened, synchronize]
  issue_comment:
    types: [created]

jobs:
  claude-review:
    if: >-
      github.event_name == 'pull_request' ||
        (github.event_name == 'issue_comment' &&
        github.event.issue.pull_request != null &&
        contains(github.event.comment.body, '/review') &&
        github.event.comment.author_association != 'NONE' &&
        github.event.comment.author_association != 'FIRST_TIME_CONTRIBUTOR')
    uses: beyondessential/maui-team/.github/workflows/claude-code-review.yml@main
    secrets: inherit
```

### Re-triggering a review

Post a comment on the PR containing `/review`. Only team members (not first-time contributors) can trigger this.

### Making review a required check

In the repository's branch protection settings (Settings → Branches → Branch protection rules):
1. Enable **Require status checks to pass before merging**
2. Add `claude-review` as a required status check
3. Separately enable **Require a pull request before merging** with at least 1 required approver for human review

## update-submodule.yml

Keeps the `.maui` submodule up to date by running on every PR. If `.maui` is behind `main` in `maui-team`, the workflow updates it and pushes the commit directly onto the PR branch — no separate PR needed.

### Caller workflow

Create `.github/workflows/update-maui.yml` in the consuming repo:

```yaml
name: Update .maui Submodule

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  update-submodule:
    uses: beyondessential/maui-team/.github/workflows/update-submodule.yml@main
    secrets: inherit
```

### Behaviour

- If `.maui` is already at the latest commit, the workflow exits with no changes.
- If `.maui` is behind, it commits the update and pushes it to the PR branch.
- Does not run on PRs from forks (the `GITHUB_TOKEN` cannot push to a fork's branch).
