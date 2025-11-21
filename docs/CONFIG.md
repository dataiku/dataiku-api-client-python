# Configuration Patterns

Configuration best practices and patterns. See [`../dataiku_framework_reference/documentation/01-prerequisites-and-setup.md`](../dataiku_framework_reference/documentation/01-prerequisites-and-setup.md) for complete details.

---

## APIKEY.txt Pattern (CRITICAL!)

**NEVER commit API keys to version control!**

### Basic Setup

```bash
# Create config directory
mkdir -p config

# Save API key
echo "your-api-key-here" > config/APIKEY.txt

# Add to .gitignore
echo "config/APIKEY.txt" >> .gitignore
```

### .gitignore Template

```gitignore
# API Keys (CRITICAL!)
config/APIKEY.txt
config/*APIKEY.txt
*.key
*.secret

# Environment files
.env
.env.local

# Logs
logs/
*.log

# Other secrets
credentials.json
```

---

## Project Structure

```
your_project/
├── config/
│   ├── APIKEY.txt          # Your API key (NEVER COMMIT!)
│   ├── config.json         # Environment config (safe to commit)
│   └── .gitignore
├── logs/                   # Auto-created logs
├── debug/                  # Debug scripts
├── testing/                # Test scripts
├── {PROJECT_KEY}_create.py
└── {PROJECT_KEY}_build.py
```

---

## Configuration Options

### Option 1: Simple APIKEY.txt + Hardcoded

```python
from dataikuapi import DSSClient
from pathlib import Path

# Read API key
api_key_path = Path(__file__).parent / "config" / "APIKEY.txt"
with open(api_key_path, 'r') as f:
    api_key = f.read().strip()

# Connect (hardcoded host)
client = DSSClient("https://dss.company.com", api_key)
```

### Option 2: Environment Variables

```bash
export DATAIKU_HOST="https://dss.company.com"
export DATAIKU_API_KEY="your-key"
```

```python
import os
from dataikuapi import DSSClient

client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)
```

### Option 3: config.json + APIKEY.txt

**config/config.json:**
```json
{
  "environments": {
    "dev": {
      "host": "https://dev-dss.company.com",
      "default_owner": "dev_user"
    },
    "prod": {
      "host": "https://dss.company.com",
      "default_owner": "prod_user"
    }
  }
}
```

**Usage:**
```python
import json
from pathlib import Path

def load_config(env="prod"):
    config_dir = Path(__file__).parent / "config"
    
    # Load config
    with open(config_dir / "config.json") as f:
        config = json.load(f)
    
    # Load API key
    with open(config_dir / "APIKEY.txt") as f:
        api_key = f.read().strip()
    
    env_config = config['environments'][env]
    env_config['api_key'] = api_key
    
    return env_config

# Usage
config = load_config("prod")
client = DSSClient(config['host'], config['api_key'])
```

### Option 4: Multi-Environment Keys

```
config/
├── dev_APIKEY.txt
├── staging_APIKEY.txt
├── prod_APIKEY.txt
└── config.json
```

```python
def get_client(env="prod"):
    config_dir = Path(__file__).parent / "config"
    
    # Load environment-specific key
    with open(config_dir / f"{env}_APIKEY.txt") as f:
        api_key = f.read().strip()
    
    # Load config
    with open(config_dir / "config.json") as f:
        config = json.load(f)
    
    env_config = config['environments'][env]
    return DSSClient(env_config['host'], api_key)

# Usage
dev_client = get_client("dev")
prod_client = get_client("prod")
```

---

## Connection Verification

### Verify Script

```python
#!/usr/bin/env python3
"""Verify Dataiku connection"""

from dataikuapi import DSSClient
from pathlib import Path

def verify_connection():
    # Load API key
    api_key_path = Path(__file__).parent / "config" / "APIKEY.txt"
    
    if not api_key_path.exists():
        print("❌ config/APIKEY.txt not found!")
        return False
    
    with open(api_key_path) as f:
        api_key = f.read().strip()
    
    # Connect
    host = "https://dss.company.com"
    client = DSSClient(host, api_key)
    
    # Test
    try:
        projects = client.list_project_keys()
        print(f"✓ Connected! {len(projects)} projects accessible")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    verify_connection()
```

---

## Logging Configuration

```python
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(project_key):
    # Create logs directory
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{project_key}_{timestamp}.log"
    
    # Configure
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(project_key)

# Usage
logger = setup_logging("CUSTOMER_ANALYTICS")
logger.info("Starting pipeline")
```

---

## Security Best Practices

1. **Never commit secrets**
   - Add to `.gitignore`
   - Use environment variables or config files
   - Keep out of version control

2. **Rotate keys regularly**
   - Every 90 days recommended
   - Generate new, delete old

3. **Use service accounts**
   - Not personal keys for automation
   - Easier to manage and rotate

4. **Minimal permissions**
   - Only grant what's needed
   - Separate keys for dev/prod

5. **Monitor usage**
   - Check DSS audit logs
   - Track API key activity

---

**Complete Guide:** [`../dataiku_framework_reference/documentation/01-prerequisites-and-setup.md`](../dataiku_framework_reference/documentation/01-prerequisites-and-setup.md)

**Back to:** [`../CLAUDE.md`](../CLAUDE.md)
