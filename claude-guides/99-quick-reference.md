# 99 - Quick Reference

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Quick lookup for common operations

---

## Setup & Connection

```python
from dataikuapi import DSSClient
import os

# Connect
client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)

# Verify
projects = client.list_project_keys()
print(f"Connected! {len(projects)} projects")
```

---

## Projects

```python
# List projects
projects = client.list_projects()

# Get project
project = client.get_project("MY_PROJECT")

# Create project
project = client.create_project(
    "NEW_PROJECT",
    "Project Name",
    "owner_username"
)

# Project variables
variables = project.get_variables()
project.set_variables({"key": "value"})

# Project settings
settings = project.get_settings()
settings.settings['shortDesc'] = "Description"
settings.save()
```

---

## Datasets

```python
# List datasets
datasets = project.list_datasets()

# Get dataset
dataset = project.get_dataset("my_dataset")

# Create SQL dataset
dataset = project.create_dataset(
    "customers",
    "PostgreSQL",
    params={
        "connection": "my_postgres",
        "table": "public.customers"
    }
)

# Get schema
schema = dataset.get_schema()

# Set schema
dataset.set_schema({
    "columns": [
        {"name": "id", "type": "bigint"},
        {"name": "name", "type": "string"}
    ],
    "userModified": True
})

# Read data
for row in dataset.iter_rows():
    print(row)

# Or as DataFrame
df = dataset.get_dataframe()

# Write data
dataset.write_with_schema(df)

# Build dataset
job = dataset.build(wait=True)

# Clear dataset
dataset.clear()

# Metadata
metadata = dataset.get_metadata()
dataset.set_metadata({
    "tags": ["production"],
    "description": "Customer data"
})
```

---

## Recipes

```python
# List recipes
recipes = project.list_recipes()

# Get recipe
recipe = project.get_recipe("my_recipe")

# Run recipe
job = recipe.run(wait=True)

# Create Python recipe
recipe = project.new_recipe(
    type="python",
    name="transform"
).with_input("input_ds").with_output("output_ds").create()

# Set Python code
definition = recipe.get_definition_and_payload()
definition['payload']['script'] = """
import dataiku
import pandas as pd

df = dataiku.Dataset("input_ds").get_dataframe()
# Transform...
dataiku.Dataset("output_ds").write_with_schema(df)
"""
recipe.set_definition_and_payload(definition)

# Create Join recipe
join_recipe = project.create_join_recipe(
    name="join_data",
    input_refs=["left_ds", "right_ds"],
    output_ref="joined_ds"
)

# Create Group recipe
group_recipe = project.create_grouping_recipe(
    name="aggregate",
    input_ref="input_ds",
    output_ref="output_ds"
)

# Update schema
recipe.compute_schema_updates().apply()
```

---

## Scenarios

```python
# List scenarios
scenarios = project.list_scenarios()

# Get scenario
scenario = project.get_scenario("daily_refresh")

# Run and wait
scenario_run = scenario.run_and_wait()
print(f"Outcome: {scenario_run.get_outcome()}")

# Run async
trigger_fire = scenario.run()
scenario_run = trigger_fire.wait_for_scenario_run()

# Monitor
while scenario_run.running:
    scenario_run.refresh()
    time.sleep(5)

print(f"Outcome: {scenario_run.get_outcome()}")

# Get last run
last_run = scenario.get_last_finished_run()
print(f"Last: {last_run.get_outcome()}")

# Get history
runs = scenario.get_last_runs(limit=10)

# Enable/disable
settings = scenario.get_settings()
settings.settings['active'] = True
settings.save()
```

---

## Jobs

```python
# List jobs
jobs = project.list_jobs()

# Get job
job = project.get_job("JOB_ID")

# Check status
status = job.get_status()
state = status['baseStatus']['state']

# Get log
log = job.get_log()

# Wait for completion
while True:
    status = job.get_status()
    if status['baseStatus']['state'] in ['DONE', 'FAILED', 'ABORTED']:
        break
    time.sleep(2)
```

---

## Flow

```python
# Get flow
flow = project.get_flow()

# Get graph
graph = flow.get_graph()

# List zones
zones = flow.list_zones()

# Create zone
zone = flow.create_zone("Zone Name", "#FF5733")
```

---

## ML

