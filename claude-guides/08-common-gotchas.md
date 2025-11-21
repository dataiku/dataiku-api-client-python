# 08 - Common Gotchas and Troubleshooting

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Comprehensive guide to common pitfalls, errors, and solutions

---

## Critical Concepts to Remember

### 1. Scope Hierarchy is MANDATORY

```python
# ❌ WRONG - Cannot skip levels
client = DSSClient(host, api_key)
dataset = client.get_dataset("my_dataset")  # AttributeError!

# ✓ CORRECT - Must go through project
client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")
dataset = project.get_dataset("my_dataset")
```

**Why:** The API enforces hierarchical access for security and organization.

---

### 2. Settings Must Be Saved

```python
# ❌ WRONG - Changes not persisted
dataset = project.get_dataset("my_dataset")
settings = dataset.get_settings()
settings.settings['description'] = "New description"
# Changes lost!

# ✓ CORRECT - Always save
dataset = project.get_dataset("my_dataset")
settings = dataset.get_settings()
settings.settings['description'] = "New description"
settings.save()  # Critical!
```

**Why:** Settings are mutable objects that require explicit save.

---

### 3. Project Keys Must Be Uppercase

```python
# ❌ WRONG
client.create_project("my_project", "My Project", "owner")  # Fails!

# ✓ CORRECT
client.create_project("MY_PROJECT", "My Project", "owner")
```

**Why:** Dataiku enforces uppercase for project keys.

---

### 4. Asynchronous Operations

Many operations are asynchronous and return handles, not results:

```python
# ❌ WRONG - Assumes immediate completion
job = dataset.build(wait=False)
print("Build complete!")  # Not true!

# ✓ CORRECT - Wait for completion
job = dataset.build(wait=False)
while True:
    status = job.get_status()
    if status['baseStatus']['state'] in ['DONE', 'FAILED', 'ABORTED']:
        break
    time.sleep(2)
```

**Why:** Builds, training, scenarios run asynchronously in DSS backend.

---

### 5. Scenario Run is Two-Step Process

```python
# ❌ WRONG - trigger_fire is not the scenario run
trigger_fire = scenario.run()
outcome = trigger_fire.get_outcome()  # AttributeError!

# ✓ CORRECT - Two steps
trigger_fire = scenario.run()
scenario_run = trigger_fire.wait_for_scenario_run()
outcome = scenario_run.get_outcome()
```

**Why:** Triggering and running are separate operations.

---

## Common Errors and Solutions

### Authentication Errors

#### Error: "401 Unauthorized"

**Causes:**
- Invalid API key
- Expired API key
- Wrong host URL

**Solutions:**
```python
# Verify API key
import os
api_key = os.getenv('DATAIKU_API_KEY')
print(f"API key length: {len(api_key) if api_key else 'Not set'}")

# Test connection
try:
    client = DSSClient(host, api_key)
    projects = client.list_project_keys()
    print(f"✓ Connected, {len(projects)} projects accessible")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

#### Error: "403 Forbidden"

**Causes:**
- API key lacks required permissions
- User account disabled
- Project/resource not accessible

**Solutions:**
```python
# Check permissions
def check_permissions(client):
    try:
        # Try admin operation
        client.get_general_settings()
        print("✓ Has admin access")
    except:
        print("ℹ Limited user access")

    # Check project access
    projects = client.list_project_keys()
    print(f"Can access {len(projects)} projects")

check_permissions(client)
```

---

### Connection Errors

#### Error: "Connection refused" or Timeout

**Causes:**
- DSS not running
- Wrong host/port
- Firewall blocking
- Network issue

**Solutions:**
```python
# Diagnose connection
import socket
import requests

def diagnose_connection(host):
    # Parse hostname
    hostname = host.split("//")[1].split(":")[0]

    # Check DNS
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✓ DNS: {hostname} -> {ip}")
    except Exception as e:
        print(f"❌ DNS failed: {e}")
        return False

    # Check HTTP
    try:
        response = requests.get(host, timeout=5)
        print(f"✓ HTTP: Status {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP failed: {e}")
        return False

    return True

diagnose_connection("https://dss.company.com")
```

---

### Dataset Errors

#### Error: "Dataset is already being built"

**Cause:** Another job is building the dataset.

**Solutions:**
```python
# Wait for existing job to finish
def wait_for_dataset_available(dataset, max_wait=300):
    """Wait for dataset to be available for building"""
    import time

    start = time.time()
    while time.time() - start < max_wait:
        try:
            job = dataset.build(wait=False)
            return job
        except Exception as e:
            if "already being built" in str(e):
                print("Dataset busy, waiting...")
                time.sleep(10)
            else:
                raise

    raise TimeoutError("Dataset still busy after max wait time")

# Usage
job = wait_for_dataset_available(dataset)
```

#### Error: "Source dataset not ready"

**Cause:** Input datasets haven't been built yet.

**Solutions:**
```python
# Build dependencies first
def build_with_dependencies(project, dataset_name):
    """Build dataset and its dependencies"""

    # Get flow
    flow = project.get_flow()
    graph = flow.get_graph()

    # Find dependencies (simplified)
    # In real scenario, parse flow graph to find all upstream datasets

    # Build upstream first
    # Then build target
    dataset = project.get_dataset(dataset_name)
    job = dataset.build(wait=True)

    return job
