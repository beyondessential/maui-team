# Tamanu dbt Project Setup Guide

## Prerequisites

1. **[uv](https://docs.astral.sh/uv/)** installed on your system
2. **PostgreSQL** database access to Tamanu instance
3. **Git** for version control

## Installation Steps

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd <project-directory>
uv sync
```

### 2. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your database credentials
```

### 3. Install dbt Dependencies

```bash
# Install dbt packages
dbt deps

# Test database connection
dbt debug
```

### 4. Project Customisation

Update the following files for your specific project:

#### pyproject.toml
- `name`: Update to your project name
- `version`: Update to match your Tamanu version

#### dbt_project.yml
- `name`: Update to your project name (must match `pyproject.toml`)
- `profile`: Update to match your project name

#### config/profiles.yml
- Profile name: Update to match your project name
- `target`: Update to your environment name (e.g., dev, staging, prod)

#### packages.yml
- `revision`: Update to match your Tamanu version (e.g., "2.32.0")
- Use specific version tags instead of "dev" branch for production deployments

#### README.md
- Update the title and description to reflect the deployment (project name, country/region, Tamanu instance)
- Remove the template boilerplate once the project-specific content is in place

### 5. Generate Survey Models

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/generate_survey_models.py
```

### 6. Build Reporting Assets

```bash
uv run python dbt_packages/tamanu_source_dbt/scripts/build_reporting_assets.py
```

This script:
- Cleans and rebuilds dbt dependencies
- Runs dbt models for the specified target
- Generates documentation
- Compiles models
- Creates reporting schema SQL files
- Generates project reports

### 7. Build and Test

```bash
dbt run
dbt docs generate
dbt docs serve
```

## Available Scripts

From the `tamanu-source-dbt` package:

- `uv run python dbt_packages/tamanu_source_dbt/scripts/generate_survey_models.py`
- `uv run python dbt_packages/tamanu_source_dbt/scripts/list_tamanu_reports.py`
- `uv run python dbt_packages/tamanu_source_dbt/scripts/build_reporting_assets.py`

## Project Structure

```
├── models/
│   ├── datasets/        # Flattened models for end users
│   ├── intermediate/    # Multi-table joins (ephemeral)
│   ├── reports/         # Final reporting models
│   └── surveys/         # Survey-specific models
├── config/
│   └── profiles.yml     # Database connection configuration
├── dbt_packages/        # External dependencies (auto-generated)
├── analyses/            # Ad-hoc SQL analyses
├── macros/              # Reusable SQL macros
├── seeds/               # Static reference data
├── snapshots/           # Point-in-time data snapshots
└── tests/               # Data quality tests
```

## Development Workflow

1. Create custom models in the appropriate `models/` subdirectory
2. Test models with `dbt run --select model_name`
3. Document models using `schema.yml` files
4. Generate documentation with `dbt docs generate`
5. Commit changes following the git conventions

## Troubleshooting

### Common Issues

1. **Connection Error**: Verify environment variables in `.env`
2. **Package Installation Failed**: Check internet connection and GitHub access
3. **Model Compilation Error**: Verify SQL syntax and model dependencies

### Getting Help

- [dbt documentation](https://docs.getdbt.com/)
- Review the `tamanu-source-dbt` package documentation
- Contact your project administrator for database access issues
