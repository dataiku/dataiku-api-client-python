# 05 - Recipe Workflows

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Creating, configuring, and running recipes programmatically

---

## Recipes in Dataiku

**Recipes** are the transformation steps in Dataiku that process data from input datasets to output datasets.

### Recipe Types

| Type | Description | Common Use |
|------|-------------|------------|
| **Visual** | | |
| - Prepare | Column operations, filtering, formulas | Data cleaning |
| - Join | Merge datasets | Combining data sources |
| - Group | Aggregations, group-by | Summaries |
| - Window | Window functions | Running totals, rankings |
| - Sync | Copy data | Simple ETL |
| - Split | Divide dataset | Train/test split |
| - Stack | Union datasets | Combining similar data |
| **Code** | | |
| - Python | Custom Python code | Complex logic |
| - R | Custom R code | Statistical analysis |
| - SQL | SQL queries | Database transformations |
| - Spark (Python/Scala/SQL) | Distributed processing | Big data |
| **Special** | | |
| - Download | HTTP/FTP download | External data |
| - Shell | Shell scripts | System integration |

---

## Listing Recipes

### List All Recipes

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")

# List all recipes
recipes = project.list_recipes()

print(f"Found {len(recipes)} recipes:")
for recipe in recipes:
    print(f"  - {recipe['name']} ({recipe['type']})")
    print(f"    Inputs: {recipe.get('inputs', {})}")
    print(f"    Outputs: {recipe.get('outputs', {})}")
```

### Filter by Type

```python
def get_recipes_by_type(project, recipe_type):
    """Get all recipes of specific type"""
    all_recipes = project.list_recipes()
    return [r for r in all_recipes if r['type'] == recipe_type]

# Usage
python_recipes = get_recipes_by_type(project, "python")
join_recipes = get_recipes_by_type(project, "join")
```

---

## Getting a Recipe

```python
project = client.get_project("MY_PROJECT")

# Get recipe handle
recipe = project.get_recipe("my_recipe")

# Get recipe definition
definition = recipe.get_definition()
print(f"Recipe type: {definition.get('type')}")
print(f"Inputs: {definition.get('inputs')}")
print(f"Outputs: {definition.get('outputs')}")
```

---

## Running Recipes

### Simple Run (Synchronous)

```python
recipe = project.get_recipe("my_recipe")

# Run and wait
job = recipe.run(wait=True)

print(f"✓ Recipe completed. Job ID: {job.id}")
```

### Asynchronous Run with Monitoring

```python
import time

recipe = project.get_recipe("long_running_recipe")

# Start recipe (non-blocking)
job = recipe.run(wait=False)

print(f"Started job {job.id}")

# Monitor progress
while True:
    status = job.get_status()
    state = status['baseStatus']['state']

    print(f"Status: {state}", end='\r')

    if state in ['DONE', 'FAILED', 'ABORTED']:
        break

    time.sleep(2)

print()  # Newline

if state == 'DONE':
    print("✓ Recipe succeeded")
else:
    print(f"❌ Recipe {state}")
    print(job.get_log())
```

### Run with Partitions

```python
# Run for specific partition
recipe = project.get_recipe("partitioned_recipe")

job = recipe.run(
    partitions=["2023-11-21"],
    wait=True
)

print("✓ Partition processed")
```

---

## Creating Recipes

### Create Python Recipe

```python
# Create Python recipe
recipe_builder = project.new_recipe(
    type="python",
    name="custom_transform"
)

# Set inputs
recipe_builder = recipe_builder.with_input("input_dataset")

# Set outputs
recipe_builder = recipe_builder.with_output("output_dataset")

# Create the recipe
recipe = recipe_builder.create()

# Set the code
recipe_def = recipe.get_definition_and_payload()
recipe_def['payload']['script'] = """
# Python recipe code
import dataiku
import pandas as pd

# Read input
input_df = dataiku.Dataset("input_dataset").get_dataframe()

# Transform
output_df = input_df[input_df['value'] > 100]

# Write output
dataiku.Dataset("output_dataset").write_with_schema(output_df)
"""

recipe.set_definition_and_payload(recipe_def)

print("✓ Python recipe created")
```

### Create Join Recipe

```python
# Create join recipe
join_recipe = project.create_join_recipe(
    name="join_customers_orders",
    input_refs=["customers", "orders"],
    output_ref="customer_orders"
)

# Configure join
definition = join_recipe.get_definition()

# Set join conditions
definition['joins'] = [{
    'table1': 0,  # First input (customers)
    'table2': 1,  # Second input (orders)
    'on': [{
        'column1': {'name': 'customer_id', 'table': 0},
        'column2': {'name': 'customer_id', 'table': 1},
        'type': '='
    }],
    'type': 'LEFT'  # LEFT JOIN
}]

