# Week 1 Work Package Assignments

**Document Status:** Implementation Guide
**Created:** 2025-11-23
**Parent Spec:** [week-1-state-management.md](./week-1-state-management.md)

---

## Overview

This document breaks down Week 1 work into **9 independent packages** that can be developed in parallel across multiple branches/agents.

### Execution Strategy

1. **Branches:** Each package gets its own branch: `claude/week1-package-{N}-{name}`
2. **Integration:** Packages merge to main as they complete
3. **Testing:** Each package includes tests that must pass before merge
4. **Coordination:** StateManager (Package 7) integrates everything at the end

---

## Package Dependencies

```
Package 1: Core Data Models (independent)
    ↓
Package 2: State Backend ←──┐
Package 3: Sync Interface   │
Package 6: DiffEngine       │  ← All depend on Package 1
Package 8: JSON Schema ─────┘
    ↓
Package 4: Dataset Sync ←── Depends on Package 3
Package 5: Recipe Sync  ←── Depends on Package 3
    ↓
Package 7: StateManager ←── Depends on Packages 2, 3, 4, 5
    ↓
Package 9: Integration Tests ←── Depends on all packages
```

---

## Package 1: Core Data Models

**Branch:** `claude/week1-package-1-data-models`
**Status:** Ready to start
**Dependencies:** None
**Estimated Effort:** 4-6 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/__init__.py`
- `dataikuapi/iac/models/__init__.py`
- `dataikuapi/iac/models/state.py`
- `dataikuapi/iac/models/diff.py`
- `dataikuapi/iac/exceptions.py`
- `tests/iac/__init__.py`
- `tests/iac/test_state.py`
- `tests/iac/test_resource.py`

### Implementation Checklist

- [ ] Create `State` class with all methods (see spec section 1)
- [ ] Create `Resource` class with validation (see spec section 2)
- [ ] Create `ResourceMetadata` class
- [ ] Create `make_resource_id()` helper function
- [ ] Create all custom exceptions in `exceptions.py`
- [ ] Write unit tests for State (create, add, remove, list, to_dict, from_dict)
- [ ] Write unit tests for Resource (validation, checksum, has_changed)
- [ ] Test resource ID parsing (project_key, resource_name properties)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
# All tests pass
pytest tests/iac/test_state.py tests/iac/test_resource.py -v

# Coverage check
pytest tests/iac/test_state.py tests/iac/test_resource.py --cov=dataikuapi.iac.models --cov-report=term-missing
# Must show >90% coverage
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.models.state import (
    State,
    Resource,
    ResourceMetadata,
    make_resource_id
)

from dataikuapi.iac.models.diff import (
    ChangeType,
    ResourceDiff
)

from dataikuapi.iac.exceptions import (
    DataikuIaCError,
    StateNotFoundError,
    StateCorruptedError,
    StateWriteError,
    ResourceNotFoundError
)
```

---

## Package 2: State Backend

**Branch:** `claude/week1-package-2-state-backend`
**Status:** Blocked by Package 1
**Dependencies:** Package 1 (State, exceptions)
**Estimated Effort:** 3-4 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/backends/__init__.py`
- `dataikuapi/iac/backends/base.py`
- `dataikuapi/iac/backends/local.py`
- `tests/iac/test_backends.py`

### Implementation Checklist

- [ ] Create `StateBackend` abstract base class (see spec section 3)
- [ ] Implement `LocalFileBackend` (see spec section 4)
- [ ] Atomic writes (write to .tmp, then rename)
- [ ] Automatic backups on save
- [ ] Directory creation if doesn't exist
- [ ] Write unit tests for LocalFileBackend
- [ ] Test load/save/exists/delete/backup methods
- [ ] Test error handling (missing file, corrupted JSON, write failures)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
# All tests pass
pytest tests/iac/test_backends.py -v

# Coverage check
pytest tests/iac/test_backends.py --cov=dataikuapi.iac.backends --cov-report=term-missing
```

### Test Scenarios

```python
def test_save_creates_file(tmp_path):
    """Save creates state file"""
    backend = LocalFileBackend(tmp_path / "test.state.json")
    state = State(environment="test")
    backend.save(state)
    assert backend.exists()

def test_atomic_write(tmp_path):
    """Write uses temp file then rename"""
    # Implementation should write to .tmp first
    pass

def test_backup_on_save(tmp_path):
    """Saving creates backup of previous state"""
    # First save
    # Second save should create backup
    pass
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.backends.base import StateBackend
from dataikuapi.iac.backends.local import LocalFileBackend
```

