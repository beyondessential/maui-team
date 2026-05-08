# Tupaia Dashboard Spec: `<dashboard_name>`

## Identity

| Field | Value |
|---|---|
| **Name** | `<dashboard_name>` |
| **Type** | Tupaia dashboard |
| **Status** | `draft` |
| **Owner** | `@<github_handle>` |
| **Linear issue** | [BES-XXX](url) |
| **Country / deployment** | |
| **Programme** | _e.g. NCD, RMNCH, IDSR_ |
| **Stakeholders** | _e.g. MoH NCD team, country focal point_ |
| **Created** | YYYY-MM-DD |
| **Last updated** | YYYY-MM-DD |

## Purpose

What questions this dashboard answers. What decisions it supports. Why a static report wouldn't suffice.

## Audience

- **Primary users:** _who uses it day-to-day_
- **Frequency:** _how often they check it_
- **Data literacy:** _technical / non-technical_
- **Access mode:** _public / authenticated / role-restricted_

## Data requirements

- **Indicators:** _list of metrics displayed_
- **Geographic granularity:** _country, district, facility, etc._
- **Temporal granularity:** _daily, monthly, quarterly, annual_
- **Disaggregation:** _sex, age band, programme, etc._
- **User-controlled filters:** _date range, facility, etc._

## Visualisations (panels)

For each panel:

### Panel: `<name>`

- **Type:** `[bar \| line \| stacked bar \| map overlay \| table \| indicator card \| pie]`
- **Metric:** `<name>`
- **Source model:** `{{ ref('<dbt_model>') }}` in `<repo>`
- **Calculation:**
  - **BL-001:** Numerator = _<definition>_
  - **BL-002:** Denominator = _<definition>_
  - **BL-003:** Aggregation level = _<level>_
- **Empty / null behaviour:** _how the panel renders with no data_

### Panel: `<name>`

_(repeat per panel)_

## Data lineage

```
tamanu_source_dbt: bases.<table>  ──►  data_staging: fct__<name>  ──►  data_lake: ds__<name> (Tupaia replica)  ──►  Tupaia dashboard
```

Link each panel back to the dbt model that powers it. If multiple panels share a model, note that — it's a dependency to track.

## Acceptance criteria

| ID | Criterion | Implements |
|---|---|---|
| AC-001 | Each panel renders without error on representative data | all |
| AC-002 | Indicator values reconcile with source-of-truth Tamanu report | BL-* |
| AC-003 | Filters update all linked panels consistently | UX |
| AC-004 | Dashboard loads within `<X>` seconds for `<largest deployment>` | performance |

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
