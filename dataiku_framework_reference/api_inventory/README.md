# Dataiku Python API Client - Comprehensive Inventory

This directory contains complete documentation of the Dataiku Python API client structure, organized for easy reference.

## Documents

### 1. **COMPREHENSIVE_API_INVENTORY.md** (1162 lines)
**The complete reference guide** covering:
- Executive summary of all major clients (DSSClient, GovernClient, FMClient variants, etc.)
- Detailed method signatures for each main class
- Complete listing of all 150+ public classes
- Settings and configuration patterns
- Async operations and futures
- Data import/export workflows
- Class hierarchies and inheritance
- Composition patterns
- Common method naming conventions
- Authentication methods
- Error handling

**Best for**: Understanding the complete API structure, learning method signatures, finding capabilities

### 2. **API_CLASS_INDEX.md** (400+ lines)
**Quick reference index** organized by category:
- Main entry point classes (7 classes)
- Project-level classes (1 major class)
- Dataset & data classes (15 classes)
- Workflow & automation classes (18 classes)
- Analytics & visualization classes (12 classes)
- Machine learning classes (20 classes)
- Agent & knowledge classes (10 classes)
- LLM & language classes (6 classes)
- Notebook classes (5 classes)
- API service classes (10 classes)
- Administration classes (35 classes)
- Governance classes (40+ classes)
- Fleet management classes (40+ classes)
- Utility classes (20+ classes)
- Taggable objects list
- Quick navigation by use case

**Best for**: Finding a specific class, understanding what classes exist in a category, discovering what you need for your use case

---

## Quick Start Guide

### If you want to understand a specific capability:

1. **Working with datasets?**
   - See: API_CLASS_INDEX.md → "Dataset & Data Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 3: DSSDataset"

2. **Creating data pipelines?**
   - See: API_CLASS_INDEX.md → "Workflow & Automation Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 9: Common Workflows"

3. **Building ML models?**
   - See: API_CLASS_INDEX.md → "Machine Learning Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 3: DSSMLTask"

4. **Managing users/security?**
   - See: API_CLASS_INDEX.md → "Administration Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 1.1: DSSClient - Users Management"

5. **Using Governance?**
   - See: API_CLASS_INDEX.md → "Governance Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 1.2: GovernClient"

6. **Managing cloud infrastructure?**
   - See: API_CLASS_INDEX.md → "Fleet Management Classes"
   - Then: COMPREHENSIVE_API_INVENTORY.md → "Part 1.3: FMClient Variants"

### If you want to learn general patterns:

1. **Method naming conventions** → COMPREHENSIVE_API_INVENTORY.md → Part 11
2. **Settings/Configuration patterns** → COMPREHENSIVE_API_INVENTORY.md → Part 4
3. **Async operations** → COMPREHENSIVE_API_INVENTORY.md → Part 5
4. **Class hierarchies** → COMPREHENSIVE_API_INVENTORY.md → Part 7
5. **Common workflows** → COMPREHENSIVE_API_INVENTORY.md → Part 9

---

## Key Facts About the API

### Client Classes (7)
- **DSSClient**: 114 public methods - Main DSS operations
- **GovernClient**: 48 public methods - Governance & compliance
- **FMClientAWS/Azure/GCP**: 4-5 methods each - Cloud infrastructure
- **APINodeClient**: 9 methods - API service predictions
- **APINodeAdminClient**: 11 methods - API node management

### Project-Level Access
- **DSSProject**: 154 public methods - Your main entry point to projects
- Access from: `client.get_project(project_key)` → `DSSProject`

### Total Public Classes
- **150+ classes** across 11 major modules
- Organized hierarchically: Client → Project → Objects
- Clear separation: Data, Workflows, Analytics, ML, Admin, Governance, Infrastructure

### Common Patterns
1. **List vs Get Pattern**: `list_*()` returns dicts, `get_*()` returns object handles
2. **Settings Pattern**: All major objects have `get_settings()` and `save()` methods
3. **Handle Pattern**: Object handles combine state + actions
4. **Builder Pattern**: Specialized creation with `new_*_creator()` methods
5. **Future Pattern**: Async operations return `DSSFuture` with `wait_for_result()`

---

## Navigation Examples