---

## Package 3: Resource Sync Interface + Project

**Branch:** `claude/week1-package-3-sync-interface`
**Status:** Blocked by Package 1
**Dependencies:** Package 1 (Resource)
**Estimated Effort:** 4-5 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/sync/__init__.py`
- `dataikuapi/iac/sync/base.py`
- `dataikuapi/iac/sync/project.py`
- `tests/iac/test_sync_project.py`

### Implementation Checklist

- [ ] Create `ResourceSync` abstract base class (see spec section 5)
- [ ] Implement `ProjectSync` (see spec section 6)
- [ ] Handle project.get_settings() correctly
- [ ] Extract relevant project attributes
- [ ] Implement fetch() for single project
- [ ] Implement list_all() for all projects
- [ ] Write unit tests with mocked DSSClient
- [ ] Write integration tests (if Dataiku instance available)
- [ ] Test error handling (project not found)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
# All tests pass
pytest tests/iac/test_sync_project.py -v

# Coverage check
pytest tests/iac/test_sync_project.py --cov=dataikuapi.iac.sync --cov-report=term-missing
```

### Test Scenarios

```python
def test_fetch_project(mock_client):
    """Can fetch project from Dataiku"""
    sync = ProjectSync(mock_client)
    resource = sync.fetch("project.TEST_PROJECT")
    assert resource.resource_type == "project"
    assert resource.resource_id == "project.TEST_PROJECT"

def test_list_all_projects(mock_client):
    """Can list all projects"""
    # Mock client.list_projects() to return test data
    sync = ProjectSync(mock_client)
    resources = sync.list_all()
    assert len(resources) > 0
```

### Integration with dataikuapi

**Critical patterns:**

```python
# Get project
project = client.get_project(project_key)

# Get settings (returns settings object)
settings = project.get_settings()

# Access settings dict
settings_dict = settings.settings

# Extract attributes
attributes = {
    "projectKey": project_key,
    "name": settings_dict.get("name", ""),
    "description": settings_dict.get("description", ""),
    # ... more
}
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.sync.base import ResourceSync
from dataikuapi.iac.sync.project import ProjectSync
```

---

## Package 4: Dataset Sync

**Branch:** `claude/week1-package-4-dataset-sync`
**Status:** Blocked by Package 3
**Dependencies:** Package 3 (ResourceSync interface)
**Estimated Effort:** 3-4 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/sync/dataset.py`
- `tests/iac/test_sync_dataset.py`

### Implementation Checklist

- [ ] Implement `DatasetSync` (see spec section 7)
- [ ] Handle dataset.get_settings() correctly
- [ ] Extract relevant dataset attributes (type, params, schema, formatType)
- [ ] Implement fetch() for single dataset
- [ ] Implement list_all() requiring project_key
- [ ] Write unit tests with mocked DSSClient
- [ ] Test error handling (dataset not found, missing project_key)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
pytest tests/iac/test_sync_dataset.py -v
pytest tests/iac/test_sync_dataset.py --cov=dataikuapi.iac.sync.dataset --cov-report=term-missing
```

### Test Scenarios

```python
def test_fetch_dataset(mock_client):
    """Can fetch dataset from Dataiku"""
    sync = DatasetSync(mock_client)
    resource = sync.fetch("dataset.TEST_PROJECT.CUSTOMERS")
    assert resource.resource_type == "dataset"

def test_list_all_requires_project_key(mock_client):
    """list_all requires project_key"""
    sync = DatasetSync(mock_client)
    with pytest.raises(ValueError):
        sync.list_all()  # No project_key
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.sync.dataset import DatasetSync
```

---

## Package 5: Recipe Sync

**Branch:** `claude/week1-package-5-recipe-sync`
**Status:** Blocked by Package 3
**Dependencies:** Package 3 (ResourceSync interface)
**Estimated Effort:** 3-4 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/sync/recipe.py`
- `tests/iac/test_sync_recipe.py`

### Implementation Checklist

- [ ] Implement `RecipeSync` (see spec section 8)
- [ ] Handle recipe.get_settings() correctly
- [ ] Handle recipe.get_payload() for code recipes
- [ ] Extract relevant recipe attributes (type, inputs, outputs, params)
- [ ] Include code/payload when available
- [ ] Implement fetch() for single recipe
- [ ] Implement list_all() requiring project_key
- [ ] Write unit tests with mocked DSSClient
- [ ] Test both code recipes (with payload) and visual recipes
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
pytest tests/iac/test_sync_recipe.py -v
pytest tests/iac/test_sync_recipe.py --cov=dataikuapi.iac.sync.recipe --cov-report=term-missing
```