```

#### Error: "Schema mismatch"

**Cause:** Output schema doesn't match recipe definition.

**Solutions:**
```python
# Update schema
recipe = project.get_recipe("my_recipe")

try:
    # Compute schema updates
    schema_updates = recipe.compute_schema_updates()
    schema_updates.apply()
    print("✓ Schema updated")
except Exception as e:
    print(f"❌ Schema update failed: {e}")

    # Manual schema fix
    output_dataset = project.get_dataset("output_dataset")
    # Define correct schema manually
    output_dataset.set_schema({
        "columns": [
            {"name": "col1", "type": "string"},
            {"name": "col2", "type": "bigint"}
        ],
        "userModified": True
    })
```

---

### Recipe Errors

#### Error: "Cannot compute schema updates"

**Cause:** Recipe configuration incomplete or invalid.

**Solutions:**
```python
# Validate recipe before schema update
def validate_recipe(recipe):
    """Check if recipe is properly configured"""

    definition = recipe.get_definition()

    # Check inputs
    if not definition.get('inputs'):
        print("❌ No inputs defined")
        return False

    # Check outputs
    if not definition.get('outputs'):
        print("❌ No outputs defined")
        return False

    # Check each input exists
    for input_type, input_list in definition['inputs'].items():
        for inp in input_list:
            try:
                project.get_dataset(inp['ref'])
            except:
                print(f"❌ Input dataset {inp['ref']} not found")
                return False

    print("✓ Recipe configuration valid")
    return True

# Usage
if validate_recipe(recipe):
    recipe.compute_schema_updates().apply()
```

---

### Scenario Errors

#### Error: "Scenario trigger fire cancelled"

**Cause:** Manual trigger fires can be cancelled if scenario runs too frequently.

**Solutions:**
```python
# Handle cancellation
trigger_fire = scenario.run()

try:
    scenario_run = trigger_fire.wait_for_scenario_run()
except Exception as e:
    if "cancelled" in str(e).lower():
        print("⚠ Trigger fire was cancelled")
        print("Scenario may be running too frequently")
        # Wait and retry
        time.sleep(60)
        trigger_fire = scenario.run()
        scenario_run = trigger_fire.wait_for_scenario_run()
    else:
        raise
```

#### Error: "Step condition failed"

**Cause:** Run condition expression evaluated to False.

**Solutions:**
```python
# Debug step conditions
scenario = project.get_scenario("my_scenario")
last_run = scenario.get_last_finished_run()

if last_run:
    details = last_run.get_details()

    for step in details.get('stepRuns', []):
        print(f"Step: {step.get('stepName')}")
        print(f"  Condition: {step.get('runCondition')}")
        print(f"  Ran: {step.get('ran', False)}")
        print(f"  Outcome: {step.get('result', {}).get('outcome')}")
```

---

### Memory Errors

#### Error: "OutOfMemoryError"

**Cause:** Loading too much data into memory.

**Solutions:**
```python
# ❌ WRONG - Load entire dataset
df = dataset.get_dataframe()  # May exhaust memory!

# ✓ BETTER - Iterate
for row in dataset.iter_rows():
    process_row(row)

# ✓ BEST - Use recipes for large data
# Let DSS handle the processing, don't pull into Python
```

#### Error: "Java heap space"

**Cause:** DSS backend out of memory.

**Solutions:**
- Increase backend Xmx in DSS settings (requires admin)
- Process data in smaller chunks
- Use more efficient recipes (SQL instead of Python)
- Clear cache datasets

---

### Permission Errors

#### Error: "User not allowed to..."

**Cause:** API key lacks required permissions.

**Solutions:**
```python
# Check what you can do
def check_capabilities(client):
    """Check what operations are permitted"""

    capabilities = {
        "admin": False,
        "create_projects": False,
        "list_users": False,
        "list_projects": False
    }

    try:
        client.get_general_settings()
        capabilities["admin"] = True
    except:
        pass

    try:
        client.list_users()
        capabilities["list_users"] = True
    except:
        pass

    try:
        projects = client.list_project_keys()
        capabilities["list_projects"] = True
        capabilities["accessible_projects"] = len(projects)
    except:
        pass

    return capabilities

caps = check_capabilities(client)
print("Capabilities:", caps)
```

---

### Data Type Errors

#### Error: "Cannot convert X to Y"

**Cause:** Schema type mismatch.

**Solutions:**
```python
# Ensure correct types when writing
import pandas as pd

df = pd.DataFrame({
    "id": [1, 2, 3],  # int
    "name": ["A", "B", "C"],  # string
    "value": [1.5, 2.3, 3.7]  # float
})

# Explicitly set types
df['id'] = df['id'].astype('int64')
df['value'] = df['value'].astype('float64')

