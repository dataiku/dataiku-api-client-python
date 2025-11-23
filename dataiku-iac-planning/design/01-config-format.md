# Configuration Format Design

**Document Status:** Draft
**Last Updated:** 2025-11-23
**Dependencies:** architecture/01-overview.md

---

## Table of Contents

1. [Overview](#overview)
2. [YAML Format](#yaml-format)
3. [Python DSL Format](#python-dsl-format)
4. [Variable Substitution](#variable-substitution)
5. [Validation Rules](#validation-rules)
6. [Best Practices](#best-practices)

---

## Overview

### Design Principles

1. **Declarative:** Describe desired state, not steps to achieve it
2. **Human-readable:** Easy to review in PRs
3. **Version-controllable:** Works well with Git
4. **Type-safe:** Validate before execution
5. **Flexible:** Support both YAML and Python

### Format Comparison

| Aspect | YAML | Python DSL |
|--------|------|------------|
| **Simplicity** | ✅ Very simple | ⚠️ Requires Python knowledge |
| **Expressiveness** | ⚠️ Limited logic | ✅ Full programming language |
| **Validation** | ✅ Schema-based | ✅ Type hints |
| **IDE Support** | ⚠️ Basic | ✅ Full autocomplete |
| **Learning Curve** | ✅ Low | ⚠️ Medium |
| **Use Case** | Simple projects | Complex logic |

---

## YAML Format

### Project Configuration

```yaml
# projects/customer_analytics.yml

# Metadata
metadata:
  version: "1.0"
  description: "Customer analytics pipeline with churn prediction"
  owner: data_team
  tags:
    - customer
    - analytics
    - production

# Project definition
project:
  key: CUSTOMER_ANALYTICS
  name: Customer Analytics Platform
  description: Customer segmentation and churn prediction

  settings:
    # Git integration
    git:
      enabled: true
      remote: git@github.com:company/customer-analytics.git

    # Access control
    permissions:
      - group: data_engineers
        role: write
      - group: data_scientists
        role: read

# Datasets
datasets:
  # SQL dataset
  - name: RAW_CUSTOMERS
    type: sql
    connection: ${SNOWFLAKE_CONNECTION}
    params:
      schema: PUBLIC
      table: customers
      mode: table

    # Optional: Schema definition
    schema:
      columns:
        - name: customer_id
          type: bigint
          nullable: false
        - name: name
          type: varchar(255)
        - name: email
          type: varchar(255)
        - name: created_at
          type: timestamp

    # Optional: Data quality checks
    checks:
      - type: not_null
        columns: [customer_id, email]
      - type: unique
        columns: [customer_id]
      - type: freshness
        column: created_at
        max_age_hours: 24

  # Managed dataset
  - name: PREPARED_CUSTOMERS
    type: managed
    connection: ${STORAGE_CONNECTION}
    format: parquet
    params:
      partition_by: [created_date]

# Recipes
recipes:
  # Python recipe
  - name: prep_customers
    type: python
    inputs:
      - RAW_CUSTOMERS
    outputs:
      - PREPARED_CUSTOMERS
    code_file: recipes/prep_customers.py
    code_env: ${PYTHON_ENV}

    # Optional: Resource limits
    resources:
      memory: 4G
      cores: 2

  # SQL recipe
  - name: customer_aggregates
    type: sql
    inputs:
      - PREPARED_CUSTOMERS
    outputs:
      - CUSTOMER_SUMMARY
    sql_file: recipes/customer_aggregates.sql
    connection: ${SNOWFLAKE_CONNECTION}

  # Visual recipe (join)
  - name: join_customers_orders
    type: join
    inputs:
      - dataset: PREPARED_CUSTOMERS
        alias: c
      - dataset: RAW_ORDERS
        alias: o
    output: CUSTOMER_ORDERS
    join_config:
      type: left
      conditions:
        - left: c.customer_id
          right: o.customer_id
      select:
        - c.*
        - o.order_total
        - o.order_date

# Scenarios
scenarios:
  - name: daily_refresh
    type: step_based
    description: Daily customer data refresh

    triggers:
      - type: schedule
        cron: "0 2 * * *"
        timezone: UTC
      - type: manual

    steps:
      - type: build_dataset
        name: build_raw
        dataset: RAW_CUSTOMERS
        partition: ${TODAY}

      - type: run_recipe
        name: prep_data
        recipe: prep_customers

      - type: build_dataset
        name: build_prepared
        dataset: PREPARED_CUSTOMERS
        partition: ${TODAY}

      - type: conditional
        name: check_row_count
        condition: "dataset_row_count('PREPARED_CUSTOMERS') > 1000"
        on_success:
          - type: notification
            channel: ${NOTIFICATION_CHANNEL}
            message: "Daily refresh complete: {{row_count}} customers"
        on_failure:
          - type: notification
            channel: ${ALERT_CHANNEL}
            message: "⚠️ Daily refresh failed: insufficient data"
            severity: error

# ML Models
models:
  - name: churn_prediction
    type: prediction
    training_dataset: CUSTOMER_FEATURES
    target_column: churned
    prediction_type: binary_classification

    algorithms:
      - random_forest
      - xgboost
      - logistic_regression

    features:
      mode: auto
      # Or explicit feature list
      # columns: [tenure_days, total_spend, ...]

    deployment:
      activate_model: true
      deploy_to_flow: true

# Dashboards
dashboards:
  - name: customer_insights
    type: standard
    pages:
      - name: Overview
        tiles:
          - type: chart
            dataset: CUSTOMER_SUMMARY
            chart_type: bar
            x: customer_segment
            y: total_revenue

          - type: metric
            dataset: CUSTOMER_SUMMARY
            aggregation: count
            label: "Total Customers"
```

### Environment Configuration

```yaml
# environments/dev.yml

environment:
  name: dev
  dataiku_host: https://dataiku-dev.company.com

variables:
  # Connections
  SNOWFLAKE_CONNECTION: SNOWFLAKE_DEV
  STORAGE_CONNECTION: S3_DEV_BUCKET

  # Code environments
  PYTHON_ENV: python39_dev

  # Notifications
  NOTIFICATION_CHANNEL: slack_dev_channel
  ALERT_CHANNEL: slack_dev_alerts

  # Dynamic variables
  TODAY: ${date:YYYY-MM-DD}
  YESTERDAY: ${date:YYYY-MM-DD:-1d}

# Override settings for dev
overrides:
  # Use smaller datasets
  datasets:
    RAW_CUSTOMERS:
      params:
        sampling: first_records
        sample_size: 10000

  # Disable expensive operations
  scenarios:
    daily_refresh:
      triggers: []  # Manual only in dev

  # Use cheaper resources
  recipes:
    "*":  # All recipes
      resources:
        memory: 2G
        cores: 1
```

```yaml
# environments/prod.yml

environment:
  name: prod
  dataiku_host: https://dataiku-prod.company.com

variables:
  SNOWFLAKE_CONNECTION: SNOWFLAKE_PROD
  STORAGE_CONNECTION: S3_PROD_BUCKET
  PYTHON_ENV: python39_prod
  NOTIFICATION_CHANNEL: slack_prod_notifications
  ALERT_CHANNEL: pagerduty_prod_alerts

# Prod-specific settings
settings:
  # Require tests to pass
  require_tests: true

  # Govern approval required
  require_approval: true

  # No auto-correct drift (manual review)
  drift_policy: alert_only
```

---

## Python DSL Format

### Equivalent Python Configuration

```python
# projects/customer_analytics.py

from dataikuapi.iac import (
    Project, Dataset, Recipe, Scenario,
    SQLDataset, ManagedDataset,
    PythonRecipe, SQLRecipe, JoinRecipe,
    StepBasedScenario, ScheduleTrigger,
    BuildDatasetStep, RunRecipeStep, ConditionalStep
)

# Create project
project = Project(
    key="CUSTOMER_ANALYTICS",
    name="Customer Analytics Platform",
    description="Customer segmentation and churn prediction",
    settings={
        "git": {
            "enabled": True,
            "remote": "git@github.com:company/customer-analytics.git"
        }
    }
)

# Define datasets
raw_customers = SQLDataset(
    name="RAW_CUSTOMERS",
    connection="${SNOWFLAKE_CONNECTION}",
    schema="PUBLIC",
    table="customers",
    schema_definition=[
        Column("customer_id", "bigint", nullable=False),
        Column("name", "varchar(255)"),
        Column("email", "varchar(255)"),
        Column("created_at", "timestamp")
    ],
    checks=[
        NotNullCheck(columns=["customer_id", "email"]),
        UniqueCheck(columns=["customer_id"]),
        FreshnessCheck(column="created_at", max_age_hours=24)
    ]
)

prepared_customers = ManagedDataset(
    name="PREPARED_CUSTOMERS",
    connection="${STORAGE_CONNECTION}",
    format="parquet",
    partition_by=["created_date"]
)

# Define recipes
prep_recipe = PythonRecipe(
    name="prep_customers",
    inputs=[raw_customers],
    outputs=[prepared_customers],
    code_file="recipes/prep_customers.py",
    code_env="${PYTHON_ENV}",
    resources={"memory": "4G", "cores": 2}
)

# Join recipe using builder pattern
join_recipe = (
    JoinRecipe("join_customers_orders")
    .left_input(prepared_customers, alias="c")
    .right_input("RAW_ORDERS", alias="o")
    .on("c.customer_id = o.customer_id")
    .select("c.*", "o.order_total", "o.order_date")
    .output("CUSTOMER_ORDERS")
    .build()
)

# Define scenario
daily_refresh = StepBasedScenario(
    name="daily_refresh",
    description="Daily customer data refresh",
    triggers=[
        ScheduleTrigger(cron="0 2 * * *", timezone="UTC")
    ],
    steps=[
        BuildDatasetStep(
            name="build_raw",
            dataset=raw_customers,
            partition="${TODAY}"
        ),
        RunRecipeStep(
            name="prep_data",
            recipe=prep_recipe
        ),
        BuildDatasetStep(
            name="build_prepared",
            dataset=prepared_customers,
            partition="${TODAY}"
        ),
        ConditionalStep(
            name="check_row_count",
            condition=lambda: dataset_row_count('PREPARED_CUSTOMERS') > 1000,
            on_success=[
                NotificationStep(
                    channel="${NOTIFICATION_CHANNEL}",
                    message="Daily refresh complete: {row_count} customers"
                )
            ],
            on_failure=[
                NotificationStep(
                    channel="${ALERT_CHANNEL}",
                    message="⚠️ Daily refresh failed: insufficient data",
                    severity="error"
                )
            ]
        )
    ]
)

# Add everything to project
project.add_datasets([raw_customers, prepared_customers])
project.add_recipes([prep_recipe, join_recipe])
project.add_scenarios([daily_refresh])

# Export configuration
if __name__ == "__main__":
    project.export("projects/customer_analytics.yml")
```

### Python DSL Advantages

**1. Type Safety:**
```python
# IDE catches errors at write time
dataset = SQLDataset(
    name="CUSTOMERS",
    connection="SNOWFLAKE",  # IDE knows this is required
    typo_field="value"  # IDE shows error: unknown field
)
```

**2. Reusable Components:**
```python
# Define reusable pattern
def create_etl_pattern(source_table: str, target_name: str):
    """Create standard ETL pattern"""
    raw = SQLDataset(name=f"RAW_{target_name}", table=source_table, ...)
    prepared = ManagedDataset(name=f"PREPARED_{target_name}", ...)
    recipe = PythonRecipe(
        name=f"prep_{target_name.lower()}",
        inputs=[raw],
        outputs=[prepared],
        code_template="standard_prep.py"
    )
    return [raw, prepared, recipe]

# Use pattern multiple times
for table in ["CUSTOMERS", "ORDERS", "PRODUCTS"]:
    project.add(*create_etl_pattern(table, table))
```

**3. Complex Logic:**
```python
# Conditional configuration based on environment
if environment == "prod":
    # Production: use large cluster
    recipe.set_resources(memory="16G", cores=8)
    recipe.set_cluster("prod_large_cluster")
else:
    # Dev: use small cluster
    recipe.set_resources(memory="4G", cores=2)
    recipe.set_cluster("dev_small_cluster")

# Dynamic dataset creation
for region in ["US", "EU", "APAC"]:
    project.add_dataset(
        SQLDataset(
            name=f"CUSTOMERS_{region}",
            table=f"customers_{region.lower()}",
            connection=f"SNOWFLAKE_{region}"
        )
    )
```

**4. Validation at Definition Time:**
```python
from dataikuapi.iac.validation import validate_project

# Validate before exporting
validation_result = validate_project(project)

if not validation_result.is_valid():
    for error in validation_result.errors:
        print(f"❌ {error.message} in {error.location}")
    sys.exit(1)

# Export only if valid
project.export("projects/customer_analytics.yml")
```

---

## Variable Substitution

### Variable Syntax

```yaml
# Simple variable
connection: ${SNOWFLAKE_CONNECTION}

# With default value
connection: ${SNOWFLAKE_CONNECTION:SNOWFLAKE_DEV}

# Nested variables
connection: ${SNOWFLAKE_${REGION}_CONNECTION}

# Built-in functions
today: ${date:YYYY-MM-DD}
yesterday: ${date:YYYY-MM-DD:-1d}
timestamp: ${datetime:YYYY-MM-DD_HH-mm-ss}
uuid: ${uuid}
git_commit: ${git:commit}
git_branch: ${git:branch}
user: ${env:USER}
```

### Variable Resolution Order

1. **Environment-specific variables** (environments/{env}.yml)
2. **Global variables** (.dataiku/variables.yml)
3. **OS environment variables** (os.environ)
4. **Default values** (if specified with :default)
5. **Error** (if not found and no default)

### Example:

```yaml
# Global variables (.dataiku/variables.yml)
variables:
  NOTIFICATION_CHANNEL: slack_default

# Dev environment (environments/dev.yml)
variables:
  SNOWFLAKE_CONNECTION: SNOWFLAKE_DEV
  # NOTIFICATION_CHANNEL not defined, will use global

# In config:
datasets:
  - name: CUSTOMERS
    connection: ${SNOWFLAKE_CONNECTION}  # Uses: SNOWFLAKE_DEV

scenarios:
  - name: daily_refresh
    steps:
      - type: notification
        channel: ${NOTIFICATION_CHANNEL}  # Uses: slack_default (global)
```

---

## Validation Rules

### Schema Validation

All YAML files are validated against JSON Schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["project"],
  "properties": {
    "project": {
      "type": "object",
      "required": ["key", "name"],
      "properties": {
        "key": {
          "type": "string",
          "pattern": "^[A-Z][A-Z0-9_]*$",
          "maxLength": 100
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        }
      }
    },
    "datasets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "type"],
        "properties": {
          "name": {
            "type": "string",
            "pattern": "^[A-Z][A-Z0-9_]*$"
          },
          "type": {
            "enum": ["sql", "managed", "uploaded", "stream"]
          }
        }
      }
    }
  }
}
```

### Semantic Validation

Beyond schema, validate business logic:

```python
class ConfigValidator:
    def validate(self, config: Configuration) -> List[ValidationError]:
        errors = []

        # Check for circular dependencies
        if self._has_circular_deps(config):
            errors.append(ValidationError(
                "Circular dependency detected in recipe graph"
            ))

        # Verify all references exist
        for recipe in config.recipes:
            for input_name in recipe.inputs:
                if not config.has_dataset(input_name):
                    errors.append(ValidationError(
                        f"Recipe '{recipe.name}' references unknown dataset '{input_name}'"
                    ))

        # Check naming conventions
        for dataset in config.datasets:
            if not dataset.name.isupper():
                errors.append(ValidationError(
                    f"Dataset '{dataset.name}' should be UPPERCASE"
                ))

        # Validate connections exist in target environment
        for dataset in config.datasets:
            connection = config.resolve_variable(dataset.connection)
            if not self._connection_exists(connection):
                errors.append(ValidationError(
                    f"Connection '{connection}' not found in target environment"
                ))

        return errors
```

---

## Best Practices

### 1. Naming Conventions

```yaml
# ✅ GOOD: Uppercase with underscores
datasets:
  - name: RAW_CUSTOMERS
  - name: PREPARED_CUSTOMERS_V2

recipes:
  - name: prep_customers  # Lowercase for recipes
  - name: aggregate_metrics

scenarios:
  - name: daily_refresh
  - name: hourly_sync

# ❌ BAD: Inconsistent casing
datasets:
  - name: rawCustomers  # camelCase
  - name: prepared-customers  # kebab-case
```

### 2. File Organization

```
my-dataiku-project/
├── projects/
│   ├── customer_analytics.yml  # One file per project
│   └── sales_reporting.yml
│
├── recipes/
│   ├── prep_customers.py  # Code referenced from config
│   ├── prep_orders.py
│   └── customer_aggregates.sql
│
├── environments/
│   ├── dev.yml  # Environment-specific overrides
│   ├── test.yml
│   └── prod.yml
│
├── tests/
│   ├── test_customer_pipeline.py
│   └── fixtures/
│       └── test_customers.csv
│
└── .dataiku/
    ├── config.yml  # Global IaC config
    ├── variables.yml  # Shared variables
    └── state/  # State files (git-ignored)
```

### 3. Use Variables for Environment Differences

```yaml
# ✅ GOOD: Environment-agnostic config
datasets:
  - name: RAW_CUSTOMERS
    connection: ${SNOWFLAKE_CONNECTION}  # Different per environment

# ❌ BAD: Hardcoded environment
datasets:
  - name: RAW_CUSTOMERS
    connection: SNOWFLAKE_DEV  # Won't work in prod
```

### 4. Document Complex Logic

```yaml
# ✅ GOOD: Explain non-obvious configuration
datasets:
  - name: CUSTOMER_SUMMARY
    type: managed
    format: parquet
    params:
      # Partition by month for efficient querying
      # We query by month 80% of the time
      partition_by: [year, month]

      # Snappy compression balances speed and size
      compression: snappy

# ❌ BAD: No context
datasets:
  - name: CUSTOMER_SUMMARY
    type: managed
    format: parquet
    params:
      partition_by: [year, month]
      compression: snappy
```

### 5. Use Separate Files for Large Configs

```yaml
# projects/customer_analytics.yml
project:
  key: CUSTOMER_ANALYTICS
  name: Customer Analytics

# Import from other files
datasets:
  $include: datasets/customer_datasets.yml

recipes:
  $include: recipes/customer_recipes.yml

scenarios:
  $include: scenarios/customer_scenarios.yml
```

---

## Summary

### Format Decision Matrix

| Use Case | Recommended Format | Why |
|----------|-------------------|-----|
| Simple projects (< 10 resources) | YAML | Readable, low learning curve |
| Complex projects (> 50 resources) | Python DSL | Reusability, type safety |
| Team with Python expertise | Python DSL | Leverage existing skills |
| Mixed skill levels | YAML | Accessible to all |
| Need dynamic logic | Python DSL | Full programming capabilities |
| Version control / PR reviews | YAML | Better diff readability |

### Hybrid Approach

**Best of both worlds:**

1. **Define in Python** (for type safety, reusability)
2. **Export to YAML** (for version control, review)
3. **Commit YAML to Git** (source of truth)

```python
# build_config.py
project = Project(...)
# ... complex Python logic
project.export("projects/customer_analytics.yml")
```

```bash
# Before committing
$ python build_config.py
$ git add projects/customer_analytics.yml
$ git commit -m "Update customer analytics config"
```

---

**Document Version:** 0.1.0
**Status:** Draft for Review
**Next Review:** TBD
