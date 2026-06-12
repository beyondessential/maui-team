# Production promotion and consumption paths

How `tamanu-source-dbt` models reach Tamanu reports in production, Tupaia
dashboards, and (future) AI-assisted ad-hoc reporting. See
[`../data-architecture.md`](../data-architecture.md) for the architecture
overview and [`decisions.md`](decisions.md) for the underlying decisions.

## Tamanu reports and the production promotion path

Tamanu reports materialise as views in the **production** Tamanu DB, not the replica. The pipeline:

1. dbt runs against the **replica** DB, where the data team iterates on models and the full `tamanu-source-dbt` dependency chain materialises as views in the replica's `reporting` schema.
2. dbt's compiled output is captured as a versioned SQL bundle at `tamanu-source-dbt/compiled/v<tamanu-version>/reporting-schema-v<tamanu-version>-standard.sql` (plus a `-sensitive.sql` variant) - self-contained, creating everything needed to support Tamanu reports against a fresh production DB.
3. The compiled bundle is promoted to production as part of a Tamanu version release. Production then has `reporting.*` views that the Tamanu app's report queries hit directly.

**Standard vs. customised deployment pipeline:**

| Stage | Standard deployment | Customised deployment |
|---|---|---|
| **dbt source** | `tamanu-source-dbt` | `tamanu-source-dbt` (as version-pinned package) + `tamanu-dbt-<deployment>` (overrides) |
| **Compiled bundle** | `tamanu-source-dbt/compiled/v<version>/` | `tamanu-dbt-<deployment>/compiled/v<version>/` (if any report model is overridden; otherwise standard bundle) |
| **Production DB** | Standard bundle applied at release | Custom bundle applied at release |
| **Replica update** | Production → replica (DevOps-owned) | Production → replica (DevOps-owned) |
| **Dagster runs** | `tamanu-source-dbt` against replica | `tamanu-dbt-<deployment>` against replica |
| **Replica output** | Standard `reporting.*` + analytics layers | Overridden `reporting.*` + analytics layers |

**Promotion rule:** the compiled bundle includes the full transitive dependency chain of `models/reports/`. Any model - base, intermediate, `ref__`, `lkp__`, `can__`, `der__`, `metric__`, `ds__` - that a Tamanu report depends on ships to production. Models outside that closure stay replica-only.

**Environment-aware materialisation.** The same model definition can compile to an **incremental table** on the replica (for analytics performance) and a **view** in the production compiled bundle (for production safety). `tamanu-source-dbt` uses target name prefixes - `reporting_*` targets compile to the production bundle, `analytics_*` targets run on the replica. One model definition serves both via dbt config:

<!-- Predicate convention: `target.name.startswith('reporting_')`. Documented in `../../standards/dbt-conventions.md` § Environment-aware materialisation. Update both sides if the convention changes. -->

```sql
{{ config(
  materialized = ('view' if target.name.startswith('reporting_') else 'incremental'),
  unique_key = 'patient_id',
  incremental_strategy = 'merge',
) }}

select ...
{% if is_incremental() %}
  where updated_at > (select max(updated_at) from {{ this }})
{% endif %}
```

The SQL itself must satisfy the more restrictive environment - if a model compiles to a view in production, the SQL must be **production-safe** (valid against the production schema, no Python models, tractable as a runtime view). If the natural implementation can't be made production-safe (e.g. window functions aggregating all encounters per patient), keep the model out of any Tamanu report's chain. It can live as an analytics-only `metric__` consumed by Tupaia via Data Tables on the replica, where the query budget is yours.

**Two deployment types support this pipeline:**

