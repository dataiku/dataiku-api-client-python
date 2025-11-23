# Simple Project Example

This is a minimal example of a Dataiku IaC project structure.

## Project Structure

```
simple-project/
├── README.md                      # This file
├── .dataiku/
│   ├── config.yml                # IaC configuration
│   └── variables.yml             # Shared variables
├── projects/
│   └── hello_dataiku.yml        # Project configuration
├── environments/
│   ├── dev.yml                  # Development environment
│   └── prod.yml                 # Production environment
├── recipes/
│   └── prep_data.py             # Python recipe code
└── tests/
    └── test_hello_pipeline.py   # Pipeline tests
```

## Quick Start

### 1. Configure Connection

Edit `.dataiku/config.yml` and add your Dataiku connection details:

```yaml
dataiku:
  dev:
    host: https://your-dataiku-dev.com
    api_key_file: ~/.dataiku/dev.key
  prod:
    host: https://your-dataiku-prod.com
    api_key_file: ~/.dataiku/prod.key
```

### 2. Plan Changes

```bash
dataiku-iac plan --environment dev
```

### 3. Apply to Development

```bash
dataiku-iac apply --environment dev
```

### 4. Run Tests

```bash
dataiku-iac test --environment dev
```

### 5. Deploy to Production

```bash
dataiku-iac plan --environment prod
dataiku-iac apply --environment prod
```

## What This Example Includes

- **1 Project:** HELLO_DATAIKU
- **2 Datasets:** RAW_DATA (SQL), PREPARED_DATA (managed)
- **1 Recipe:** prep_data (Python)
- **1 Scenario:** daily_refresh
- **Tests:** Schema and pipeline tests

## Learning Path

1. **Review** `projects/hello_dataiku.yml` to understand config format
2. **Check** `environments/*.yml` to see environment-specific variables
3. **Look at** `recipes/prep_data.py` to see recipe code
4. **Read** `tests/test_hello_pipeline.py` to understand testing

## Next Steps

After understanding this example:
- Check out `ml-pipeline/` for ML workflow example
- See `multi-env/` for complex multi-environment setup
- Review `ci-cd-templates/` for GitHub Actions/GitLab CI examples
