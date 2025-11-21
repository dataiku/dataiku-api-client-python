# 02 - Authentication and Connection Patterns

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Understanding scope hierarchy, authentication methods, and connection patterns

---

## Scope Hierarchy (CRITICAL CONCEPT)

The Dataiku API uses a **hierarchical scope pattern**. Understanding this is essential:

```
DSSClient (Instance Level)
    ↓
DSSProject (Project Level)
    ↓
DSSDataset / DSSRecipe / DSSScenario / ... (Item Level)
```

**Key Principle:** Each scope level restricts what operations you can perform.

### Scope Levels Explained

| Level | Class | What You Can Do | What You Cannot Do |
|-------|-------|-----------------|-------------------|
| **Instance** | `DSSClient` | List/create projects, manage users, admin tasks | Access project items directly |
| **Project** | `DSSProject` | List/create datasets/recipes, access project items | Access other projects' items |
| **Item** | `DSSDataset`, `DSSRecipe`, etc. | Work with specific item | Access other items |

### Example: The Wrong Way

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# ❌ WRONG - Cannot get dataset directly from client
dataset = client.get_dataset("my_dataset")  # AttributeError!
```

### Example: The Right Way

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# ✓ CORRECT - Must go through project scope
project = client.get_project("MY_PROJECT")
dataset = project.get_dataset("my_dataset")
```

---

## Authentication Methods

### Method 1: API Key Authentication (Most Common)

```python
from dataikuapi import DSSClient

client = DSSClient(
    "https://dss.yourcompany.com",
    "your-api-key-here"
)
```

**How it works:**
- Uses HTTP Basic Authentication
- API key as username, empty password
- Key sent in `Authorization` header: `Basic base64(api_key:)`

### Method 2: Bearer Token (OAuth2/JWT)

Used primarily for API Node endpoints:

```python
from dataikuapi.apinode_client import APINodeClient

client = APINodeClient(
    "https://apinode.yourcompany.com",
    "bearer-token-here"
)
```

**When to use:**
- Accessing deployed API services
- Integration with OAuth2 systems
- Token-based authentication requirements

### Method 3: Internal Ticket (Plugin Development)

```python
from dataikuapi import DSSClient

client = DSSClient(
    "http://localhost:11200",
    internal_ticket="internal-ticket-from-dss"
)
```

**When to use:**
- DSS plugin development
- Internal DSS processes
- Rarely needed for normal automation

---

## Connection Patterns

### Pattern 1: Simple Script (Basic)

For one-off scripts:

```python
from dataikuapi import DSSClient
import os

# Get credentials from environment
client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)

# Do work
project = client.get_project("MY_PROJECT")
dataset = project.get_dataset("customers")
dataset.build()
```

### Pattern 2: Context Manager (Recommended)

For proper resource management:

```python
from dataikuapi import DSSClient
import os

class DataikuConnection:
    """Context manager for Dataiku connections"""

    def __init__(self, host=None, api_key=None):
        self.host = host or os.getenv('DATAIKU_HOST')
        self.api_key = api_key or os.getenv('DATAIKU_API_KEY')
        self.client = None

    def __enter__(self):
        self.client = DSSClient(self.host, self.api_key)
        # Verify connection
        self.client.list_project_keys()
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        if exc_type:
            print(f"Error occurred: {exc_val}")
        return False

# Usage
with DataikuConnection() as client:
    project = client.get_project("MY_PROJECT")
    # Do work...
```

### Pattern 3: Singleton Client (Long-Running Services)

For services that keep one connection:

```python
from dataikuapi import DSSClient
import os
from threading import Lock

class DataikuClientSingleton:
    """Thread-safe singleton for Dataiku client"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.client = DSSClient(
            os.getenv('DATAIKU_HOST'),
            os.getenv('DATAIKU_API_KEY')
        )

    def get_client(self):
        return self.client

# Usage
dataiku = DataikuClientSingleton()
client = dataiku.get_client()
```

### Pattern 4: Multi-Instance Connection

For working with multiple DSS instances:

```python
from dataikuapi import DSSClient

class MultiInstanceManager:
    """Manage connections to multiple DSS instances"""

    def __init__(self):
        self.clients = {}

    def add_instance(self, name, host, api_key):
        """Register a DSS instance"""
        self.clients[name] = DSSClient(host, api_key)

    def get_client(self, name):
        """Get client for specific instance"""
        if name not in self.clients:
            raise ValueError(f"Instance '{name}' not registered")
        return self.clients[name]

    def sync_project(self, source_instance, target_instance, project_key):
        """Example: Sync project from one instance to another"""
        source = self.get_client(source_instance)
        target = self.get_client(target_instance)

        # Export from source
        source_project = source.get_project(project_key)
        export_stream = source_project.get_export_stream()

        # Import to target
        target.prepare_project_import(export_stream).execute()

# Usage
manager = MultiInstanceManager()
manager.add_instance("dev", "https://dev-dss.company.com", "dev-key")
manager.add_instance("prod", "https://prod-dss.company.com", "prod-key")

dev_client = manager.get_client("dev")
prod_client = manager.get_client("prod")
```

