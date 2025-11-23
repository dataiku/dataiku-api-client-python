# Week 1 Technical Specification: State Management Foundation

**Document Status:** Detailed Implementation Spec
**Created:** 2025-11-23
**Phase:** POC Week 1
**Dependencies:** None (foundational)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Specifications](#component-specifications)
4. [Data Schemas](#data-schemas)
5. [Implementation Details](#implementation-details)
6. [Work Breakdown](#work-breakdown)
7. [Testing Strategy](#testing-strategy)
8. [Integration Points](#integration-points)

---

## Overview

### Objectives

Build the foundational state management system that:
- Tracks Dataiku resources (projects, datasets, recipes) in a state file
- Syncs state with actual Dataiku instances
- Detects differences between desired and actual state
- Provides basis for plan/apply workflow in Week 2+

### Success Criteria

- [ ] State file format defined and validated with JSON Schema
- [ ] Can track 1 project, 2 datasets, 1 recipe in state
- [ ] Sync algorithm accurately reflects Dataiku resources
- [ ] Diff algorithm identifies: added, removed, modified resources
- [ ] All components have >90% test coverage
- [ ] Documentation allows parallel development of Week 2 features

### Non-Goals for Week 1

- ❌ Apply/execution logic (Week 3)
- ❌ YAML config parsing (Week 2)
- ❌ Remote state backends (Phase 1, Month 3)
- ❌ Complex recipes or visual recipes (Week 2+)

---

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────┐
│ Week 1 Scope                                            │
│                                                         │
│  ┌─────────────────┐                                   │
│  │ StateManager    │ ← Main orchestrator                │
│  └────────┬────────┘                                   │
│           │                                             │
│           ├──→ StateBackend (load/save state)          │
│           │     └─→ LocalFileBackend                   │
│           │                                             │
│           ├──→ ResourceSync (sync with Dataiku)        │
│           │     ├─→ ProjectSync                        │
│           │     ├─→ DatasetSync                        │
│           │     └─→ RecipeSync                         │
│           │                                             │
│           └──→ DiffEngine (compare states)             │
│                                                         │
│  Data Models:                                          │
│  ├─→ State (container for all resources)              │
│  ├─→ Resource (generic resource representation)        │
│  └─→ ResourceDiff (change representation)             │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
              ┌───────────────────────┐
              │ dataikuapi            │
              │ (existing library)    │
              └───────────────────────┘
```

### Component Boundaries

**StateManager** (Orchestrator)
- Coordinates all state operations
- Delegates to backends and sync engines
- Public API for Week 2+ features

**StateBackend** (Storage Interface)
- Abstract interface for state persistence
- LocalFileBackend implementation for Week 1
- Extensible to S3Backend in Phase 1

**ResourceSync** (Dataiku Integration)
- Queries Dataiku for current state
- Converts Dataiku API responses to Resource objects
- Type-specific sync logic (Project/Dataset/Recipe)

**DiffEngine** (Comparison)
- Compares two State objects
- Identifies added/removed/modified resources
- Generates structured diff output

**SettingsManager** (Normalization)
- Abstracts Dataiku's settings pattern
- Provides path-based get/set interface
- Handles settings dict manipulation

---

## Component Specifications

### 1. State (Data Model)

**Purpose:** Container for all tracked resources

**Interface:**
```python
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime

@dataclass
class State:
    """
    Represents the complete state of tracked Dataiku resources.

    Attributes:
        version: State file format version (currently 1)
        serial: Incrementing counter for state changes
        lineage: Git commit or identifier for tracking
        environment: Target environment (dev, prod, etc.)
        updated_at: Last update timestamp
        resources: Map of resource_id -> Resource
    """
    version: int = 1
    serial: int = 0
    lineage: Optional[str] = None
    environment: str = ""
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resources: Dict[str, 'Resource'] = field(default_factory=dict)

    def get_resource(self, resource_id: str) -> Optional['Resource']:
        """Get resource by ID"""
        return self.resources.get(resource_id)

    def add_resource(self, resource: 'Resource') -> None:
        """Add or update resource"""
        self.resources[resource.resource_id] = resource
        self.serial += 1
        self.updated_at = datetime.utcnow()

    def remove_resource(self, resource_id: str) -> Optional['Resource']:
        """Remove resource, return removed resource or None"""
        resource = self.resources.pop(resource_id, None)
        if resource:
            self.serial += 1
            self.updated_at = datetime.utcnow()
        return resource

    def has_resource(self, resource_id: str) -> bool:
        """Check if resource exists"""
        return resource_id in self.resources

    def list_resources(self, resource_type: Optional[str] = None) -> list['Resource']:
        """List all resources, optionally filtered by type"""
        resources = self.resources.values()
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        return list(resources)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "version": self.version,
            "serial": self.serial,
            "lineage": self.lineage,
            "environment": self.environment,
            "updated_at": self.updated_at.isoformat(),
            "resources": {
                rid: resource.to_dict()
                for rid, resource in self.resources.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'State':
        """Create from dict"""
        resources = {
            rid: Resource.from_dict(rdata)
            for rid, rdata in data.get("resources", {}).items()
        }
        return cls(
            version=data.get("version", 1),
            serial=data.get("serial", 0),
            lineage=data.get("lineage"),
            environment=data.get("environment", ""),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            resources=resources
        )
```

**Testing Requirements:**
- [ ] Can create empty state
- [ ] Can add/remove/get resources
- [ ] Serial increments on changes
- [ ] to_dict/from_dict round-trip preserves data
- [ ] list_resources filters correctly

---

### 2. Resource (Data Model)

**Purpose:** Generic representation of any Dataiku resource

**Interface:**
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

@dataclass
class ResourceMetadata:
    """Tracking metadata for a resource"""
    deployed_at: datetime
    deployed_by: str
    dataiku_internal_id: Optional[str] = None
    checksum: str = ""

    def to_dict(self) -> dict:
        return {
            "deployed_at": self.deployed_at.isoformat(),
            "deployed_by": self.deployed_by,
            "dataiku_internal_id": self.dataiku_internal_id,
            "checksum": self.checksum
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ResourceMetadata':
        return cls(
            deployed_at=datetime.fromisoformat(data["deployed_at"]),
            deployed_by=data["deployed_by"],
            dataiku_internal_id=data.get("dataiku_internal_id"),
            checksum=data.get("checksum", "")
        )


@dataclass
class Resource:
    """
    Generic resource representation.

    Resource ID Format:
        {resource_type}.{project_key}[.{resource_name}]

    Examples:
        - project.CUSTOMER_ANALYTICS
        - dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
        - recipe.CUSTOMER_ANALYTICS.prep_customers
        - model.CUSTOMER_ANALYTICS.churn_prediction

    Attributes:
        resource_type: Type of resource (project, dataset, recipe, etc.)
        resource_id: Unique identifier (see format above)
        attributes: Resource-specific attributes from Dataiku
        metadata: Tracking metadata (deployment info, checksums, etc.)
    """
    resource_type: str
    resource_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: ResourceMetadata = field(default_factory=lambda: ResourceMetadata(
        deployed_at=datetime.utcnow(),
        deployed_by="system"
    ))

    def __post_init__(self):
        """Validate and compute checksum"""
        self._validate_resource_id()
        if not self.metadata.checksum:
            self.metadata.checksum = self.compute_checksum()

    def _validate_resource_id(self) -> None:
        """Validate resource_id format"""
        parts = self.resource_id.split('.')

        if len(parts) < 2:
            raise ValueError(
                f"Invalid resource_id format: {self.resource_id}. "
                f"Expected: {self.resource_type}.PROJECT_KEY[.RESOURCE_NAME]"
            )

        if parts[0] != self.resource_type:
            raise ValueError(
                f"resource_id prefix '{parts[0]}' doesn't match "
                f"resource_type '{self.resource_type}'"
            )

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of attributes"""
        # Sort keys for consistent hashing
        normalized = json.dumps(self.attributes, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()

    def has_changed(self, other: 'Resource') -> bool:
        """Check if resource has changed compared to another"""
        if self.resource_id != other.resource_id:
            raise ValueError("Cannot compare different resources")
        return self.compute_checksum() != other.compute_checksum()

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "attributes": self.attributes,
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Resource':
        """Create from dict"""
        return cls(
            resource_type=data["resource_type"],
            resource_id=data["resource_id"],
            attributes=data.get("attributes", {}),
            metadata=ResourceMetadata.from_dict(data.get("metadata", {}))
        )

    @property
    def project_key(self) -> str:
        """Extract project key from resource_id"""
        parts = self.resource_id.split('.')
        return parts[1] if len(parts) > 1 else ""

    @property
    def resource_name(self) -> str:
        """Extract resource name from resource_id"""
        parts = self.resource_id.split('.')
        return parts[2] if len(parts) > 2 else ""


def make_resource_id(resource_type: str, project_key: str,
                     resource_name: Optional[str] = None) -> str:
    """
    Helper to construct resource IDs.

    Examples:
        make_resource_id("project", "CUSTOMER_ANALYTICS")
        -> "project.CUSTOMER_ANALYTICS"

        make_resource_id("dataset", "CUSTOMER_ANALYTICS", "RAW_CUSTOMERS")
        -> "dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS"
    """
    if resource_name:
        return f"{resource_type}.{project_key}.{resource_name}"
    return f"{resource_type}.{project_key}"
```

**Testing Requirements:**
- [ ] Resource ID validation works correctly
- [ ] Checksum computation is deterministic
- [ ] has_changed detects attribute differences
- [ ] to_dict/from_dict round-trip
- [ ] project_key/resource_name extraction
- [ ] make_resource_id helper function

---

### 3. StateBackend (Interface)

**Purpose:** Abstract interface for state persistence

**Interface:**
```python
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

class StateBackend(ABC):
    """
    Abstract interface for state storage backends.

    Implementations:
        - LocalFileBackend (Week 1)
        - S3Backend (Phase 1, Month 3)
        - GitBackend (future)
    """

    @abstractmethod
    def load(self) -> State:
        """
        Load state from backend.

        Returns:
            State object

        Raises:
            StateNotFoundError: If state doesn't exist
            StateCorruptedError: If state is invalid
        """
        pass

    @abstractmethod
    def save(self, state: State) -> None:
        """
        Save state to backend.

        Args:
            state: State to persist

        Raises:
            StateWriteError: If save fails
        """
        pass

    @abstractmethod
    def exists(self) -> bool:
        """Check if state exists"""
        pass

    @abstractmethod
    def delete(self) -> None:
        """Delete state (use with caution)"""
        pass

    @abstractmethod
    def backup(self, suffix: str = "backup") -> Path:
        """
        Create backup of current state.

        Args:
            suffix: Backup file suffix

        Returns:
            Path to backup file
        """
        pass
```

**Testing Requirements:**
- Tests defined at interface level
- Each backend implementation must pass all tests
- Mock backend for testing other components

---

### 4. LocalFileBackend (Implementation)

**Purpose:** File-based state storage for local development

**Implementation:**
```python
import json
from pathlib import Path
from typing import Optional
import shutil

class StateNotFoundError(Exception):
    """State file doesn't exist"""
    pass

class StateCorruptedError(Exception):
    """State file is invalid"""
    pass

class StateWriteError(Exception):
    """Failed to write state"""
    pass


class LocalFileBackend(StateBackend):
    """
    Local file-based state storage.

    Storage location: .dataiku/state/{environment}.state.json

    Features:
        - Atomic writes (write to temp, then rename)
        - Automatic backups on save
        - JSON Schema validation
    """

    def __init__(self, state_file: Path):
        """
        Args:
            state_file: Path to state file
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> State:
        """Load state from file"""
        if not self.exists():
            raise StateNotFoundError(f"State file not found: {self.state_file}")

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            # TODO: Add JSON Schema validation here

            return State.from_dict(data)

        except json.JSONDecodeError as e:
            raise StateCorruptedError(f"Invalid JSON in state file: {e}")
        except Exception as e:
            raise StateCorruptedError(f"Failed to parse state: {e}")

    def save(self, state: State) -> None:
        """Save state to file atomically"""
        try:
            # Backup existing state if it exists
            if self.exists():
                self.backup(suffix=f"pre-serial-{state.serial}")

            # Write to temp file first
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)

            # Atomic rename
            temp_file.rename(self.state_file)

        except Exception as e:
            raise StateWriteError(f"Failed to save state: {e}")

    def exists(self) -> bool:
        """Check if state file exists"""
        return self.state_file.exists()

    def delete(self) -> None:
        """Delete state file"""
        if self.exists():
            self.state_file.unlink()

    def backup(self, suffix: str = "backup") -> Path:
        """Create backup of state file"""
        if not self.exists():
            raise StateNotFoundError("No state to backup")

        backup_file = self.state_file.with_suffix(f'.{suffix}.json')
        shutil.copy2(self.state_file, backup_file)
        return backup_file
```

**Testing Requirements:**
- [ ] Save creates file with valid JSON
- [ ] Load reads and parses state correctly
- [ ] Atomic write (temp file, then rename)
- [ ] Automatic backup on save
- [ ] Handles missing state file
- [ ] Handles corrupted JSON
- [ ] Directory creation if doesn't exist

---

### 5. ResourceSync (Interface)

**Purpose:** Sync Dataiku resources into state

**Interface:**
```python
from abc import ABC, abstractmethod
from dataikuapi import DSSClient

class ResourceSync(ABC):
    """
    Abstract interface for syncing resources from Dataiku.

    Each resource type (project, dataset, recipe) has its own implementation.
    """

    def __init__(self, client: DSSClient):
        """
        Args:
            client: Dataiku API client
        """
        self.client = client

    @abstractmethod
    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch single resource from Dataiku.

        Args:
            resource_id: Full resource ID (e.g., "project.CUSTOMER_ANALYTICS")

        Returns:
            Resource object

        Raises:
            ResourceNotFoundError: If resource doesn't exist in Dataiku
        """
        pass

    @abstractmethod
    def list_all(self, project_key: Optional[str] = None) -> list[Resource]:
        """
        List all resources of this type.

        Args:
            project_key: Optional filter by project

        Returns:
            List of Resource objects
        """
        pass

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type identifier"""
        pass
```

---

### 6. ProjectSync (Implementation)

**Purpose:** Sync projects from Dataiku

**Implementation:**
```python
class ProjectSync(ResourceSync):
    """Sync projects from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "project"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch project from Dataiku.

        Args:
            resource_id: "project.PROJECT_KEY"
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 2 or parts[0] != "project":
            raise ValueError(f"Invalid project resource_id: {resource_id}")

        project_key = parts[1]

        try:
            # Get project from Dataiku
            project = self.client.get_project(project_key)

            # Get settings
            settings = project.get_settings()

            # Build attributes dict
            attributes = {
                "projectKey": project_key,
                "name": settings.settings.get("name", ""),
                "description": settings.settings.get("description", ""),
                "shortDesc": settings.settings.get("shortDesc", ""),
                "tags": settings.settings.get("tags", []),
                "checklists": settings.settings.get("checklists", {}),
                # Add other relevant settings
            }

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",  # TODO: get actual user
                dataiku_internal_id=None  # Projects use key as ID
            )

            return Resource(
                resource_type="project",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(f"Project {project_key} not found: {e}")

    def list_all(self, project_key: Optional[str] = None) -> list[Resource]:
        """List all projects (project_key filter ignored for projects)"""
        try:
            projects = self.client.list_projects()
            resources = []

            for project_info in projects:
                project_key = project_info["projectKey"]
                resource_id = make_resource_id("project", project_key)

                # Fetch full details for each project
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list projects: {e}")
```

**Testing Requirements:**
- [ ] Can fetch existing project
- [ ] Raises error for non-existent project
- [ ] Attributes include key settings
- [ ] list_all returns all projects
- [ ] Resource ID format is correct

---

### 7. DatasetSync (Implementation)

**Purpose:** Sync datasets from Dataiku

**Implementation:**
```python
class DatasetSync(ResourceSync):
    """Sync datasets from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "dataset"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch dataset from Dataiku.

        Args:
            resource_id: "dataset.PROJECT_KEY.DATASET_NAME"
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 3 or parts[0] != "dataset":
            raise ValueError(f"Invalid dataset resource_id: {resource_id}")

        project_key = parts[1]
        dataset_name = parts[2]

        try:
            # Get dataset from Dataiku
            project = self.client.get_project(project_key)
            dataset = project.get_dataset(dataset_name)

            # Get settings
            settings = dataset.get_settings()

            # Build attributes dict
            attributes = {
                "name": dataset_name,
                "type": settings.settings.get("type", ""),
                "params": settings.settings.get("params", {}),
                "schema": settings.settings.get("schema", {}),
                "formatType": settings.settings.get("formatType", ""),
                "tags": settings.settings.get("tags", []),
            }

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",
                dataiku_internal_id=dataset_name  # Datasets use name within project
            )

            return Resource(
                resource_type="dataset",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(
                f"Dataset {project_key}.{dataset_name} not found: {e}"
            )

    def list_all(self, project_key: Optional[str] = None) -> list[Resource]:
        """List all datasets, optionally filtered by project"""
        if not project_key:
            raise ValueError("project_key required for listing datasets")

        try:
            project = self.client.get_project(project_key)
            datasets = project.list_datasets()
            resources = []

            for dataset_info in datasets:
                dataset_name = dataset_info["name"]
                resource_id = make_resource_id("dataset", project_key, dataset_name)

                # Fetch full details
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list datasets for {project_key}: {e}")
```

**Testing Requirements:**
- [ ] Can fetch existing dataset
- [ ] Raises error for non-existent dataset
- [ ] Attributes include type, params, schema
- [ ] list_all requires project_key
- [ ] list_all returns all datasets in project

---

### 8. RecipeSync (Implementation)

**Purpose:** Sync recipes from Dataiku

**Implementation:**
```python
class RecipeSync(ResourceSync):
    """Sync recipes from Dataiku"""

    @property
    def resource_type(self) -> str:
        return "recipe"

    def fetch(self, resource_id: str) -> Resource:
        """
        Fetch recipe from Dataiku.

        Args:
            resource_id: "recipe.PROJECT_KEY.RECIPE_NAME"
        """
        # Parse resource_id
        parts = resource_id.split('.')
        if len(parts) != 3 or parts[0] != "recipe":
            raise ValueError(f"Invalid recipe resource_id: {resource_id}")

        project_key = parts[1]
        recipe_name = parts[2]

        try:
            # Get recipe from Dataiku
            project = self.client.get_project(project_key)
            recipe = project.get_recipe(recipe_name)

            # Get settings
            settings = recipe.get_settings()

            # Get payload (code for code recipes)
            payload = None
            recipe_type = settings.settings.get("type", "")
            if recipe_type in ["python", "sql", "r"]:
                try:
                    payload = recipe.get_payload()
                except:
                    payload = None

            # Build attributes dict
            attributes = {
                "name": recipe_name,
                "type": recipe_type,
                "inputs": settings.settings.get("inputs", {}),
                "outputs": settings.settings.get("outputs", {}),
                "params": settings.settings.get("params", {}),
                "tags": settings.settings.get("tags", []),
            }

            # Include code if available
            if payload:
                attributes["payload"] = payload

            # Create resource
            metadata = ResourceMetadata(
                deployed_at=datetime.utcnow(),
                deployed_by="system",
                dataiku_internal_id=recipe_name
            )

            return Resource(
                resource_type="recipe",
                resource_id=resource_id,
                attributes=attributes,
                metadata=metadata
            )

        except Exception as e:
            raise ResourceNotFoundError(
                f"Recipe {project_key}.{recipe_name} not found: {e}"
            )

    def list_all(self, project_key: Optional[str] = None) -> list[Resource]:
        """List all recipes, optionally filtered by project"""
        if not project_key:
            raise ValueError("project_key required for listing recipes")

        try:
            project = self.client.get_project(project_key)
            recipes = project.list_recipes()
            resources = []

            for recipe_info in recipes:
                recipe_name = recipe_info["name"]
                resource_id = make_resource_id("recipe", project_key, recipe_name)

                # Fetch full details
                resource = self.fetch(resource_id)
                resources.append(resource)

            return resources

        except Exception as e:
            raise RuntimeError(f"Failed to list recipes for {project_key}: {e}")
```

**Testing Requirements:**
- [ ] Can fetch existing recipe
- [ ] Raises error for non-existent recipe
- [ ] Attributes include type, inputs, outputs
- [ ] Payload included for code recipes
- [ ] list_all requires project_key

---

### 9. StateManager (Orchestrator)

**Purpose:** Main coordinator for state operations

**Interface:**
```python
from typing import Optional, List

class StateManager:
    """
    Main orchestrator for state management.

    Coordinates:
        - Loading/saving state via backend
        - Syncing with Dataiku
        - Comparing states
    """

    def __init__(self,
                 backend: StateBackend,
                 client: DSSClient,
                 environment: str):
        """
        Args:
            backend: State storage backend
            client: Dataiku API client
            environment: Target environment name
        """
        self.backend = backend
        self.client = client
        self.environment = environment

        # Initialize sync engines
        self.project_sync = ProjectSync(client)
        self.dataset_sync = DatasetSync(client)
        self.recipe_sync = RecipeSync(client)

        self._sync_registry = {
            "project": self.project_sync,
            "dataset": self.dataset_sync,
            "recipe": self.recipe_sync,
        }

    def load_state(self) -> State:
        """
        Load state from backend.

        Returns:
            State object, or empty state if doesn't exist
        """
        if self.backend.exists():
            return self.backend.load()
        else:
            # Return empty state
            return State(environment=self.environment)

    def save_state(self, state: State) -> None:
        """Save state to backend"""
        state.environment = self.environment
        self.backend.save(state)

    def sync_resource(self, resource_id: str) -> Resource:
        """
        Sync single resource from Dataiku.

        Args:
            resource_id: Resource to sync

        Returns:
            Updated Resource object
        """
        resource_type = resource_id.split('.')[0]

        if resource_type not in self._sync_registry:
            raise ValueError(f"Unknown resource type: {resource_type}")

        sync_engine = self._sync_registry[resource_type]
        return sync_engine.fetch(resource_id)

    def sync_project(self, project_key: str, include_children: bool = True) -> State:
        """
        Sync entire project and optionally its datasets/recipes.

        Args:
            project_key: Project to sync
            include_children: Include datasets and recipes

        Returns:
            State with synced resources
        """
        state = State(environment=self.environment)

        # Sync project
        project_id = make_resource_id("project", project_key)
        project_resource = self.project_sync.fetch(project_id)
        state.add_resource(project_resource)

        if include_children:
            # Sync datasets
            for dataset_resource in self.dataset_sync.list_all(project_key):
                state.add_resource(dataset_resource)

            # Sync recipes
            for recipe_resource in self.recipe_sync.list_all(project_key):
                state.add_resource(recipe_resource)

        return state

    def sync_all(self) -> State:
        """
        Sync all accessible projects and resources.

        Returns:
            State with all synced resources
        """
        state = State(environment=self.environment)

        # Get all projects
        for project_resource in self.project_sync.list_all():
            state.add_resource(project_resource)

            project_key = project_resource.project_key

            # Get datasets and recipes for each project
            for dataset_resource in self.dataset_sync.list_all(project_key):
                state.add_resource(dataset_resource)

            for recipe_resource in self.recipe_sync.list_all(project_key):
                state.add_resource(recipe_resource)

        return state
```

**Testing Requirements:**
- [ ] load_state returns empty state if doesn't exist
- [ ] load_state loads from backend if exists
- [ ] save_state persists to backend
- [ ] sync_resource delegates to correct sync engine
- [ ] sync_project includes children when requested
- [ ] sync_all handles multiple projects

---

### 10. DiffEngine (Comparison)

**Purpose:** Compare states and identify changes

**Interface:**
```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ChangeType(Enum):
    """Type of change"""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

@dataclass
class ResourceDiff:
    """Represents a change to a resource"""
    change_type: ChangeType
    resource_id: str
    resource_type: str
    old_resource: Optional[Resource] = None
    new_resource: Optional[Resource] = None
    attribute_diffs: dict = None

    def __str__(self) -> str:
        """Human-readable representation"""
        symbol = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.MODIFIED: "~",
            ChangeType.UNCHANGED: " ",
        }[self.change_type]

        return f"{symbol} {self.resource_id}"


class DiffEngine:
    """
    Compare two states and generate diff.

    Identifies:
        - Resources added in new state
        - Resources removed from old state
        - Resources modified between states
        - Resources unchanged
    """

    def diff(self, old_state: State, new_state: State) -> List[ResourceDiff]:
        """
        Compare two states.

        Args:
            old_state: Previous state
            new_state: Current state

        Returns:
            List of ResourceDiff objects
        """
        diffs = []

        old_ids = set(old_state.resources.keys())
        new_ids = set(new_state.resources.keys())

        # Resources added
        for resource_id in new_ids - old_ids:
            diffs.append(ResourceDiff(
                change_type=ChangeType.ADDED,
                resource_id=resource_id,
                resource_type=new_state.resources[resource_id].resource_type,
                new_resource=new_state.resources[resource_id]
            ))

        # Resources removed
        for resource_id in old_ids - new_ids:
            diffs.append(ResourceDiff(
                change_type=ChangeType.REMOVED,
                resource_id=resource_id,
                resource_type=old_state.resources[resource_id].resource_type,
                old_resource=old_state.resources[resource_id]
            ))

        # Resources potentially modified
        for resource_id in old_ids & new_ids:
            old_resource = old_state.resources[resource_id]
            new_resource = new_state.resources[resource_id]

            if old_resource.has_changed(new_resource):
                # Detailed attribute diff
                attr_diffs = self._diff_attributes(
                    old_resource.attributes,
                    new_resource.attributes
                )

                diffs.append(ResourceDiff(
                    change_type=ChangeType.MODIFIED,
                    resource_id=resource_id,
                    resource_type=new_resource.resource_type,
                    old_resource=old_resource,
                    new_resource=new_resource,
                    attribute_diffs=attr_diffs
                ))
            else:
                # Unchanged (optional: exclude from output)
                diffs.append(ResourceDiff(
                    change_type=ChangeType.UNCHANGED,
                    resource_id=resource_id,
                    resource_type=new_resource.resource_type,
                    old_resource=old_resource,
                    new_resource=new_resource
                ))

        return diffs

    def _diff_attributes(self, old_attrs: dict, new_attrs: dict) -> dict:
        """
        Detailed diff of attribute dictionaries.

        Returns:
            Dict with keys: added, removed, modified
        """
        old_keys = set(old_attrs.keys())
        new_keys = set(new_attrs.keys())

        result = {
            "added": {},
            "removed": {},
            "modified": {}
        }

        # Added attributes
        for key in new_keys - old_keys:
            result["added"][key] = new_attrs[key]

        # Removed attributes
        for key in old_keys - new_keys:
            result["removed"][key] = old_attrs[key]

        # Modified attributes
        for key in old_keys & new_keys:
            if old_attrs[key] != new_attrs[key]:
                result["modified"][key] = {
                    "old": old_attrs[key],
                    "new": new_attrs[key]
                }

        return result

    def summary(self, diffs: List[ResourceDiff]) -> dict:
        """
        Summarize diffs.

        Returns:
            Dict with counts: {added: N, removed: N, modified: N, unchanged: N}
        """
        summary = {
            "added": 0,
            "removed": 0,
            "modified": 0,
            "unchanged": 0
        }

        for diff in diffs:
            summary[diff.change_type.value] += 1

        return summary

    def format_output(self, diffs: List[ResourceDiff],
                     include_unchanged: bool = False) -> str:
        """
        Format diffs for human readability.

        Args:
            diffs: List of diffs
            include_unchanged: Show unchanged resources

        Returns:
            Formatted string
        """
        lines = []

        # Summary
        summary = self.summary(diffs)
        lines.append(f"Diff Summary:")
        lines.append(f"  {summary['added']} added")
        lines.append(f"  {summary['removed']} removed")
        lines.append(f"  {summary['modified']} modified")
        if include_unchanged:
            lines.append(f"  {summary['unchanged']} unchanged")
        lines.append("")

        # Details
        for diff in diffs:
            if diff.change_type == ChangeType.UNCHANGED and not include_unchanged:
                continue

            lines.append(str(diff))

            if diff.change_type == ChangeType.MODIFIED and diff.attribute_diffs:
                for key, change in diff.attribute_diffs.get("modified", {}).items():
                    lines.append(f"    {key}: {change['old']} → {change['new']}")

        return "\n".join(lines)
```

**Testing Requirements:**
- [ ] Detects added resources
- [ ] Detects removed resources
- [ ] Detects modified resources (checksum change)
- [ ] Detailed attribute diffs
- [ ] Summary counts are correct
- [ ] Format output is readable

---

## Data Schemas

### State File JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Dataiku IaC State File",
  "type": "object",
  "required": ["version", "serial", "updated_at", "resources"],
  "properties": {
    "version": {
      "type": "integer",
      "const": 1,
      "description": "State file format version"
    },
    "serial": {
      "type": "integer",
      "minimum": 0,
      "description": "Incrementing counter for state changes"
    },
    "lineage": {
      "type": ["string", "null"],
      "description": "Git commit or identifier"
    },
    "environment": {
      "type": "string",
      "description": "Target environment (dev, prod, etc.)"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Last update timestamp (ISO 8601)"
    },
    "resources": {
      "type": "object",
      "description": "Map of resource_id to resource",
      "additionalProperties": {
        "$ref": "#/definitions/resource"
      }
    }
  },
  "definitions": {
    "resource": {
      "type": "object",
      "required": ["resource_type", "resource_id", "attributes", "metadata"],
      "properties": {
        "resource_type": {
          "type": "string",
          "enum": ["project", "dataset", "recipe", "scenario", "model"]
        },
        "resource_id": {
          "type": "string",
          "pattern": "^[a-z_]+\\.[A-Z][A-Z0-9_]*(\\.[A-Z][A-Za-z0-9_]*)?$",
          "description": "Format: {type}.{PROJECT}[.{NAME}]"
        },
        "attributes": {
          "type": "object",
          "description": "Resource-specific attributes"
        },
        "metadata": {
          "$ref": "#/definitions/metadata"
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["deployed_at", "deployed_by", "checksum"],
      "properties": {
        "deployed_at": {
          "type": "string",
          "format": "date-time"
        },
        "deployed_by": {
          "type": "string"
        },
        "dataiku_internal_id": {
          "type": ["string", "null"]
        },
        "checksum": {
          "type": "string",
          "pattern": "^[a-f0-9]{64}$",
          "description": "SHA256 checksum of attributes"
        }
      }
    }
  }
}
```

**Validation:**
- Create `dataiku_iac/schemas/state_v1.schema.json`
- Use `jsonschema` library to validate
- Validation happens on load and save

---

## Implementation Details

### Project Structure

```
dataiku-api-client-python/
├── dataikuapi/
│   └── iac/                          # New IaC module
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── state.py              # State, Resource, ResourceMetadata
│       │   └── diff.py               # ResourceDiff, ChangeType
│       ├── backends/
│       │   ├── __init__.py
│       │   ├── base.py               # StateBackend interface
│       │   └── local.py              # LocalFileBackend
│       ├── sync/
│       │   ├── __init__.py
│       │   ├── base.py               # ResourceSync interface
│       │   ├── project.py            # ProjectSync
│       │   ├── dataset.py            # DatasetSync
│       │   └── recipe.py             # RecipeSync
│       ├── manager.py                # StateManager
│       ├── diff.py                   # DiffEngine
│       ├── exceptions.py             # Custom exceptions
│       └── schemas/
│           └── state_v1.schema.json  # JSON Schema
│
└── tests/
    └── iac/
        ├── test_state.py
        ├── test_resource.py
        ├── test_backends.py
        ├── test_sync_project.py
        ├── test_sync_dataset.py
        ├── test_sync_recipe.py
        ├── test_manager.py
        ├── test_diff.py
        └── fixtures/
            ├── sample_state.json
            └── test_project.json
```

### Dependencies

Add to `setup.py` or `pyproject.toml`:

```python
install_requires=[
    "dataikuapi>=14.1.3",
    "jsonschema>=4.0.0",
]
```

### Error Handling

All custom exceptions in `exceptions.py`:

```python
class DataikuIaCError(Exception):
    """Base exception for Dataiku IaC"""
    pass

class StateNotFoundError(DataikuIaCError):
    """State file doesn't exist"""
    pass

class StateCorruptedError(DataikuIaCError):
    """State file is invalid"""
    pass

class StateWriteError(DataikuIaCError):
    """Failed to write state"""
    pass

class ResourceNotFoundError(DataikuIaCError):
    """Resource doesn't exist in Dataiku"""
    pass
```

### Logging

Use Python's standard logging:

```python
import logging

logger = logging.getLogger("dataikuapi.iac")

# In code:
logger.info(f"Loading state from {self.state_file}")
logger.debug(f"Synced resource: {resource_id}")
logger.warning(f"Resource not found: {resource_id}")
logger.error(f"Failed to save state: {e}")
```

---

## Work Breakdown

### Task Dependencies

```
Task A: Data Models (State, Resource, ResourceMetadata)
  └─→ No dependencies

Task B: StateBackend Interface + LocalFileBackend
  └─→ Depends on: Task A

Task C: ResourceSync Interface
  └─→ Depends on: Task A

Task D: ProjectSync Implementation
  └─→ Depends on: Task C

Task E: DatasetSync Implementation
  └─→ Depends on: Task C

Task F: RecipeSync Implementation
  └─→ Depends on: Task C

Task G: StateManager
  └─→ Depends on: Task B, Task D, Task E, Task F

Task H: DiffEngine
  └─→ Depends on: Task A

Task I: JSON Schema + Validation
  └─→ Depends on: Task A

Task J: Integration Tests
  └─→ Depends on: All tasks
```

### Parallelizable Work Packages

**Package 1: Core Data Models** (Independent)
- File: `dataikuapi/iac/models/state.py`
- File: `dataikuapi/iac/models/diff.py`
- File: `dataikuapi/iac/exceptions.py`
- Tests: `tests/iac/test_state.py`, `tests/iac/test_resource.py`
- Assignable: Developer A or Agent 1

**Package 2: State Backend** (Depends on Package 1)
- File: `dataikuapi/iac/backends/base.py`
- File: `dataikuapi/iac/backends/local.py`
- Tests: `tests/iac/test_backends.py`
- Assignable: Developer B or Agent 2

**Package 3: Resource Sync - Project** (Depends on Package 1)
- File: `dataikuapi/iac/sync/base.py`
- File: `dataikuapi/iac/sync/project.py`
- Tests: `tests/iac/test_sync_project.py`
- Assignable: Developer C or Agent 3

**Package 4: Resource Sync - Dataset** (Depends on Package 3)
- File: `dataikuapi/iac/sync/dataset.py`
- Tests: `tests/iac/test_sync_dataset.py`
- Assignable: Developer D or Agent 4

**Package 5: Resource Sync - Recipe** (Depends on Package 3)
- File: `dataikuapi/iac/sync/recipe.py`
- Tests: `tests/iac/test_sync_recipe.py`
- Assignable: Developer E or Agent 5

**Package 6: DiffEngine** (Depends on Package 1)
- File: `dataikuapi/iac/diff.py`
- Tests: `tests/iac/test_diff.py`
- Assignable: Developer F or Agent 6

**Package 7: StateManager** (Depends on Packages 2, 3, 4, 5)
- File: `dataikuapi/iac/manager.py`
- Tests: `tests/iac/test_manager.py`
- Assignable: Developer G or Agent 7

**Package 8: JSON Schema + Validation** (Depends on Package 1)
- File: `dataikuapi/iac/schemas/state_v1.schema.json`
- Update: `LocalFileBackend` to use schema validation
- Tests: Schema validation tests
- Assignable: Developer H or Agent 8

**Package 9: Integration Tests** (Depends on all)
- File: `tests/iac/test_integration.py`
- Requires: Real Dataiku instance or mocks
- Assignable: Developer I or Agent 9

### Execution Plan

**Day 1-2:**
- Start: Packages 1, 3, 6 in parallel (independent)
- Complete: Core models, sync interface, diff engine

**Day 3:**
- Start: Packages 2, 4, 5, 8 in parallel (now unblocked)
- Complete: Backend, dataset sync, recipe sync, schema

**Day 4:**
- Start: Package 7 (now unblocked)
- Complete: StateManager

**Day 5:**
- Start: Package 9
- Complete: Integration tests
- Demo and documentation

---

## Testing Strategy

### Unit Tests

**Coverage Target:** >90% for all components

**Test Files:**
- `test_state.py` - State, Resource, ResourceMetadata
- `test_resource.py` - Resource ID validation, checksums
- `test_backends.py` - LocalFileBackend
- `test_sync_project.py` - ProjectSync
- `test_sync_dataset.py` - DatasetSync
- `test_sync_recipe.py` - RecipeSync
- `test_manager.py` - StateManager
- `test_diff.py` - DiffEngine

**Example Test Structure:**

```python
# tests/iac/test_state.py

import pytest
from datetime import datetime
from dataikuapi.iac.models.state import State, Resource, ResourceMetadata

class TestState:
    """Test State model"""

    def test_create_empty_state(self):
        """Can create empty state"""
        state = State(environment="dev")
        assert state.version == 1
        assert state.serial == 0
        assert state.environment == "dev"
        assert len(state.resources) == 0

    def test_add_resource_increments_serial(self):
        """Adding resource increments serial"""
        state = State()
        initial_serial = state.serial

        resource = Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"name": "Test Project"}
        )
        state.add_resource(resource)

        assert state.serial == initial_serial + 1

    def test_to_dict_from_dict_roundtrip(self):
        """State serialization round-trip preserves data"""
        original = State(environment="prod", serial=5)
        original.add_resource(Resource(
            resource_type="project",
            resource_id="project.TEST",
            attributes={"key": "value"}
        ))

        # Convert to dict and back
        data = original.to_dict()
        restored = State.from_dict(data)

        assert restored.version == original.version
        assert restored.serial == original.serial
        assert restored.environment == original.environment
        assert len(restored.resources) == len(original.resources)
```

### Integration Tests

**Requirements:**
- Access to Dataiku instance (dev environment)
- Test project with known datasets/recipes
- Cleanup after tests

**Test Scenarios:**

```python
# tests/iac/test_integration.py

import pytest
from dataikuapi import DSSClient
from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.backends.local import LocalFileBackend
from pathlib import Path

@pytest.fixture
def dataiku_client():
    """Fixture: Dataiku client"""
    # TODO: Configure from environment
    host = "https://dataiku-dev.company.com"
    api_key = "..."
    return DSSClient(host, api_key)

@pytest.fixture
def state_manager(dataiku_client, tmp_path):
    """Fixture: StateManager with temp backend"""
    state_file = tmp_path / "test.state.json"
    backend = LocalFileBackend(state_file)
    return StateManager(backend, dataiku_client, "test")

class TestIntegration:
    """Integration tests against real Dataiku"""

    def test_sync_existing_project(self, state_manager):
        """Can sync existing project from Dataiku"""
        # Assuming TEST_PROJECT exists in Dataiku
        state = state_manager.sync_project("TEST_PROJECT", include_children=True)

        # Verify project synced
        assert state.has_resource("project.TEST_PROJECT")

        # Verify has datasets
        datasets = state.list_resources("dataset")
        assert len(datasets) > 0

        # Verify has recipes
        recipes = state.list_resources("recipe")
        assert len(recipes) > 0

    def test_save_and_load_state(self, state_manager):
        """Can save and reload state"""
        # Sync from Dataiku
        original_state = state_manager.sync_project("TEST_PROJECT")

        # Save
        state_manager.save_state(original_state)

        # Load
        loaded_state = state_manager.load_state()

        # Verify same
        assert loaded_state.serial == original_state.serial
        assert len(loaded_state.resources) == len(original_state.resources)

    def test_detect_drift(self, state_manager):
        """Can detect drift between state and Dataiku"""
        # Sync initial state
        old_state = state_manager.sync_project("TEST_PROJECT")
        state_manager.save_state(old_state)

        # TODO: Modify something in Dataiku

        # Sync again
        new_state = state_manager.sync_project("TEST_PROJECT")

        # Diff
        from dataikuapi.iac.diff import DiffEngine
        diff_engine = DiffEngine()
        diffs = diff_engine.diff(old_state, new_state)

        # Should detect changes
        summary = diff_engine.summary(diffs)
        assert summary["modified"] > 0
```

### Test Data Fixtures

Create sample state files for testing:

```json
// tests/iac/fixtures/sample_state.json
{
  "version": 1,
  "serial": 1,
  "lineage": "git:abc123",
  "environment": "test",
  "updated_at": "2025-01-15T10:30:00Z",
  "resources": {
    "project.TEST_PROJECT": {
      "resource_type": "project",
      "resource_id": "project.TEST_PROJECT",
      "attributes": {
        "projectKey": "TEST_PROJECT",
        "name": "Test Project",
        "description": "Test project for unit tests"
      },
      "metadata": {
        "deployed_at": "2025-01-15T10:30:00Z",
        "deployed_by": "test_user",
        "dataiku_internal_id": null,
        "checksum": "abc123..."
      }
    }
  }
}
```

---

## Integration Points

### With Existing dataikuapi

**Key Integration Points:**

1. **DSSClient** - Entry point for all Dataiku operations
   ```python
   from dataikuapi import DSSClient
   client = DSSClient(host, api_key)
   ```

2. **DSSProject** - Project operations
   ```python
   project = client.get_project(project_key)
   settings = project.get_settings()
   ```

3. **DSSDataset** - Dataset operations
   ```python
   dataset = project.get_dataset(dataset_name)
   settings = dataset.get_settings()
   ```

4. **DSSRecipe** - Recipe operations
   ```python
   recipe = project.get_recipe(recipe_name)
   settings = recipe.get_settings()
   payload = recipe.get_payload()
   ```

**Settings Pattern:**
All Dataiku resources follow this pattern:
```python
settings_obj = resource.get_settings()
settings_dict = settings_obj.settings  # Actual settings dict
# Modify
settings_dict["key"] = "value"
# Save
settings_obj.save()
```

Our abstraction should normalize this.

### SettingsManager (Future - Week 2+)

**Not required for Week 1**, but design consideration:

```python
class SettingsManager:
    """Normalize Dataiku settings access"""

    @staticmethod
    def get_value(settings_obj, path: str) -> Any:
        """
        Get value from settings using dot notation.

        Example:
            get_value(dataset_settings, "params.connection")
        """
        keys = path.split('.')
        value = settings_obj.settings
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
        return value

    @staticmethod
    def set_value(settings_obj, path: str, value: Any) -> None:
        """Set value in settings using dot notation"""
        keys = path.split('.')
        target = settings_obj.settings
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
```

This can wait until we need it for apply operations.

---

## Acceptance Criteria

### Week 1 Complete When:

- [ ] All code packages implemented and merged
- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests passing against real Dataiku
- [ ] Can sync 1 project with 2 datasets and 1 recipe
- [ ] State file format validated with JSON Schema
- [ ] Diff correctly identifies added/removed/modified resources
- [ ] Documentation complete for all public APIs
- [ ] Demo script works end-to-end
- [ ] Ready for Week 2 development (plan/apply)

### Demo Script

```python
# demo_week1.py - End-to-end demonstration

from dataikuapi import DSSClient
from dataikuapi.iac.manager import StateManager
from dataikuapi.iac.backends.local import LocalFileBackend
from dataikuapi.iac.diff import DiffEngine
from pathlib import Path

# Setup
client = DSSClient("https://dataiku-dev.company.com", "api-key")
backend = LocalFileBackend(Path(".dataiku/state/demo.state.json"))
manager = StateManager(backend, client, "dev")

# Sync from Dataiku
print("Syncing TEST_PROJECT from Dataiku...")
state = manager.sync_project("TEST_PROJECT", include_children=True)

print(f"Synced {len(state.resources)} resources:")
for resource in state.list_resources():
    print(f"  - {resource.resource_id}")

# Save state
print("\nSaving state...")
manager.save_state(state)
print(f"Saved to: {backend.state_file}")

# Reload state
print("\nReloading state...")
loaded_state = manager.load_state()
print(f"Loaded {len(loaded_state.resources)} resources")

# Diff (should be no changes)
print("\nComparing states...")
diff_engine = DiffEngine()
diffs = diff_engine.diff(state, loaded_state)
summary = diff_engine.summary(diffs)
print(f"Summary: {summary}")

# Sync again (simulate drift detection)
print("\nSync again to check for drift...")
new_state = manager.sync_project("TEST_PROJECT", include_children=True)
diffs = diff_engine.diff(loaded_state, new_state)
print(diff_engine.format_output(diffs))

print("\n✓ Week 1 demo complete!")
```

---

## Next Steps (Week 2 Preview)

After Week 1 completes, Week 2 will add:
- YAML configuration parser
- Plan generation (desired config → target state)
- Plan output formatting
- Basic validation

Week 1 provides the foundation:
- ✅ State management
- ✅ Dataiku sync
- ✅ Diff engine

Week 2 builds on top:
- Configuration → Desired State
- Desired State ↔ Current State (using our diff engine)
- Plan = Actions to reconcile

---

**Document Version:** 1.0
**Status:** Ready for Implementation
**Next Review:** After Package 1-3 completion (Day 2)
