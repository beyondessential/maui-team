# Runbook: Adding a New Report

Applies to `tamanu-source-dbt` and `tamanu-dbt-*` repos. Follow steps in order; steps
marked **[parallel]** can be delegated to separate agents running simultaneously.

## Prerequisites

- A working dbt environment (`dbt deps` run, database connection configured)
- Access to `report_translations_standard.csv` (or the deployment-specific translations CSV)

---

## Steps

### 1. Find a reference report **[parallel with step 2]**

Search `models/reports/sql/standard/` for an existing report that is structurally similar
to the one you are adding (same entity type, similar columns). Use it as a template.

```bash
ls models/reports/sql/standard/
```

### 2. Check translation coverage **[parallel with step 1]**

Identify every user-facing column label the new report will expose. Check whether each
already exists in `report_translations_standard.csv`.

```bash
grep -i "<label_name>" report_translations_standard.csv
```

Note any labels that are missing — you will add them in step 6.

---

### 3. Create the standard report

Create the SQL model at `models/reports/sql/standard/<name>-line-list.sql`.

- Use `{{ ref('ds__<dataset>') }}` — never `source()` directly
- Apply `{{ translate_label('field_name') }}` for all user-facing column aliases
- Apply `{{ to_user_selected_timezone(field) }}` for all datetime fields
- Include `order by` (reports layer allows it; bases and datasets do not)

Create the matching config at `models/reports/config/<name>-line-list.json`.

### 4. Create the sensitive report

Create `models/reports/sql/sensitive/sensitive-<name>-line-list.sql` and
`models/reports/config/sensitive-<name>-line-list.json`.

The sensitive version extends the standard report with personally identifiable or
clinically sensitive columns. It must include everything the standard report includes
plus the additional sensitive fields.

### 5. Add missing translations

If step 2 found missing labels, add them to `report_translations_standard.csv`:

- Follow sentence casing: `"Patient name"`, not `"patient_name"` or `"Patient Name"`
- Use concept prefixes: `patient_name`, not just `name`
- The macro auto-prefixes with `report.reporting.` — do not include this in the CSV key

Then regenerate the translation macro:

```bash
python scripts/generate_translation_macro.py
```

---

### 6. Validate **[parallel checks]**

Run these checks independently:

```bash
# Validate report config JSON structure
python scripts/validate_report_configs.py

# Check all translation labels resolve
python scripts/check_translations.py

# Lint SQL
sqlfluff fix models/reports/sql/standard/<name>-line-list.sql
sqlfluff fix models/reports/sql/sensitive/sensitive-<name>-line-list.sql
```

### 7. Run dbt tests

```bash
dbt test --profiles-dir config --select <name>_line_list sensitive_<name>_line_list
```

### 8. Verify the report list

`list_tamanu_reports.md` is auto-generated — do not edit it manually. Confirm the new
reports appear correctly:

```bash
python scripts/list_tamanu_reports.py
```

---

## Checklist before opening a PR

- [ ] Standard report SQL + config created
- [ ] Sensitive report SQL + config created
- [ ] All new labels added to translations CSV
- [ ] Translation macro regenerated (if CSV changed)
- [ ] `validate_report_configs.py` passes
- [ ] `check_translations.py` passes
- [ ] `sqlfluff fix` applied
- [ ] `dbt test` passes on affected models
