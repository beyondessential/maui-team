# Reusable Workflows

## claude-code-review.yml

Runs Claude Code review on pull requests. Uses a repo-local `REVIEW.md` if present, otherwise falls back to `.maui/REVIEW.md`.

### Setup

**1. Add the submodule**

```bash
git submodule add https://github.com/<org>/maui-team .maui
git commit -m "chore: add maui-team submodule"
```

**2. Add `ANTHROPIC_API_KEY` as a repository secret**

In the repo: Settings → Secrets and variables → Actions → New repository secret.

**3. Create the caller workflow**

Create `.github/workflows/code-review.yml` in the consuming repo:

```yaml
name: Code Review

on:
  pull_request:
    types: [opened, reopened]
  issue_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write
  issues: read
  id-token: write
  actions: read

jobs:
  review:
    if: >-
      github.event_name == 'pull_request' ||
        (github.event_name == 'issue_comment' &&
        github.event.issue.pull_request != null &&
        contains(github.event.comment.body, '/review') &&
        github.event.comment.author_association != 'NONE' &&
        github.event.comment.author_association != 'FIRST_TIME_CONTRIBUTOR')
    uses: <org>/maui-team/.github/workflows/claude-code-review.yml@main
    secrets: inherit
```

### Re-triggering a review

Post a comment on the PR containing `/review`. Only team members (not first-time contributors) can trigger this.

### Making review a required check

In the repository's branch protection settings (Settings → Branches → Branch protection rules):
1. Enable **Require status checks to pass before merging**
2. Add `claude-review` as a required status check
3. Separately enable **Require a pull request before merging** with at least 1 required approver for human review
