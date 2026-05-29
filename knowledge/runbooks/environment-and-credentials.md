# Runbook: Environment and credentials

How to obtain every credential, secret, and connection string needed to work on Maui
team repositories. If you've just been onboarded, also read
`onboarding-checklist.md`.

## Quick reference — what do I need?

| Working on… | You need |
|---|---|
| Any dbt project (`tamanu-source-dbt`, `tamanu-dbt-*`, `data-staging`) | `.env` with PostgreSQL credentials; access to a Tamanu replica |
| Tamanu deployment-specific projects | Above, plus the deployment's `META_*` secrets if running publish-artifacts locally |
| `data-lake` (being renamed to `bes-data-pipelines`) | AWS access (OIDC role or temporary creds), database credentials for non-Tamanu sources, Dagster Cloud / Dagster+ token if applicable |
| `fsm-data-migration` | Source FSM EHR credentials + target Tamanu credentials |
| `datatools` CLI development | Project depends on the command; ask team lead |
| Authoring specs / using AI tooling | `ANTHROPIC_API_KEY` for local Claude Code use |

## Where to request credentials

Single source of truth: **ask the data lead in the Maui team channel.** There is no
self-service portal. The data lead routes the request to whoever owns the resource
(DevOps for replica access, Ops for deployment-specific credentials, IT for OIDC role
trust).

If the data lead is unavailable, post in the team channel and tag a senior engineer.
Never request credentials in a public channel or by DM to an external party.

## Local development — `.env`

dbt projects expect a `.env` at the repo root. The shape is:

```bash
# PostgreSQL connection
DBT_HOST=<replica hostname>
DBT_PORT=5432
DBT_DBNAME=<database name>
DBT_USER=<your username>
DBT_PASSWORD=<your password>

# dbt target
DBT_TARGET=analytics_dev
```

The repo's `config/profiles.yml` reads these via `{{ env_var('DBT_...') }}`. Never
commit a populated `.env`. The `.env.example` in each repo shows the variables; copy
it and fill in.

### How to get the values

- **`DBT_HOST` / `DBT_PORT` / `DBT_DBNAME`** — from the data lead. Each deployment
  has its own replica.
- **`DBT_USER` / `DBT_PASSWORD`** — your personal credentials. Request as part of
  onboarding. DevOps provisions; the data lead routes the request.
- **`DBT_TARGET`** — pick from the targets listed in `config/profiles.yml`.
  `analytics_dev` is the safe default for replica-based work; `reporting_*` targets
  compile the production bundle (see architecture D6) and should not be run locally
  without coordination.

## CI / GitHub Actions secrets

Workflows that need credentials read them from GitHub repository secrets. Add via
**Settings → Secrets and variables → Actions** on the repository.

| Secret | Used by | How to obtain |
|---|---|---|
| `ANTHROPIC_API_KEY` | `claude-code-review.yml` | BES team Anthropic console; ask team lead |
| `DBT_HOST` / `DBT_DBNAME` / `DBT_USER` / `DBT_PASSWORD` / `DBT_PORT` | `dbt-tests.yml` | DevOps via the data lead. Use a CI-specific account, not a personal one |
| `META_CERT` | `publish-artifacts.yml` | Ops; one per deployment |
| `META_KEY` | `publish-artifacts.yml` | Ops; private key paired with `META_CERT` |
| `META_URL` *(repository variable, not secret)* | `publish-artifacts.yml` | Ops; one per environment (staging/prod) |

AWS credentials in `publish-artifacts.yml` are obtained via OIDC — no static secret
needed, but the IAM role
`arn:aws:iam::491618206332:role/gha-s3-tamanu-translations` must trust the calling
repository. Request the trust update from IT/DevOps when setting up a new
deployment repo.

## Rotation

- **Personal database credentials** — rotate when leaving the team or when
  compromised. Request rotation from DevOps via the data lead.
- **CI database credentials (`DBT_*`)** — rotate every 90 days. The data lead tracks
  the schedule.
- **`META_CERT` / `META_KEY`** — Ops controls the rotation calendar (per
  deployment). Coordinate before the certificate expires; the meta-server logs
  expiry warnings.
- **`ANTHROPIC_API_KEY`** — rotate annually or on team-lead change. The
  team-channel-owner rotates the team key; individual developer keys are
  personal.

If a credential is suspected to be exposed (committed by accident, posted in a
public channel, included in a screenshot), notify the data lead immediately and
follow up with a written summary. Do not attempt to "fix" by force-pushing — the
credential is already in git history.

## Common failure modes

- **`dbt debug` fails with "connection refused"** — replica is down for maintenance,
  or your IP isn't whitelisted. Check the DevOps status board; if the issue
  persists, escalate via team lead.
- **`dbt run` against `reporting_*` errors with permission denied** — production
  targets require explicit access; request from data lead.
- **`publish-artifacts.yml` fails with "OIDC role assumption denied"** — the IAM
  role trust hasn't been updated for this repo. Request the update from IT/DevOps
  citing the failing workflow run.
- **`claude-code-review.yml` fails silently** — likely missing `ANTHROPIC_API_KEY`.
  Check Settings → Secrets; re-add if missing.

## See also

- [`onboarding-checklist.md`](onboarding-checklist.md) — first-week setup steps
- [`tamanu-dbt-setup.md`](tamanu-dbt-setup.md) — per-project setup for dbt repos
- [`../../.github/workflows/README.md`](../../.github/workflows/README.md) — full
  workflow reference
