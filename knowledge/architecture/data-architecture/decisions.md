# Architectural decisions

Numbered architectural decisions for the Maui data architecture. Cross-referenced
throughout other docs as `(D1)`, `(D2)`, etc. See
[`../data-architecture.md`](../data-architecture.md) for the architecture
overview and [`production-promotion.md`](production-promotion.md) for how these
decisions land in the production pipeline.

## D1 — OMOP-lite as the canonical clinical model

Adopt OMOP-shaped domains (person, visit, condition, measurement, observation, drug exposure) as the canonical representation of Tamanu clinical data. Do not commit to full OMOP CDM compliance.

**What OMOP is:** the Observational Medical Outcomes Partnership (OMOP) Common Data Model is an internationally adopted standard for structuring clinical data for analytics. It defines a consistent set of tables - person, visit, condition, measurement, and so on - so that the same analytical question can be asked the same way across different health systems. Maintained by OHDSI (the Observational Health Data Sciences and Informatics community), it is the dominant standard for EHR-derived observational research.

**"Lite" means:** we adopt OMOP's table shapes and column naming conventions without committing to full compliance (no requirement to run OHDSI tools like ATLAS or ACHILLES end-to-end, no integer ID remapping, no complete vocabulary coverage upfront).

**"Lite" means:**
- OMOP-shaped tables and column names where they fit naturally
- Concept ID shadow columns alongside local values (never replacing them)
- OMOP vocabulary lookups via `map__omop_<domain>` seeds, populated on demand only
- Native UUIDs as primary keys - no hashing or remapping to OMOP integer IDs
- No requirement to support OHDSI tools (ATLAS, ACHILLES) end-to-end

**Why:** OMOP is the natural shape for EHR-derived analytics; person-event modelling beats fact/dimension for clinical data. Lite gets us 80% of the value (consistent shape, standard vocabularies, research-tool compatibility) for ~20% of the effort of full compliance.

**Escalation path:** if a concrete federation, multi-site research, or OHDSI-tooling requirement arises, revisit. Lite-to-full is a smaller jump than ad-hoc-to-full.

**Alternatives considered:**

| CDM | Designed for | Why rejected for BES |
|---|---|---|
| **PCORnet CDM** | US patient-centred outcomes research; lineage from FDA Mini-Sentinel | Heavily oriented around US billing/claims vocabularies; little international or Pacific adoption; no derived-elements layer comparable to OMOP's |
| **i2b2** | Clinical data warehousing with simple ETL | Single denormalised fact table is the opposite of the multi-domain `can__` design; analytics complexity moves from one-time mapping to every-metric runtime; no built-in standardised vocabulary |
| **Sentinel CDM** | FDA post-market drug safety surveillance | Narrow domain focus; not designed for general clinical analytics |
| **CDISC SDTM** | Clinical trial submissions to FDA | Mismatch with observational data; SDTM's structure is shaped for trial-submission formats rather than EHR-derived analytics |
| **openEHR** | Source-level clinical record specification (archetypes/templates) | Different architectural layer entirely - openEHR is what an EHR like Tamanu could be *built on*; analytics on openEHR data still typically requires transformation into OMOP or similar. Not a substitute for OMOP at the analytics layer. |
| **No CDM (Tamanu-native)** | Lowest upfront effort | Every metric pays the abstraction cost that `can__` would have paid once. Vocabulary mapping, soft-delete handling, schema-version churn all land in individual metrics. Cost is invisible until it isn't. |

OMOP-lite was chosen because it has the strongest research-community adoption, the most mature standardised vocabularies (OHDSI Athena), the only major CDM with active derived-elements support (cohorts, eras), and the natural fit with multi-domain clinical modelling. The remaining serious contender at the analytics layer is FHIR, which is out of scope for the data team per D4.

---

## D2 — Four layer prefixes mapped to OMOP categories

The dbt layer structure in `tamanu-source-dbt` maps directly onto OMOP's own table categorisation:

| Layer prefix | OMOP category | Purpose |
|---|---|---|
| `ref__` | Standardized Health System Data | OMOP health system entities: care sites, locations, providers |
| `lkp__` | (BES-specific) | data-team-curated lookups: analytic groupings, cross-system mappings, standard codings, hierarchies not in Tamanu |
| `can__` | Standardized Clinical Data | Canonical patient-event facts (OMOP-lite shape) |
| `der__` | Standardized Derived Elements | Computed analytic constructs - cohorts, eras, episodes |
| `vocab__` | Standardized Vocabularies | OHDSI Athena concept tables (future - see OQ-005) |

Two OMOP categories are not represented as dedicated layers:
- Standardized Health Economics - not relevant in BES context
- Metadata - handled by dbt and source-tracking conventions

