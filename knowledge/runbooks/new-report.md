# Adding a New Report

Applies to `tamanu-source-dbt` and `tamanu-dbt-*` repos. `[parallel]` steps can
be delegated to separate agents.

## Where reports live

| Repo | SQL path | Config path | Variants |
|---|---|---|---|
| `tamanu-source-dbt` | `models/reports/sql/standard/<name>.sql` (+ `sensitive/sensitive-<name>.sql`) | `models/reports/config/standard/<name>.json` (+ `sensitive/...`) | standard / sensitive split — only here |
| `tamanu-dbt-<deployment>` | `models/reports/sql/<name>.sql` | `models/reports/config/<name>.json` | none — all reports assumed custom |

Steps below show paths using the `tamanu-source-dbt` convention; in
`tamanu-dbt-*` drop the `standard/` (or `sensitive/`) segment.

## Naming

| Type | Suffix | When |
|---|---|---|
| Line list | `<description>-line-list.sql` | One row per patient/encounter |
| Summary | `<description>-summary.sql` | Aggregated counts/metrics |
| Grouped summary | `<description>-summary-by-<grouping>.sql` | Aggregated + broken down |

Sensitive variants *(tamanu-source-dbt only)*: `sensitive-<name>.sql`.

## Production promotion

Reports ship to production via a **compiled SQL bundle** at each Tamanu release
(under `tamanu-source-dbt/compiled/v<version>/`). For customised deployments,
`tamanu-dbt-<deployment>` produces its own bundle.

What this means:

- **The bundle includes the full `ref()` chain.** Every upstream model becomes a
  view in production.
- **Production-safe SQL** — no Python models, valid against production schema,
  tractable as a view. Heavy work (window functions over all patients, multi-
  domain aggregation) belongs in a replica-only `metric__` consumed via Data
  Tables.
- **Env-aware materialisation** — upstream models materialise as views in the
  bundle (`reporting_*`) and `incremental` / `table` on the replica
  (`analytics_*`). See
  [`../standards/dbt-conventions.md`](../standards/dbt-conventions.md).
- **Pin packages** — `tamanu-dbt-<deployment>` pins `tamanu-source-dbt` to a
  specific tag, never a branch. The bundle is only reproducible if upstream is
  pinned.

Full architecture:
[`../architecture/data-architecture/production-promotion.md`](../architecture/data-architecture/production-promotion.md).

## Prerequisites

- `dbt deps` run; DB connection configured
- `report_translations_standard.csv` (or deployment-specific equivalent) accessible

---

## Steps

### 1. Find a reference report `[parallel with 2]`

```bash
# tamanu-source-dbt
ls models/reports/sql/standard/

# tamanu-dbt-<deployment>
ls models/reports/sql/
```

Pick a structurally similar existing report as a template.

### 2. Check translation coverage `[parallel with 1]`

```bash
grep -i "<label_name>" report_translations_standard.csv
```

Note missing labels — added in step 5.

### 3. Report SQL

Create the SQL at the per-repo path (see Where reports live above):

- `tamanu-source-dbt`: `models/reports/sql/standard/<name>.sql`
- `tamanu-dbt-<deployment>`: `models/reports/sql/<name>.sql`

Conventions:

- `{{ ref(...) }}` for all upstream — typically `ds__<dataset>`; `metric__`,
  `der__`, `can__` directly when natural. Never `source()` (D10)
- `{{ translate_label('field_name') }}` for user-facing column aliases
- `{{ to_user_selected_timezone(field) }}` for datetime fields
- `order by` allowed (reports only)
- Production-safe SQL (see Production promotion above)

Matching config at the equivalent path under `models/reports/config/`.

### 4. Sensitive variant *(tamanu-source-dbt only)*

Only create when the report includes encounters from sensitive facilities;
`standard/` excludes them, `sensitive/` includes them. `tamanu-dbt-*`
deployment repos don't carry this split — skip this step there.

`models/reports/sql/sensitive/sensitive-<name>.sql` +
`models/reports/config/sensitive/sensitive-<name>.json`.

If standard + sensitive share > ~10 lines of SELECT/WHERE logic, extract into
`macros/reports/<name>.sql` parameterised on `is_sensitive`:

```sql
-- standard
{{ <name>_report(is_sensitive=false) }}

-- sensitive
{{ <name>_report(is_sensitive=true) }}
```

Macro picks `ds__<name>` vs `ds__sensitive_<name>`. See
`encounter_summary_report`, `admissions_line_list_report` for examples.

### 5. Add missing translations

To `report_translations_standard.csv`:

- Sentence case (`"Patient name"`, not `"patient_name"` or `"Patient Name"`)
- Concept prefixes per
  [`../standards/tamanu-dbt-conventions.md` § Translation prefixes](../standards/tamanu-dbt-conventions.md#translation-prefixes)
  (`survey<SurveyID><Field>` for survey-bound fields, bare concept for generic
  labels)
- Don't include the auto-prefix `report.reporting.` in the CSV key

```bash
python scripts/generate_translation_macro.py
```

### 6. Validate `[parallel]`

```bash
python scripts/validate_report_configs.py
python scripts/check_translations.py

# tamanu-source-dbt
sqlfluff fix models/reports/sql/standard/<name>.sql
sqlfluff fix models/reports/sql/sensitive/sensitive-<name>.sql  # if applicable

# tamanu-dbt-<deployment>
sqlfluff fix models/reports/sql/<name>.sql
```

### 7. dbt tests

```bash
# tamanu-source-dbt with sensitive variant
dbt test --profiles-dir config --select <name> sensitive_<name>

# tamanu-dbt-<deployment>
dbt test --profiles-dir config --select <name>
```

### 8. Verify the report list

`list_tamanu_reports.md` is auto-generated — never edit it manually.

```bash
python scripts/list_tamanu_reports.py
```

---

## PR checklist

- [ ] Report SQL + config in the right directory
      (`standard/` for `tamanu-source-dbt`; directly under `models/reports/sql/`
      for `tamanu-dbt-*`)
- [ ] Sensitive variant in `sensitive/` *(tamanu-source-dbt only)* if the
      report includes sensitive facilities
- [ ] All new labels in translations CSV
- [ ] Translation macro regenerated if CSV changed
- [ ] `validate_report_configs.py` + `check_translations.py` pass
- [ ] `sqlfluff fix` applied
- [ ] `dbt test` passes on affected models