### Test Scenarios

```python
def test_fetch_python_recipe(mock_client):
    """Can fetch Python recipe with payload"""
    sync = RecipeSync(mock_client)
    resource = sync.fetch("recipe.TEST_PROJECT.prep_data")
    assert resource.attributes["type"] == "python"
    assert "payload" in resource.attributes

def test_fetch_visual_recipe(mock_client):
    """Can fetch visual recipe without payload"""
    # Visual recipes don't have payload
    pass
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.sync.recipe import RecipeSync
```

---

## Package 6: DiffEngine

**Branch:** `claude/week1-package-6-diff-engine`
**Status:** Blocked by Package 1
**Dependencies:** Package 1 (State, Resource)
**Estimated Effort:** 4-5 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/diff.py`
- `tests/iac/test_diff.py`

### Implementation Checklist

- [ ] Create `ChangeType` enum (see spec section 10)
- [ ] Create `ResourceDiff` class
- [ ] Implement `DiffEngine` class
- [ ] Implement diff() method (compare two states)
- [ ] Implement _diff_attributes() for detailed attribute diffs
- [ ] Implement summary() method
- [ ] Implement format_output() for human-readable output
- [ ] Write unit tests for all diff scenarios
- [ ] Test: added, removed, modified, unchanged resources
- [ ] Test: attribute-level diffs
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
pytest tests/iac/test_diff.py -v
pytest tests/iac/test_diff.py --cov=dataikuapi.iac.diff --cov-report=term-missing
```

### Test Scenarios

```python
def test_diff_detects_added_resources():
    """Diff identifies resources added in new state"""
    old_state = State()
    new_state = State()
    new_state.add_resource(Resource(...))

    engine = DiffEngine()
    diffs = engine.diff(old_state, new_state)

    assert len(diffs) == 1
    assert diffs[0].change_type == ChangeType.ADDED

def test_diff_detects_modified_attributes():
    """Diff identifies attribute changes"""
    # Create two resources with different attributes
    # Diff should show MODIFIED with attribute_diffs
    pass
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.diff import (
    DiffEngine,
    ResourceDiff,
    ChangeType
)
```

---

## Package 7: StateManager

**Branch:** `claude/week1-package-7-state-manager`
**Status:** Blocked by Packages 2, 3, 4, 5
**Dependencies:** StateBackend, all Sync implementations
**Estimated Effort:** 4-5 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/manager.py`
- `tests/iac/test_manager.py`

### Implementation Checklist

- [ ] Implement `StateManager` class (see spec section 9)
- [ ] Initialize with backend, client, environment
- [ ] Create sync registry for all resource types
- [ ] Implement load_state() with fallback to empty state
- [ ] Implement save_state()
- [ ] Implement sync_resource() with delegation
- [ ] Implement sync_project() with include_children option
- [ ] Implement sync_all() for complete sync
- [ ] Write unit tests with mocked dependencies
- [ ] Write integration tests with real Dataiku (if available)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
pytest tests/iac/test_manager.py -v
pytest tests/iac/test_manager.py --cov=dataikuapi.iac.manager --cov-report=term-missing
```

### Test Scenarios

```python
def test_load_state_creates_empty_if_not_exists(mock_backend, mock_client):
    """load_state returns empty state if file doesn't exist"""
    mock_backend.exists.return_value = False
    manager = StateManager(mock_backend, mock_client, "dev")
    state = manager.load_state()
    assert len(state.resources) == 0

def test_sync_project_includes_children(mock_backend, mock_client):
    """sync_project includes datasets and recipes when requested"""
    manager = StateManager(mock_backend, mock_client, "dev")
    state = manager.sync_project("TEST", include_children=True)
    # Should have project + datasets + recipes
    pass
```

### Interface Contract

**Exports from this package:**

```python
from dataikuapi.iac.manager import StateManager
```

---

## Package 8: JSON Schema Validation