Above these four sit the BES-specific layers: `metric__` (D5), `ds__` (datasets), and `models/reports/` (Tamanu reports). `lkp__` is also BES-specific and sits alongside the OMOP-mapped four (used as join targets by `can__`, `der__`, `metric__`, and `ds__`).

`surveys` is a Tamanu-specific generated layer (one `<survey_id>` view per Tamanu survey form, with one column per question) that pivots `bases/` survey responses into a wide queryable shape. It sits alongside `bases/` / `ref__` / `lkp__` as a base layer feeding `can__measurement`, `can__observation`, and other downstream models. Always a view; never edited manually — regenerated by script when survey definitions change.

### `ref__` — OMOP health system data

`ref__` follows OMOP's Standardized Health System Data category - it wraps Tamanu's own facility, location, and provider data in OMOP-shaped models so `can__` models have stable, typed join targets with consistent column naming.

| Model | OMOP entity | Source |
|---|---|---|
| `ref__care_site` | `CARE_SITE` | Deployment's `public.*` via `bases/` |
| `ref__location` | `LOCATION` | Deployment's `public.*` via `bases/` |
| `ref__provider` | `PROVIDER` | Deployment's `public.*` via `bases/` |

The value of the wrapper is the OMOP column naming and typing (`care_site_id`, `care_site_name`, `place_of_service_concept_id`, etc.) - `can__` models join to `ref__care_site`, not to `base__facilities`. This keeps the layer contract intact and makes `can__` models portable across OMOP tooling.

The package ships **mock seed data** for these models for package testing and CI. Production environments read the deployment's real `public.*` data through `bases/`.

### `lkp__` — data-team-curated lookups

`lkp__` holds reference data that the data team curates and owns - analytic groupings, cross-system mappings, and standard codings that aren't OMOP health system entities and don't live in Tamanu's source data.

**What `lkp__` is for:**
- **Analytic groupings** - standard buckets used across metrics (`lkp__age_band`, `lkp__pregnancy_trimester`)
- **Cross-system mappings** - bind IDs across systems (`lkp__facility_tupaia_mapping` binds Tamanu facility UUIDs to Tupaia entity codes)
- **Hierarchies not in Tamanu** - administrative or health-system context Tamanu doesn't model (`lkp__health_district`, `lkp__village_hierarchy`)
- **Standard codings** - reference vocabularies shipped as seeds (`lkp__imaging_type`, `lkp__encounter_class`, `lkp__lab_category`, `lkp__vital_type`)

| Model | Purpose | Data source |
|---|---|---|
| `lkp__age_band` | Standard age bucketings for analytics | Seed in `tamanu-source-dbt` |
| `lkp__imaging_type` | Imaging modalities (X-ray, CT, MRI, …) | Seed in `tamanu-source-dbt` |
| `lkp__encounter_class` | Encounter classes (inpatient, outpatient, emergency, …) | Seed in `tamanu-source-dbt` |
| `lkp__lab_category` | Lab test categories | Seed in `tamanu-source-dbt` |
| `lkp__vital_type` | Vital sign types | Seed in `tamanu-source-dbt` |
| `lkp__facility_tupaia_mapping` | Bind Tamanu facility UUIDs to Tupaia entity codes | Seed in `tamanu-dbt-<deployment>` (inherently per-deployment) |
| (further `lkp__` models as needed) |

Standard seeds live in `tamanu-source-dbt` and are rarely overridden. Cross-system mappings and deployment-specific hierarchies are inherently per-deployment and live in `tamanu-dbt-<deployment>` projects.

`lkp__` is distinct from `map__<system>_<domain>` seeds (e.g. `map__omop_*`, `map__dhis_*`, `map__tupaia_*`) - those translate Tamanu identifiers to an external system's identifiers; `lkp__` models are operational lookup tables used as join targets by `can__`, `der__`, `metric__`, and `ds__` models.

**Materialisation:** `lkp__` models are always views. The seed (or upstream `bases/` model, where the lookup is derived) is the source of truth; the view is a thin typed projection. No incremental or table materialisation - lookups are small and slow-changing, so view-on-seed reads are cheap.

### `can__` — canonical clinical data

| Model | Purpose |
|---|---|
| `can__person` | One row per patient, OMOP-shaped demographics + concept shadows |
| `can__visit_occurrence` | Encounters (inpatient, outpatient, emergency) |
| `can__condition_occurrence` | Diagnoses (encounter + registry conditions) |
| `can__measurement` | Quantitative survey results, vitals, labs |
| `can__observation` | Qualitative survey results, social history, flags |
| `can__drug_exposure` | Prescriptions |
| `can__observation_period` | Time spans during which a patient is "at-risk to have a clinical event recorded" (placed in `can__` for usage simplicity though OMOP categorises it as a derived element) |

