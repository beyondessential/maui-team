# Dagster Pipeline Spec: `<pipeline_name>`

## Identity

| Field | Value |
|---|---|
| **Name** | `<asset_or_job_name>` |
| **Type** | Dagster `[asset \| job \| sensor \| schedule]` |
| **Status** | `draft` |
| **Owner** | `@<github_handle>` |
| **Linear issue** | [MAUI-XXX](url) |
| **Repo** | `data-lake` (or other) |
| **Trigger** | `[schedule \| sensor \| manual \| on-demand]` |
| **Schedule** | `0 2 * * *` (cron) or N/A |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

## Purpose

Why this pipeline exists. What it produces. Who depends on the output.

## Inputs

- **Upstream Dagster assets:** _list_
- **External sources:** _databases, APIs, files — note connection method_
- **Required configuration:** _env vars, secrets, run config; note where they're set_

## Outputs

- **Materialised assets:** _table names, schemas, target system_
- **Side effects:** _replication, file uploads, alerts_
- **Downstream consumers:** _other Dagster assets, dbt projects, Tupaia_

## Processing logic

Numbered steps. Each is a `BL` clause.

- **BL-001:** Extract from `<source>` filtered to `<criteria>`.
- **BL-002:** Transform — `<steps>`.
- **BL-003:** Load to `<target>` using `<strategy>` (full refresh / append / upsert).
- **BL-004:** On failure: `<retry / alert / quarantine behaviour>`.

## SLAs

| SLA | Target |
|---|---|
| Freshness | Output materialised within `<X>` hours of source change |
| Runtime budget | Pipeline completes within `<Y>` minutes |
| Success rate | ≥ `<Z>`% over rolling 30 days |

## Error handling

| Failure mode | Behaviour | Alerting |
|---|---|---|
| Source unavailable | Retry 3x with exponential backoff, fail run after | Slack `#data-alerts` |
| Schema drift | Fail fast | Slack `#data-alerts` |
| Partial data | _<decision: proceed / fail / quarantine>_ | _<channel>_ |

## Acceptance criteria

| ID | Criterion | Implements |
|---|---|---|
| AC-001 | Pipeline runs to completion on representative test data | BL-001..003 |
| AC-002 | Pipeline raises a known exception on missing source | BL-004 |
| AC-003 | Output asset row count is within expected range | data integrity |

## Dependencies

- **Upstream assets:** _list with repo + asset key_
- **Downstream assets / dbt projects:** _list_
- **External systems:** _e.g. Tamanu DB, S3 bucket, Tupaia replication target_

## Open questions

| ID | Question | Owner | Due |
|---|---|---|---|
| OQ-001 | | @<owner> | YYYY-MM-DD |

## Divergence from current code

_Mode A (retrospective) only._

| ID | Divergence | Resolution |
|---|---|---|
| DV-001 | | |

## Change log

| Date | Author | Change |
|---|---|---|
| YYYY-MM-DD | @<owner> | Initial draft |
