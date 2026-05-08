# SDD Principles — Background Reading

This document captures the theory behind the spec-driven-development skill, for when a user asks "why are we doing it this way" or wants to ground the approach in industry practice.

## Core principles

1. **Spec is the source of truth.** Code derives from spec, not the other way round. When they disagree, the spec is correct and the code is wrong.

2. **Specs are versioned and reviewed like code.** They live in the repo, change via PR, and gate downstream work.

3. **Numbered clauses anchor traceability.** Every rule has an ID; code comments reference the ID; tests assert the ID. A reader can grep one ID and find rule + implementation + test.

4. **Acceptance criteria are testable.** Each AC maps to a runnable check. If you can't test it, the criterion isn't specified well enough.

5. **Open questions are first-class.** Unknowns are explicit, owned, and dated — not hidden in code TODOs.

## Why this fits data engineering

Data work has additional needs that map well to SDD:

- **Data contracts** — producer/consumer agreements about schema, grain, and freshness. The spec's input/output schemas are data contracts.
- **Lineage clarity** — explicit upstream/downstream sections force the spec author to think about impact.
- **Test-driven culture** — dbt and Great Expectations both reward explicit acceptance criteria; SDD provides them.
- **Multi-stakeholder communication** — specs let non-technical stakeholders (PMs, country partners) verify intent without reading SQL.

## Inspiration / further reading

- **Open Data Contract Standard (ODCS / bitol)** — https://bitol-io.github.io/open-data-contract-standard/ — the closest formal data spec standard. The skill adapts ODCS's spirit (contracts, structured fields) without binding to its YAML schema.
- **Specification by Example (Gojko Adzic)** — given/when/then style for behavioural specs.
- **Arc42** — architecture decision records and component specs, the model for this skill's "Identity" / "Lineage" / "Acceptance criteria" sections.

## Why we don't fully adopt ODCS

ODCS is YAML-first and oriented toward dataset contracts at the boundary between systems. Maui's specs need to cover pipelines, migrations, and dashboards too — wider than ODCS's scope. Markdown gives non-technical reviewers (PMs, country partners) easier access. The ID-anchoring convention (`BL-XXX`, `AC-XXX`, `OQ-XXX`, `DV-XXX`, `DQ-XXX`) is the Maui-specific layer that gives us code-level traceability across all artefact types — that's the part to defend if anyone proposes replacing this approach with a stricter ODCS adoption.

## When SDD is the wrong tool

- **Trivial fixes.** A null check or a typo correction does not warrant a spec.
- **Hotfixes.** Time-to-fix > spec value.
- **Throwaway exploration.** Notebooks, scratch SQL, one-off "let me see what's in this table" queries.

A useful test: would a teammate reading the code in six months know *why* it does what it does? If yes, no spec needed. If no, spec it.
