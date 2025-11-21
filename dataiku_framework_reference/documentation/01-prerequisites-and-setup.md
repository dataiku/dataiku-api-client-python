# 01 - Prerequisites and Setup

**Purpose:** Project structure, API key management, and configuration patterns for framework development

---

## Recommended Project Structure

When building frameworks or wrappers for Dataiku, use this structure:

```
your_project/
├── config/
│   ├── APIKEY.txt           # Dataiku API key (never commit!)
│   ├── config.json          # Environment configuration
│   └── .gitignore           # Ensure APIKEY.txt is ignored!
├── dataiku_framework_reference/  # This documentation (read-only)
│   ├── documentation/
│   ├── api_inventory/
│   └── README.md
├── claude-guides/           # Usage guides (read-only reference)
├── documentation/           # Your project docs
├── logs/                    # Auto-created log files
│   └── .gitignore          # Ignore all logs
├── debug/                   # Debugging scripts and utilities
├── testing/                 # Validation and test scripts
├── dataiku_framework/       # Your wrapper framework code
│   ├── __init__.py
│   ├── client.py
│   ├── projects.py
│   ├── datasets.py
│   ├── recipes.py
│   ├── scenarios.py
│   ├── jobs.py
│   └── utils.py
├── examples/                # Usage examples for your framework
├── tests/                   # Unit and integration tests
├── {PROJECT_KEY}_create_project.py    # Project-specific scripts
├── {PROJECT_KEY}_run_pipeline.py
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup (if distributing)
└── README.md                # Project documentation
```

---

## API Key Setup

### Step 1: Generate API Key in Dataiku

1. **Log in to your Dataiku DSS instance**
   - Navigate to your Dataiku URL (e.g., `https://dss.yourcompany.com`)

2. **Access your user profile**
   - Click your username/avatar in the top-right corner
   - Select "Profile" or "Settings"

3. **Navigate to API Keys**
   - Look for "API Keys" tab or section
   - May be under "Security" or "Developer" settings

4. **Create a new API key**
   - Click "Create New Key" or similar button
   - Give it a descriptive name: `Framework Development - Production` or `Automation Scripts`
   - Optionally set expiration date (recommended for security)

5. **Copy the API key immediately**
   - You'll only see the key once!
   - It looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Step 2: Save API Key Securely

Create `config/APIKEY.txt` in your project:

```bash
# Create config directory
mkdir -p config

# Save API key (replace with your actual key)
echo "your-actual-api-key-here" > config/APIKEY.txt

# Verify it was saved
cat config/APIKEY.txt
```

### Step 3: Secure the API Key

**CRITICAL:** Never commit API keys to version control!

Create or update `.gitignore`:

```gitignore
# In project root .gitignore
config/APIKEY.txt
config/*.txt
*.key
*.secret

# Also ignore logs
logs/
*.log

# And other sensitive files
config/config.json  # If it contains secrets
.env
.env.local
credentials.json
```

Create `config/.gitignore`:

```gitignore
# In config/.gitignore
APIKEY.txt
*.txt
*.key
*.secret
```

---

## File Naming Convention

### Pattern: `{PROJECT_KEY}_filename.py`

**Why this pattern?**
- Groups files alphabetically by project
- Easy identification of project ownership
- Better organization with multiple projects
- Clear project context when viewing file list

**Examples:**

```python
# Good naming
customer_analytics_create_project.py
customer_analytics_build_pipeline.py
customer_analytics_test_scenarios.py

sales_reporting_create_project.py
sales_reporting_daily_refresh.py

data_quality_audit_datasets.py
data_quality_validation_rules.py

# Bad naming
create_project.py           # Which project?
pipeline.py                 # Not descriptive
test.py                     # Too generic
my_script_final_v2.py       # Unclear
```

**Directory structure with naming:**

```
your_project/
├── customer_analytics_create_project.py
├── customer_analytics_build_pipeline.py
├── customer_analytics_test_scenarios.py
├── sales_reporting_create_project.py
├── sales_reporting_daily_refresh.py
├── data_quality_audit_datasets.py
└── data_quality_validation_rules.py
```

Files are automatically grouped by project when sorted!

---

## Configuration Patterns

### Option 1: Simple APIKEY.txt + Hardcoded Config

