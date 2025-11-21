# Dataiku Python API - Claude Code Navigation Guides

**Purpose:** These guides are designed to help Claude Code sessions navigate and use the Dataiku Python API effectively. They document common workflows, patterns, gotchas, and best practices.

**Audience:** Claude Code AI sessions (not human developers)

---

## Guide Structure

### Getting Started

1. **[01-prerequisites-and-setup.md](01-prerequisites-and-setup.md)**
   - Installation and environment setup
   - API key generation and management
   - Connection verification
   - Common setup issues

2. **[02-authentication-and-connection.md](02-authentication-and-connection.md)**
   - Scope hierarchy (CRITICAL CONCEPT)
   - Authentication methods
   - Connection patterns
   - Permission handling

### Core Operations

3. **[03-project-operations.md](03-project-operations.md)**
   - Creating and configuring projects
   - Project metadata and variables
   - Project contents and flow
   - Export/import patterns

4. **[04-dataset-operations.md](04-dataset-operations.md)**
   - Dataset CRUD operations
   - Schema management
   - Reading and writing data
   - Building and partitioning
   - Dataset metadata

5. **[05-recipe-workflows.md](05-recipe-workflows.md)**
   - Recipe types and creation
   - Running and monitoring recipes
   - Schema updates
   - Recipe dependencies

6. **[06-scenario-automation.md](06-scenario-automation.md)**
   - Creating and configuring scenarios
   - Scenario steps and triggers
   - Running and monitoring
   - Notifications and reporters

### Advanced Topics

7. **[07-ml-workflows.md](07-ml-workflows.md)**
   - ML task operations
   - Model training and evaluation
   - Saved models and versioning
   - Model deployment

8. **[08-common-gotchas.md](08-common-gotchas.md)**
   - Critical concepts to remember
   - Common errors and solutions
   - Best practices
   - Debugging checklist

### Quick Reference

9. **[99-quick-reference.md](99-quick-reference.md)**
   - Cheat sheet for common operations
   - Code snippets
   - Quick patterns
   - Essential reminders

---

## Quick Start

**First time?** Read in order:
1. Prerequisites and Setup
2. Authentication and Connection
3. Project Operations
4. Dataset Operations

**Need specific help?** Jump to:
- Recipes → 05-recipe-workflows.md
- Automation → 06-scenario-automation.md
- ML → 07-ml-workflows.md
- Troubleshooting → 08-common-gotchas.md
- Quick lookup → 99-quick-reference.md

---

## Critical Concepts

### 1. Scope Hierarchy (MUST UNDERSTAND)

```
DSSClient (Instance Level)
    ↓
DSSProject (Project Level)
    ↓
DSSDataset / DSSRecipe / DSSScenario (Item Level)
```

**You must go through each level!** Cannot skip.

### 2. Settings Must Be Saved

```python
# ❌ WRONG
settings = dataset.get_settings()
settings.settings['description'] = "New"
# Changes lost!

# ✓ CORRECT
settings = dataset.get_settings()
settings.settings['description'] = "New"
settings.save()  # Critical!
```

### 3. Async Operations

Many operations (builds, scenarios, training) are asynchronous. You must wait for completion.

### 4. Project Keys Must Be Uppercase

`MY_PROJECT` ✓ not `my_project` ❌

### 5. Variables Are Strings

```python
variables = project.get_variables()
batch_size = int(variables["batch_size"])  # Convert!
```

---

## Common Patterns

### Basic ETL

```python
from dataikuapi import DSSClient
import os

# Connect
client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)

# Get project
project = client.get_project("MY_PROJECT")

# Build source
source = project.get_dataset("source_data")
source.build(wait=True)

# Run transformation
recipe = project.get_recipe("transform_data")
recipe.run(wait=True)

# Verify output
output = project.get_dataset("final_output")
metadata = output.get_metadata()
print(f"✓ Output has {metadata.get('recordCount', 0)} rows")
```

### Automation Pipeline

```python
# Run scenario
scenario = project.get_scenario("daily_refresh")
scenario_run = scenario.run_and_wait()

if scenario_run.get_outcome() == 'SUCCESS':
    print("✓ Pipeline succeeded")
else:
    print("❌ Pipeline failed")
    # Get logs, send alerts, etc.
```

---

## Environment Setup

```bash
# Required
export DATAIKU_HOST="https://dss.yourcompany.com"
export DATAIKU_API_KEY="your-api-key-here"

# Multi-environment setup
export DATAIKU_DEV_HOST="https://dev-dss.company.com"
export DATAIKU_DEV_API_KEY="dev-key"
export DATAIKU_PROD_HOST="https://prod-dss.company.com"
export DATAIKU_PROD_API_KEY="prod-key"
```

---

## Resources

- **Official API Docs:** https://developer.dataiku.com/latest/api-reference/python/
- **Main Dataiku Docs:** https://doc.dataiku.com/
- **GitHub:** https://github.com/dataiku/dataiku-api-client-python
- **PyPI:** https://pypi.org/project/dataiku-api-client/

---

## Contributing to These Guides

These guides are maintained for Claude Code sessions. When updating:

1. Keep examples practical and tested
2. Include gotchas and common mistakes
3. Show both ❌ wrong and ✓ correct patterns
4. Focus on what Claude Code needs to know
5. Keep code snippets copy-pasteable

---

## Version Info

- **Guide Version:** 1.0
- **API Version:** 14.1.3+
- **Last Updated:** 2025-11-21
- **Python:** 3.7+

---

## Quick Gotchas Reminder

1. ⚠️ **Scope hierarchy** - Must go through project
2. ⚠️ **Save settings** - Always call `.save()`
3. ⚠️ **Uppercase project keys** - `MY_PROJECT` not `my_project`
4. ⚠️ **Variables are strings** - Convert types!
5. ⚠️ **Async operations** - Wait for completion
6. ⚠️ **Schema updates** - Call `compute_schema_updates().apply()`
7. ⚠️ **Scenario runs** - Two-step process

---

Happy automating! 🚀