# Select columns
definition['selectedColumns'] = [
    {'name': 'customer_id', 'table': 0},
    {'name': 'customer_name', 'table': 0},
    {'name': 'email', 'table': 0},
    {'name': 'order_id', 'table': 1},
    {'name': 'order_date', 'table': 1},
    {'name': 'amount', 'table': 1}
]

join_recipe.set_definition(definition)

print("✓ Join recipe created")
```

### Create Group Recipe

```python
# Create grouping/aggregation recipe
group_recipe = project.create_grouping_recipe(
    name="aggregate_by_customer",
    input_ref="orders",
    output_ref="customer_summary"
)

# Configure grouping
definition = group_recipe.get_definition()

# Group by columns
definition['keys'] = [
    {'column': 'customer_id'}
]

# Aggregations
definition['values'] = [
    {
        'column': 'order_id',
        'function': 'count',
        'outputColumn': 'total_orders'
    },
    {
        'column': 'amount',
        'function': 'sum',
        'outputColumn': 'total_spent'
    },
    {
        'column': 'amount',
        'function': 'avg',
        'outputColumn': 'avg_order_value'
    },
    {
        'column': 'order_date',
        'function': 'max',
        'outputColumn': 'last_order_date'
    }
]

group_recipe.set_definition(definition)

print("✓ Group recipe created")
```

### Create Sync Recipe (Simple Copy)

```python
# Create sync recipe to copy data
sync_recipe = project.create_sync_recipe(
    name="copy_to_prod",
    input_ref="staging_data",
    output_ref="production_data"
)

print("✓ Sync recipe created")
```

### Create SQL Recipe

```python
# Create SQL query recipe
sql_recipe = project.new_recipe(
    type="sql_query",
    name="custom_sql"
).with_input("input_table").with_output("output_table").create()

# Set SQL code
definition = sql_recipe.get_definition_and_payload()
definition['payload']['query'] = """
SELECT
    customer_id,
    COUNT(*) as order_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount,
    MAX(order_date) as last_order
FROM input_table
WHERE order_date >= '2023-01-01'
GROUP BY customer_id
HAVING COUNT(*) > 5
ORDER BY total_amount DESC
"""

sql_recipe.set_definition_and_payload(definition)

print("✓ SQL recipe created")
```

### Create Window Recipe

```python
# Create window recipe (for running totals, rankings, etc.)
window_recipe = project.create_window_recipe(
    name="add_rankings",
    input_ref="sales_data",
    output_ref="sales_with_ranks"
)

# Configure window functions
definition = window_recipe.get_definition()

definition['windows'] = [{
    'partitioningColumns': ['region'],
    'orderColumns': [
        {'column': 'sales_amount', 'desc': True}
    ],
    'windowFrame': {
        'mode': 'ROWS',
        'upperBound': 0,
        'lowerBound': -1000000000  # Unbounded
    },
    'aggregates': [
        {
            'column': 'sales_amount',
            'function': 'rank',
            'outputColumn': 'sales_rank'
        },
        {
            'column': 'sales_amount',
            'function': 'sum',
            'outputColumn': 'running_total'
        }
    ]
}]

window_recipe.set_definition(definition)

print("✓ Window recipe created")
```

---

## Modifying Existing Recipes

### Update Python Recipe Code

```python
recipe = project.get_recipe("my_python_recipe")

# Get current definition
definition = recipe.get_definition_and_payload()

# Update code
definition['payload']['script'] = """
import dataiku
import pandas as pd
import numpy as np

# New updated code
input_df = dataiku.Dataset("input_dataset").get_dataframe()

# Enhanced transformation
input_df['new_column'] = input_df['value'] * 2
input_df['log_value'] = np.log(input_df['value'] + 1)

dataiku.Dataset("output_dataset").write_with_schema(input_df)
"""

# Save
recipe.set_definition_and_payload(definition)

print("✓ Recipe updated")
```

### Update Join Conditions

```python
recipe = project.get_recipe("join_recipe")

definition = recipe.get_definition()

# Modify join type
definition['joins'][0]['type'] = 'INNER'  # Change to INNER JOIN

# Add additional join condition
definition['joins'][0]['on'].append({
    'column1': {'name': 'country', 'table': 0},
    'column2': {'name': 'country', 'table': 1},
    'type': '='
})

recipe.set_definition(definition)

print("✓ Join updated")
```

### Add Column to Group Recipe

```python
recipe = project.get_recipe("group_recipe")