# Write with schema
dataset.write_with_schema(df)
```

---

### Variable Errors

#### Error: Variables are strings

**Gotcha:** Project variables are always strings.

**Solutions:**
```python
# ❌ WRONG - Assumes int
variables = project.get_variables()
batch_size = variables["batch_size"]  # This is a string!
for i in range(batch_size):  # TypeError!
    ...

# ✓ CORRECT - Convert types
variables = project.get_variables()
batch_size = int(variables["batch_size"])
enabled = variables["enabled"].lower() == "true"
threshold = float(variables["threshold"])
```

---

### SSL/Certificate Errors

#### Error: "SSL certificate verification failed"

**Causes:**
- Self-signed certificate
- Expired certificate
- Missing CA certificate

**Solutions:**
```python
# Development only - disable verification
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = DSSClient(
    host,
    api_key,
    no_check_certificate=True  # DEV ONLY!
)

# Production - use proper certificates
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'
client = DSSClient(host, api_key)
```

---

### API Rate Limiting

#### Error: "Too many requests"

**Cause:** Hitting API rate limits.

**Solutions:**
```python
import time
from functools import wraps

def rate_limit(calls_per_second=2):
    """Decorator to rate limit API calls"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed

            if wait_time > 0:
                time.sleep(wait_time)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper
    return decorator

# Usage
@rate_limit(calls_per_second=2)
def get_dataset_schema(project, dataset_name):
    dataset = project.get_dataset(dataset_name)
    return dataset.get_schema()

# Now automatically rate limited
for ds_name in dataset_names:
    schema = get_dataset_schema(project, ds_name)
```

---

## Best Practices to Avoid Issues

### 1. Always Use Try-Except

```python
def safe_operation(func, *args, **kwargs):
    """Wrapper for safe API operations"""
    try:
        return func(*args, **kwargs)
    except DataikuException as e:
        print(f"Dataiku API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Usage
result = safe_operation(dataset.build, wait=True)
if result:
    print("Success")
else:
    print("Failed")
```

### 2. Validate Before Operating

```python
def safe_build_dataset(project, dataset_name):
    """Build dataset with validation"""

    # Check dataset exists
    try:
        dataset = project.get_dataset(dataset_name)
    except:
        print(f"❌ Dataset {dataset_name} not found")
        return None

    # Check not already building
    # Check inputs are ready
    # Then build

    try:
        job = dataset.build(wait=True)
        print(f"✓ Built {dataset_name}")
        return job
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return None
```

### 3. Use Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in code
logger.info("Starting dataset build")
try:
    job = dataset.build(wait=True)
    logger.info(f"Build succeeded: {job.id}")
except Exception as e:
    logger.error(f"Build failed: {e}", exc_info=True)
```

### 4. Implement Retries

```python
from functools import wraps
import time

def retry(max_attempts=3, delay=1, backoff=2):
    """Retry decorator with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise

                    print(f"Attempt {attempts} failed: {e}")
                    print(f"Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

# Usage
@retry(max_attempts=3, delay=2, backoff=2)
def build_dataset(dataset):
    return dataset.build(wait=True)

job = build_dataset(dataset)
```

### 5. Clean Up Resources

```python
class DataikuSession:
    """Context manager for Dataiku operations"""

    def __init__(self, host, api_key):
        self.host = host
        self.api_key = api_key
        self.client = None

    def __enter__(self):
        self.client = DSSClient(self.host, self.api_key)
        # Verify connection
        self.client.list_project_keys()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        if exc_type:
            logging.error(f"Error in session: {exc_val}")
        return False

# Usage
with DataikuSession(host, api_key) as client:
    project = client.get_project("MY_PROJECT")
    # Do work...
# Automatic cleanup
```

---

## Debugging Checklist

When something goes wrong, check these in order:

1. **Connection**
   - [ ] Can you ping the DSS host?
   - [ ] Is DSS running?
   - [ ] Is the API key valid?

2. **Permissions**
   - [ ] Can you list projects?
   - [ ] Can you access the specific project?
   - [ ] Does the user have required permissions?

3. **Resources**
   - [ ] Does the dataset/recipe/scenario exist?
   - [ ] Is it in the project you're accessing?
   - [ ] Are names spelled correctly (case-sensitive)?

4. **Dependencies**
   - [ ] Are input datasets built?
   - [ ] Are schemas up to date?
   - [ ] Are connections configured?

5. **State**
   - [ ] Is a job already running?
   - [ ] Is the scenario active?
   - [ ] Are there conflicting operations?

6. **Configuration**
   - [ ] Did you call `.save()` on settings?
   - [ ] Did you update schemas after recipe changes?
   - [ ] Are variable types correct (strings)?

---

## Getting Help

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# Now API calls will be logged
client = DSSClient(host, api_key)
```

### Inspect API Calls

```python
# Access internal session to see what's being called
client = DSSClient(host, api_key)

# Enable request logging
import http.client
http.client.HTTPConnection.debuglevel = 1

# Now you'll see all HTTP requests
project = client.get_project("MY_PROJECT")
```

---

## Next Steps

- **99-quick-reference.md** - Quick lookup for common operations
- Review specific guides for detailed patterns

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
