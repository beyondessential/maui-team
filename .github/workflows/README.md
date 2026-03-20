# Reusable Workflows

See the [root README](../../README.md) for full new-repo setup instructions.

## claude-code-review.yml

Runs on every PR and on `/review` comments. On pull requests it first updates the `.maui` submodule if it is behind `main`, commits the change to the PR branch, then runs the Claude Code review against the latest code.

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

## publish-artifacts.yml

Runs on release events. Publishes compiled dbt artifacts to S3 and registers them with the meta-server. Intended for `tamanu-source-dbt` and `tamanu-dbt-*` repos.

The deployment name is derived from the calling repository name:
- `tamanu-source-dbt` → `standard` (artifacts at `M.m.x/`)
- `tamanu-dbt-<name>` → `<name>` (artifacts at `M.m.x/<name>/`)

The `list-reports` job only runs for the `standard` deployment on its latest release.

### Secrets and variables required

- `META_CERT` — client certificate for authenticating with the meta-server
- `META_KEY` — private key for the client certificate
- `META_URL` — base URL of the meta-server (repository variable)

AWS credentials are obtained via OIDC — no static AWS secrets required. The IAM role `arn:aws:iam::491618206332:role/gha-s3-tamanu-translations` must trust the calling repository.

### Caller workflow

Create `.github/workflows/publish-artifacts.yml` in the consuming repo:

```yaml
name: Publish Artifacts

on:
  release:
    types: [published]

jobs:
  publish:
    uses: beyondessential/maui-team/.github/workflows/publish-artifacts.yml@main
    secrets: inherit
```