definition = recipe.get_definition()

# Add new aggregation
definition['values'].append({
    'column': 'profit',
    'function': 'sum',
    'outputColumn': 'total_profit'
})

recipe.set_definition(definition)

print("✓ Aggregation added")
```

---

## Schema Updates

### Compute and Apply Schema Updates

After creating/modifying a recipe, you often need to update the output schema:

```python
recipe = project.get_recipe("my_recipe")

# Compute what schema changes are needed
schema_updates = recipe.compute_schema_updates()

# Apply the updates
schema_updates.apply()

print("✓ Schema updated")
```

### Handle Schema Conflicts

```python
recipe = project.get_recipe("my_recipe")

try:
    schema_updates = recipe.compute_schema_updates()
    schema_updates.apply()
    print("✓ Schema updated successfully")
except Exception as e:
    print(f"❌ Schema update failed: {e}")

    # Get output dataset and manually set schema
    output_dataset = project.get_dataset("output_dataset")

    # Define expected schema
    new_schema = {
        "columns": [
            {"name": "id", "type": "bigint"},
            {"name": "name", "type": "string"},
            {"name": "value", "type": "double"}
        ],
        "userModified": True
    }

    output_dataset.set_schema(new_schema)
    print("✓ Schema set manually")
```

---

## Recipe Dependencies and Flow

### Get Recipe Inputs and Outputs

```python
recipe = project.get_recipe("my_recipe")

definition = recipe.get_definition()

# Get inputs
inputs = definition.get('inputs', {})
print("Inputs:")
for input_type, input_list in inputs.items():
    for inp in input_list:
        print(f"  - {inp.get('ref')} ({input_type})")

# Get outputs
outputs = definition.get('outputs', {})
print("Outputs:")
for output_type, output_list in outputs.items():
    for out in output_list:
        print(f"  - {out.get('ref')} ({output_type})")
```

### Add Input to Recipe

```python
recipe = project.get_recipe("my_recipe")

definition = recipe.get_definition()

# Add new input dataset
if 'main' not in definition['inputs']:
    definition['inputs']['main'] = []

definition['inputs']['main'].append({
    'ref': 'new_input_dataset',
    'deps': []
})

recipe.set_definition(definition)

print("✓ Input added")
```

---

## Recipe Status and Validation

### Check if Recipe Can Run

```python
def can_recipe_run(recipe):
    """Check if recipe's inputs are ready"""

    try:
        definition = recipe.get_definition()

        # Get all input datasets
        input_refs = []
        for input_list in definition.get('inputs', {}).values():
            input_refs.extend([i['ref'] for i in input_list])

        # Check each input
        for input_ref in input_refs:
            try:
                input_dataset = recipe.project.get_dataset(input_ref)
                # Try to get schema (quick check if dataset is accessible)
                input_dataset.get_schema()
            except Exception as e:
                print(f"❌ Input {input_ref} not ready: {e}")
                return False

        return True

    except Exception as e:
        print(f"❌ Cannot validate recipe: {e}")
        return False

# Usage
recipe = project.get_recipe("my_recipe")
if can_recipe_run(recipe):
    job = recipe.run(wait=True)
else:
    print("Recipe cannot run - inputs not ready")