**Branch:** `claude/week1-package-8-json-schema`
**Status:** Blocked by Package 1
**Dependencies:** Package 1 (State model)
**Estimated Effort:** 2-3 hours

### Deliverables

**Files to Create:**
- `dataikuapi/iac/schemas/state_v1.schema.json`
- `dataikuapi/iac/validation.py` (optional helper)
- `tests/iac/test_schema_validation.py`

### Implementation Checklist

- [ ] Create JSON Schema file (see spec "Data Schemas" section)
- [ ] Add jsonschema dependency to setup.py
- [ ] Update LocalFileBackend to validate on load
- [ ] Optional: Create validation helper functions
- [ ] Write tests for schema validation
- [ ] Test: valid state passes validation
- [ ] Test: invalid state fails validation (wrong version, missing fields, etc.)
- [ ] Achieve >90% test coverage

### Acceptance Criteria

```bash
pytest tests/iac/test_schema_validation.py -v

# Valid state should pass
# Invalid states should raise StateCorruptedError
```

### Test Scenarios

```python
def test_valid_state_passes_validation():
    """Valid state file passes JSON Schema validation"""
    # Create state, convert to dict, validate
    pass

def test_invalid_version_fails():
    """State with wrong version fails validation"""
    invalid_data = {"version": 999, ...}
    # Should raise validation error
    pass

def test_missing_required_fields_fails():
    """State missing required fields fails validation"""
    pass
```

### Integration with LocalFileBackend

Update `LocalFileBackend.load()` to include:

```python
import jsonschema
from pathlib import Path

def load(self) -> State:
    # ... existing code ...

    # Load schema
    schema_file = Path(__file__).parent / "schemas" / "state_v1.schema.json"
    with open(schema_file) as f:
        schema = json.load(f)

    # Validate
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise StateCorruptedError(f"State validation failed: {e.message}")

    # ... rest of code ...
```

### Interface Contract

**Exports from this package:**

```python
# Schema file available at:
# dataikuapi/iac/schemas/state_v1.schema.json

# Optional validation helper:
from dataikuapi.iac.validation import validate_state
```

---

## Package 9: Integration Tests

**Branch:** `claude/week1-package-9-integration`
**Status:** Blocked by all packages
**Dependencies:** All packages 1-8
**Estimated Effort:** 3-4 hours

### Deliverables

**Files to Create:**
- `tests/iac/test_integration.py`
- `tests/iac/fixtures/test_project.json` (optional)
- `tests/iac/conftest.py` (pytest fixtures)

### Implementation Checklist

- [ ] Create pytest fixtures for Dataiku client
- [ ] Create fixtures for test data (if using mocks)
- [ ] Implement end-to-end test scenarios (see spec section "Testing Strategy")
- [ ] Test: sync existing project from Dataiku
- [ ] Test: save and reload state
- [ ] Test: detect drift between state and Dataiku
- [ ] Test: complete workflow (sync → save → modify → sync → diff)
- [ ] Document how to run against real Dataiku instance
- [ ] Document test data requirements

### Acceptance Criteria

```bash
# Integration tests pass
pytest tests/iac/test_integration.py -v

# Can run against real Dataiku (with proper configuration)
export DATAIKU_HOST="https://..."
export DATAIKU_API_KEY="..."
pytest tests/iac/test_integration.py -v --real-dataiku
```

### Test Scenarios

See spec section "Integration Tests" for full scenarios.

**Key tests:**
1. Sync project with datasets and recipes
2. Save state to file
3. Load state from file
4. Verify state matches Dataiku
5. Detect drift when Dataiku changes
6. Generate accurate diffs

### Configuration

Create `tests/iac/conftest.py`:

```python
import pytest
import os
from dataikuapi import DSSClient
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.manager import StateManager

@pytest.fixture
def dataiku_host():
    return os.environ.get("DATAIKU_HOST", "https://dataiku-dev.company.com")

@pytest.fixture
def dataiku_api_key():
    return os.environ.get("DATAIKU_API_KEY", "test-key")

@pytest.fixture
def dataiku_client(dataiku_host, dataiku_api_key):
    return DSSClient(dataiku_host, dataiku_api_key)

@pytest.fixture
def state_manager(dataiku_client, tmp_path):
    backend = LocalFileBackend(tmp_path / "test.state.json")
    return StateManager(backend, dataiku_client, "test")
```

