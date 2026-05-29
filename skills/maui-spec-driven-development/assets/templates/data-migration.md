# Data Migration Spec: `<migration_name>`

## Identity

| Field | Value |
|---|---|
| **Name** | `<migration_name>` (e.g. `fsm-to-tamanu-patients`) |
| **Type** | Data migration |
| **Status** | `draft` |
| **Owner** | `@<github_handle>` |
| **Linear issue** | [BES-XXX](url) |
| **Source system** | `<name + version>` |
| **Target system** | Tamanu `<version>` |
| **Country / deployment** | _e.g. fj, ki, fsm_ |
| **Cutover date** | YYYY-MM-DD |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

## Purpose

What is being migrated, why, and what drives the deadline.

## Scope

- **In scope:** _entities / tables to migrate_
- **Out of scope:** _entities NOT being migrated, with reason_
- **Volume estimate:** _record counts per entity_

## Source schema

Brief summary of source tables, types, key relationships, and known data quality issues. Link to detailed source schema docs rather than reproducing them in full.

## Target schema

Tamanu tables touched, model dependencies. Link to Tamanu docs rather than reproducing.

## Mapping rules

For each target entity, document the mapping. Each rule is a `BL` clause.

### Patients (target table: `tamanu.patients`)

- **BL-001:** `tamanu.patients.first_name` ← `fsm.person.given_name`, trimmed and title-cased.
- **BL-002:** `tamanu.patients.date_of_birth` ← `fsm.person.birth_date`. Non-null required; null values quarantined.
- **BL-003:** ID strategy — _new uuid, deterministic from source ID, or preserve source ID?_

### Encounters (target table: `tamanu.encounters`)

- **BL-010:** _<rule>_
- **BL-011:** _<rule>_

_Add per-entity sections. Number BL ranges per entity (001–009 for patients, 010–019 for encounters, etc.) so IDs stay readable as the spec grows._

## Data quality checks

### Pre-migration

- **DQ-001:** Source row counts captured per table.
- **DQ-002:** Source column null-rate snapshot.

### Mid-migration

- **DQ-010:** Quarantine row counts per entity.
- **DQ-011:** Reject log captured with reason per row.

### Post-migration

- **DQ-020:** Target row count = source row count − quarantined.
- **DQ-021:** Reconciliation reports per key entity (counts by date, by facility, by programme).
- **DQ-022:** Spot-check N records per entity matches source.

## Cutover plan

| Time | Action |
|---|---|
| T-N days | Dry run on staging |
| T-1 day | Freeze source system, take final snapshot |
| T-0 | Migration window |
| T+1 | Validation, sign-off |

## Rollback plan

- **Trigger conditions:** _what failures cause us to roll back?_
- **Restore procedure:** _step-by-step_
- **Decision authority:** _who calls the rollback?_

## Acceptance criteria

| ID | Criterion | Implements |
|---|---|---|
| AC-001 | All in-scope entities migrated; counts reconciled | BL-* + DQ-020 |
| AC-002 | Spot-check of N records per entity matches source | DQ-022 |
| AC-003 | Tamanu app smoke tests pass post-cutover | end-to-end |
| AC-004 | Quarantine count is below agreed threshold | DQ-010 |

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