```python
# List ML tasks
ml_tasks = project.list_ml_tasks()

# Get ML task
ml_task = project.get_ml_task("predict_churn")

# Train
ml_task.train()

# Get trained models
models = ml_task.get_trained_models_details()

# List saved models
saved_models = project.list_saved_models()

# Get saved model
saved_model = project.get_saved_model("model_id")

# List versions
versions = saved_model.list_versions()
```

---

## Common Patterns

### ETL Pipeline

```python
# Build source → Run recipe → Check output
source = project.get_dataset("source")
source.build(wait=True)

recipe = project.get_recipe("transform")
recipe.run(wait=True)

output = project.get_dataset("output")
metadata = output.get_metadata()
print(f"Output has {metadata.get('recordCount', 0)} rows")
```

### Scenario Chain

```python
scenarios = ["ingest", "transform", "export"]

for scenario_name in scenarios:
    scenario = project.get_scenario(scenario_name)
    run = scenario.run_and_wait()

    if run.get_outcome() != 'SUCCESS':
        print(f"Failed at {scenario_name}")
        break
```

### Incremental Build

```python
from datetime import datetime, timedelta

# Build only recent partitions
dataset = project.get_dataset("sales_by_date")

today = datetime.now()
partitions = [
    (today - timedelta(days=i)).strftime("%Y-%m-%d")
    for i in range(7)
]

for partition in partitions:
    dataset.build(partition=partition, wait=True)
    print(f"✓ Built {partition}")
```

---

## Error Handling

```python
from dataikuapi.utils import DataikuException

try:
    dataset.build(wait=True)
except DataikuException as e:
    print(f"Dataiku error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Retry Logic

```python
from functools import wraps
import time

def retry(max_attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    print(f"Attempt {attempt+1} failed, retrying...")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3)
def build_dataset(dataset):
    return dataset.build(wait=True)
```

---

## Scope Hierarchy Reminder

```
DSSClient (Instance)
    ↓
DSSProject (Project)
    ↓
DSSDataset / DSSRecipe / DSSScenario (Items)
```

**Always go through the hierarchy!**

---

## Key Gotchas

1. **Save settings:** `settings.save()`
2. **Project keys:** Must be UPPERCASE
3. **Variables:** Are always strings
4. **Scenario run:** Two-step process
5. **Schema updates:** Call `compute_schema_updates().apply()`
6. **Async operations:** Wait for completion
7. **Scope hierarchy:** Must go through project

---

## Environment Variables

```bash
# Set these
export DATAIKU_HOST="https://dss.company.com"
export DATAIKU_API_KEY="your-api-key"

# Optional
export DATAIKU_DEV_HOST="https://dev-dss.company.com"
export DATAIKU_DEV_API_KEY="dev-key"
export DATAIKU_PROD_HOST="https://prod-dss.company.com"
export DATAIKU_PROD_API_KEY="prod-key"
```

---

## Useful Snippets

### Check Connection

```python
def test_connection(host, api_key):
    try:
        client = DSSClient(host, api_key)
        projects = client.list_project_keys()
        print(f"✓ Connected, {len(projects)} projects")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
```

### Safe Build

```python
def safe_build(dataset):
    try:
        job = dataset.build(wait=True)
        print(f"✓ Built successfully")
        return job
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return None
```

### Project Inventory

```python
def inventory(project):
    return {
        "datasets": len(project.list_datasets()),
        "recipes": len(project.list_recipes()),
        "scenarios": len(project.list_scenarios()),
        "ml_tasks": len(project.list_ml_tasks())
    }

print(inventory(project))
```

---

## Documentation Links

- **Setup:** `01-prerequisites-and-setup.md`
- **Authentication:** `02-authentication-and-connection.md`
- **Projects:** `03-project-operations.md`
- **Datasets:** `04-dataset-operations.md`
- **Recipes:** `05-recipe-workflows.md`
- **Scenarios:** `06-scenario-automation.md`
- **ML:** `07-ml-workflows.md`
- **Troubleshooting:** `08-common-gotchas.md`

---

## API Reference

**Official Docs:** https://developer.dataiku.com/latest/api-reference/python/

**Common Classes:**
- `DSSClient` - Main client
- `DSSProject` - Project handle
- `DSSDataset` - Dataset handle
- `DSSRecipe` - Recipe handle
- `DSSScenario` - Scenario handle
- `DSSJob` - Job handle
- `DSSMLTask` - ML task handle

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