### `der__` — standardised derived elements

Cohorts are the first and most-used derived element in BES; OMOP's other derived elements (`condition_era`, `drug_era`, `dose_era`, `episode`) can be added here if and when needed. This layer corresponds directly to OMOP's "Standardized Derived Elements" category - it is not "a semantic application of `can__`"; it is OMOP's own separate layer for computed analytic constructs.

| Model | Purpose |
|---|---|
| `der__cohort_<program>` | Cohort membership for a program / registry |
| (future) `der__condition_era` | Combined condition occurrences into chronic-care episodes |
| (future) `der__drug_era` | Combined drug exposures into continuous treatment periods |

**Why `can__` (and the family) and not `omop__`:** the prefixes describe our layers, not our commitment to a specific external standard. `can__` survives the OMOP-lite → full-OMOP → next-standard evolution. The `omop` token stays in `map__omop_<domain>` because those seeds genuinely target OMOP vocabularies - the prefix there describes the destination, not the layer.

**`map__<system>_<domain>` is the general prefix for external-system code translation.** `map__omop_<domain>` is one instance (OMOP vocabularies); `map__dhis_<entity>` (DHIS2 UIDs — data elements, category option combos, org units), `map__tupaia_<entity>` (Tupaia entity codes), and similar bindings to other downstream systems follow the same shape. The prefix says "this translates Tamanu identifiers to the named external system's identifiers"; the suffix names the entity domain. Materialisation: seed-backed by default; view-over-`(values …)` when the dataset is small enough that authoring a CSV adds no value and the SQL keeps it inline-reviewable. Per [`../../standards/dbt-conventions.md`](../../standards/dbt-conventions.md) § `map__<system>_<domain>`, `map__<system>_*` is distinct from `lkp__`: `map__` *translates* between code systems; `lkp__` is operational join targets (analytic groupings, hierarchies, deployment-local codings) used by `can__` / `der__` / `metric__` / `ds__`.

**Per-deployment variation:** standard implementations of `ref__`, `lkp__`, `can__`, `der__`, `metric__`, and `ds__` models live in `tamanu-source-dbt`. Most deployments run these directly. Deployments with genuine customisation needs create a `tamanu-dbt-<deployment>` project that references `tamanu-source-dbt` as a package and overrides only the specific models that need deployment-specific behaviour. See [`production-promotion.md`](production-promotion.md) § Version skew.

---

## D3 — Standards-aware, documentation-required indicator definitions

Every `metric__` model - Tamanu-derived or non-Tamanu - declares its **definition source** in the metric registry. The source can be any of:

- An external standard (WHO SMART DAK, WHO Core 100, WHO/UNICEF indicators, SDG, DHIS2 Health Data Toolkit, regional frameworks like MANA, donor M&E frameworks like Global Fund / PEPFAR, OHDSI Phenotype Library, etc.)
- An internal BES definition (when no suitable external standard exists or the context is BES-specific)

**No hierarchy is enforced.** What matters is that the definition is documented, reviewable, and traceable to its source. The choice of standard for any given metric is a domain question (which standard does the reporting audience expect? which is most operationally useful?), not an architectural rule.

**When using an external standard:**
- Adopt the definition verbatim - same numerator, denominator, disaggregations, indicator codes
- Local extensions allowed as separate `metric_id`s with `variant_id` set, never as silent modifications to the original
- Record the source code in `metric_definitions.csv` via dedicated columns (`who_smart_code`, `who_core_100_code`, `sdg_code`, `dhis2_toolkit_code`, `mana_code`, etc., added on demand rather than all up front)

**When using an internal BES definition:**
- Document the rationale in `metric_definitions.csv` (`source = "BES"`, plus a short justification field)
- Reviewers check whether an external standard exists and was deliberately skipped - if so, the deliberate skip should be noted

**Catalogues worth knowing.** This is not an exhaustive list, just commonly relevant ones - adopt verbatim where they apply.

| Catalogue | Scope |
|---|---|
| **WHO Digital Adaptation Kits (DAKs)** | Currently relevant: ANC, immunisation, HIV, TB. Machine-readable indicator definitions packaged with care logic |
| **WHO Global Reference List of 100 Core Health Indicators** | Cross-cutting health system indicators (mortality, morbidity, service coverage, financing, health systems) |
| **WHO/UNICEF Indicators for Assessing Infant and Young Child Feeding Practices** | Nutrition, infant and young child feeding |
| **DHIS2 Health Data Toolkit** | Pre-packaged indicator definitions for many program areas |
| **SDG Health Indicators (SDG-3 and related)** | UN Sustainable Development Goal monitoring |
| **Pacific Monitoring Alliance for NCD Action (MANA) Dashboard indicators** | Pacific-specific NCD monitoring |
| **Global Fund / PEPFAR M&E frameworks** | HIV, TB, malaria program indicators where countries report to these donors |
| **OHDSI Phenotype Library** | Standardised cohort / phenotype definitions, OMOP-shaped |