```

---

## Bulk Recipe Operations

### Run Multiple Recipes in Sequence

```python
def run_recipe_chain(project, recipe_names):
    """Run multiple recipes in sequence"""

    results = []

    for recipe_name in recipe_names:
        try:
            print(f"Running {recipe_name}...")
            recipe = project.get_recipe(recipe_name)
            job = recipe.run(wait=True)

            results.append({
                "recipe": recipe_name,
                "status": "success",
                "job_id": job.id
            })
            print(f"✓ {recipe_name} completed")

        except Exception as e:
            results.append({
                "recipe": recipe_name,
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ {recipe_name} failed: {e}")
            break  # Stop on first failure

    return results

# Usage
recipes = ["ingest_data", "clean_data", "aggregate_data", "export_results"]
results = run_recipe_chain(project, recipes)
```

### Create Recipe Pipeline from Config

```python
import yaml

def create_pipeline_from_config(project, config_file):
    """Create a series of recipes from config"""

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    for recipe_config in config['recipes']:
        recipe_type = recipe_config['type']

        if recipe_type == 'python':
            recipe = project.new_recipe(
                type="python",
                name=recipe_config['name']
            )

            for inp in recipe_config.get('inputs', []):
                recipe = recipe.with_input(inp)

            for out in recipe_config.get('outputs', []):
                recipe = recipe.with_output(out)

            recipe = recipe.create()

            # Set code
            if 'code' in recipe_config:
                definition = recipe.get_definition_and_payload()
                definition['payload']['script'] = recipe_config['code']
                recipe.set_definition_and_payload(definition)

        elif recipe_type == 'join':
            recipe = project.create_join_recipe(
                name=recipe_config['name'],
                input_refs=recipe_config['inputs'],
                output_ref=recipe_config['outputs'][0]
            )
            # Configure join details...

        elif recipe_type == 'group':
            recipe = project.create_grouping_recipe(
                name=recipe_config['name'],
                input_ref=recipe_config['inputs'][0],
                output_ref=recipe_config['outputs'][0]
            )
            # Configure grouping details...

        print(f"✓ Created recipe: {recipe_config['name']}")

# Example config.yaml:
# recipes:
#   - name: join_data
#     type: join
#     inputs: [customers, orders]
#     outputs: [customer_orders]
#
#   - name: aggregate
#     type: group
#     inputs: [customer_orders]
#     outputs: [customer_summary]
#
#   - name: custom_logic
#     type: python
#     inputs: [customer_summary]
#     outputs: [final_output]
#     code: |
#       import dataiku
#       # Python code here...
```

---

## Common Patterns

### Pattern: Data Quality Check Recipe

```python
# Create Python recipe that validates data
recipe = project.new_recipe(
    type="python",
    name="data_quality_check"
).with_input("input_data").with_output("valid_data").create()

definition = recipe.get_definition_and_payload()
definition['payload']['script'] = """
import dataiku
import pandas as pd

# Read input
df = dataiku.Dataset("input_data").get_dataframe()

# Quality checks
initial_count = len(df)

# Remove nulls in critical columns
df = df.dropna(subset=['id', 'email'])

# Remove duplicates
df = df.drop_duplicates(subset=['id'])

# Validate email format
df = df[df['email'].str.contains('@', na=False)]

# Validate value ranges
df = df[df['value'] >= 0]

final_count = len(df)
print(f"Quality check: {initial_count} -> {final_count} rows ({initial_count - final_count} removed)")

# Write clean data
dataiku.Dataset("valid_data").write_with_schema(df)
"""

recipe.set_definition_and_payload(definition)
```

### Pattern: Conditional Recipe Execution

```python
def run_if_updated(recipe, input_dataset_name):
    """Run recipe only if input was recently updated"""

    # Get input dataset last build time
    input_dataset = project.get_dataset(input_dataset_name)
    input_metadata = input_dataset.get_metadata()
    input_last_build = input_metadata.get('lastBuild', {}).get('endTime', 0)

    # Get recipe's output last build time
    definition = recipe.get_definition()
    output_ref = list(definition['outputs'].values())[0][0]['ref']
    output_dataset = project.get_dataset(output_ref)
    output_metadata = output_dataset.get_metadata()
    output_last_build = output_metadata.get('lastBuild', {}).get('endTime', 0)

    # Compare timestamps
    if input_last_build > output_last_build:
        print(f"Input updated, running recipe {recipe.name}")
        job = recipe.run(wait=True)
        return job
    else:
        print(f"Input not updated, skipping recipe {recipe.name}")
        return None
```

---

## Common Gotchas

### 1. Must Call compute_schema_updates()

```python
# ❌ WRONG - Schema may be out of sync
recipe = project.create_join_recipe(...)
recipe.run()  # May fail!

# ✓ CORRECT - Update schema first
recipe = project.create_join_recipe(...)
recipe.compute_schema_updates().apply()
recipe.run()
```

### 2. Recipe Names vs Dataset Names

```python
# Recipe name and output dataset name can be different!
recipe = project.get_recipe("my_recipe")
definition = recipe.get_definition()

output_dataset_name = definition['outputs']['main'][0]['ref']
# May not equal "my_recipe"!
```

### 3. Python Recipe Code Runs in DSS

```python
# Code runs on DSS backend, not locally!
# Can only use packages installed in DSS code environment
definition['payload']['script'] = """
# This runs on DSS, not your local machine
import dataiku  # Available in DSS
import custom_package  # Only if installed in DSS code env!
"""
```

### 4. Join Recipe Table Indices

```python
# Table indices in join recipe:
# 0 = first input
# 1 = second input
# 2 = third input, etc.

# When referencing columns in join conditions:
'column1': {'name': 'id', 'table': 0},  # From first input
'column2': {'name': 'id', 'table': 1},  # From second input
```

---

## Next Steps

- **06-scenario-automation.md** - Automating recipe execution
- **07-ml-workflows.md** - Machine learning recipes
- **08-common-gotchas.md** - More troubleshooting

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