### Example 1: Work with a dataset
```
Start: DSSClient
→ client.get_project("PROJECT_KEY")  [DSSProject]
→ project.get_dataset("dataset_name") [DSSDataset]
→ dataset.get_definition()             [dict config]
→ dataset.read_dataframe()             [pandas DataFrame]
→ dataset.get_settings()               [DSSDatasetSettings]
→ dataset.delete()                     [void]
```

### Example 2: Create and run a recipe
```
Start: DSSClient
→ client.get_project("PROJECT_KEY")    [DSSProject]
→ project.create_recipe(...)           [DSSRecipe]
→ recipe.get_definition()              [dict config]
→ recipe.run()                         [DSSFuture]
→ future.wait_for_result()             [dict result]
```

### Example 3: Train a model
```
Start: DSSClient
→ client.get_project("PROJECT_KEY")    [DSSProject]
→ project.get_ml_task("task_id")       [DSSMLTask]
→ ml_task.train("algorithm")           [DSSFuture]
→ future.wait_for_result()             [dict result]
→ project.get_saved_model("sm_id")     [DSSSavedModel]
→ saved_model.set_active_version()     [void]
```

### Example 4: Manage users
```
Start: DSSClient
→ client.create_user(login, ...)       [DSSUser]
→ user.get_settings()                  [DSSUserSettings]
→ user.get_activity()                  [DSSUserActivity]
→ client.get_authorization_matrix()    [DSSAuthorizationMatrix]
```

### Example 5: Deploy API
```
Start: DSSClient
→ client.get_apideployer()             [DSSAPIDeployer]
→ deployer.get_infra("infra_name")     [DSSAPIDeployerInfra]
→ infra.get_deployment("api_name")     [DSSAPIDeployerDeployment]
→ deployment.get_settings()            [DSSAPIDeployerDeploymentSettings]
```

---

## Document Statistics

| Aspect | Count |
|--------|-------|
| Total classes documented | 150+ |
| Main client classes | 7 |
| DSSClient methods | 114 |
| DSSProject methods | 154 |
| Total documented lines | 1500+ |
| Use case examples | 10+ |
| Pattern explanations | 14 |
| Workflow examples | 5+ |

---

## How to Use These Documents

1. **For learning**: Start with API_CLASS_INDEX.md to get the big picture, then drill down into COMPREHENSIVE_API_INVENTORY.md for details

2. **For reference**: Keep COMPREHENSIVE_API_INVENTORY.md handy when coding - it has all method signatures

3. **For troubleshooting**: Check the "Common Workflows" section to see if your use case is covered

4. **For discovering features**: Browse the class index by category to find related functionality

5. **For understanding patterns**: Read "Key Design Patterns" section to understand how the API works consistently

---

## API Entry Points

```python
# DSS Operations
from dataikuapi import DSSClient
client = DSSClient(host="http://localhost:11200", api_key="YOUR_KEY")

# Governance
from dataikuapi import GovernClient
govern = GovernClient(host, api_key)

# Cloud Infrastructure
from dataikuapi import FMClientAWS, FMClientAzure, FMClientGCP
fm_aws = FMClientAWS(host, api_key)

# API Services
from dataikuapi import APINodeClient
api_client = APINodeClient(host, api_key)
```

---

## Related Files in This Repository

- `dataikuapi/dssclient.py` - Main DSSClient implementation (2100+ lines)
- `dataikuapi/govern_client.py` - GovernClient implementation (800+ lines)
- `dataikuapi/fmclient.py` - FMClient variants (600+ lines)
- `dataikuapi/dss/` - 60+ modules for project-level objects
- `dataikuapi/govern/` - 15+ modules for governance
- `dataikuapi/fm/` - 10+ modules for fleet management

---

## Notes

- These documents reflect the current state of the Dataiku Python API client
- Class counts and method counts are based on code analysis of the repository
- All public methods (non-underscore) are included
- Return types are inferred from code analysis and documentation
- Builder patterns and creator classes are fully documented
- Async operations via DSSFuture are explained

---

**Last Updated**: 2024-11-21
**API Version**: Based on latest code in repository
**Completeness**: Comprehensive (150+ classes, 1000+ methods documented)