**Wide format for all `metric__` outputs.** Every `metric__` model - Tamanu-derived in `tamanu-source-dbt` or non-Tamanu in `bes-data-pipelines` - uses the wide-format output shape defined in D5: one row per (subject, period, disaggregation combination), with values in dedicated columns. This shape is best for analytics workflows (Tupaia Data Tables, ad-hoc analyses, exports) - it queries directly without unpivot or jsonb extraction, supports column-level dbt tests, and gives Tupaia a predictable contract. The wide-format shape applies regardless of definition source (standard or internal) and regardless of data source (Tamanu or non-Tamanu).

---

## D4 — FHIR is out of scope for the data team

**What FHIR is:** Fast Healthcare Interoperability Resources (FHIR) is the international standard for exchanging healthcare data between systems - resource-oriented JSON, RESTful APIs, used for transactional point-of-care exchange. Maintained by HL7.

FHIR and OMOP solve different problems. FHIR is for interoperability and exchange; OMOP is for analytics. The industry pattern (used at most major academic medical centres and national health systems) is FHIR at the system boundary, OMOP at the analytics layer, with ETL between them.

The Tamanu dev / integration team owns FHIR resources, mappings, and any FHIR-shaped APIs Tamanu exposes. The data team consumes Tamanu's database directly via `tamanu-source-dbt`, in OMOP-lite shape.

If a future use case demands FHIR ingestion or output from the data layer (research federation, MoH partner integration, Tamanu deprecating direct DB access), raise it as a joint dev + data scoping exercise. The likely shape: `bases/` unpacks inbound FHIR resources, or a layer above `can__` maps to outbound FHIR. `can__` itself stays OMOP-shaped.

---

## D5 — `metric__` as the single source of truth for indicators

Indicators derived from Tamanu data live as dbt models in `tamanu-source-dbt/models/metrics/`, computed in the Tamanu replica DB. One model per indicator. All consumers (Tamanu aggregation reports, Tupaia via Data Tables (D9), ad-hoc analyses) source from `metric__` - never recompute the underlying logic.

Indicators derived from non-Tamanu data are out of scope for this layer's first iteration. The same shape and registry pattern should extend to `data-warehouse`-based indicators when that work is scoped (see OQ-002). Cross-source indicators (e.g. drug availability per condition prevalence) are deferred until the single-source pattern is stable.

**Tupaia consumption:** Tupaia reads `metric__` outputs via Data Tables backed by External Database Connections (D9). The Data Table SQL is a simple `select *` pass-through - all semantic logic lives in dbt.

**Standard output shape** (all `metric__` models):

| Column | Type | Notes |
|---|---|---|
| `metric_id` | text | From `metric_definitions.csv`; matches model name |
| `variant_id` | text | Nullable; deployment-specific override identifier |
| `subject_id` | uuid | Patient ID for patient-grain metrics; entity ID for org-grain |
| `period_start` | date | Inclusive |
| `period_end` | date | Inclusive |
| `period_granularity` | text | `day` / `week` / `month` / `quarter` / `year` |
| `value_numeric` | numeric | Nullable; for quantitative metrics |
| `value_boolean` | boolean | Nullable; for binary metrics (e.g. controlled / not controlled) |
| **disaggregation columns** | various | Explicit columns per disaggregation (e.g. `sex text`, `age_band text`, `facility_id uuid`). Each metric declares its own. NULL means "rolled up across this dimension" - see below. |

**On disaggregation as explicit columns:** each metric's disaggregations are explicit, named, typed columns rather than a single `jsonb` column. This means:
- Per-metric schema evolution (adding a new disaggregation is a model + registry PR), accepted as the cost
- Column-level dbt tests (e.g. `accepted_values` on `sex`, `not_null` on `facility_id`)
- Direct queryability from Tupaia Data Tables - no jsonb extraction at query time
- NULL in a disaggregation column means "this row is rolled up across that dimension." A metric's output therefore typically contains multiple rows for the same `period_start`: one with all disaggregation columns populated (full breakdown), and roll-ups with one or more dimensions NULL. Models declare in YAML which roll-up combinations they produce, so consumers know which subsets to expect.

