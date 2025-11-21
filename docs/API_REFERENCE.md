# API Reference Guide

Navigation to complete API reference documentation.

---

## Quick Navigation

### API Inventory (Complete Reference)

**Location:** [`../dataiku_framework_reference/api_inventory/`](../dataiku_framework_reference/api_inventory/)

| File | Purpose |
|------|---------|
| **classes_and_methods.md** (39KB, 1,162 lines) | Complete class/method inventory |
| **class_index.md** (16KB, 500 lines) | Quick reference by category |
| **common_patterns.md** | Workflow patterns |
| **coverage_analysis.md** | Gap analysis & wrapper roadmap |

### Framework Development

**Location:** [`../dataiku_framework_reference/documentation/`](../dataiku_framework_reference/documentation/)

| File | Purpose |
|------|---------|
| **01-prerequisites-and-setup.md** | Project structure, APIKEY.txt |
| **02-api-overview.md** | API architecture |
| **03-10-*.md** | References to detailed guides |

---

## Main Client Classes

### DSSClient (Primary)

**Entry point for Dataiku DSS operations**

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
```

**Key Methods:**
- `list_projects()` - Get all projects
- `get_project(key)` - Access specific project
- `create_project(...)` - Create new project
- `list_users()` - List users (admin)
- `get_general_settings()` - Instance settings (admin)

### DSSProject (154 methods!)

**Container for all project resources**

```python
project = client.get_project("MY_PROJECT")
```

**Key Methods:**
- Datasets: `list_datasets()`, `get_dataset()`, `create_dataset()`
- Recipes: `list_recipes()`, `get_recipe()`, `create_*_recipe()`
- Scenarios: `list_scenarios()`, `get_scenario()`, `create_scenario()`
- Jobs: `list_jobs()`, `get_job()`
- ML: `list_ml_tasks()`, `get_ml_task()`
- Flow: `get_flow()`

### Other Clients

- **GovernClient** - Dataiku Govern operations
- **FMClient** - Fleet Management (AWS/Azure/GCP)
- **APINodeClient** - Deployed API services
- **APINodeAdminClient** - API Node administration

---

## Core Resource Classes

### Datasets

**DSSDataset** - Dataset operations

```python
dataset = project.get_dataset("my_dataset")
```

**Key Methods:**
- `get_schema()`, `set_schema()`
- `get_settings()`, `get_metadata()`
- `iter_rows()`, `get_dataframe()`
- `build()`, `clear()`
- `write_with_schema(df)`

### Recipes

**DSSRecipe** - Recipe operations

```python
recipe = project.get_recipe("my_recipe")
```

**Key Methods:**
- `run()` - Execute recipe
- `get_definition()`, `set_definition()`
- `compute_schema_updates().apply()`

### Scenarios

**DSSScenario** - Scenario operations

```python
scenario = project.get_scenario("my_scenario")
```

**Key Methods:**
- `run()` - Trigger scenario
- `run_and_wait()` - Run synchronously
- `get_last_runs()` - Get history
- `get_settings()` - Configure scenario

### Jobs

**DSSJob** - Job monitoring

```python
job = dataset.build(wait=False)
```

**Key Methods:**
- `get_status()` - Check status
- `get_log()` - Get logs
- `abort()` - Cancel job

---

## Complete Inventory

### 150+ Classes Documented

**See:** [`../dataiku_framework_reference/api_inventory/classes_and_methods.md`](../dataiku_framework_reference/api_inventory/classes_and_methods.md)

**Categories:**
1. Client Classes (7)
2. Project & Flow (10+)
3. Datasets (20+)
4. Recipes (15+)
5. Scenarios (10+)
6. Jobs & Futures (5+)
7. ML & Models (25+)
8. Admin (20+)
9. Plugins (15+)
10. API Node (10+)
11. Govern (10+)
12. Fleet Management (5+)

### Quick Lookup by Category

**See:** [`../dataiku_framework_reference/api_inventory/class_index.md`](../dataiku_framework_reference/api_inventory/class_index.md)

**Use Cases:**
- Find class by purpose
- Browse by category
- Quick method lookup
- Discover related classes

---

## Common Patterns

**See:** [`PATTERNS.md`](PATTERNS.md) or [`../dataiku_framework_reference/api_inventory/common_patterns.md`](../dataiku_framework_reference/api_inventory/common_patterns.md)

- Client initialization
- Resource access (List → Get → Operate)
- Settings modification (Get → Modify → Save)
- Build/execute patterns
- Async operations
- Error handling

---

## Framework Development

### Gap Analysis & Roadmap

**See:** [`../dataiku_framework_reference/api_inventory/coverage_analysis.md`](../dataiku_framework_reference/api_inventory/coverage_analysis.md)

**Contents:**
- Coverage by category
- What's lightly documented
- Inconsistencies found
- Wrapper development roadmap (3 phases)
- Priority recommendations

### API Maturity Assessment

**Strengths:**
- ✓ Comprehensive coverage
- ✓ Consistent patterns
- ✓ Well typed
- ✓ Stable API

**Opportunities for wrappers:**
- Simplify async operations
- Add validation
- Better type hints
- Smart defaults
- Helper methods

---

## Official Documentation

- **Developer Docs:** https://developer.dataiku.com/latest/api-reference/python/
- **Main Docs:** https://doc.dataiku.com/
- **GitHub:** https://github.com/dataiku/dataiku-api-client-python

---

**Back to:** [`../CLAUDE.md`](../CLAUDE.md)
