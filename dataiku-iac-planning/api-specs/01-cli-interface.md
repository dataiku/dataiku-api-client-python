# CLI Interface Specification

**Document Status:** Draft
**Last Updated:** 2025-11-23

---

## Table of Contents

1. [Overview](#overview)
2. [Command Structure](#command-structure)
3. [Core Commands](#core-commands)
4. [State Management Commands](#state-management-commands)
5. [Testing Commands](#testing-commands)
6. [Utility Commands](#utility-commands)
7. [Global Options](#global-options)
8. [Output Formats](#output-formats)
9. [Exit Codes](#exit-codes)

---

## Overview

### CLI Design Principles

1. **Intuitive:** Follow Terraform/kubectl conventions
2. **Consistent:** Same patterns across all commands
3. **Safe:** Require confirmation for destructive operations
4. **Helpful:** Provide suggestions and next steps
5. **Scriptable:** Machine-readable output formats

### Installation

```bash
# Via pip
$ pip install dataikuapi[iac]

# Verify installation
$ dataiku-iac version
Dataiku IaC v0.1.0
Python API v14.1.3

# Get help
$ dataiku-iac --help
$ dataiku-iac <command> --help
```

---

## Command Structure

```
dataiku-iac <command> [subcommand] [options] [arguments]
```

### Command Categories

```
Core Operations:
  init       Initialize new project
  plan       Preview changes
  apply      Apply changes
  destroy    Destroy resources

State Management:
  state      Manage state
  import     Import existing resources
  export     Export to configuration

Testing:
  test       Run tests
  validate   Validate configuration

Utilities:
  version    Show version
  config     Manage configuration
  login      Authenticate
```

---

## Core Commands

### `init` - Initialize Project

**Purpose:** Initialize new Dataiku IaC project

```bash
$ dataiku-iac init [OPTIONS]
```

**Options:**
```
--project-dir PATH    Directory to initialize (default: current)
--from-existing KEY   Import from existing Dataiku project
--template NAME       Use project template
--git                 Initialize Git repository
--remote URL          Configure remote state backend
```

**Examples:**

```bash
# Initialize new project
$ dataiku-iac init
Initializing Dataiku IaC project...
  ✓ Created .dataiku/
  ✓ Created projects/
  ✓ Created environments/
  ✓ Created .gitignore

Next steps:
  1. Edit .dataiku/config.yml to configure Dataiku connection
  2. Create project config in projects/my_project.yml
  3. Run: dataiku-iac plan --environment dev

# Initialize from existing Dataiku project
$ dataiku-iac init --from-existing CUSTOMER_ANALYTICS
Connecting to Dataiku...
Exporting project CUSTOMER_ANALYTICS...
  ✓ Exported 5 datasets
  ✓ Exported 12 recipes
  ✓ Exported 3 scenarios

Configuration saved to: projects/customer_analytics.yml

# Use template
$ dataiku-iac init --template ml-pipeline
Using template: ml-pipeline
  ✓ Created project structure
  ✓ Added example datasets
  ✓ Added example recipes
  ✓ Added training scenario

Edit projects/ml_pipeline.yml to customize.
```

**Output Structure:**
```
.
├── .dataiku/
│   ├── config.yml
│   ├── variables.yml
│   └── state/
├── projects/
│   └── example.yml
├── environments/
│   ├── dev.yml
│   └── prod.yml
├── recipes/
├── tests/
└── .gitignore
```

---

### `plan` - Preview Changes

**Purpose:** Show what changes will be made without executing them

```bash
$ dataiku-iac plan [OPTIONS]
```

**Options:**
```
--environment, -e ENV   Target environment (required)
--config-dir PATH       Configuration directory (default: current)
--out FILE              Save plan to file
--detailed              Show detailed diff
--json                  Output as JSON
--no-color              Disable colored output
```

**Examples:**

```bash
# Basic plan
$ dataiku-iac plan --environment prod

Dataiku IaC Plan

Environment: prod
Config: projects/customer_analytics.yml
Target: https://dataiku-prod.company.com

Refreshing state... Done.

Changes to be applied:

  + dataset.CUSTOMER_ANALYTICS.NEW_CUSTOMERS
      name: "NEW_CUSTOMERS"
      connection: "SNOWFLAKE_PROD"
      type: "sql"
      table: "new_customers"

  ~ recipe.CUSTOMER_ANALYTICS.prep_customers
      ~ code: "recipes/prep_customers.py"
        - line 45: old logic
        + line 45: new logic

  - dataset.CUSTOMER_ANALYTICS.OLD_TEMP_DATA
      (marked for deletion)

Plan: 1 to add, 1 to change, 1 to destroy.

⚠️  Warnings:
  - Deleting OLD_TEMP_DATA will lose data
  - NEW_CUSTOMERS has no data quality checks

✓ Validation passed:
  - All connections exist
  - No circular dependencies
  - Schemas are compatible

To apply this plan:
  dataiku-iac apply --environment prod

# Save plan for later
$ dataiku-iac plan -e prod --out plan.json
Plan saved to: plan.json

# Detailed diff
$ dataiku-iac plan -e prod --detailed
...
Recipe: prep_customers
  File: recipes/prep_customers.py

  @@ -42,7 +42,7 @@
   def process(df):
  -    # Old transformation
  -    df['value'] = df['value'] * 1.1
  +    # New transformation
  +    df['value'] = df['value'] * 1.2
       return df
...
```

---

### `apply` - Apply Changes

**Purpose:** Execute planned changes

```bash
$ dataiku-iac apply [OPTIONS]
```

**Options:**
```
--environment, -e ENV   Target environment (required)
--config-dir PATH       Configuration directory
--plan FILE             Use saved plan
--auto-approve          Skip confirmation prompt
--parallelism N         Number of parallel operations (default: 10)
--target RESOURCE       Apply only specific resource
--resume                Resume interrupted apply
--rollback              Rollback last apply
```

**Examples:**

```bash
# Interactive apply with confirmation
$ dataiku-iac apply -e prod

Dataiku IaC Apply

Environment: prod
Plan: 1 to add, 1 to change, 1 to destroy

Do you want to apply these changes?
  Only 'yes' will be accepted to approve.

  Enter a value: yes

Applying changes...

[1/3] Creating dataset NEW_CUSTOMERS... ✓ (2.3s)
[2/3] Updating recipe prep_customers... ✓ (1.1s)
[3/3] Deleting dataset OLD_TEMP_DATA... ✓ (0.5s)

Apply complete! Resources: 1 added, 1 changed, 1 destroyed.

State saved to: .dataiku/state/prod.state.json

Next steps:
  - Build datasets: dataiku-iac build --environment prod
  - Run tests: dataiku-iac test --environment prod

# Auto-approve (for CI/CD)
$ dataiku-iac apply -e prod --auto-approve

# Resume interrupted apply
$ dataiku-iac apply -e prod --resume
Resuming from checkpoint...
  Skipping completed: [1/3, 2/3]
  Retrying failed: [3/3] Deleting dataset...
  ✓ (0.4s)

# Apply specific resource only
$ dataiku-iac apply -e prod --target dataset.CUSTOMER_ANALYTICS.NEW_CUSTOMERS
```

**Error Handling:**

```bash
$ dataiku-iac apply -e prod

Applying changes...
[1/3] Creating dataset NEW_CUSTOMERS... ✓
[2/3] Updating recipe prep_customers... ✗

Error: Recipe update failed
  Connection 'SNOWFLAKE_PROD' not found

Apply failed at step 2/3.

Recovery options:
  1. Fix the issue and resume:
     dataiku-iac apply -e prod --resume

  2. Rollback changes:
     dataiku-iac apply -e prod --rollback

  3. View checkpoint:
     dataiku-iac state show-checkpoint

Checkpoint saved for recovery.
```

---

### `destroy` - Destroy Resources

**Purpose:** Remove resources from Dataiku

```bash
$ dataiku-iac destroy [OPTIONS]
```

**Options:**
```
--environment, -e ENV   Target environment
--target RESOURCE       Destroy specific resource
--keep-data             Keep dataset data when destroying
--force                 Skip confirmation
```

**Examples:**

```bash
# Destroy all resources
$ dataiku-iac destroy -e dev

⚠️  WARNING: This will destroy all resources in environment 'dev'

The following resources will be destroyed:
  - project.CUSTOMER_ANALYTICS
  - 5 datasets
  - 12 recipes
  - 3 scenarios

Data in managed datasets will be DELETED unless --keep-data is used.

Type 'destroy' to confirm: destroy

Destroying resources...
[1/20] Deleting scenario daily_refresh... ✓
[2/20] Deleting recipe prep_customers... ✓
...

Destroy complete! 20 resources destroyed.

# Destroy specific resource
$ dataiku-iac destroy -e dev --target dataset.CUSTOMER_ANALYTICS.TEMP_DATA

# Keep data when destroying
$ dataiku-iac destroy -e dev --keep-data
```

---

## State Management Commands

### `state` - Manage State

```bash
$ dataiku-iac state <subcommand> [OPTIONS]
```

**Subcommands:**

```bash
# List state resources
$ dataiku-iac state list -e prod
Projects: 1
  - CUSTOMER_ANALYTICS (deployed: 2025-01-15 10:30:00)

Datasets: 5
  - RAW_CUSTOMERS (healthy)
  - PREPARED_CUSTOMERS (healthy)
  - CUSTOMER_SUMMARY (healthy)
  - ORDERS (healthy)
  - TEMP_DATA (drifted)

Recipes: 12
  - prep_customers (healthy)
  - aggregate_metrics (healthy)
  ...

# Show specific resource
$ dataiku-iac state show dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
Resource: dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
Type: dataset
Status: healthy
Deployed: 2025-01-15 10:31:00 by alice@company.com
Config checksum: sha256:abc123...

Metadata:
  connection: SNOWFLAKE_PROD
  table: customers
  last_built: 2025-01-15 14:00:00
  row_count: 1,500,000

Dependencies: (none)

# Detect drift
$ dataiku-iac state drift -e prod

Drift Detection Report

Environment: prod
Synced at: 2025-01-15 14:30:00

Drifted Resources: 2
  ~ recipe.CUSTOMER_ANALYTICS.prep_customers
      code: MODIFIED (checksum mismatch)
      last_modified: 2025-01-15 13:00:00 by bob@company.com

  ~ dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
      connection: SNOWFLAKE_PROD → SNOWFLAKE_PROD_READ_REPLICA

Unmanaged Resources: 1
  ? dataset.CUSTOMER_ANALYTICS.TEMP_DEBUG
      created: 2025-01-15 14:00:00 by charlie@company.com

Recommendations:
  1. Import drift: dataiku-iac import prep_customers
  2. Or revert: dataiku-iac apply --auto-correct-drift

# Sync state with Dataiku
$ dataiku-iac state sync -e prod
Syncing state with Dataiku...
  ✓ Verified 18/20 resources
  ⚠️ 2 resources drifted
  ℹ️ 1 unmanaged resource found

State updated: .dataiku/state/prod.state.json

# Remove resource from state (doesn't delete from Dataiku)
$ dataiku-iac state rm dataset.CUSTOMER_ANALYTICS.TEMP_DATA
Removed from state: dataset.CUSTOMER_ANALYTICS.TEMP_DATA

Note: Resource still exists in Dataiku.
To delete from Dataiku: dataiku-iac destroy --target ...
```

---

### `import` - Import Existing Resources

```bash
$ dataiku-iac import [RESOURCE_TYPE] [RESOURCE_ID] [OPTIONS]
```

**Examples:**

```bash
# Import entire project
$ dataiku-iac import project CUSTOMER_ANALYTICS -e prod
Importing project CUSTOMER_ANALYTICS...
  ✓ Exported configuration to: projects/customer_analytics.yml
  ✓ Exported 5 datasets
  ✓ Exported 12 recipes
  ✓ Added to state

# Import specific dataset
$ dataiku-iac import dataset CUSTOMER_ANALYTICS.NEW_DATASET -e prod
Importing dataset NEW_DATASET...
  ✓ Added to: projects/customer_analytics.yml (under datasets)
  ✓ Added to state

Commit this change to Git to manage via IaC.

# Import and update existing config (merge)
$ dataiku-iac import recipe prep_customers -e prod --update-config
Dataset prep_customers has changed in Dataiku:
  - code modified
  - resources changed: 2G → 4G

Updated configuration:
  projects/customer_analytics.yml (recipe.prep_customers)
  recipes/prep_customers.py (code)

Review changes and commit to Git.
```

---

### `export` - Export to Configuration

```bash
$ dataiku-iac export [OPTIONS]
```

**Examples:**

```bash
# Export current Dataiku project to YAML
$ dataiku-iac export --project CUSTOMER_ANALYTICS -e prod --output ./config/
Exporting to configuration...
  ✓ projects/customer_analytics.yml
  ✓ recipes/prep_customers.py
  ✓ recipes/aggregate_metrics.sql

# Export as Python DSL
$ dataiku-iac export --project CUSTOMER_ANALYTICS -e prod --format python
Generated: projects/customer_analytics.py
```

---

## Testing Commands

### `test` - Run Tests

```bash
$ dataiku-iac test [OPTIONS]
```

**Options:**
```
--environment, -e ENV   Test environment
--pattern PATTERN       Test file pattern (default: test_*.py)
--verbose, -v           Verbose output
--junit-xml FILE        Output JUnit XML report
--coverage              Include coverage report
--fail-fast             Stop on first failure
```

**Examples:**

```bash
# Run all tests
$ dataiku-iac test -e test

Running tests for environment: test

test_customer_pipeline.py::test_raw_customers_schema ... ✓ (0.3s)
test_customer_pipeline.py::test_prep_recipe_execution ... ✓ (4.2s)
test_customer_pipeline.py::test_full_pipeline ... ✓ (12.5s)

3 passed in 17.0s

# Run specific test file
$ dataiku-iac test -e test --pattern test_customer*.py

# Generate JUnit XML for CI/CD
$ dataiku-iac test -e test --junit-xml test-results.xml
Tests complete. Report: test-results.xml

# Fail fast
$ dataiku-iac test -e test --fail-fast
```

---

### `validate` - Validate Configuration

```bash
$ dataiku-iac validate [OPTIONS]
```

**Examples:**

```bash
# Validate configuration
$ dataiku-iac validate -e prod

Validating configuration...

✓ YAML syntax valid
✓ Schema validation passed
✓ All variables resolved:
  - SNOWFLAKE_CONNECTION → SNOWFLAKE_PROD
  - PYTHON_ENV → python39_prod

✓ All connections exist in target environment
✓ All code environments exist
✓ No circular dependencies
✓ All dataset references valid

⚠️ Warnings (2):
  - dataset.NEW_CUSTOMERS: No data quality checks defined
  - recipe.prep_customers: High memory usage (16G)

Validation: PASSED (with warnings)

# Strict validation (warnings are errors)
$ dataiku-iac validate -e prod --strict
...
⚠️ Warnings found
Validation: FAILED
```

---

## Utility Commands

### `version` - Show Version

```bash
$ dataiku-iac version
Dataiku IaC: v0.1.0
Python API: v14.1.3
Python: 3.9.7

$ dataiku-iac version --json
{
  "iac_version": "0.1.0",
  "api_version": "14.1.3",
  "python_version": "3.9.7"
}
```

---

### `config` - Manage Configuration

```bash
# View current config
$ dataiku-iac config show
Configuration:
  config_dir: /path/to/project
  state_backend: hybrid
  remote_backend: s3://dataiku-iac-state/myorg/myproject

Environments:
  dev: https://dataiku-dev.company.com
  prod: https://dataiku-prod.company.com

# Set configuration value
$ dataiku-iac config set state_backend s3
Updated: state_backend = s3

# List environments
$ dataiku-iac config list-environments
dev    https://dataiku-dev.company.com
test   https://dataiku-test.company.com
prod   https://dataiku-prod.company.com
```

---

### `login` - Authenticate

```bash
# Interactive login
$ dataiku-iac login -e prod
Dataiku host: https://dataiku-prod.company.com
API key: ********

Testing connection... ✓
Credentials saved to: ~/.dataiku/credentials

# Use existing API key
$ dataiku-iac login -e prod --api-key $DATAIKU_API_KEY

# Use API key from file
$ dataiku-iac login -e prod --api-key-file ~/.secrets/dataiku.key
```

---

## Global Options

Available for all commands:

```
--config-dir PATH         Configuration directory (default: current)
--log-level LEVEL        Logging level (debug, info, warn, error)
--no-color               Disable colored output
--json                   Output as JSON (where applicable)
--help, -h               Show help
--version, -v            Show version
```

**Examples:**

```bash
# Debug logging
$ dataiku-iac plan -e prod --log-level debug

# JSON output
$ dataiku-iac plan -e prod --json > plan.json

# No color (for CI/CD)
$ dataiku-iac apply -e prod --no-color
```

---

## Output Formats

### Human-Readable (Default)

```
Dataiku IaC Plan

Environment: prod
Changes: 1 to add, 1 to change, 0 to destroy

  + dataset.CUSTOMER_ANALYTICS.NEW_CUSTOMERS
  ~ recipe.CUSTOMER_ANALYTICS.prep_customers

Plan: 1 to add, 1 to change, 0 to destroy
```

### JSON Format

```json
{
  "environment": "prod",
  "changes": {
    "add": 1,
    "change": 1,
    "destroy": 0
  },
  "actions": [
    {
      "action": "add",
      "resource_type": "dataset",
      "resource_id": "CUSTOMER_ANALYTICS.NEW_CUSTOMERS",
      "changes": {
        "name": "NEW_CUSTOMERS",
        "connection": "SNOWFLAKE_PROD"
      }
    },
    {
      "action": "change",
      "resource_type": "recipe",
      "resource_id": "CUSTOMER_ANALYTICS.prep_customers",
      "changes": {
        "code": "modified"
      }
    }
  ],
  "warnings": [],
  "validation": {
    "passed": true,
    "errors": []
  }
}
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage error (invalid options) |
| 3 | Validation failed |
| 4 | Authentication failed |
| 5 | Resource not found |
| 6 | State lock held |
| 7 | Plan has changes (for CI/CD) |
| 8 | Tests failed |

**Usage in CI/CD:**

```bash
# Check if plan has changes
dataiku-iac plan -e prod --check
exit_code=$?

if [ $exit_code -eq 7 ]; then
  echo "Changes detected, review required"
  exit 1
elif [ $exit_code -eq 0 ]; then
  echo "No changes, proceeding"
  exit 0
else
  echo "Error occurred"
  exit $exit_code
fi
```

---

## Summary

### Command Workflow

```
Development:
  dataiku-iac init
  dataiku-iac login -e dev
  (edit configuration)
  dataiku-iac validate -e dev
  dataiku-iac plan -e dev
  dataiku-iac apply -e dev
  dataiku-iac test -e dev

Production Deployment:
  git push
  (CI/CD runs:)
  dataiku-iac plan -e prod
  dataiku-iac validate -e prod --strict
  dataiku-iac test -e test
  (manual approval)
  dataiku-iac apply -e prod --auto-approve

State Management:
  dataiku-iac state drift -e prod
  dataiku-iac import (resources)
  dataiku-iac export --project PROJECT
```

---

**Document Version:** 0.1.0
**Status:** Draft for Review
**Next Review:** TBD