Pre-aggregated metrics omit `subject_id`. Per-patient metrics keep `subject_id` populated; disaggregation columns are still present and typically NULL since the patient's identity carries the dimension values implicitly.

**Registry seed - `metric_definitions.csv`.** The canonical registry lives at
`tamanu-source-dbt/seeds/metric_definitions.csv` for Tamanu-derived metrics
(equivalent seed in `bes-data-pipelines` for non-Tamanu metrics). All
deployments inherit the canonical registry automatically via the `tamanu-source-dbt`
package — consumers read it as `{{ ref('metric_definitions') }}` without having
to redeclare anything.

**Deployment-specific entries** (deployment-only definitions, or
deployment-flagged `variant_id` overrides of an upstream metric) live in
`tamanu-dbt-<deployment>/seeds/metric_definitions_<deployment>.csv` — same
schema, distinct filename so it composes alongside the canonical seed without
shadowing it. The canonical seed is the source of truth for standard metrics
and never gets overwritten by a deployment.

> Use a deployment-specific row when:
> - The metric exists only at one deployment (no shared standard upstream)
> - Or the metric is a `variant_of` an upstream metric, where the deployment
>   has changed the definition rules (D5 § Definition variance)
>
> Don't use it for implementation-only differences — those go via dbt model
> override with the upstream row unchanged (D5 § Implementation difference).

Schema (shared across canonical and deployment-specific seeds):


| Column | Description |
|---|---|
| `metric_id` | Globally unique; stable; never reused. Snake case (e.g. `hypertension_control_6m`) |
| `name` | Human-readable label |
| `description` | What it measures, in plain English |
| `numerator_description` | Numerator in words |
| `denominator_description` | Denominator in words |
| `data_source` | `tamanu`, `msupply`, `senaite`, `weather`, etc. - which source system the metric derives from |
| `definition_source` | Where the definition comes from: external standard name (e.g. `WHO_SMART_HIV`, `WHO_CORE_100`, `SDG`, `DHIS2_HDT`, `MANA`, `GLOBAL_FUND`, `OHDSI`, `IYCF`) or `BES` for internal definitions |
| `definition_source_code` | The standard's own identifier for the indicator if external (e.g. WHO DAK indicator code, SDG code, DHIS2 data element code); `NULL` for `BES` |
| `definition_rationale` | Short justification - for external standards, why this one over others; for `BES`, why an internal definition rather than an external standard |
| `tupaia_code` | Legacy Tupaia indicator code being replaced; else `NULL` |
| `unit` | `count`, `percentage`, `rate_per_1000`, etc. |
| `subject_grain` | `patient`, `encounter`, `facility`, etc. |
| `disaggregations` | Comma-separated list of disaggregation column names the metric produces (e.g. `sex,age_band,facility_id`) |
| `variant_of` | If this row is a deployment-specific definition variant of an upstream metric, the parent `metric_id`; else `NULL`. See "Definition variance" below |
| `owner` | Team or person responsible |
| `status` | `draft` / `approved` / `deprecated` |
| `spec_path` | Path to SDD spec |

**Two kinds of deployment variation - handle them differently:**

| Kind | Example | Mechanism | `variant_id` |
|---|---|---|---|
| **Implementation difference** | Deployment uses a different survey form for blood pressure but the metric is still "% controlled at 6 months by WHO definition" | dbt package override - deployment repo defines `metric__<id>.sql` with deployment-specific SQL; dbt resolution makes it win | `NULL` - consumers see the same metric, same definition, same number-shape |
| **Definition variance** | Deployment uses age band 18-69 instead of WHO standard 18-64; numerator includes additional conditions the standard excludes | Same dbt override mechanism, AND set `variant_id` on the output rows to a stable identifier | Deployment-set value (e.g. `fj_moh_2024`) |

The override mechanism is the same; what differs is whether the deployment flags the variation as semantically meaningful. Implementation overrides are invisible by design - that's the point of the package + override pattern. Definition variants are registered in the deployment project's `metric_definitions_<deployment>.csv` with `variant_of = <parent_metric_id>` and a description of what differs. Reviewers check this on PR.

**Worked example.** A simple `metric__` model and its registry entry:

