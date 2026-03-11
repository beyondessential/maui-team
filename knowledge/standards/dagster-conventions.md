# Dagster Conventions

## Assets

- Name assets using `snake_case` nouns that describe the data they produce, not the operation
- Group related assets using `AssetGroup` or `@asset(group_name=...)`
- Use `key_prefix` to namespace assets by domain or source system
- Prefer software-defined assets (SDAs) over op-based jobs for new pipelines

## Asset dependencies

- Declare dependencies explicitly via function parameters (Dagster resolves the graph)
- Avoid implicit dependencies through shared I/O side effects
- Use `AssetIn` for non-default input configuration (partitions, key overrides)

## Partitioning

- Use partitioned assets for incremental data loads
- Define partition definitions at the asset level, not the job level
- Handle missing partitions gracefully — check upstream data availability before materialising

## Resources

- Define shared connections (databases, APIs, cloud clients) as resources
- Inject resources via `@asset(required_resource_keys=...)` or typed parameters
- Do not instantiate clients inside asset functions — always use resources

## Jobs

- Define jobs to group related assets for scheduling or manual execution
- Use `define_asset_job` for asset-based jobs
- Name jobs descriptively: `<domain>_<frequency>_job` (e.g. `tamanu_daily_job`)

## Sensors and schedules

- Use schedules for time-based triggers; use sensors for event-based triggers
- Keep sensor evaluation functions lightweight — do not perform heavy computation in the sensor body
- Set appropriate `minimum_interval_seconds` to avoid polling overhead

## Ops (legacy / non-asset pipelines)

- Prefer assets for new work; ops for cases where asset semantics don't fit
- Keep ops single-purpose; compose with graphs
- Use `Out` and `In` types explicitly

## Naming conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Assets | `snake_case` noun | `patient_encounters` |
| Jobs | `snake_case` with `_job` suffix | `tamanu_daily_job` |
| Schedules | `snake_case` with `_schedule` suffix | `tamanu_daily_schedule` |
| Sensors | `snake_case` with `_sensor` suffix | `s3_arrival_sensor` |
| Resources | `snake_case` noun | `postgres_resource` |

## Logging

- Keep log messages concise: `context.log.info("Fetched 1234 records")` not verbose narratives
- Mask secrets in log output: `key[:4] + "****"`
- Never log raw credentials, tokens, or PII

## Project-specific conventions

Add repo-specific asset groupings, resource configurations, or partition strategies in the repo's `AGENT.md`.
