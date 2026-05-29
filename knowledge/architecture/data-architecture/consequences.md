# Consequences

Trade-offs the architecture accepts. Read together with [`decisions.md`](decisions.md).

## What gets easier

- One indicator definition, two consumers — Tamanu and Tupaia stop drifting
- A third consumer comes for free — AI-assisted ad-hoc reporting can be built on the same canonical layer, with `metric_definitions.csv` as the agent's structured catalogue and `can__` / `lkp__` / `ref__` as its query targets
- The data assistant can ground decisions in canonical models with known shape — `metric_definitions.csv` is a structured catalogue an agent can query directly
- Onboarding a new deployment becomes "fork the canonical pattern" rather than "redesign the stack"
- Research / federation cases become reachable with incremental work, not a rewrite
- One copy of every modelled output (D9) — lineage simplifies, sync failures go away, storage drops
- Analytics query load is isolated from production — Tupaia and ad-hoc analyses hit replicas

## Architectural costs — real trade-offs we accept

- **Migration overhead.** Two competing patterns coexist (`fct__` / `dim__` vs `can__` / `metric__`) until consumers migrate. Old models stay until replaced; new work goes to `can__` / `metric__`.
- **Tamanu reports are bound to the Tamanu release cycle.** A change to a Tamanu report (or any model in its dependency chain) ships via a Tamanu version release, not a dbt re-run. Analytics-side models iterate independently.
- **Source DB query load increases** with direct query (D9). Materialisation and indexing become first-class concerns for analytics-only `metric__` and `ds__` models.
- **Data Tables in Tupaia become a coordination surface.** Schema changes to a `metric__` model must be paired with Data Table review (D9 schema-changes-are-paired rule).
- **Replica freshness is bounded** by the replica update cadence. Stakeholders asking for "live" numbers need to be redirected to Tamanu reports or accept the staleness window.
- **Cross-source queries need a federation strategy.** Tamanu × `data-warehouse` queries don't have a clean home today (see OQ-003).

## Operational discipline — costs of any shared-definition architecture

- `metric_definitions.csv` becomes a coordination point — PRs reviewed for definition correctness, not just code correctness
- Distinguishing implementation overrides (silent) from definition variants (`variant_id`-flagged) requires reviewer discipline
- Indicator migration is invisible work — the dashboard renders the same number, but the path to it changes

## What we are deliberately not doing

- Full OMOP CDM compliance
- FHIR ingestion or export from the data layer
- Federated cross-deployment analytics (until a concrete case arises)
- Replacing Tupaia's viz-builder indicator service for user-defined indicators — only canonical health indicators move upstream
