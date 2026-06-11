# Phase 0 deliverables

Phase 0 closes when these are done. Estimated 2–4 weeks. Tracked items live in
Linear; this list mirrors them for in-repo visibility.

- [ ] **This document approved by the data team.** `status: approved` in the
      [`../data-architecture.md`](../data-architecture.md) header.
- [x] **Updates to `dbt-conventions.md`** *(done — see
      [`../../standards/dbt-conventions.md`](../../standards/dbt-conventions.md))*.
      Frames the new layer structure (`ref__`, `lkp__`, `can__`, `der__`,
      `metric__`, `ds__`) and its mapping to OMOP categories (D2); documents the
      environment-aware materialisation pattern (incremental/table on replica,
      view in compiled bundle); documents the `bases/`-only rule for `public.*`
      access (D10).
- [x] **`derived-elements-conventions.md` content updated** *(done — see
      [`../../standards/derived-elements-conventions.md`](../../standards/derived-elements-conventions.md))*.
      Broadened to cover the full `der__` layer (cohorts, eras, episodes),
      reframed as OMOP's "Standardized Derived Elements" layer, with the cohort
      naming convention `der__cohort_<program>` throughout. Derived elements
      build on `can__` (and `ref__` / `lkp__` for facility-scoped definitions
      and analytic groupings).
      [`../../runbooks/new-derived-element.md`](../../runbooks/new-derived-element.md)
      updated to match.
- [ ] **`new-metric.md` runbook drafted** in
      [`../../runbooks/`](../../runbooks/), mirroring the structure of
      `new-derived-element.md` and `new-report.md`. *Until this lands, an
      agent adding a new `metric__` should follow `new-derived-element.md` as
      the closest pattern and consult D5 for the registry contract.*
- [ ] **`metric_definitions.csv` schema agreed** and seeded with 1–2 reference
      indicators (port one existing Tupaia indicator end-to-end as the proof of
      concept, including the paired Tupaia Data Table + External Database
      Connection). A proposed unified schema covering metrics, cohorts, eras,
      and episodes (with a `kind` discriminator) is drafted in
      [`../../standards/derived-elements-conventions.md`](../../standards/derived-elements-conventions.md)
      § Registry; team agreement and seeding pending. Resolution of
      [OQ-004](open-questions.md) (override vs extend semantics for deployment
      seeds) closes alongside this deliverable.
- [ ] **One reference `can__` model built** in
      `tamanu-source-dbt/models/canonical/` — `can__person` is the natural pick
      (lowest variance, highest reuse). Establishes the pattern others copy.
- [ ] **Reference `ref__` and `lkp__` models built** — one of each pattern:
  - **`ref__` OMOP wrapper:** `ref__care_site` reading from `bases/`, applying
    OMOP column naming. Establishes the health system data wrapper pattern
  - **Standard `lkp__` seed in `tamanu-source-dbt`:** `lkp__age_group` shipping
    real data as a seed. Establishes the standard lookup seed pattern
  - **Deployment-specific `lkp__` mapping:** `lkp__facility_tupaia_mapping` in
    a sample `tamanu-dbt-<deployment>` project, binding Tamanu facility UUIDs
    to Tupaia entity codes. Addresses OQ-008 concretely
- [ ] **D10 enforcement check** — add a dbt CI hook or sqlfluff rule that fails
      PRs referencing `public.*` outside `bases/` models. Mechanical
      implementation, but a one-time setup that prevents the rule from
      drifting.

Phases 1+ are out of scope here; they kick off only once Phase 0 closes. First
Phase 1 item is expected to be the **indicator inventory** — cataloguing the
top 20–30 indicators in active use across Tupaia dashboards and Tamanu reports,
which becomes the migration backlog.
