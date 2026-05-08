# Data Extract Spec: `<extract_name>`

## Identity

| Field | Value |
|---|---|
| **Name** | `<extract_name>` |
| **Type** | Data extract |
| **Status** | `draft` |
| **Owner** | `@<github_handle>` |
| **Linear issue** | [BES-XXX](url) |
| **Requester** | `<stakeholder name + role>` |
| **Delivery cadence** | `[one-off \| weekly \| monthly \| on-request]` |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

## Purpose

Why this extract is needed. What decisions or downstream uses it supports. Why a regular dataset/dashboard wouldn't meet the need.

## Data scope

- **Population:** _which patients / encounters / events?_
- **Date range:** _from → to (or rolling window)_
- **Filters:** _active programme, country, facility, age band, etc._
- **Exclusions:** _test patients, soft-deleted, withdrawn consent, etc._

## Output schema

| Column | Source | Type | Description | Notes |
|---|---|---|---|---|
| `patient_id` | `bases.patients.id` | uuid | Stable patient identifier | _de-identified? hashed?_ |
| `encounter_date` | `bases.encounters.start_date` | date | | |
| ... | | | | |

## Business logic

- **BL-001:** Population definition (which patients qualify).
- **BL-002:** Inclusion criteria (events, encounters, observations).
- **BL-003:** Exclusions (test patients, withdrawn consent, soft-deleted).
- **BL-004:** Derivations / calculated fields.
- **BL-005:** Sort order, dedup strategy, tie-breaking rules.

## Sensitivity & access

- **PII fields:** _list and mark each_
- **Masking rules:** _which fields are hashed / redacted / dropped before delivery_
- **Approved recipients:** _who is authorised to receive this extract_
- **Storage:** _where the extract lives once delivered, retention period, deletion process_

## Delivery

| Aspect | Value |
|---|---|
| **Format** | `[CSV \| Excel \| Parquet \| Postgres dump]` |
| **Destination** | `[secure file share \| S3 \| email \| SFTP]` |
| **Encryption** | `[yes/no, method — e.g. age, GPG, password-protected ZIP]` |
| **Schedule** | _when delivered_ |
| **Naming convention** | `<prefix>_<YYYYMMDD>.<ext>` |

## Acceptance criteria

| ID | Criterion | Implements |
|---|---|---|
| AC-001 | Row count within ±5% of expected population size | BL-001..003 |
| AC-002 | No PII columns present in unencrypted output | sensitivity rules |
| AC-003 | Output passes the ingest schema validation of the receiving system | output schema |

## Open questions

| ID | Question | Owner | Due |
|---|---|---|---|
| OQ-001 | | @<owner> | YYYY-MM-DD |

## Divergence from current implementation

_Mode A (retrospective) only._

| ID | Divergence | Resolution |
|---|---|---|
| DV-001 | | |

## Change log

| Date | Author | Change |
|---|---|---|
| YYYY-MM-DD | @<owner> | Initial draft |