```sql
-- models/metrics/metric__hypertension_controlled.sql
{{ config(
  materialized = ('view' if target.name.startswith('reporting_') else 'incremental'),
  unique_key = ['metric_id', 'subject_id', 'period_start', 'sex', 'age_band', 'facility_id'],
) }}

select
  'hypertension_controlled' as metric_id,
  null::text                as variant_id,
  patient_id                as subject_id,
  date_trunc('month', m.measurement_date)::date as period_start,
  (date_trunc('month', m.measurement_date) + interval '1 month - 1 day')::date as period_end,
  'month'                   as period_granularity,
  case when m.systolic < 140 and m.diastolic < 90 then 1 else 0 end as value_numeric,
  p.sex,
  ab.age_band,
  cs.care_site_id           as facility_id
from {{ ref('can__measurement') }} m
join {{ ref('can__person') }} p on p.person_id = m.person_id
join {{ ref('lkp__age_band') }} ab on ab.age_years = p.age_at_measurement
join {{ ref('ref__care_site') }} cs on cs.care_site_id = m.care_site_id
where m.measurement_concept_id in (3004249, 3012888)  -- systolic, diastolic BP
```

Corresponding `metric_definitions.csv` row:

```csv
metric_id,name,description,numerator_description,denominator_description,unit,subject_grain,disaggregations,definition_source,definition_source_code,owner,status
hypertension_controlled,Hypertension control rate,Patients with controlled BP at last measurement,Patients with systolic < 140 and diastolic < 90,Patients with a BP measurement in period,percentage,patient,"sex,age_band,facility_id",WHO PEN,PEN-CVD-3,data team,active
```

Tupaia consumes via a Data Table: `select * from {dbt_schema}.metric__hypertension_controlled`. The dashboard chooses which disaggregations to render and which to roll up by filtering on those columns - NULL rows on a disaggregation column are the roll-up.

**Why this layer:**
- Definitions are version-controlled and reviewable
- Definitions are testable (dbt tests + Great Expectations - see D8)
- Definitions are introspectable by agents - the data assistant can read `metric_definitions.csv` to answer "what indicators do we have, what do they mean, and what shape do they return?" without parsing SQL
- Single computation path → no drift between platforms
- Tupaia is one consumer among many, not the owner

---

## D6 — Consumer-shaped datasets (`ds__`)

`ds__` models are presentation-layer datasets shaped for a specific consumer - wide, denormalised, often pre-aggregated. They sit downstream of `ref__`, `can__`, `der__`, and `metric__`, joining across them as needed, and never feed back into them.

Examples of `ds__` shapes:

| Pattern | Grain | Sources from | Used for |
|---|---|---|---|
| Patient summary | One row per patient | `can__person`, latest from `can__visit`, `can__condition`, `can__measurement`; optionally scoped by `der__cohort_<program>` | Operational line-list reports, dashboards showing "current state per patient" |
| Encounter line-list | One row per encounter | `can__visit_occurrence` + joined `can__` facts | Activity reports, audit trails |
| Indicator time series | One row per metric × period × disaggregation | `metric__<id>` | Tupaia dashboards |
| Cohort enrolment summary | One row per cohort × period | `der__cohort_<program>` | Registry tracking dashboards |

**Patient summary is not a cohort.** A cohort tracks subject × period membership; a patient summary tracks one row per patient with current/latest state. They compose - `ds__ncd_patient_summary` can scope its population to `der__cohort_ncd` membership - but they answer different questions ("was this patient in this cohort during this period?" vs. "what is this patient's current state?"). Picking the wrong layer leads to either over-engineered cohorts pretending to be snapshots or under-engineered summaries with no temporal logic.

`ds__` models are typically the entry point for Tupaia Data Tables and Tamanu reports. They are not the source of truth for any indicator - that's `metric__`'s job.

---

## D7 — Kimball layer (`data-staging`) retired as consumers migrate

> **Sunset.** This decision is in force only until Phase 5 § 5b
> (`dim__` → `ref__` / `can__` migration; see `../../runbooks/refactoring-guide.md`)
> completes and the `data-staging` package merges into `tamanu-source-dbt`.

`data-staging` (`fct__` / `dim__`) is on a soft retirement path. No hard cut-over date - but new work does not land there, and consumers migrate to `can__` / `metric__` as opportunities arise.

**Treatment of existing models:**
- Active and stable: leave in place; migrate when next non-trivial change is needed
- Active and frequently changing: prioritise migration
- Unused: deprecate and remove

The `dataset/` flattened models in `data-staging` migrate to per-consumer locations based on data source:
- Tamanu-derived datasets → `tamanu-source-dbt/models/datasets/` (as `ds__` models, the right home per D6) or directly into `models/reports/` if they are specifically Tamanu-report-bound
- Non-Tamanu-derived datasets → `data-warehouse` RDS, in dbt projects within the `bes-data-pipelines` repo (or wherever non-Tamanu modelling settles - see OQ-002)
- Cross-source datasets → deferred; revisit once both single-source patterns are stable

**Why now:** the Kimball layer was the right answer when fact/dim was the only modelling pattern in use. With `ref__`, `lkp__`, `can__`, `der__` covering canonical clinical structure, `metric__` covering indicator semantics, and `ds__` covering consumer-shaped datasets, the staging layer is redundant for new work and a maintenance burden going forward.

