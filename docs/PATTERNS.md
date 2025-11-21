# Common Patterns

Quick reference for common code patterns. See [`../dataiku_framework_reference/api_inventory/common_patterns.md`](../dataiku_framework_reference/api_inventory/common_patterns.md) for complete details.

---

## Table of Contents

1. [Scope Hierarchy Pattern](#scope-hierarchy-pattern)
2. [Resource Access Pattern](#resource-access-pattern)
3. [Settings Modification Pattern](#settings-modification-pattern)
4. [Build/Execute Patterns](#buildexecute-patterns)
5. [Async Operation Patterns](#async-operation-patterns)
6. [Data Access Patterns](#data-access-patterns)
7. [Error Handling Patterns](#error-handling-patterns)

---

## Scope Hierarchy Pattern

**MANDATORY: Always go through the hierarchy**

```python
# Scope hierarchy
client = DSSClient(host, api_key)        # Instance level
project = client.get_project(key)        # Project level  
dataset = project.get_dataset(name)      # Item level

# ❌ WRONG - Cannot skip levels
dataset = client.get_dataset(name)

# ✓ CORRECT - Must go through project
project = client.get_project(key)
dataset = project.get_dataset(name)
```

---

## Resource Access Pattern

**Standard pattern: List → Get → Operate**

```python
# 1. List resources (lightweight)
datasets = project.list_datasets()
for ds in datasets:
    print(ds['name'], ds['type'])

# 2. Get specific resource (full handle)
dataset = project.get_dataset("my_dataset")

# 3. Operate on resource
schema = dataset.get_schema()
dataset.build(wait=True)
```

**Applies to:**
- Projects: `list_projects()` → `get_project()`
- Datasets: `list_datasets()` → `get_dataset()`
- Recipes: `list_recipes()` → `get_recipe()`
- Scenarios: `list_scenarios()` → `get_scenario()`
- Users: `list_users()` → `get_user()`

---

## Settings Modification Pattern

**Universal: Get → Modify → Save**

```python
# 1. Get settings
settings = resource.get_settings()

# 2. Modify settings dict
settings.settings['key'] = 'value'

# 3. Save changes (CRITICAL!)
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

**CRITICAL:** Forgetting `.save()` is the most common mistake!

---

## Build/Execute Patterns

### Synchronous (Wait for Completion)

```python
# Build dataset
job = dataset.build(wait=True)
print(f"✓ Completed: {job.id}")

# Run recipe
job = recipe.run(wait=True)

# Run scenario
scenario_run = scenario.run_and_wait()
```

### Asynchronous (Non-Blocking)

```python
# Start build
job = dataset.build(wait=False)

# Monitor progress
import time
while True:
    status = job.get_status()
    state = status['baseStatus']['state']
    
    if state in ['DONE', 'FAILED', 'ABORTED']:
        break
    
    print(f"Status: {state}")
    time.sleep(2)

print(f"Final state: {state}")
```

### Scenario (Two-Step!)

```python
# ❌ WRONG
trigger_fire = scenario.run()
outcome = trigger_fire.get_outcome()  # Fails!

# ✓ CORRECT - Two steps
trigger_fire = scenario.run()
scenario_run = trigger_fire.wait_for_scenario_run()  # Step 1
outcome = scenario_run.get_outcome()  # Step 2
```

---

## Async Operation Patterns

### Using DSSFuture

```python
# Operations return futures
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

### Iterate Rows (Memory Efficient)

```python
dataset = project.get_dataset("large_dataset")

for row in dataset.iter_rows():
    process_row(row)
```

### Get DataFrame (Small Datasets)

```python
dataset = project.get_dataset("small_dataset")
df = dataset.get_dataframe()
print(len(df))
```

### Write DataFrame

```python
import pandas as pd

df = pd.DataFrame({'col1': [1, 2, 3]})

dataset = project.get_dataset("output")
dataset.write_with_schema(df)
```

---

## Error Handling Patterns

### Try-Except with DataikuException

```python
from dataikuapi.utils import DataikuException

try:
    dataset.build(wait=True)
except DataikuException as e:
    print(f"Dataiku error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry Logic

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
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3)
def build_dataset(dataset):
    return dataset.build(wait=True)
```

---

## Complete Pattern Reference

For more patterns including:
- Client initialization variations
- Multi-resource operations
- Parallel execution
- Framework development patterns

See: [`../dataiku_framework_reference/api_inventory/common_patterns.md`](../dataiku_framework_reference/api_inventory/common_patterns.md)

---

**Quick Reference:** [`../CLAUDE.md`](../CLAUDE.md)
