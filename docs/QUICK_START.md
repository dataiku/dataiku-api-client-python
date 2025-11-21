# Quick Start Guide

Get productive with the Dataiku Python API in 5 minutes.

---

## Table of Contents

1. [Setup (2 minutes)](#setup)
2. [First Connection (1 minute)](#first-connection)
3. [Common Operations (2 minutes)](#common-operations)
4. [Next Steps](#next-steps)

---

## Setup

### Install the API Client

```bash
pip install dataiku-api-client
```

### Get Your API Key

1. Log into your Dataiku DSS instance
2. Click your profile (top right) → Settings/Profile
3. Navigate to "API Keys"
4. Create new key or copy existing one
5. **Save it somewhere safe** - you'll only see it once!

### Save API Key Securely

**Option 1: Environment Variable (Recommended)**

```bash
export DATAIKU_API_KEY="your-api-key-here"
export DATAIKU_HOST="https://dss.yourcompany.com"
```

**Option 2: Config File (Never commit!)**

Create `config/APIKEY.txt`:
```bash
mkdir config
echo "your-api-key-here" > config/APIKEY.txt
echo "config/APIKEY.txt" >> .gitignore  # CRITICAL!
```

---

## First Connection

### Verify Connection

```python
from dataikuapi import DSSClient
import os

# Connect
client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)

# Test connection
projects = client.list_project_keys()
print(f"✓ Connected! Found {len(projects)} projects")
print(f"Projects: {projects}")
```

**Expected output:**
```
✓ Connected! Found 5 projects
Projects: ['PROJECT1', 'PROJECT2', 'PROJECT3', 'PROJECT4', 'PROJECT5']
```

---

## Common Operations

### Access a Project

```python
# Get project handle
project = client.get_project("MY_PROJECT")

# List project contents
datasets = project.list_datasets()
recipes = project.list_recipes()
scenarios = project.list_scenarios()

print(f"Datasets: {len(datasets)}")
print(f"Recipes: {len(recipes)}")
print(f"Scenarios: {len(scenarios)}")
```

### Build a Dataset

```python
# Get dataset
dataset = project.get_dataset("my_dataset")

# Build it (synchronous - waits for completion)
job = dataset.build(wait=True)

print(f"✓ Dataset built successfully! Job ID: {job.id}")
```

### Run a Recipe

```python
# Get recipe
recipe = project.get_recipe("my_recipe")

# Run it (synchronous)
job = recipe.run(wait=True)

print(f"✓ Recipe completed! Job ID: {job.id}")
```

### Execute a Scenario

```python
# Get scenario
scenario = project.get_scenario("daily_refresh")

# Run and wait for completion
scenario_run = scenario.run_and_wait()

# Check outcome
outcome = scenario_run.get_outcome()
print(f"Scenario outcome: {outcome}")

if outcome == 'SUCCESS':
    print("✓ Scenario succeeded!")
else:
    print(f"✗ Scenario failed: {outcome}")
```

### Read Dataset Data

```python
# Get dataset
dataset = project.get_dataset("customers")

# Option 1: Iterate rows (memory efficient for large datasets)
for row in dataset.iter_rows():
    print(row)
    break  # Just show first row

# Option 2: Get as pandas DataFrame (small datasets only)
df = dataset.get_dataframe()
print(f"Loaded {len(df)} rows")
print(df.head())
```

---

## Complete First Script

Put it all together:

```python
#!/usr/bin/env python3
"""
My First Dataiku API Script
"""
from dataikuapi import DSSClient
import os

def main():
    # Connect
    client = DSSClient(
        os.getenv('DATAIKU_HOST'),
        os.getenv('DATAIKU_API_KEY')
    )
    print("✓ Connected to Dataiku")

    # Access project
    project = client.get_project("MY_PROJECT")
    print(f"✓ Accessed project: MY_PROJECT")

    # Build a dataset
    dataset = project.get_dataset("my_dataset")
    print(f"Building dataset: my_dataset...")
    job = dataset.build(wait=True)
    print(f"✓ Dataset built! Job: {job.id}")

    # Run a recipe
    recipe = project.get_recipe("my_recipe")
    print(f"Running recipe: my_recipe...")
    job = recipe.run(wait=True)
    print(f"✓ Recipe completed! Job: {job.id}")

    print("\n✓ All operations completed successfully!")

if __name__ == "__main__":
    main()
```

Save as `my_first_script.py` and run:

```bash
python my_first_script.py
```

---

## Common First-Time Issues

### Issue: "401 Unauthorized"

**Cause:** Invalid API key

**Fix:**
```bash
# Check your API key is set correctly
echo $DATAIKU_API_KEY

# Re-generate API key in DSS if needed
```

### Issue: "Connection refused"

**Cause:** Cannot reach DSS instance

**Fix:**
```bash
# Check host is correct
echo $DATAIKU_HOST

# Test connectivity
curl -I $DATAIKU_HOST
```

### Issue: "AttributeError: 'DSSClient' object has no attribute 'get_dataset'"

**Cause:** Skipped scope hierarchy

**Fix:**
```python
# ❌ WRONG
dataset = client.get_dataset("my_dataset")

# ✓ CORRECT - Must go through project
project = client.get_project("MY_PROJECT")
dataset = project.get_dataset("my_dataset")
```

See full hierarchy: [../CLAUDE.md#scope-hierarchy](../CLAUDE.md#scope-hierarchy)

---

## Next Steps

**Now that you're connected:**

1. **Plan your project** → [`PROJECT_PLANNING.md`](PROJECT_PLANNING.md)
   - Create detailed plan before coding
   - Avoid common mistakes
   - Follow naming conventions

2. **Learn common patterns** → [`PATTERNS.md`](PATTERNS.md)
   - Resource access patterns
   - Settings modification
   - Error handling

3. **Deep dive into workflows** → [`WORKFLOW_GUIDES.md`](WORKFLOW_GUIDES.md)
   - Complete guides for all operations
   - Datasets, recipes, scenarios, ML

4. **Troubleshooting** → [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
   - Common errors and solutions
   - Debugging tips

---

## Quick Reference Card

```python
# Connect
from dataikuapi import DSSClient
client = DSSClient(host, api_key)

# Navigate scope hierarchy
project = client.get_project("PROJECT_KEY")
dataset = project.get_dataset("dataset_name")
recipe = project.get_recipe("recipe_name")
scenario = project.get_scenario("scenario_name")

# Build/Run
dataset.build(wait=True)
recipe.run(wait=True)
scenario.run_and_wait()

# Read data
for row in dataset.iter_rows(): ...
df = dataset.get_dataframe()

# Modify settings (MUST save!)
settings = resource.get_settings()
settings.settings['key'] = 'value'
settings.save()  # CRITICAL!
```

---

**Ready to build? Start planning:** [`PROJECT_PLANNING.md`](PROJECT_PLANNING.md)

**Need help?** [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md)
