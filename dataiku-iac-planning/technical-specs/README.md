# Technical Specifications - Week 1: State Management Foundation

**Phase:** POC Week 1
**Status:** Ready for Implementation
**Created:** 2025-11-23

---

## Overview

This directory contains detailed technical specifications for **Week 1: State Management Foundation** of the Dataiku IaC POC.

These specifications enable **parallel development** across multiple teams/agents by providing:
- Complete component interfaces
- Clear dependency graphs
- Independent work packages
- Comprehensive test requirements

---

## Documents

### 1. [Week 1 State Management Specification](./week-1-state-management.md)

**75+ pages** - Complete technical specification for state management foundation.

**Contents:**
- Architecture & component boundaries
- 10 detailed component specifications with code
- Data schemas (JSON Schema included)
- Implementation details
- Testing strategy (unit + integration)
- Integration with existing dataikuapi
- Demo script

**Use this for:** Understanding the complete system design and implementation details.

---

### 2. [Week 1 Work Packages](./week-1-work-packages.md)

**30+ pages** - Work breakdown for parallel development.

**Contents:**
- 9 independent parallelizable packages
- Dependency graph and execution waves
- Per-package deliverables and acceptance criteria
- Test scenarios for each package
- Branch naming conventions
- Integration checkpoints
- Merge strategy

**Use this for:** Assigning work to developers/agents and tracking progress.

---

## Quick Start

### For Developers

1. **Read the overview** in [week-1-state-management.md](./week-1-state-management.md#overview)
2. **Choose a package** from [week-1-work-packages.md](./week-1-work-packages.md#work-breakdown)
3. **Create your branch:** `claude/week1-package-{N}-{name}`
4. **Implement** following the spec
5. **Test** to >90% coverage
6. **Push** and create PR

### For Package Assignments

**Wave 1 (Independent - Start Immediately):**
- Package 1: Core Data Models
- Package 3: Sync Interface + Project
- Package 6: DiffEngine

**Wave 2 (Depends on Wave 1):**
- Package 2: State Backend
- Package 4: Dataset Sync
- Package 5: Recipe Sync
- Package 8: JSON Schema

**Wave 3 (Integration):**
- Package 7: StateManager

**Wave 4 (Validation):**
- Package 9: Integration Tests

---

## Key Technical Decisions

### 1. Resource ID System

Hierarchical IDs that track across environments:
```
project.CUSTOMER_ANALYTICS
dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
recipe.CUSTOMER_ANALYTICS.prep_customers
```

Dataiku internal IDs stored as metadata, not used as primary keys.

### 2. State Storage

- **Format:** JSON files
- **Location:** `.dataiku/state/{environment}.state.json`
- **Validation:** JSON Schema v1
- **Sync:** Full reconciliation (not delta)
- **Checksums:** SHA256 of attributes

### 3. Generic Resource Abstraction

Not hardcoded per resource type. Easy to extend to scenarios, models, dashboards.

### 4. Settings Normalization

Clean abstraction over Dataiku's `.settings.settings` pattern for future apply operations.

---

## Success Criteria

Week 1 is complete when:

- [ ] All 9 packages implemented and merged
- [ ] All tests passing (unit + integration)
- [ ] >90% code coverage overall
- [ ] Can track 1 project, 2 datasets, 1 recipe
- [ ] State sync works with real Dataiku
- [ ] Diff detects added/removed/modified
- [ ] Demo script works end-to-end
- [ ] Ready for Week 2 (plan/apply)

---

## Architecture Summary

```
StateManager (orchestrator)
    ├─→ StateBackend (storage)
    │   └─→ LocalFileBackend
    │
    ├─→ ResourceSync (Dataiku integration)
    │   ├─→ ProjectSync
    │   ├─→ DatasetSync
    │   └─→ RecipeSync
    │
    └─→ DiffEngine (comparison)

Data Models:
    ├─→ State (container)
    ├─→ Resource (generic resource)
    ├─→ ResourceMetadata (tracking info)
    └─→ ResourceDiff (change representation)
```

---

## File Structure (After Implementation)

```
dataikuapi/
└── iac/                          # New IaC module
    ├── __init__.py
    ├── models/
    │   ├── state.py              # State, Resource, ResourceMetadata
    │   └── diff.py               # ResourceDiff, ChangeType
    ├── backends/
    │   ├── base.py               # StateBackend interface
    │   └── local.py              # LocalFileBackend
    ├── sync/
    │   ├── base.py               # ResourceSync interface
    │   ├── project.py            # ProjectSync
    │   ├── dataset.py            # DatasetSync
    │   └── recipe.py             # RecipeSync
    ├── manager.py                # StateManager
    ├── diff.py                   # DiffEngine
    ├── exceptions.py             # Custom exceptions
    └── schemas/
        └── state_v1.schema.json  # JSON Schema

tests/
└── iac/
    ├── test_state.py
    ├── test_resource.py
    ├── test_backends.py
    ├── test_sync_project.py
    ├── test_sync_dataset.py
    ├── test_sync_recipe.py
    ├── test_manager.py
    ├── test_diff.py
    ├── test_integration.py
    └── fixtures/
```

---

## Dependencies

Add to `setup.py` or `pyproject.toml`:

```python
install_requires=[
    "dataikuapi>=14.1.3",
    "jsonschema>=4.0.0",
]
```

---

## Next Steps After Week 1

**Week 2: Plan Workflow**
- YAML configuration parser
- Configuration → Desired State
- Plan generation (diff + validation)
- Plan output formatting

**Week 3: Apply with Checkpointing**
- Execution engine
- Project create/update operations
- Dataset create/update operations
- Resume capability from checkpoint

**Week 4: Demo & Validation**
- End-to-end demo
- Feedback collection
- Go/no-go decision for Phase 1

---

## Questions or Issues?

- **Specification questions:** See detailed spec in [week-1-state-management.md](./week-1-state-management.md)
- **Package assignment:** See [week-1-work-packages.md](./week-1-work-packages.md)
- **Implementation blockers:** Coordinate via team channel
- **Spec updates needed:** Create issue or discuss with team lead

---

**Document Version:** 1.0
**Last Updated:** 2025-11-23
**Maintained By:** Development Team
