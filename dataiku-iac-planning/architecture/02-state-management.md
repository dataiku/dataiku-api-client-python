# State Management Architecture

**Document Status:** Draft
**Last Updated:** 2025-11-23
**Dependencies:** 01-overview.md

---

## Table of Contents

1. [Overview](#overview)
2. [State File Format](#state-file-format)
3. [State Storage Options](#state-storage-options)
4. [State Synchronization](#state-synchronization)
5. [State Locking](#state-locking)
6. [Drift Detection](#drift-detection)
7. [State Migration](#state-migration)

---

## Overview

### The Challenge

Dataiku's internal tri-state architecture makes external state management critical:

| Dataiku Layer | Content | Problem |
|---------------|---------|---------|
| Filesystem | Recipe code, notebooks, configs | Instance-local, not shared |
| Database | Metadata, job history | Can be external Postgres (HA) |
| Git | Optional per-project | Not source of truth |

**Our Solution:** External state tracking that acts as authoritative record of what's deployed.

---

## State File Format

### Schema Version 1.0

```json
{
  "$schema": "https://dataiku.io/schemas/iac-state-v1.json",
  "version": 1,
  "serial": 1234,
  "lineage": "git:abc123def456",
  "dataiku_version": "14.1.3",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z",
  "environment": {
    "name": "prod",
    "host": "https://dataiku-prod.company.com",
    "variables": {
      "SNOWFLAKE_CONNECTION": "SNOWFLAKE_PROD",
      "PYTHON_ENV": "python39_prod"
    }
  },
  "resources": {
    "project.CUSTOMER_ANALYTICS": {
      "type": "project",
      "id": "CUSTOMER_ANALYTICS",
      "deployed_at": "2025-01-15T10:30:00Z",
      "deployed_by": "alice@company.com",
      "config_checksum": "sha256:abc123...",
      "status": "healthy",
      "metadata": {
        "name": "Customer Analytics Platform",
        "description": "Customer segmentation and churn",
        "owner": "data_team"
      },
      "dependencies": []
    },
    "dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS": {
      "type": "dataset",
      "id": "RAW_CUSTOMERS",
      "project": "CUSTOMER_ANALYTICS",
      "deployed_at": "2025-01-15T10:31:00Z",
      "deployed_by": "alice@company.com",
      "config_checksum": "sha256:def456...",
      "status": "healthy",
      "metadata": {
        "connection": "SNOWFLAKE_PROD",
        "table": "customers",
        "schema_checksum": "sha256:789abc...",
        "last_built": "2025-01-15T12:00:00Z",
        "row_count": 1500000
      },
      "dependencies": []
    },
    "recipe.CUSTOMER_ANALYTICS.prep_customers": {
      "type": "recipe",
      "id": "prep_customers",
      "project": "CUSTOMER_ANALYTICS",
      "deployed_at": "2025-01-15T10:32:00Z",
      "deployed_by": "alice@company.com",
      "config_checksum": "sha256:ghi789...",
      "status": "healthy",
      "metadata": {
        "recipe_type": "python",
        "code_checksum": "sha256:jkl012...",
        "inputs": ["RAW_CUSTOMERS"],
        "outputs": ["PREPARED_CUSTOMERS"],
        "last_run": "2025-01-15T13:00:00Z"
      },
      "dependencies": [
        "dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS"
      ]
    }
  },
  "metadata": {
    "last_apply_duration": 45.3,
    "last_apply_actions": {
      "added": 0,
      "changed": 1,
      "destroyed": 0
    },
    "warnings": [],
    "checkpoints": []
  }
}
```

### Key Fields

**Top Level:**
- `version`: State file format version (semantic versioning)
- `serial`: Incrementing number for ordering
- `lineage`: Git commit hash of deployed config
- `dataiku_version`: Target Dataiku version

**Per Resource:**
- `type`: Resource type (project, dataset, recipe, etc.)
- `id`: Unique identifier within type
- `deployed_at`: When deployed
- `deployed_by`: Who deployed
- `config_checksum`: SHA256 of source config
- `status`: healthy, degraded, failed, unknown
- `metadata`: Type-specific metadata
- `dependencies`: Other resources this depends on

---

## State Storage Options

### Option 1: Local File (Development)

**Storage:** `.dataiku/state/{environment}.state.json` (git-ignored)

**Pros:**
- ✅ Simple implementation
- ✅ Works offline
- ✅ No external dependencies
- ✅ Fast access

**Cons:**
- ❌ Not shared across team
- ❌ No locking mechanism
- ❌ Lost if directory deleted
- ❌ Not suitable for CI/CD

**Use Case:** Local development, personal testing

**Implementation:**
```python
class LocalStateStore:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir

    def load(self, environment: str) -> State:
        state_file = self.state_dir / f"{environment}.state.json"
        if not state_file.exists():
            return State.empty()
        return State.from_json(state_file.read_text())

    def save(self, environment: str, state: State):
        state_file = self.state_dir / f"{environment}.state.json"
        state_file.write_text(state.to_json(indent=2))
```

---

### Option 2: S3/Cloud Storage (Production)

**Storage:** `s3://dataiku-iac-state/{org}/{project}/{environment}.state.json`

**Pros:**
- ✅ Shared across team
- ✅ Versioned (S3 versioning)
- ✅ Durable
- ✅ Can use DynamoDB for locking
- ✅ Audit trail (CloudTrail)

**Cons:**
- ❌ Requires AWS/cloud credentials
- ❌ Network dependency
- ❌ Slightly slower access
- ❌ Additional cost

**Use Case:** Team collaboration, CI/CD, production

**Implementation:**
```python
import boto3

class S3StateStore:
    def __init__(self, bucket: str, prefix: str):
        self.s3 = boto3.client('s3')
        self.bucket = bucket
        self.prefix = prefix

    def load(self, environment: str) -> State:
        key = f"{self.prefix}/{environment}.state.json"
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return State.from_json(response['Body'].read())
        except self.s3.exceptions.NoSuchKey:
            return State.empty()

    def save(self, environment: str, state: State):
        key = f"{self.prefix}/{environment}.state.json"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=state.to_json(indent=2),
            ContentType='application/json',
            Metadata={
                'deployed-by': state.deployed_by,
                'deployed-at': state.updated_at.isoformat()
            }
        )

    def list_versions(self, environment: str) -> List[StateVersion]:
        """List all versions of state file"""
        key = f"{self.prefix}/{environment}.state.json"
        response = self.s3.list_object_versions(
            Bucket=self.bucket,
            Prefix=key
        )
        return [
            StateVersion(
                version_id=v['VersionId'],
                timestamp=v['LastModified'],
                size=v['Size']
            )
            for v in response.get('Versions', [])
        ]
```

---

### Option 3: Hybrid (Recommended)

**Approach:** Local cache + remote authoritative

```python
class HybridStateStore:
    def __init__(self, local: LocalStateStore, remote: S3StateStore):
        self.local = local
        self.remote = remote

    def load(self, environment: str, use_cache: bool = True) -> State:
        """Load from cache if fresh, otherwise fetch from remote"""
        if use_cache:
            local_state = self.local.load(environment)
            if local_state and self._is_fresh(local_state):
                return local_state

        # Fetch from remote
        remote_state = self.remote.load(environment)

        # Update local cache
        self.local.save(environment, remote_state)

        return remote_state

    def save(self, environment: str, state: State):
        """Save to remote, then update local cache"""
        # Remote is authoritative
        self.remote.save(environment, state)

        # Update local cache
        self.local.save(environment, state)

    def _is_fresh(self, state: State, max_age_seconds: int = 300) -> bool:
        """Check if cached state is fresh enough"""
        age = (datetime.utcnow() - state.cached_at).total_seconds()
        return age < max_age_seconds
```

**Configuration:**
```yaml
# .dataiku/config.yml
state_backend:
  type: hybrid

  local:
    path: .dataiku/state

  remote:
    type: s3
    bucket: dataiku-iac-state
    prefix: myorg/myproject
    region: us-east-1

  cache:
    enabled: true
    max_age_seconds: 300
```

---

## State Synchronization

### Sync Process

**Purpose:** Keep state file in sync with actual Dataiku resources

```
State File (what we think is deployed)
    ↕ sync
Dataiku Resources (what's actually deployed)
```

**Sync Algorithm:**

```python
class StateSynchronizer:
    def sync(self, state: State, client: DSSClient) -> State:
        """Synchronize state with actual Dataiku resources"""

        updated_state = State(
            version=state.version,
            serial=state.serial + 1,
            lineage=state.lineage
        )

        # For each resource in state
        for resource_id, resource in state.resources.items():
            actual = self._fetch_actual_resource(client, resource)

            if actual is None:
                # Resource in state but not in Dataiku
                resource.status = "missing"
                resource.metadata['sync_error'] = "Resource not found in Dataiku"

            elif self._has_changed(resource, actual):
                # Resource exists but has changed outside IaC
                resource.status = "drifted"
                resource.metadata['drift'] = self._calculate_drift(resource, actual)
                resource.metadata['actual_checksum'] = actual.checksum

            else:
                # Resource matches state
                resource.status = "healthy"

            updated_state.resources[resource_id] = resource

        # Discover resources not in state
        orphaned = self._find_orphaned_resources(client, state)
        for orphan in orphaned:
            orphan.status = "unmanaged"
            orphan.metadata['sync_warning'] = "Not managed by IaC"
            updated_state.resources[orphan.id] = orphan

        updated_state.synced_at = datetime.utcnow()
        return updated_state
```

**When to Sync:**
- Before `plan` (to detect drift)
- After `apply` (to record actual state)
- Periodically in CI/CD (to detect out-of-band changes)
- On demand via `dataiku-iac state sync`

---

## State Locking

### Why Locking is Critical

**Problem:** Concurrent applies can corrupt state

```
User A: dataiku-iac apply --environment prod
User B: dataiku-iac apply --environment prod  (same time)

Without locking:
1. Both read state (serial=100)
2. Both make changes
3. Both write state (serial=101)
4. Second write overwrites first
5. First user's changes are lost
```

### Lock Implementation

**Option 1: File Locks (Local Development)**

```python
import fcntl

class FileLock:
    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.fd = None

    def acquire(self, timeout: int = 60):
        """Acquire exclusive lock"""
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self.fd = open(self.lock_file, 'w')

        start = time.time()
        while True:
            try:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.fd.write(json.dumps({
                    'acquired_at': datetime.utcnow().isoformat(),
                    'acquired_by': os.environ.get('USER'),
                    'pid': os.getpid()
                }))
                self.fd.flush()
                return
            except BlockingIOError:
                if time.time() - start > timeout:
                    raise LockTimeout(f"Could not acquire lock after {timeout}s")
                time.sleep(1)

    def release(self):
        """Release lock"""
        if self.fd:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()
            self.lock_file.unlink(missing_ok=True)
```

**Option 2: DynamoDB Lock (Production)**

```python
import boto3

class DynamoDBLock:
    def __init__(self, table_name: str, lock_id: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.lock_id = lock_id
        self.acquired = False

    def acquire(self, timeout: int = 60):
        """Acquire lock via conditional write"""
        start = time.time()

        while True:
            try:
                self.table.put_item(
                    Item={
                        'LockID': self.lock_id,
                        'AcquiredAt': datetime.utcnow().isoformat(),
                        'AcquiredBy': os.environ.get('USER', 'unknown'),
                        'TTL': int(time.time()) + 3600  # 1 hour max
                    },
                    ConditionExpression='attribute_not_exists(LockID)'
                )
                self.acquired = True
                return

            except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
                # Lock already exists
                if time.time() - start > timeout:
                    # Check if lock is stale
                    lock_info = self._get_lock_info()
                    raise LockHeld(
                        f"Lock held by {lock_info['AcquiredBy']} "
                        f"since {lock_info['AcquiredAt']}"
                    )
                time.sleep(1)

    def release(self):
        """Release lock"""
        if self.acquired:
            self.table.delete_item(Key={'LockID': self.lock_id})
            self.acquired = False

    def force_release(self):
        """Force release stale lock (admin only)"""
        self.table.delete_item(Key={'LockID': self.lock_id})
```

**Usage:**

```python
# Context manager ensures lock is always released
with state_store.lock(environment='prod', timeout=60) as lock:
    state = state_store.load('prod')
    plan = planner.plan(config, state)
    result = executor.apply(plan)
    state_store.save('prod', result.state)
```

---

## Drift Detection

### What is Drift?

**Drift:** Resources changed outside of IaC management

**Examples:**
- User modifies recipe code in UI
- Admin changes connection settings
- Dataset schema updated manually
- Scenario trigger modified

### Detection Algorithm

```python
class DriftDetector:
    def detect_drift(self, state: State, client: DSSClient) -> DriftReport:
        """Detect differences between state and actual resources"""

        drift_report = DriftReport()

        for resource_id, resource in state.resources.items():
            actual = self._fetch_actual(client, resource)

            if actual is None:
                drift_report.add_deleted(resource)
                continue

            drifts = self._compare(resource, actual)
            if drifts:
                drift_report.add_drifted(resource, drifts)

        # Check for resources not in state
        all_actual = self._fetch_all_resources(client)
        for actual in all_actual:
            if actual.id not in state.resources:
                drift_report.add_unmanaged(actual)

        return drift_report

    def _compare(self, expected: Resource, actual: Resource) -> List[Drift]:
        """Compare expected vs actual and return differences"""
        drifts = []

        # Compare metadata
        if expected.metadata.get('connection') != actual.metadata.get('connection'):
            drifts.append(Drift(
                field='connection',
                expected=expected.metadata.get('connection'),
                actual=actual.metadata.get('connection'),
                severity='high'
            ))

        # Compare checksums
        if expected.config_checksum != actual.config_checksum:
            drifts.append(Drift(
                field='configuration',
                expected=expected.config_checksum,
                actual=actual.config_checksum,
                severity='medium'
            ))

        return drifts
```

**Drift Report Output:**

```
Drift Detection Report

Environment: prod
Synced at: 2025-01-15 14:30:00

Drifted Resources: 2
  ~ recipe.CUSTOMER_ANALYTICS.prep_customers
      code: MODIFIED (checksum mismatch)
      severity: medium
      last_modified: 2025-01-15 13:00:00 by bob@company.com

  ~ dataset.CUSTOMER_ANALYTICS.RAW_CUSTOMERS
      connection: SNOWFLAKE_PROD → SNOWFLAKE_PROD_READ_REPLICA
      severity: high
      last_modified: 2025-01-15 12:00:00 by alice@company.com

Deleted Resources: 0

Unmanaged Resources: 1
  ? dataset.CUSTOMER_ANALYTICS.TEMP_DATA
      created: 2025-01-15 14:00:00 by charlie@company.com
      note: Not managed by IaC

Recommendations:
  1. Import drifted resources: dataiku-iac import prep_customers
  2. Or update state to match: dataiku-iac state update --from-actual
  3. Manage unmanaged resources: dataiku-iac import TEMP_DATA
```

### Drift Handling Strategies

**1. Auto-Correct (Revert to IaC)**
```bash
$ dataiku-iac apply --auto-correct-drift

Detected drift in 2 resources
Reverting to IaC-defined state...
  ✓ recipe.prep_customers (code reverted)
  ✓ dataset.RAW_CUSTOMERS (connection restored)
```

**2. Import Changes (Update IaC)**
```bash
$ dataiku-iac import prep_customers --update-config

Importing changes from Dataiku...
  Updated: recipes/prep_customers.py
  Updated: projects/customer_analytics.yml (checksum)

Commit these changes to Git to accept drift.
```

**3. Ignore (Mark as Expected)**
```yaml
# .dataiku/drift-policy.yml
ignore_drift:
  - resource: recipe.CUSTOMER_ANALYTICS.prep_customers
    fields: [code]
    reason: "Hotfix applied, will be synced next sprint"
    expires: 2025-01-20
```

---

## State Migration

### Version Upgrades

**When state file format changes:**

```python
class StateMigrator:
    def migrate(self, state_data: dict) -> State:
        """Migrate state file to current version"""

        version = state_data.get('version', 0)

        # Apply migrations sequentially
        migrations = [
            self._migrate_v0_to_v1,
            self._migrate_v1_to_v2,
            # ... future migrations
        ]

        for i in range(version, len(migrations)):
            state_data = migrations[i](state_data)
            state_data['version'] = i + 1

        return State.from_dict(state_data)

    def _migrate_v0_to_v1(self, data: dict) -> dict:
        """Migration from v0 to v1"""
        # Add new fields with defaults
        data['lineage'] = 'unknown'
        data['environment'] = {'name': 'default'}

        # Restructure resources
        for resource in data.get('resources', {}).values():
            resource['dependencies'] = []

        return data
```

**Auto-migration:**
```bash
$ dataiku-iac state migrate --from 0 --to 1

Migrating state file from v0 to v1...
  ✓ Added lineage field
  ✓ Added environment section
  ✓ Restructured resource dependencies

Backup saved to: .dataiku/state/prod.state.v0.backup.json
```

---

## Summary

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Storage** | Hybrid (local + S3) | Development simplicity + production durability |
| **Locking** | DynamoDB for prod, file locks for dev | Team collaboration requires distributed locks |
| **Sync Strategy** | On-demand + periodic | Balance freshness with performance |
| **Drift Policy** | Detect and report, user decides | Don't auto-correct without user consent |
| **State Format** | JSON | Human-readable, version-controllable, widely supported |

### State File Lifecycle

```
1. Init: Create empty state
2. Plan: Load state, detect drift
3. Apply: Update state with changes
4. Sync: Reconcile with Dataiku
5. Lock: Prevent concurrent modification
6. Backup: Version in S3
7. Migrate: Upgrade format as needed
```

---

## Next Steps

1. **Implement state file schema** with validation
2. **Build state store adapters** (local, S3, hybrid)
3. **Design lock manager** with timeout and force-release
4. **Create drift detector** with comparison algorithm
5. **Test state migration** between versions

---

**Document Version:** 0.1.0
**Status:** Draft for Review
**Next Review:** TBD