| Deployment | When run | What it does | Owner |
|---|---|---|---|
| **Release deployment** | Per Tamanu version release | Generates the compiled SQL bundle (`compiled/v<version>/reporting-schema-v<version>-standard.sql`) by running `tamanu-source-dbt` against a representative dataset on the target Tamanu version. The bundle is an audit artefact, version-controlled in the repo. | Tamanu engineering (infrastructure) + data team (reporting schema) |
| **Clone deployment** | Per deployment, per upgrade | Brings up a clone of a deployment's production data on the target Tamanu version. The matching compiled bundle is installed from the repo; for customised deployments, the data team additionally runs the `tamanu-dbt-<deployment>` project. Validated end-to-end before production promotion. | Ops (clone infrastructure) + data team (override application) |

This separation handles Tamanu version skew in two non-conflicting places: per-version bundle generation produces the artefact; per-deployment validation confirms the artefact plus overrides work against actual data before it ships.

## Typical workload split

Tamanu reports in production and Tupaia dashboards have complementary roles:

| | Tamanu reports (production) | Tupaia dashboards (replica) |
|---|---|---|
| **Typical shape** | Line lists - patient-level rows, often filterable by user | Aggregated indicators - counts, rates, time series, broken down by facility / district / time |
| **Materialisation** | Views (per the promotion rule) | Incremental tables, or views over incremental tables |
| **Query complexity** | Generally simple - join cleaned `bases/` models, filter, project | Often heavy - multi-domain joins, window functions, period aggregations |
| **Freshness** | Live (reads production directly) | Bounded by replica update cadence |
| **Refs to `ref__` / `lkp__`** | Generally not needed - line lists project from `bases/` directly | `ref__` used for OMOP-shaped joins (care site, location, provider); `lkp__` used for analytic groupings (age groups), cross-system mappings (Tamanu↔Tupaia facility codes) |
| **Audience** | Clinicians and front-line operational users in the Tamanu app | Program managers, MoH stakeholders, executives reading dashboards |

The work that *wants* to be a view (line list extraction) is what ships to production; the work that *wants* to be incremental (heavy aggregation) lives on the replica.

## Replica freshness

The Tamanu replica DB is periodically updated from the production DB. It is not a streaming replica - there is an inherent staleness window. This is DevOps-owned infrastructure.

What this means for the data team:

- **Replica data is bounded-stale, not real-time.** Staleness varies per deployment depending on the update schedule. Sub-hourly freshness is out of scope.
- **dbt-built objects persist across replica updates.** Views and tables in the dbt schema survive each update cycle and are refreshed incrementally by Dagster after each update.
- **Views reflect new data automatically; materialised models are incremental.** dbt views read fresh `public.*` after each replica update. Materialised models use incremental refresh keyed on `updated_at` from the source. Tamanu's `updated_at` reliably bumps on every meaningful change, so late-arriving facts (backdated corrections, edits) are picked up correctly.
- **For Tupaia consumers,** assume a refresh window matching the replica update cadence. Stakeholders needing live data should be directed to Tamanu reports instead.

Replica update cadence is per-deployment DevOps-owned config - raise changes with DevOps as a separate ask.

---

## Version skew and per-deployment variation

Each Tamanu deployment runs a different Tamanu version, and **some** deployments need customisation (local reference data, programs, surveys, reports). The architecture handles both via two paths:

- **Standard (no customisation):** the standard compiled bundle from `tamanu-source-dbt/compiled/v<version>/` is applied to production at release. Dagster runs `tamanu-source-dbt` directly against the deployment's replica. Deployment-specific reference data flows in via the deployment's own `public.*` data through `bases/`.
- **Customisation:** a `tamanu-dbt-<deployment>` project is created. It references `tamanu-source-dbt` as a version-pinned dbt package and overrides only the specific models that need deployment-specific behaviour. Dagster runs this project instead; a custom compiled bundle is produced if any model in a Tamanu report's chain is overridden.

Creating a `tamanu-dbt-<deployment>` project is a deliberate decision - the customisation has to justify the overhead of a separate repo, version-pinning, and CI. Standard is the baseline; create a per-deployment project only when a real customisation need arises.

**When to override vs. when to upstream:**