---

## D8 — Spec-driven development for non-trivial data work

**Why this matters:** clinical and indicator definitions are easy to get wrong in ways that aren't visible from the SQL alone. A model that compiles cleanly and passes tests can still represent the wrong concept - wrong cohort criteria, wrong unit, wrong subject grain, wrong handling of edge cases. Spec-driven development (SDD) catches these in writing before they're catched in PR review, and gives reviewers something concrete to challenge that isn't just "this code is wrong."

The spec is the authoritative description of intent. The code implements the spec. Numbered business-logic clauses (`BL-001`, `BL-002`, …) are referenced in code comments, so every line of clinical logic traces back to a sentence in the spec a reviewer agreed to.

Use SDD specs (via the `maui-spec-driven-development` skill — templates live in
`.maui/skills/maui-spec-driven-development/assets/templates/`) for:

- New `ref__` and `lkp__` models
- New `can__` domain models
- New `der__` derived elements
- New `metric__` definitions
- New `ds__` datasets (including Tamanu report inputs and Tupaia consumption datasets)
- Data migrations
- Semantic changes to existing models (anything that could alter a number consumers see)

Spec **not** required for:

- Bugfixes <~50 lines with no semantic change
- Pure refactoring (e.g. renaming a CTE, splitting a model)
- Dependency / version bumps
- Linting and formatting
- Urgent ad-hoc extracts

The threshold sits in the author's judgement. Reviewers flag when it has been misjudged.

**Testing expectations.** Specs define what the model should compute; tests assert that the implementation does what the spec says. Three layers of testing apply across the architecture:

| Layer | Test type | Tool |
|---|---|---|
| Schema-level invariants | `not_null`, `unique`, `relationships`, `accepted_values`, `expression_is_true` | dbt schema tests in `<model>.yml` |
| Logic-level behaviour | Mocked inputs, expected outputs, scenario coverage | dbt unit tests (`unit_test__<model>.yml`) |
| Data quality on real data | Distribution drift, freshness, completeness, cross-model invariants | dbt singular tests; Great Expectations (early-stage adoption, expanding) |

Schema tests are mandatory for `metric__`, `ds__`, and `models/reports/` models (primary keys, expected ranges, unit consistency). Unit tests are recommended for models with non-trivial logic - cohort membership rules, window functions, multi-source joins. Great Expectations covers data quality concerns that span models or check distributions over time.

Tests are named for the spec acceptance criterion they assert (`ac_NNN_<model>_<assertion>` for schema tests; a `failed_ac` discriminator column in singular tests). When a test fails, the spec clause it violated is identifiable from the test output.

**Data quality monitoring.** Tupaia consumes `metric__` outputs directly via Data Tables - when those outputs are wrong, late, or missing, dashboards silently render incorrect numbers. The data team owns detecting this:

- **Freshness** is monitored by Dagster (post-replica-update incremental runs report success / failure / lag)
- **Completeness and correctness** are monitored by Great Expectations suites attached to `metric__` and `ds__` models; failures surface as Dagster alerts
- **Schema drift** between `metric__` outputs and Data Table consumers is caught at PR time (D9 schema-changes-are-paired rule)

Specific monitoring SLOs and alert routing are out of scope for this document - they belong in an operational runbook.

**Backfills.** When a `metric__` definition changes in a way that alters historical values (per D5 `variant_id`), the metric is rebuilt from the earliest affected period forward. The `variant_id` column lets consumers distinguish old-definition rows from new-definition rows during the cutover. Routine reprocessing is handled by Dagster; large historical backfills are scoped as their own work items.

---

## D9 — Direct query, not replication

Tupaia queries source databases (per-deployment Tamanu **replicas**, `data-warehouse`) directly through Tupaia's **External Database Connections** and **Data Tables**. Modelled outputs are not replicated to Tupaia's own database.

**Replicas, not production.** Tamanu analytics workloads (including Tupaia and ad-hoc) hit the per-deployment replica DBs, not the production Tamanu DBs. This is deliberate: analytics query load is isolated from the live Tamanu app. Tamanu reports are the only consumer that runs against production, and they do so via pre-built views from the compiled SQL bundle (see [`production-promotion.md`](production-promotion.md) § Tamanu reports and the production promotion path).

**The mechanism** (Tupaia-side, for reference):
- An **External Database Connection** is a registered connection in Tupaia (code, host, credentials) pointing to a source DB. One per per-deployment Tamanu replica + one for `data-warehouse`.
- A **Data Table** (`type: sql`) references an External Database Connection by code and holds a configured SQL query. The `data-table-server` microservice executes it.
- Reports and dashboards consume Data Tables via `report-server`, applying config-driven transformations.

