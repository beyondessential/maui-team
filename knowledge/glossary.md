# Glossary

Terms used across Maui team repositories. Lift definitions from here when a reader
hits an unfamiliar term in any other doc. If a definition here drifts from a more
authoritative source (the architecture doc, an external standard), the authoritative
source wins — file an issue and update this glossary.

## Systems and platforms

- **Tamanu** — open-source electronic health record (EHR) maintained by BES. Source
  of the clinical data the Maui team models. Deployed in multiple countries; each
  deployment can carry local customisation.
- **Tupaia** — open-source visualisation platform maintained by BES. Surfaces health
  indicators for program managers, ministries of health, and partner organisations.
- **mSupply** — health-commodity management system (stock, orders, dispensing, cold
  chain). Another data source the Maui team pipelines.
- **SENAITE** — laboratory information system. A non-Tamanu data source.
- **FluTracking** — population-level influenza-like-illness surveillance data.
- **NIWA** — New Zealand's National Institute of Water and Atmospheric Research;
  external source of weather/climate data used as analytic context.
- **FSM EHR** — the predecessor EHR being migrated from in `fsm-data-migration`.

## Maui repositories

- **`maui-team`** — this repo. Shared AI knowledge, reusable GHA workflows, the
  spec-driven-development skill. Imported by every other repo as the `.maui`
  submodule.
- **`tamanu-source-dbt`** — canonical dbt project for Tamanu reporting. Source of
  base models, the compiled production bundle, and the reference layer taxonomy.
- **`tamanu-dbt-<deployment>`** — per-deployment dbt projects (e.g. `tamanu-dbt-fj`,
  `tamanu-dbt-msf-syria`). Override `tamanu-source-dbt` only where the deployment
  needs customisation.
- **`data-staging`** — external dbt package historically hosting standard Tupaia
  reporting models. **Being merged into `tamanu-source-dbt`**; treat as in-flight
  legacy.
- **`data-lake`** — Dagster orchestration for dbt pipelines and non-Tamanu
  modelling (mSupply, FluTracking, NIWA, …). Rename to **`bes-data-pipelines`**
  is in flight but blocked on dependency updates; the repo and code references
  are still `data-lake`.
- **`fsm-data-migration`** — one-off migration from FSM EHR to Tamanu.
- **`datatools`** — CLI commands for data tasks across Tamanu/Tupaia.

## Three things named `data-lake` — don't confuse them

This is the most common source of confusion. All three are referenced in code and
docs you may encounter:

- **`data-lake` RDS instance** *(retired)* — the previous shared RDS, being replaced
  by the **`data-warehouse`** RDS.
- **`data-lake` GitHub repo** *(rename in flight)* — to be renamed to
  **`bes-data-pipelines`** once dependency updates land. Operative name is still
  `data-lake`; the new name appears in architecture docs as the target.
- **Tupaia's `data-lake` service** *(unrelated)* — a Tupaia-side data-broker for the
  replication-backed pattern being unwound (architecture D9). Not a BES Maui repo;
  the name is a coincidence.

The architecture doc opens with this naming note ([`architecture/data-architecture.md`](architecture/data-architecture.md)).

## Standards bodies and clinical conventions

- **OMOP** — Observational Medical Outcomes Partnership. Open clinical data model
  governed by OHDSI. The Maui layer taxonomy maps onto OMOP's table categories
  (architecture D2).
- **OMOP-lite** — informal name for the BES subset of OMOP applied in `can__` and
  `der__`. Covers the patient-event facts and derived elements relevant to
  primary-care reporting; doesn't aim for full OMOP coverage.
- **OHDSI** — Observational Health Data Sciences and Informatics. Steward of OMOP.
- **Athena** — OHDSI's concept lookup service: <https://athena.ohdsi.org/>. Used to
  look up OMOP `concept_id` values when populating `map__omop_<domain>` seeds.
- **FHIR** — Fast Healthcare Interoperability Resources. Another health-data
  standard; mentioned occasionally for comparison but not the BES modelling target.
- **WHO SMART / DAK** — WHO Standards-based Machine-Readable Adaptive Kits / Digital
  Adaptation Kits. Source of standardised indicator definitions used in
  `metric_definitions.csv`.
- **PEPFAR** — US President's Emergency Plan for AIDS Relief. Another standardised
  indicator-set source for HIV programmes.
- **DHIS2** — open-source health management information system; another indicator
  catalogue source.
- **MANA** — Maternal-And-Newborn-care indicator framework (BES-curated for
  partners).
- **SDG** — UN Sustainable Development Goals; some health indicators have SDG codes.

## dbt model layer prefixes

See [`standards/dbt-conventions.md`](standards/dbt-conventions.md) § Model layers
for the full table.