```python
# customer_analytics_create_project.py
from dataikuapi import DSSClient
from pathlib import Path

# Read API key
api_key_path = Path(__file__).parent / "config" / "APIKEY.txt"
with open(api_key_path, 'r') as f:
    api_key = f.read().strip()

# Connect
client = DSSClient("https://dss.yourcompany.com", api_key)

# Use client
project = client.get_project("CUSTOMER_ANALYTICS")
```

### Option 2: config.json + APIKEY.txt

Create `config/config.json`:

```json
{
  "environments": {
    "dev": {
      "host": "https://dev-dss.yourcompany.com",
      "default_owner": "dev_user"
    },
    "staging": {
      "host": "https://staging-dss.yourcompany.com",
      "default_owner": "staging_user"
    },
    "prod": {
      "host": "https://dss.yourcompany.com",
      "default_owner": "prod_user"
    }
  },
  "projects": {
    "CUSTOMER_ANALYTICS": {
      "description": "Customer behavior analytics pipeline",
      "tags": ["production", "analytics"]
    },
    "SALES_REPORTING": {
      "description": "Daily sales reporting automation",
      "tags": ["production", "reporting"]
    }
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

Usage:

```python
import json
from pathlib import Path
from dataikuapi import DSSClient

def load_config(env="prod"):
    """Load configuration for specific environment"""
    config_dir = Path(__file__).parent / "config"

    # Load config.json
    with open(config_dir / "config.json", 'r') as f:
        config = json.load(f)

    # Load API key
    with open(config_dir / "APIKEY.txt", 'r') as f:
        api_key = f.read().strip()

    # Get environment config
    env_config = config['environments'][env]
    env_config['api_key'] = api_key

    return env_config, config

def get_client(env="prod"):
    """Get configured DSS client"""
    env_config, _ = load_config(env)

    return DSSClient(
        env_config['host'],
        env_config['api_key']
    )

# Usage
if __name__ == "__main__":
    client = get_client("prod")
    projects = client.list_project_keys()
    print(f"Connected to production: {len(projects)} projects")
```

### Option 3: Multi-Environment with Separate Keys

```
config/
├── dev_APIKEY.txt
├── staging_APIKEY.txt
├── prod_APIKEY.txt
└── config.json
```

```python
def get_client(env="prod"):
    """Get client for specific environment"""
    config_dir = Path(__file__).parent / "config"

    # Load environment-specific API key
    api_key_path = config_dir / f"{env}_APIKEY.txt"
    with open(api_key_path, 'r') as f:
        api_key = f.read().strip()

    # Load config
    with open(config_dir / "config.json", 'r') as f:
        config = json.load(f)

    env_config = config['environments'][env]

    return DSSClient(env_config['host'], api_key)

# Usage
dev_client = get_client("dev")
prod_client = get_client("prod")
```

---

## Required API Key Permissions

Your API key needs these permissions:

### Minimum (Read-Only Analysis):
- ✓ Read project
- ✓ Read project data
- ✓ Execute SQL queries

### Standard (Most Automation):
- ✓ Read project
- ✓ Write project
- ✓ Create/modify datasets
- ✓ Create/modify recipes
- ✓ Run recipes and scenarios
- ✓ Build datasets
- ✓ Access managed folders

### Advanced (Full Automation):
- ✓ All Standard permissions
- ✓ Create projects
- ✓ Modify project settings
- ✓ Create/modify scenarios
- ✓ Manage project variables
- ✓ Deploy to API nodes

### Admin (Instance Management):
- ✓ All Advanced permissions
- ✓ Manage users and groups
- ✓ Manage connections
- ✓ Manage code environments
- ✓ Access instance settings
- ✓ Create API keys

**How to check permissions:**

```python
from dataikuapi import DSSClient

def check_permissions(client):
    """Check what permissions the API key has"""
    capabilities = {
        "list_projects": False,
        "create_project": False,
        "admin_access": False,
        "list_users": False
    }

    try:
        projects = client.list_project_keys()
        capabilities["list_projects"] = True
        print(f"✓ Can list projects ({len(projects)} accessible)")
    except Exception as e:
        print(f"✗ Cannot list projects: {e}")

    try:
        # Try admin operation
        users = client.list_users()
        capabilities["admin_access"] = True
        capabilities["list_users"] = True
        print(f"✓ Has admin access (can list {len(users)} users)")
    except:
        print("ℹ No admin access (normal user)")

    return capabilities

# Usage
client = get_client()
caps = check_permissions(client)
```

---

## Python Environment Setup

### Required Packages

Create `requirements.txt`:

```txt
# Dataiku API client
dataiku-api-client==14.1.3

