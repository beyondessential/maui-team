# dbt Model Metadata

Every dbt model's YAML needs a `meta:` block. When data spans multiple levels,
use the highest applicable classification.

```yaml
meta:
  owner: "bes-maui"
  domain: "clinical"
  pii: true
  classification: "restricted"
```

The block gives AI agents and reviewers the context to handle the model
correctly (ownership, PII, sensitivity). Readiness is encoded by the layer
prefix ([`dbt-conventions.md`](dbt-conventions.md) § Model layers); no separate
`tier` field.

## Owner

| Owner | When |
|---|---|
| `bes-maui` | Maui-team-built models |
| `bes-tamanu` | Tamanu source models |
| `flutracking` | FluTracking surveillance |
| `niwa` | NIWA weather/climate |

Add a new owner when ingesting a new external source.

## Domain

What the data is *about*, not who owns it or who can access it.

| Domain | Examples |
|---|---|
| `clinical` | Encounters, diagnoses, medications, registry, births, deaths |
| `admin` | Billing, scheduling, users, roles |
| `supply_chain` | Stock, orders, dispensing, cold chain (mSupply) |
| `surveillance` | Population-level disease monitoring (FluTracking, dengue) |
| `environmental_health` | Food retailers, household surveys |
| `asset_management` | Equipment, vehicles, infrastructure |
| `external` | Non-Maui context data (NIWA weather) |

Source mapping:

| Source | Domain |
|---|---|
| Tamanu clinical tables | `clinical` |
| Tamanu admin tables | `admin` |
| mSupply | `supply_chain` |
| FluTracking, Dengue surveillance | `surveillance` |
| NIWA | `external` |
| Environmental health | `environmental_health` |
| Asset management | `asset_management` |

## Classification

Authoritative source: BES
[Data Classification Policy](https://beyond-essential.slab.com/posts/p-9-data-classification-policy-4e4cypfy)
(Slab — BES sign-in required). The table below mirrors it; the policy wins if
they disagree.

| Level | Includes | Controls |
|---|---|---|
| `restricted` | PHI, PII, credentials, regulated/contractual data | Strict ACLs + encryption at rest + in transit; access logged; never copy outside approved infra |
| `confidential` | Internal operational/business data (financials, partnership terms) | Need-to-know; no external sharing without authorisation |
| `internal` | General internal information | All BES staff; not for public release |
| `public` | Marketing, published reports, open-data outputs | No controls required |

### `pii` flag

`pii: true` means the model has PII columns. PII models are almost always
`restricted` in practice, but `pii` is independent of classification level.