### Interface Contract

**Exports from this package:**

Integration tests don't export interfaces, but validate that all packages work together correctly.

---

## Coordination & Integration

### Branch Naming Convention

```
claude/week1-package-1-data-models
claude/week1-package-2-state-backend
claude/week1-package-3-sync-interface
claude/week1-package-4-dataset-sync
claude/week1-package-5-recipe-sync
claude/week1-package-6-diff-engine
claude/week1-package-7-state-manager
claude/week1-package-8-json-schema
claude/week1-package-9-integration
```

### Merge Order

1. **First Wave** (independent):
   - Package 1: Core Data Models
   - Merge to main immediately when complete

2. **Second Wave** (depends on Package 1):
   - Package 2: State Backend
   - Package 3: Sync Interface (includes ProjectSync)
   - Package 6: DiffEngine
   - Package 8: JSON Schema
   - Merge as each completes

3. **Third Wave** (depends on Package 3):
   - Package 4: Dataset Sync
   - Package 5: Recipe Sync
   - Merge as each completes

4. **Fourth Wave** (depends on Packages 2-5):
   - Package 7: StateManager
   - Merge when complete

5. **Final Wave** (depends on all):
   - Package 9: Integration Tests
   - Final validation before Week 1 complete

### Testing Before Merge

Each package must:
- [ ] Pass all unit tests
- [ ] Achieve >90% code coverage
- [ ] Pass linting (flake8, black, mypy)
- [ ] Include docstrings for all public APIs
- [ ] Update package __init__.py with exports

### Integration Checkpoints

**Checkpoint 1** (After Packages 1-3):
- Can create State and Resource objects
- Can save/load state from file
- Can sync projects from Dataiku

**Checkpoint 2** (After Packages 4-6):
- Can sync datasets and recipes
- Can compute diffs between states

**Checkpoint 3** (After Package 7):
- StateManager orchestrates all operations
- End-to-end workflow works

**Checkpoint 4** (After Packages 8-9):
- Schema validation works
- Integration tests pass
- Week 1 complete!

---

## Development Tools

### Running Tests

```bash
# Single package
pytest tests/iac/test_state.py -v

# With coverage
pytest tests/iac/ --cov=dataikuapi.iac --cov-report=html

# Integration tests only
pytest tests/iac/test_integration.py -v
```

### Code Quality

```bash
# Format code
black dataikuapi/iac/

# Lint
flake8 dataikuapi/iac/

# Type checking
mypy dataikuapi/iac/
```

### Documentation

Each module should have:
- Module-level docstring
- Class docstrings
- Method docstrings with Args/Returns/Raises

Example:
```python
class StateManager:
    """
    Main orchestrator for state management.

    Coordinates state operations including loading, saving, syncing
    with Dataiku, and comparing states.

    Example:
        >>> manager = StateManager(backend, client, "prod")
        >>> state = manager.sync_project("MY_PROJECT")
        >>> manager.save_state(state)
    """

    def sync_project(self, project_key: str,
                     include_children: bool = True) -> State:
        """
        Sync entire project and optionally its datasets/recipes.

        Args:
            project_key: Dataiku project key
            include_children: If True, include datasets and recipes

        Returns:
            State object with synced resources

        Raises:
            ResourceNotFoundError: If project doesn't exist
        """
        pass
```

---

## Communication

### Daily Standup (Async)

Each package owner reports:
1. **Completed yesterday:** What tasks finished
2. **Plan for today:** What tasks starting
3. **Blockers:** Any dependencies or issues

### Blocking Issues

If a package is blocked:
1. Post in coordination channel
2. Tag blocking package owner
3. Explore workarounds (mocks, stubs)

### Code Review

- All PRs require review before merge
- Focus on: correctness, test coverage, interface contracts
- Quick reviews (< 4 hours) to unblock dependent packages

---

## Success Metrics

Week 1 is complete when:

- [ ] All 9 packages merged to main
- [ ] All tests passing (unit + integration)
- [ ] >90% code coverage overall
- [ ] Demo script works end-to-end
- [ ] Documentation complete
- [ ] Ready to start Week 2 (plan/apply)

### Demo Script Location

`demos/week1_state_management.py` - See spec for full demo script

---

**Document Version:** 1.0
**Status:** Ready for Distribution
**Next Review:** Daily during Week 1 development