| Case | Action |
|---|---|
| Tamanu facility / provider / location data | Flows through `bases/` → `ref__` automatically. No override needed unless the deployment has a schema difference in `public.*` |
| Standard `lkp__` seed (age groups, modality types, encounter classes) | Override in `tamanu-dbt-<deployment>` only if deployment has truly custom types. Flagged as divergence in review |
| Cross-system mapping or deployment-specific hierarchy (e.g. `lkp__facility_tupaia_mapping`, `lkp__health_district`) | Define in `tamanu-dbt-<deployment>` - inherently per-deployment |
| Different survey form, program registry ID, or other local data in a `can__` / `der__` model | Override in `tamanu-dbt-<deployment>` |
| Genuinely different definition (numerator, denominator, disaggregation) in a `metric__` model | Override AND set `variant_id` on the output to flag the semantic difference (see D5) |
| Custom report not covered by the standard bundle | Define in `tamanu-dbt-<deployment>`; produces a custom compiled bundle for that deployment's production |
| Improvement that would benefit all deployments | Upstream to `tamanu-source-dbt` |
| Long-lived local override that diverges only because the standard was never updated | Upstream the local logic, retire the override |

---

## Report config

Report config is the binding between `metric__` outputs and what end users see - chart type, disaggregation selectors, period controls, filter widgets, map overlay styles, layout, default aggregations, units, captions. The data team owns this layer on both Tamanu and Tupaia surfaces.

This is distinct from visual design systems (palettes, typography, layout chrome, mobile responsiveness) - those stay with platform owners: Tupaia engineering for Tupaia, Tamanu engineering for Tamanu. Report config sits on top of the design system, configuring it with metric-specific choices.

### Tamanu reports

