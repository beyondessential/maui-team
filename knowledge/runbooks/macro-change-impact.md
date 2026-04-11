# Runbook: Macro Change Impact Analysis

Use this runbook when adding a new macro that should replace an existing pattern across
models, or when modifying an existing macro in a way that may affect downstream behaviour.

Steps marked **[parallel]** can be delegated to separate agents running simultaneously.

---

## Steps

### 1. Find all affected models **[parallel]**

Run these searches simultaneously to map the full scope before touching any files:

```bash
# Models using the macro directly
grep -r "{{ macro_name" models/ macros/

# Models using the pattern the macro replaces (if rolling out a new macro)
grep -r "<old_pattern>" models/

# Check if the macro is also used in tamanu-dbt-* repos via the package
grep -r "{{ macro_name" dbt_packages/ 2>/dev/null || true
```

Compile the full list of files that need updating before proceeding.

### 2. Categorise affected models **[parallel]**

Once you have the file list, split the review across model layers simultaneously:

```
Agent A → check affected base models: does the change affect filtering logic?
Agent B → check affected dataset/intermediate models: does it change column outputs?
Agent C → check affected report models: does it change user-facing output?
```

This reveals whether the change is isolated to one layer or cascades through the DAG.

---

### 3. Update models

Work through the file list from step 1, applying the change consistently.

If rolling out a new macro to replace a pattern:
- Replace every instance of the old pattern with the new macro call
- Do not mix old and new patterns within the same file
- Apply `sqlfluff fix` to each file after editing

If modifying an existing macro:
- Update `macros/<file>.sql`
- Verify callsites still pass correct arguments — check macro signature changes

### 4. Run dbt tests on affected models

```bash
dbt test --profiles-dir config --select <affected_model_1> <affected_model_2> ...
```

For a broad rollout, test by tag or path:

```bash
dbt test --profiles-dir config --select models/reports/
```

### 5. Check deployment repo impact

If this repo is `tamanu-source-dbt`, the macro change will propagate to all
`tamanu-dbt-*` repos on their next `dbt deps` run.

- Note the impact in the PR description
- If the macro change breaks backward compatibility, coordinate with deployment repo
  maintainers before merging

Check which deployment repos are registered:

```bash
cat .github/deployment-repos.yml
```

---

## Checklist before opening a PR

- [ ] Full list of affected models compiled before starting edits
- [ ] All instances of old pattern replaced (no mixed usage)
- [ ] `sqlfluff fix` applied to all edited files
- [ ] `dbt test` passes on all affected models
- [ ] PR description notes impact on `tamanu-dbt-*` repos (if applicable)
- [ ] Unit tests added or updated if the macro logic change affects testable behaviour