**Conventions for `metric__` Data Tables:**
- **One Data Table per `metric__` model.** Not one per dashboard. The Data Table is a 1:1 pass-through of the metric.
- **Naming.** Data Table name matches the `metric_id` (e.g. `hypertension_control_6m`).
- **SQL inside the Data Table is trivial** - `select * from {dbt_schema}.metric__<id>` with optional period/entity parameter binding. All semantic logic lives in dbt; Tupaia just reads.
- **Schema changes are paired.** A PR that changes a `metric__` model's output schema must include a Data Table review. Tupaia admin-panel changes happen alongside the dbt change, not after.
- **Definitions live in Tupaia's admin panel.** Version-controlled Data Table definitions are a future improvement; for now the dbt `metric__` model is the authoritative artefact and Tupaia stores the trivial pass-through. If a Data Table's SQL ever grows beyond `select *`, that's a signal to push the logic upstream into `metric__` rather than maintain it in two places.

This is parallel to the older Tupaia data-broker `data-lake` service (a Tupaia-side replication-backed service being unwound - unrelated to the BES `bes-data-pipelines` repo despite the name overlap). Data Tables are the forward path.

**Current state:** existing pipelines still replicate modelled outputs from source DBs to Tupaia via the Tupaia-side data-broker. This is being unwound model-by-model, with dashboards migrated to Data Tables as they're touched.

**What this does NOT mean:** in-database materialisation is still expected. `metric__` models materialise as tables in their home DB; Data Tables read those tables. "No replication" means "no cross-DB copying of outputs," not "no materialisation."

---

## D10 — Reporting sources from `bases/`, never from `public.*`

All modelling and reporting (`ref__`, `lkp__`, `can__`, `der__`, `metric__`, `ds__`, Tamanu reports under `models/reports/`) sources from `bases/` models, never from `public.*` tables directly.

**What `bases/` does:**
- Filters soft-deleted rows (Tamanu uses logical deletion via `deleted_at`-style columns; reporting must not surface deleted records)
- Drops internal metadata columns (sync metadata, audit fields, server-internal flags)
- Normalises column naming where Tamanu uses inconsistent casing or domain-leaking names
- Provides a stable boundary between Tamanu's evolving schema and downstream models

**Why this is non-negotiable:**
- Reporting from `public.*` directly counts deleted records, leaking removed patients, voided encounters, and rolled-back data into dashboards and reports
- Internal metadata fields (e.g. sync timestamps, server IDs) can accidentally end up in line-list outputs, creating data leakage and noise
- Tamanu's schema evolves between versions - `bases/` absorbs that churn so downstream models don't have to. Direct `public.*` references break on every version bump
- Without this rule, the production compiled bundle has no protection against accidentally exposing deleted data through Tamanu reports

**Applies in all environments:**
- Replica analytics (`metric__`, `ds__`, ad-hoc work)
- Production line-list reports (in the compiled bundle)
- Per-deployment dbt project overrides (a deployment can override `bases/` if their Tamanu deployment has schema differences, but never bypass `bases/` to query `public.*` from a downstream model)

**Sources:** dbt `sources` definitions in `tamanu-source-dbt/models/sources/` declare `public.*` tables. `bases/` models are the *only* layer permitted to `select from {{ source('tamanu', 'table') }}`. Every other layer uses `{{ ref('base__table') }}`.

**Enforcement:** dbt's `lineage` graph makes this auditable. A linting check or dbt CI hook can fail PRs that reference `public.*` outside `bases/`. Worth adding to the Phase 0 conventions work.

---

## D11 — Data team owns report config on both Tamanu and Tupaia

Report config - the binding between `metric__` outputs and what end users see (chart type, disaggregation selectors, period controls, filter widgets, map overlay styles, layout) - is the data team's responsibility for both surfaces.

- **Tamanu reports** (current state): SQL and config in `tamanu-source-dbt/models/reports/` and `models/reports/config/`, shipped via the compiled bundle at each release.
- **Tupaia dashboard items and map overlays** (target state): a data-team-owned standard visual template library for the two Tupaia visual primitives, imported into Tupaia via the admin panel's existing import capability. Per-deployment authors assemble dashboards from these templates in the admin panel.

Visual design systems (palettes, typography, layout chrome, mobile responsive design) stay with platform owners (Tupaia engineering, Tamanu engineering). Report config sits on top of the design system, configuring it with metric-specific choices.

See [`production-promotion.md`](production-promotion.md) § Report config for mechanics on both surfaces and the migration path for Tupaia.
