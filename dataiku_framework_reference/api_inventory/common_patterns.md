# Common Patterns in Dataiku Python API

**Purpose:** Frequently used workflows and patterns for framework development

---

## Table of Contents

1. [Client Initialization Patterns](#client-initialization-patterns)
2. [Resource Access Patterns](#resource-access-patterns)
3. [Settings Modification Pattern](#settings-modification-pattern)
4. [Build and Execute Patterns](#build-and-execute-patterns)
5. [Async Operation Patterns](#async-operation-patterns)
6. [Data Access Patterns](#data-access-patterns)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Multi-Resource Patterns](#multi-resource-patterns)

---

## Client Initialization Patterns

### Pattern 1: Basic Connection
```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project(project_key)
```

### Pattern 2: Context Manager
```python
class DataikuConnection:
    def __enter__(self):
        self.client = DSSClient(host, api_key)
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup
        return False

with DataikuConnection() as client:
    # Use client
    pass
```

---

## Resource Access Patterns

### Pattern: List → Get → Operate

**Standard across all resources:**

```python
# 1. List resources (lightweight)
datasets = project.list_datasets()
for ds_info in datasets:
    print(ds_info['name'], ds_info['type'])

# 2. Get specific resource (full handle)
dataset = project.get_dataset("my_dataset")

# 3. Operate on resource
schema = dataset.get_schema()
dataset.build()
```

**Applies to:**
- Projects: `client.list_projects()` → `client.get_project()`
- Datasets: `project.list_datasets()` → `project.get_dataset()`
- Recipes: `project.list_recipes()` → `project.get_recipe()`
- Scenarios: `project.list_scenarios()` → `project.get_scenario()`
- Users: `client.list_users()` → `client.get_user()`

---

## Settings Modification Pattern

**Universal pattern for all settings objects:**

```python
# 1. Get settings
settings = resource.get_settings()

# 2. Modify settings dict
settings.settings['key'] = 'value'

# 3. Save changes
settings.save()
```

**Examples:**

```python
# Project settings
project_settings = project.get_settings()
project_settings.settings['shortDesc'] = "New description"
project_settings.save()

# Dataset settings
dataset_settings = dataset.get_settings()
dataset_settings.settings['description'] = "Customer data"
dataset_settings.save()

# Scenario settings
scenario_settings = scenario.get_settings()
scenario_settings.settings['active'] = True
scenario_settings.save()
```

---

## Build and Execute Patterns

### Pattern 1: Synchronous Build

```python
# Build and wait for completion
job = dataset.build(wait=True)
print(f"Job {job.id} completed")
```

### Pattern 2: Asynchronous Build with Monitoring

```python
# Start build
job = dataset.build(wait=False)

# Monitor progress
while True:
    status = job.get_status()
    if status['baseStatus']['state'] in ['DONE', 'FAILED', 'ABORTED']:
        break
    time.sleep(2)
```

### Pattern 3: Recipe Execution

```python
recipe = project.get_recipe("transform_data")
job = recipe.run(wait=True)
```

### Pattern 4: Scenario Execution (Two-Step!)

```python
# Step 1: Trigger scenario
trigger_fire = scenario.run()

# Step 2: Wait for run to start
scenario_run = trigger_fire.wait_for_scenario_run()

# Step 3: Monitor completion
scenario_run.wait_for_completion()
```

---

## Async Operation Patterns

### Pattern: Using DSSFuture

```python
# Many operations return futures
future = some_async_operation()

# Check if done (non-blocking)
if future.has_result():
    result = future.get_result()

# Wait for result (blocking)
result = future.wait_for_result()

# Get state
state = future.peek_state()
```

---

## Data Access Patterns

### Pattern 1: Iterate Rows (Memory Efficient)

```python
dataset = project.get_dataset("large_dataset")

for row in dataset.iter_rows():
    process(row)
```

### Pattern 2: Get DataFrame (Small Datasets)

```python
dataset = project.get_dataset("small_dataset")
df = dataset.get_dataframe()
```

### Pattern 3: Write DataFrame

```python
dataset = project.get_dataset("output")
dataset.write_with_schema(df)
```

---

## Error Handling Patterns

### Pattern 1: Try-Except with DataikuException

```python
from dataikuapi.utils import DataikuException

try:
    dataset.build(wait=True)
except DataikuException as e:
    print(f"Dataiku error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Pattern 2: Retry Logic

```python
from functools import wraps
import time

def retry(max_attempts=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(2 ** attempt)
        return wrapper
    return decorator

@retry(max_attempts=3)
def build_dataset(dataset):
    return dataset.build(wait=True)
```

---

## Multi-Resource Patterns

### Pattern: Build Dependencies First

```python
# Build in dependency order
source1 = project.get_dataset("SOURCE1")
source2 = project.get_dataset("SOURCE2")
intermediate = project.get_dataset("INTERMEDIATE")
final = project.get_dataset("FINAL")

# Build sources
source1.build(wait=True)
source2.build(wait=True)

# Build downstream (recipe runs automatically)
final.build(wait=True)  # Builds INTERMEDIATE too if needed
```

### Pattern: Parallel Operations

```python
from concurrent.futures import ThreadPoolExecutor

datasets = ["DS1", "DS2", "DS3", "DS4"]

def build_dataset(ds_name):
    ds = project.get_dataset(ds_name)
    return ds.build(wait=True)

# Build in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(build_dataset, ds) for ds in datasets]
    results = [f.result() for f in futures]
```

---

See `classes_and_methods.md` for complete API reference.
