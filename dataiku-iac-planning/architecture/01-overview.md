# Architecture Overview

**Document Status:** Draft
**Last Updated:** 2025-11-23
**Reviewers:** TBD

---

## Table of Contents

1. [System Context](#system-context)
2. [High-Level Architecture](#high-level-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Integration Points](#integration-points)
6. [Deployment Model](#deployment-model)
7. [Constraints & Assumptions](#constraints--assumptions)

---

## System Context

### The Problem

Dataiku currently has a **tri-state architecture** that prevents proper HA and state management:

```
┌─────────────────────────────────────┐
│ Dataiku Instance (Not HA)           │
│                                     │
│ ┌─────────────────┐                │
│ │ Filesystem      │ (instance-local)│
│ │ - Recipe code   │                │
│ │ - Notebooks     │                │
│ │ - Configs       │                │
│ └─────────────────┘                │
│          ↕                          │
│ ┌─────────────────┐                │
│ │ Database        │ (SQLite/Postgres)│
│ │ - Metadata      │                │
│ │ - Job history   │                │
│ │ - Scenarios     │                │
│ └─────────────────┘                │
│          ↕                          │
│ ┌─────────────────┐                │
│ │ Git Repository  │ (per-project)  │
│ │ - Optional      │                │
│ │ - Not source    │                │
│ │   of truth      │                │
│ └─────────────────┘                │
└─────────────────────────────────────┘
```

**Problems:**
- ❌ No single source of truth
- ❌ Automation/Design nodes are not HA
- ❌ If node dies mid-scenario, no recovery
- ❌ Manual environment promotion (clicks)
- ❌ No declarative configuration
- ❌ Poor CI/CD integration

### The Solution

**External state management** with declarative configuration:

```
┌──────────────────────────────────────────────┐
│ Git Repository (Source of Truth)             │
│ ├── projects/customer_analytics.yml         │
│ ├── environments/prod.yml                   │
│ └── .dataiku/state/prod.state.json          │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ Dataiku IaC Engine (External Orchestrator)   │
│ ├── Parser: YAML → Internal Model           │
│ ├── Planner: Diff desired vs actual         │
│ ├── Validator: Pre-flight checks            │
│ └── Executor: Apply with checkpoints        │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│ Dataiku Nodes (Managed Resources)            │
│ ├── Design Node (dev)                       │
│ ├── Automation Node (prod - recoverable)    │
│ └── Govern Node (approvals)                 │
└──────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Git is single source of truth
- ✅ External state enables recovery
- ✅ Declarative configs (YAML/Python)
- ✅ Plan/Apply workflow (preview changes)
- ✅ Automatic environment remapping
- ✅ CI/CD native

---

## High-Level Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: User Interface                                 │
│ ├── CLI (dataiku-iac plan/apply/test)                  │
│ ├── CI/CD Templates (GitHub Actions, GitLab CI)        │
│ └── Python API (programmatic access)                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Orchestration                                  │
│ ├── Configuration Parser (YAML/Python → Model)         │
│ ├── Validation Engine (pre-flight checks)              │
│ ├── Planning Engine (diff, dependency resolution)      │
│ ├── Execution Engine (apply, rollback, recovery)       │
│ └── Testing Framework (schema, pipeline tests)         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: State Management                               │
│ ├── State Store (current state tracking)               │
│ ├── State Sync (Dataiku ↔ State reconciliation)       │
│ ├── State Lock (concurrent operation prevention)       │
│ └── Checkpoint Manager (recovery points)               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Dataiku Integration                            │
│ ├── Dataiku Python API (dataikuapi.dss)               │
│ ├── Builders (fluent APIs for complex operations)      │
│ ├── Unified Async (consistent async handling)          │
│ └── Govern Client (approval workflows)                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ External Systems                                         │
│ ├── Dataiku Nodes (Design, Automation, Govern)         │
│ ├── Git Repository (version control)                   │
│ ├── CI/CD Systems (GitHub, GitLab, Jenkins)            │
│ └── Secret Stores (vault, AWS Secrets, etc.)           │
└─────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Configuration Parser

**Responsibility:** Convert YAML/Python configs to internal model

```python
class ConfigurationParser:
    """Parse and validate configuration files"""

    def parse_yaml(self, config_file: Path) -> Configuration:
        """Parse YAML configuration"""

    def parse_python(self, config_file: Path) -> Configuration:
        """Parse Python DSL configuration"""

    def validate(self, config: Configuration) -> ValidationResult:
        """Validate configuration against schema"""

    def resolve_variables(self, config: Configuration,
                         environment: Environment) -> Configuration:
        """Resolve environment variables"""
```

**Inputs:**
- YAML/Python configuration files
- Environment variable definitions
- Schema definitions

**Outputs:**
- Validated internal configuration model
- Validation errors (if any)

---

### 2. State Manager

**Responsibility:** Track current vs desired state

```python
class StateManager:
    """Manage state tracking and synchronization"""

    def __init__(self, state_file: Path, client: DSSClient):
        self.state_file = state_file
        self.client = client

    def sync(self) -> State:
        """Sync state with actual Dataiku resources"""

    def save(self, state: State):
        """Persist state to file"""

    def lock(self) -> StateLock:
        """Acquire lock for concurrent protection"""

    def detect_drift(self) -> DriftReport:
        """Detect differences between state and actual"""
```

**State File Format:**
```json
{
  "version": 1,
  "serial": 1234,
  "lineage": "git:abc123def",
  "resources": {
    "project.CUSTOMER_ANALYTICS": {
      "type": "project",
      "deployed_at": "2025-01-15T10:30:00Z",
      "deployed_by": "alice@company.com",
      "checksum": "sha256:...",
      "metadata": {...}
    }
  }
}
```

---

### 3. Planning Engine

**Responsibility:** Calculate diff between desired and actual state

```python
class PlanningEngine:
    """Generate execution plans"""

    def plan(self,
             desired: Configuration,
             current: State) -> Plan:
        """Generate plan showing what will change"""

    def validate_plan(self, plan: Plan) -> ValidationResult:
        """Validate plan is safe to execute"""

    def estimate_impact(self, plan: Plan) -> ImpactAnalysis:
        """Estimate resources, time, and risk"""
```

**Plan Output:**
```
Plan: 3 to add, 1 to change, 0 to destroy

+ dataset.CUSTOMER_ANALYTICS.NEW_DATA
  name: "NEW_DATA"
  connection: "SNOWFLAKE_PROD"

~ recipe.CUSTOMER_ANALYTICS.prep_data
  code: changed (234 lines modified)

Warnings:
  - NEW_DATA has no data quality checks

Validations:
  ✓ All connections exist
  ✓ No circular dependencies
  ✓ Schemas are compatible
```

---

### 4. Execution Engine

**Responsibility:** Execute plans with checkpointing and recovery

```python
class ExecutionEngine:
    """Execute plans with fault tolerance"""

    def apply(self, plan: Plan, options: ApplyOptions) -> ApplyResult:
        """Execute plan with checkpointing"""

    def rollback(self, checkpoint: Checkpoint) -> RollbackResult:
        """Rollback to previous state"""

    def resume(self, checkpoint: Checkpoint) -> ApplyResult:
        """Resume interrupted apply"""
```

**Execution Flow:**
```
1. Acquire state lock
2. Create checkpoint
3. For each action in plan:
   a. Record action start
   b. Execute action
   c. Record action completion
   d. Update state
4. Release lock
5. Save final state

On failure:
- Keep checkpoint
- Release lock
- Allow resume or rollback
```

---

### 5. Testing Framework

**Responsibility:** Validate pipelines before deployment

```python
class TestingFramework:
    """Pipeline testing capabilities"""

    def run_tests(self, test_suite: TestSuite,
                  environment: Environment) -> TestResults:
        """Execute test suite"""

    def load_fixtures(self, fixtures: Dict[str, Path]):
        """Load test data"""

    def assert_schema(self, dataset: str, expected: Schema):
        """Validate dataset schema"""

    def assert_pipeline(self, scenario: str,
                       expected_output: Path):
        """Validate pipeline output"""
```

---

## Data Flow

### Plan Workflow

```
User: dataiku-iac plan --environment prod
    ↓
1. Load configuration from Git
    projects/customer_analytics.yml
    environments/prod.yml
    ↓
2. Resolve environment variables
    ${SNOWFLAKE_CONNECTION} → SNOWFLAKE_PROD
    ↓
3. Load current state
    .dataiku/state/prod.state.json
    ↓
4. Sync state with Dataiku
    Query actual resources via API
    ↓
5. Calculate diff
    desired - current = changes needed
    ↓
6. Validate plan
    Check connections exist
    Verify schemas compatible
    Detect circular dependencies
    ↓
7. Generate plan output
    Human-readable summary
    Machine-readable JSON
    ↓
8. (Optional) Submit to Govern
    Create approval workflow
```

---

### Apply Workflow

```
User: dataiku-iac apply --environment prod
    ↓
1. Load plan (or regenerate)
    ↓
2. Acquire state lock
    Prevent concurrent modifications
    ↓
3. Create checkpoint
    Record current state for rollback
    ↓
4. Execute plan actions sequentially
    For each action:
      ├─ Log action start
      ├─ Execute via Dataiku API
      ├─ Wait for completion
      ├─ Verify success
      ├─ Update state
      └─ Save checkpoint
    ↓
5. On success:
    ├─ Save final state
    ├─ Delete checkpoint
    ├─ Release lock
    └─ Return success

6. On failure:
    ├─ Keep checkpoint
    ├─ Release lock
    └─ Provide recovery options
       ├─ Resume: continue from checkpoint
       ├─ Rollback: revert to previous state
       └─ Force: retry failed action
```

---

### Test Workflow

```
User: dataiku-iac test --environment test
    ↓
1. Create isolated test environment
    Clone from template or use dedicated
    ↓
2. Load test fixtures
    Inject test data into datasets
    ↓
3. Apply configuration
    Deploy to test environment
    ↓
4. Run test suite
    ├─ Schema tests
    ├─ Data quality tests
    ├─ Recipe execution tests
    └─ End-to-end pipeline tests
    ↓
5. Collect results
    Pass/fail for each test
    ↓
6. Cleanup (optional)
    Remove test environment
    ↓
7. Report results
    Human-readable summary
    JUnit XML for CI/CD
```

---

## Integration Points

### 1. Dataiku API Integration

**Interface:** Existing `dataikuapi` Python package

**Usage:**
```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")
dataset = project.create_dataset("new_dataset", "PostgreSQL")
```

**Wrapper Approach:**
- Use existing API (don't modify it)
- Add builders for complex operations
- Standardize async patterns
- Handle idempotency at IaC layer

---

### 2. Govern Integration

**Interface:** `dataikuapi.govern_client`

**Approval Workflow:**
```python
from dataikuapi.govern_client import GovernClient

govern = GovernClient(host, api_key)
project = govern.get_project(project_id)

# Create approval request
artifact = project.create_artifact(
    name=f"Deployment Plan - {timestamp}",
    type="deployment_plan"
)

# Submit for approval
workflow = artifact.create_workflow(
    approvers={"technical": [...], "business": [...]}
)

# Check approval status
if workflow.is_approved():
    # Proceed with apply
    pass
```

---

### 3. Git Integration

**Repository Structure:**
```
my-dataiku-projects/
├── .git/
├── projects/
│   ├── customer_analytics.yml
│   └── sales_reporting.yml
├── environments/
│   ├── dev.yml
│   ├── test.yml
│   └── prod.yml
├── recipes/
│   └── prep_customers.py
└── .dataiku/
    ├── state/
    │   ├── dev.state.json (git-ignored)
    │   ├── test.state.json (git-ignored)
    │   └── prod.state.json (git-ignored)
    └── config.yml
```

**Git Workflow:**
1. Developer commits config changes
2. PR opened
3. CI runs `dataiku-iac plan`
4. Plan posted to PR as comment
5. Reviewers approve
6. PR merged to main
7. CI runs `dataiku-iac apply`

---

### 4. CI/CD Integration

**GitHub Actions Example:**
```yaml
name: Dataiku Deploy
on:
  pull_request:
  push:
    branches: [main]

jobs:
  plan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Plan
        run: dataiku-iac plan --environment prod

  apply:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Apply
        run: dataiku-iac apply --environment prod --auto-approve
```

---

## Deployment Model

### Development Environment

```
Developer Workstation
    ↓
Local Git Repository
    ↓
dataiku-iac CLI
    ↓
Dataiku Design Node (dev)
```

**Workflow:**
1. Edit YAML configs locally
2. Run `dataiku-iac plan --environment dev`
3. Review changes
4. Run `dataiku-iac apply --environment dev`
5. Test in Design node
6. Commit to Git

---

### Production Environment

```
Git Repository (GitHub/GitLab)
    ↓
CI/CD Pipeline
    ↓
dataiku-iac CLI (in container)
    ↓
Govern Node (approval)
    ↓
Dataiku Automation Node (prod)
```

**Workflow:**
1. PR merged to main
2. CI triggers
3. Plan generated
4. Submitted to Govern
5. Approvers notified
6. On approval, apply executes
7. Automation node updated

---

## Constraints & Assumptions

### Technical Constraints

1. **Cannot fix HA at node level**
   - Design/Automation nodes will remain non-HA
   - Must work around this limitation
   - External state management is the solution

2. **Must materialize datasets**
   - Dataiku cannot project schemas
   - Datasets must be built before use
   - Testing requires actual execution

3. **Backward compatibility required**
   - Existing API must keep working
   - Cannot break current users
   - Layer on top, don't modify core

4. **Database can be external Postgres**
   - Enterprise deployments use external DB
   - This is already HA-capable
   - Filesystem and Git are the issues

### Assumptions

1. **Git is available**
   - All users have Git repositories
   - CI/CD is Git-based
   - This is standard for DevOps teams

2. **API keys are managed externally**
   - Not stored in Git
   - Retrieved from secrets manager
   - Standard security practice

3. **Environments are relatively stable**
   - Connections don't change frequently
   - Code envs are pre-configured
   - Variables handle differences

4. **Network connectivity**
   - CI/CD can reach Dataiku nodes
   - Govern node is accessible
   - No air-gapped deployments (initially)

---

## Next Steps

1. **Review this architecture** with technical stakeholders
2. **Detail state management** design (02-state-management.md)
3. **Design execution engine** with checkpointing (03-execution-engine.md)
4. **Plan recovery strategy** for failures (04-recovery-strategy.md)
5. **Document integration points** in detail (05-integration-points.md)

---

## Open Questions

1. **State storage location:** Local files? S3? Both?
2. **Lock implementation:** File locks? DynamoDB? Redis?
3. **Checkpoint granularity:** Per-action? Per-resource-type? Configurable?
4. **Test environment:** Dedicated instance? Clone projects? Both?
5. **Govern integration depth:** Mandatory? Optional? Configurable?

**These will be addressed in subsequent design documents.**

---

**Document Version:** 0.1.0
**Status:** Draft for Review
**Next Review:** TBD