### Pattern 5: Retry Logic (Production)

For resilient connections:

```python
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """Decorator for retrying failed API calls"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except DataikuException as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    print(f"Attempt {retries} failed: {e}")
                    print(f"Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

class ResilientDataikuClient:
    """Dataiku client with automatic retry logic"""

    def __init__(self, host, api_key):
        self.host = host
        self.api_key = api_key
        self._client = None

    @retry_on_failure(max_retries=3)
    def connect(self):
        """Connect with retry logic"""
        self._client = DSSClient(self.host, self.api_key)
        # Test connection
        self._client.list_project_keys()
        return self._client

    @property
    def client(self):
        if self._client is None:
            self._client = self.connect()
        return self._client

# Usage
resilient_client = ResilientDataikuClient(host, api_key)
client = resilient_client.client
```

---

## Permission-Aware Patterns

### Pattern 6: Check Before Execute

Always check permissions before attempting operations:

```python
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException

def safe_create_dataset(project, dataset_name, connection, table):
    """Create dataset with permission checking"""

    try:
        # Check if we can list datasets (basic permission check)
        project.list_datasets()
    except DataikuException as e:
        print(f"❌ No permission to access project: {e}")
        return None

    try:
        # Check if dataset already exists
        existing = [d for d in project.list_datasets()
                   if d['name'] == dataset_name]
        if existing:
            print(f"Dataset {dataset_name} already exists")
            return project.get_dataset(dataset_name)

        # Try to create
        dataset = project.create_dataset(
            dataset_name,
            "SQL",
            params={"connection": connection, "table": table}
        )
        print(f"✓ Created dataset {dataset_name}")
        return dataset

    except DataikuException as e:
        if "not allowed" in str(e).lower():
            print(f"❌ No permission to create datasets: {e}")
        else:
            print(f"❌ Failed to create dataset: {e}")
        return None

# Usage
client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")
dataset = safe_create_dataset(project, "new_table", "postgres", "public.users")
```

### Pattern 7: Admin vs User Detection

Determine what the current key can do:

```python
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException

class PermissionChecker:
    """Check what permissions current API key has"""

    def __init__(self, client):
        self.client = client
        self._is_admin = None
        self._can_create_projects = None

    def is_admin(self):
        """Check if key has admin privileges"""
        if self._is_admin is None:
            try:
                self.client.get_general_settings()
                self._is_admin = True
            except:
                self._is_admin = False
        return self._is_admin

    def can_create_projects(self):
        """Check if key can create projects"""
        if self._can_create_projects is None:
            try:
                # Try to get authorization matrix (admin only)
                self.client.get_authorization_matrix()
                self._can_create_projects = True
            except:
                self._can_create_projects = False
        return self._can_create_projects

    def can_access_project(self, project_key):
        """Check if key can access specific project"""
        try:
            self.client.get_project(project_key)
            return True
        except:
            return False

    def get_accessible_projects(self):
        """Get list of all accessible projects"""
        try:
            return self.client.list_project_keys()
        except:
            return []

# Usage
client = DSSClient(host, api_key)
checker = PermissionChecker(client)

if checker.is_admin():
    print("Running with admin privileges")
else:
    print("Running with limited user privileges")
    projects = checker.get_accessible_projects()
    print(f"Can access {len(projects)} projects: {projects}")
```

---

## Connection Pooling and Reuse

### Best Practice: Reuse Client Objects

**❌ INEFFICIENT:**

```python
# Creating new client for each operation
def get_dataset_schema(project_key, dataset_name):
    client = DSSClient(host, api_key)  # New connection each time!
    project = client.get_project(project_key)
    dataset = project.get_dataset(dataset_name)
    return dataset.get_schema()

# Called 100 times = 100 connections!
for dataset_name in datasets:
    schema = get_dataset_schema("MY_PROJECT", dataset_name)
```

**✓ EFFICIENT:**

```python
# Reuse client across operations
def get_dataset_schemas(client, project_key, dataset_names):
    project = client.get_project(project_key)

    schemas = {}
    for dataset_name in dataset_names:
        dataset = project.get_dataset(dataset_name)
        schemas[dataset_name] = dataset.get_schema()

    return schemas

# Single client for all operations
client = DSSClient(host, api_key)
schemas = get_dataset_schemas(client, "MY_PROJECT", datasets)
```

### Session Management