- **`base__<entity>`** (under `bases/`) — the only layer allowed to read `public.*`
  directly. Filters deleted rows; normalises naming. Architecture D10.
- **`ref__<entity>`** — OMOP health-system data wrappers. Care site, location,
  provider, with OMOP column names. OMOP "Standardized Health System Data".
- **`lkp__<entity>`** — data-team-curated lookups: analytic groupings (`age_band`),
  cross-system mappings (`facility_tupaia_mapping`), standard codings. Seed-backed.
- **`can__<entity>`** — canonical clinical-event facts in OMOP-lite shape:
  `can__person`, `can__visit_occurrence`, `can__condition_occurrence`,
  `can__measurement`, `can__drug_exposure`, `can__observation`. OMOP "Standardized
  Clinical Data".
- **`der__<element>`** — derived analytic constructs: cohorts
  (`der__cohort_<program>`), eras, episodes. OMOP "Standardized Derived Elements".
- **`metric__<id>`** — health indicators. Single source of truth shared by Tamanu
  reports and Tupaia. Mandatory entry in `metric_definitions.csv`.
- **`int__<description>`** — shared intermediate logic, always `ephemeral`. Inserted
  between layers where needed.
- **`ds__<description>`** — denormalised, consumer-shaped datasets. Join across
  `can__`, `der__`, `metric__`.
- **`models/reports/`** — Tamanu reports (`<description>_line_list` and similar).
  Apply translations, date formatting, report configs. `order by` allowed.

### Legacy prefixes still in active use

- **`fct__`** *(legacy, active)* — event-grain facts alongside `surveys`.
- **`dim__`** *(legacy, soft retirement)* — Kimball dimensions; new work uses
  `ref__` (health system) and `can__` (clinical).
- **`coh__`** *(legacy, renaming)* — cohorts; new work uses `der__cohort_<program>`.
- **`surveys`** *(legacy, active)* — generated survey models; never edited manually.

## Output surfaces

- **Tamanu report** — a SQL view in production that the Tamanu app exposes as a
  patient-level line list or summary. Authored in `tamanu-source-dbt/models/reports/`
  with a paired JSON config. Ships via the compiled bundle (see below).
- **Compiled bundle** — the SQL artefact built per Tamanu release containing the
  transitive closure of every report's dependency chain. Lives in
  `tamanu-source-dbt/compiled/v<version>/`. Models in the bundle must be
  production-safe (no Python models, valid as views over the production schema).
- **Production-safe** — SQL that compiles to a view in the production bundle. No
  Python models, valid against the production schema (no replica-only columns),
  tractable as a runtime view (no heavy window functions across all patients).
- **Replica** — the periodically-refreshed copy of the Tamanu production database
  used for analytics. DevOps-owned. Tupaia reads it; Maui dbt projects run against
  it. Bounded-stale, not real-time.
- **Tupaia Data Table** — a Tupaia visualisation primitive that reads a single
  database table or view. The architecture's preferred surface for `metric__`
  consumption (architecture D9 — replaces the replication-backed pattern).
- **External Database Connection** — the Tupaia admin-panel construct that wires a
  Data Table to its source database. Pairs with each Data Table.
- **Line list** — a Tamanu report shape: one row per patient (or per encounter).
- **Sensitive report** — a parallel report variant that includes encounters from
  sensitive facilities (excluded by default in the standard variant). Naming:
  `sensitive-<name>.sql`.

## Workflow concepts

- **`reporting_*` target** — dbt target prefix used when compiling the production
  bundle. Triggers `view` materialisation (architecture: production-safe).
- **`analytics_*` target** — dbt target prefix used when running against the
  replica. Allows `incremental` or `table` materialisations.
- **env-aware materialisation** — model uses
  `target.name.startswith('reporting_')` to pick `view` for production vs heavier
  materialisation on the replica.
- **Release deployment** — per-Tamanu-version environment used to generate the
  compiled bundle.
- **Clone deployment** — per-deployment, per-upgrade environment used to validate a
  bundle against actual deployment data before production promotion. Ops-owned.
- **Variant** — a deployment-specific override of a `metric__` that flags
  semantically meaningful divergence from the canonical definition. Tracked via the
  `variant_id` column.

## Spec-driven development (SDD)

See [`standards/sdd-conventions.md`](standards/sdd-conventions.md) for the rules.

- **BL** — Business logic clause. Numbered rule in a spec (e.g. `BL-001`).
- **AC** — Acceptance criterion. Numbered, testable check.
- **OQ** — Open question. Owner + due date.
- **DV** — Divergence between current code and ideal spec (retrospective specs).
- **DQ** — Data quality check (migration specs).
- **Spec anchor** — the `-- BL-001:` / `# BL-001:` comment in code that traces back
  to the corresponding clause in a spec.