Current state. Report config lives in `tamanu-source-dbt/models/reports/config/`, version-controlled alongside the SQL. Both the SQL and the config ship to production via the compiled bundle at each Tamanu release (see [Tamanu reports and the production promotion path](#tamanu-reports-and-the-production-promotion-path) above).

### Tupaia dashboard items and map overlays

Target state. A data-team-owned **standard visual template library** holds reusable templates for the two Tupaia visual primitives:

- **Dashboard items** - the individual visualisations that compose a dashboard: bar charts, time series, KPI cards, tables, comparison panels
- **Map overlays** - choropleth, point, and shaded polygon overlays on Tupaia's maps

Each template encodes the binding between a `metric__` output shape and presentation defaults: chart type, aggregation, period granularity, disaggregation behaviour, and - for map overlays - classification scheme, overlay style, and entity-grain expectations.

Templates are imported into Tupaia via the admin panel's existing import capability. Per-deployment authors in the admin panel assemble dashboards from standard dashboard item templates and configure map overlays from standard overlay templates, applying deployment-specific customisation on top (which entities, which time period defaults, which dashboard layout).

This mirrors the Tamanu pattern: standard config in a data-team repo, deployed via import, per-deployment customisation overlaid. It also gives report config the same review surface as data architecture - one PR can update a `metric__` model and the templates that consume it, instead of dbt changes in git and visual changes in the admin panel.

**Why this matters for map overlays specifically.** Map overlays bind metric values to map features via entity IDs. A standard map overlay template encodes the entity-grain expectation (facility / district / country), the classification scheme (quantile, equal interval, custom breaks), and how the overlay reacts to NULL roll-ups. Without standard templates, each new map overlay reinvents these choices in the admin panel.

**Migration from current state.** Today, all dashboard items and map overlays are configured directly in Tupaia's admin panel, DB-backed and not version-controlled. The direction of travel is settled - templates as the standard, version-controlled in a data-team-owned repo - but the path from here to there is not. What we know:

1. Repo location is the first decision (OQ-006) - blocks everything else
2. Template schemas (one for dashboard items, one for map overlays) need joint scoping with Tupaia engineering and likely a prototype (OQ-007)
3. Migration of existing config is staged, not big-bang - high-traffic items first, with deployment-specific custom visuals remaining in the admin panel longer-term (OQ-009)

The sequencing, cutover criteria, and what stays in the admin panel permanently are open. The Tupaia engineering team also likely needs to extend the admin panel's import schema to accept the template format - that's part of the OQ-007 scoping conversation.

### AI-assisted ad-hoc reporting

The same canonical layer that powers Tamanu reports and Tupaia visuals positions us to offer end users a third consumption surface: AI-assisted ad-hoc reporting. Program managers, MoH analysts, and country partners ask questions in natural language; an agent grounds itself in the data layer, generates analytic queries, and returns answers - with the option to save the result as a Data Table that surfaces in Tupaia like any other visual.

This is a future capability, not something the team is actively building today. What this document establishes is that the architecture **is positioned for it**, by virtue of the same decisions that serve Tamanu reports and Tupaia:

| Architectural choice | Why it enables AI-assisted reporting |
|---|---|
| `metric_definitions.csv` as a structured registry (D5) | Agent reads "what indicators exist, what they mean, how they're shaped" without parsing SQL |
| Wide-format `metric__` outputs with explicit disaggregation columns (D5) | Agent knows what dimensions can be sliced and the column names to use |
| Standard `unit` and `definition_source` columns (D5) | Agent formats output correctly and cites the standard the indicator follows |
| OMOP-lite `can__` shape (D1) | Well-documented public standard - LLMs understand it; agents generate analytic queries against `can__` more reliably than against bespoke schemas |
| `bases/`-only access (D10) | Agent-generated queries hit cleaned models, not raw `public.*` with soft-deletes and metadata noise |
| Data Tables convention (D9) | Agent-generated results can be persisted as a Data Table and surfaced in Tupaia, rather than dying in a chat window |

**What AI-assisted reporting is good for:** exploratory questions that don't warrant a permanent dashboard, one-off cuts of existing indicators, drill-downs into a specific district or facility, "what does this indicator look like for my province over the last 12 months", quick comparisons across deployments.

**What it isn't a replacement for:** curated dashboards that program staff rely on routinely, indicator definitions themselves (those still live in `metric__` and `metric_definitions.csv`, not generated on the fly), regulatory or donor reports that require approved templates and audit trails.

**Boundaries this raises:**
- Which user roles can run agent-generated queries, and against which data (sensitive vs non-sensitive)?
- Do agent-generated queries get reviewed before execution, or do guardrails (read-only access, query timeouts, row limits) suffice?
- How is the agent's reasoning audited - the natural-language question, the generated SQL, the answer returned?
- How does this interact with Tupaia's existing viz-builder for user-defined indicators - replace, complement, or separate surface?

These are governance and integration questions, captured as OQ-010 and OQ-011.

### Visual contract from the data layer

This subsection connects two parts of the architecture. The data shape decisions in D5 (`metric__` output) and D9 (Data Tables as the consumption mechanism) constrain what report config can and can't do. Templates encode those constraints once; per-deployment authors don't need to rediscover them.

The data architecture decisions already lock in a contract that report config relies on:

| Data contract | What report config can rely on |
|---|---|
| `metric__` wide-format output with explicit disaggregation columns | Templates can configure filter widgets and grouping selectors from declared columns |
| NULL means "rolled up across this dimension" | Filter and grouping widgets interpret NULL consistently across all metrics |
| `period_granularity` is a column | Time series widgets offer day / week / month / quarter / year toggles from one Data Table |
| Standard `unit` values in `metric_definitions.csv` (`count`, `percentage`, `rate_per_1000`) | Templates derive number formatting, axis labels, legend units from the registry |
| `definition_source` + `definition_source_code` | Templates can surface the standard the indicator follows in tooltips / captions |
| `subject_grain` / `entity_grain` (future, see OQ-008) | Templates pin the right entity-hierarchy level for map overlays |

When the data contract changes (a new disaggregation, a renamed column, a new metric variant), the standard template library is one of the things that needs updating - which is the point of version-controlling it.
