# Reusable Workflows

## claude-code-review.yml

Runs Claude Code review on pull requests. Uses a repo-local `REVIEW.md` if present, otherwise falls back to `.maui/REVIEW.md`.

### Caller requirements

The calling repo must:
1. Have this repo as a submodule at `.maui/` (for the fallback `REVIEW.md`)
2. Have `ANTHROPIC_API_KEY` set as a repository secret

### Usage

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