# Common utilities
python-dateutil>=2.8.0
requests>=2.28.0

# Data processing (if needed)
pandas>=1.5.0
numpy>=1.24.0

# Logging and configuration
pyyaml>=6.0
python-dotenv>=0.20.0

# Testing
pytest>=7.0.0
pytest-cov>=4.0.0
```

### Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import dataikuapi; print(dataikuapi.__version__)"
```

---

## Logging Setup

Create proper logging for debugging:

```python
# common/logging_config.py
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(project_key, log_level="INFO"):
    """Configure logging for project scripts"""

    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{project_key}_{timestamp}.log"

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(project_key)
    logger.info(f"Logging initialized: {log_file}")

    return logger

# Usage in scripts
if __name__ == "__main__":
    logger = setup_logging("CUSTOMER_ANALYTICS", "DEBUG")
    logger.info("Starting pipeline execution")
    # Your code here
    logger.info("Pipeline completed successfully")
```

---

## Connection Verification Script

Create `debug/verify_connection.py`:

```python
#!/usr/bin/env python3
"""
Verify Dataiku API connection and permissions
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException

def verify_connection():
    """Verify API connection and basic permissions"""

    print("=" * 60)
    print("DATAIKU API CONNECTION VERIFICATION")
    print("=" * 60)

    # Load API key
    try:
        api_key_path = Path(__file__).parent.parent / "config" / "APIKEY.txt"
        with open(api_key_path, 'r') as f:
            api_key = f.read().strip()
        print(f"✓ API key loaded from {api_key_path}")
        print(f"  Key length: {len(api_key)} characters")
    except FileNotFoundError:
        print("✗ APIKEY.txt not found!")
        print("  Expected location: config/APIKEY.txt")
        return False
    except Exception as e:
        print(f"✗ Error loading API key: {e}")
        return False

    # Get host from config or use default
    host = "https://dss.yourcompany.com"  # Update this!

    # Try to connect
    try:
        client = DSSClient(host, api_key)
        print(f"✓ Client created for host: {host}")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return False

    # Test authentication
    try:
        projects = client.list_project_keys()
        print(f"✓ Authentication successful")
        print(f"  Accessible projects: {len(projects)}")
        if projects:
            print(f"  Sample projects: {projects[:5]}")
    except DataikuException as e:
        print(f"✗ Authentication failed: {e}")
        return False

    # Check admin permissions
    try:
        users = client.list_users()
        print(f"✓ Admin access: YES")
        print(f"  Total users: {len(users)}")
    except:
        print("ℹ Admin access: NO (normal user)")

    # Check connections
    try:
        connections = client.list_connections()
        print(f"✓ Can list connections: {len(connections)} found")
    except:
        print("ℹ Cannot list connections (limited permissions)")

    print("\n" + "=" * 60)
    print("CONNECTION VERIFICATION COMPLETE")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = verify_connection()
    sys.exit(0 if success else 1)
```

Run it:

```bash
python debug/verify_connection.py
```

---

## Best Practices

### 1. Never Commit Secrets

```gitignore
# Always in .gitignore
config/APIKEY.txt
config/*APIKEY.txt
*.key
*.secret
.env
credentials.json
```

### 2. Use Environment-Specific Keys

- Separate keys for dev/staging/prod
- Different permission levels per environment
- Easy to rotate without affecting other envs

### 3. Document Your Config

```python
# config/README.md
"""
Configuration Files

APIKEY.txt - Your Dataiku API key (never commit!)
  - Get from: https://dss.company.com → Profile → API Keys
  - Permissions needed: Read, Write, Create datasets/recipes

config.json - Environment and project configuration
  - Contains: hosts, default owners, project metadata
  - Safe to commit (no secrets)
"""
```

### 4. Validate Early

```python
def validate_config():
    """Validate all required config files exist"""
    config_dir = Path(__file__).parent / "config"

    required = [
        config_dir / "APIKEY.txt",
        config_dir / "config.json"
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(f"Required config missing: {path}")

    print("✓ All required config files present")

# Run at script start
validate_config()
```

---

## Next Steps

1. **Set up your project structure** using the recommended layout
2. **Create config/APIKEY.txt** with your API key
3. **Test connection** using `debug/verify_connection.py`
4. **Read next guide:** `02-api-overview.md` to understand the API architecture

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