The `DSSClient` internally uses a `requests.Session` which pools connections:

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# The internal session is reused
# Access it if needed for advanced config:
client._session.timeout = 30  # Set timeout
client._session.verify = True  # Enable SSL verification
```

---

## Environment-Specific Configurations

### Configuration Class Pattern

```python
from dataclasses import dataclass
from dataikuapi import DSSClient
import os

@dataclass
class DataikuConfig:
    """Environment-specific configuration"""
    host: str
    api_key: str
    timeout: int = 30
    verify_ssl: bool = True

    @classmethod
    def from_env(cls, env='prod'):
        """Load config from environment"""
        env_prefix = f"DATAIKU_{env.upper()}_"

        return cls(
            host=os.getenv(f"{env_prefix}HOST"),
            api_key=os.getenv(f"{env_prefix}API_KEY"),
            timeout=int(os.getenv(f"{env_prefix}TIMEOUT", "30")),
            verify_ssl=os.getenv(f"{env_prefix}VERIFY_SSL", "true").lower() == "true"
        )

    def create_client(self):
        """Create configured client"""
        client = DSSClient(
            self.host,
            self.api_key,
            no_check_certificate=not self.verify_ssl
        )
        client._session.timeout = self.timeout
        return client

# Usage - different configs for different environments
# Set environment variables:
# DATAIKU_DEV_HOST=https://dev-dss.company.com
# DATAIKU_DEV_API_KEY=dev-key
# DATAIKU_PROD_HOST=https://prod-dss.company.com
# DATAIKU_PROD_API_KEY=prod-key

dev_config = DataikuConfig.from_env('dev')
dev_client = dev_config.create_client()

prod_config = DataikuConfig.from_env('prod')
prod_client = prod_config.create_client()
```

---

## Common Connection Issues and Solutions

### Issue 1: "Failed to connect" / Timeout

```python
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException
import socket

def diagnose_connection(host, api_key):
    """Diagnose connection issues"""

    print(f"Diagnosing connection to: {host}")

    # Check DNS resolution
    try:
        hostname = host.split("//")[1].split(":")[0]
        ip = socket.gethostbyname(hostname)
        print(f"✓ DNS resolution successful: {hostname} -> {ip}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return

    # Check basic connectivity
    try:
        import requests
        response = requests.get(host, timeout=5)
        print(f"✓ Basic HTTP connectivity successful (status: {response.status_code})")
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout - check network/firewall")
        return
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return

    # Check API endpoint
    try:
        response = requests.get(f"{host}/public/api/", timeout=5)
        print(f"✓ API endpoint accessible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ API endpoint not accessible: {e}")
        return

    # Try authentication
    try:
        client = DSSClient(host, api_key)
        projects = client.list_project_keys()
        print(f"✓ Authentication successful, {len(projects)} projects accessible")
    except DataikuException as e:
        print(f"❌ Authentication failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# Usage
diagnose_connection("https://dss.company.com", "your-api-key")
```

### Issue 2: SSL Certificate Problems

```python
from dataikuapi import DSSClient
import urllib3

# Option 1: Disable warnings (DEV ONLY!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client = DSSClient(
    "https://dss-with-selfsigned-cert.com",
    "api-key",
    no_check_certificate=True  # DEV ONLY!
)

# Option 2: Specify CA bundle (PRODUCTION)
import os
os.environ['REQUESTS_CA_BUNDLE'] = '/path/to/ca-bundle.crt'

client = DSSClient("https://dss.company.com", "api-key")
```

### Issue 3: Rate Limiting / Too Many Requests

```python
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException
import time

def rate_limited_operation(func, max_attempts=3, backoff_factor=2):
    """Execute operation with rate limit handling"""

    for attempt in range(max_attempts):
        try:
            return func()
        except DataikuException as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            else:
                raise

# Usage
client = DSSClient(host, api_key)

def get_all_projects():
    return client.list_projects()

projects = rate_limited_operation(get_all_projects)
```

---

## Best Practices Summary

1. **Understand scope hierarchy** - Always go through correct levels
2. **Reuse client objects** - Don't create new clients unnecessarily
3. **Check permissions first** - Wrap operations in try/except
4. **Use environment variables** - Never hardcode credentials
5. **Implement retry logic** - For production resilience
6. **Set appropriate timeouts** - Default may be too long/short
7. **Handle SSL properly** - Use proper certificates in production
8. **Log authentication attempts** - For debugging and security
9. **Use context managers** - For proper resource cleanup
10. **Test connection before operations** - Fail fast with good errors

---

## Next Steps

- **03-project-operations.md** - Working with projects
- **04-dataset-operations.md** - Dataset CRUD operations
- **08-common-gotchas.md** - More troubleshooting tips

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
