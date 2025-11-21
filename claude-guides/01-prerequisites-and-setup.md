# 01 - Prerequisites and Setup

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Guide for setting up and configuring the Dataiku Python API client

---

## Overview

The Dataiku Python API provides programmatic access to Dataiku DSS (Data Science Studio) for automation, integration, and custom workflows. There are TWO distinct Python packages:

1. **`dataiku`** - Internal package for use INSIDE DSS (recipes, notebooks, webapps)
2. **`dataikuapi`** - Client package for EXTERNAL use (automation, administration, remote control)

**This guide focuses on `dataikuapi` for external API access.**

---

## Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install dataiku-api-client
```

### Method 2: Install from source

```bash
git clone https://github.com/dataiku/dataiku-api-client-python.git
cd dataiku-api-client-python
pip install -e .
```

### Version Compatibility

- Python 3.7+ required
- API client version should match or be close to your DSS instance version
- Check your DSS version: Administration → About Dataiku DSS

```python
# Check installed version
import dataikuapi
print(dataikuapi.__version__)  # e.g., "14.1.3"
```

---

## API Key Generation

**CRITICAL:** You must have a valid API key to use the client.

### Creating a Personal API Key

1. Log into your Dataiku DSS instance
2. Click your profile icon (top right)
3. Select "API Keys" or "Settings"
4. Click "Create New Key"
5. Give it a description (e.g., "Automation Script - Production ETL")
6. **Copy the key immediately** - you won't see it again
7. Store securely (environment variable, secrets manager, NOT in code)

### API Key Types

| Type | Scope | Use Case |
|------|-------|----------|
| **Personal** | User's permissions | Development, testing |
| **Project-level** | Single project | Limited automation |
| **Global Admin** | Instance-wide | Administration, multi-project automation |

### API Key Permissions

- Keys inherit the user's permissions
- Cannot do more than the user can do manually
- If you get `SecurityException`, check user permissions in DSS
- Admin keys needed for: creating projects, managing users, instance settings

---

## Environment Setup

### Secure API Key Storage

**NEVER hardcode API keys in scripts!**

#### Option 1: Environment Variables (Recommended)

```bash
# In ~/.bashrc or ~/.zshrc
export DATAIKU_API_KEY="your-api-key-here"
export DATAIKU_HOST="https://dss.yourcompany.com"
```

```python
import os
from dataikuapi import DSSClient

api_key = os.environ.get('DATAIKU_API_KEY')
host = os.environ.get('DATAIKU_HOST')

client = DSSClient(host, api_key)
```

#### Option 2: Config File (for development)

```python
# config.py (add to .gitignore!)
DATAIKU_CONFIG = {
    "host": "https://dss.yourcompany.com",
    "api_key": "your-api-key-here"
}
```

```python
from config import DATAIKU_CONFIG
from dataikuapi import DSSClient

client = DSSClient(
    DATAIKU_CONFIG['host'],
    DATAIKU_CONFIG['api_key']
)
```

#### Option 3: Secrets Manager (for production)

```python
# Example with AWS Secrets Manager
import boto3
import json
from dataikuapi import DSSClient

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

secrets = get_secret('dataiku/prod/api-credentials')
client = DSSClient(secrets['host'], secrets['api_key'])
```

---

## Connection Configuration

### Basic Connection

```python
from dataikuapi import DSSClient

# Simplest form
client = DSSClient(
    host="https://dss.yourcompany.com",
    api_key="your-api-key"
)

# Test connection
projects = client.list_project_keys()
print(f"Connected! Found {len(projects)} projects")
```

### Advanced Connection Options

```python
from dataikuapi import DSSClient

client = DSSClient(
    host="https://dss.yourcompany.com",
    api_key="your-api-key",

    # SSL/TLS options
    no_check_certificate=False,  # Set True for self-signed certs (DEV ONLY!)

    # Client certificate authentication
    client_certificate=("/path/to/cert.pem", "/path/to/key.pem"),

    # Custom headers (rarely needed)
    extra_headers={"X-Custom-Header": "value"}
)
```

### Internal Ticket (Advanced)

For internal DSS communications, you may use tickets instead of API keys:

```python
client = DSSClient(
    host="http://localhost:11200",
    internal_ticket="ticket-from-dss-process"
)
```

**Note:** This is typically only for DSS plugin development or internal automation.

---

## Network and Connectivity

### Firewall Requirements

- DSS API runs on the design node
- Default port: **11200** (configurable)
- HTTPS recommended for production
- Ensure your client can reach: `https://<dss-host>:<port>/public/api/`

### Testing Connectivity

```bash
# Test basic connectivity
curl -I https://dss.yourcompany.com/public/api/

# Test authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://dss.yourcompany.com/public/api/projects/
```

### Proxy Configuration

If behind a corporate proxy:

```python
import os

# Set proxy environment variables
os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
os.environ['HTTPS_PROXY'] = 'http://proxy.company.com:8080'
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

# Then create client normally
from dataikuapi import DSSClient
client = DSSClient(host, api_key)
```

Or configure in requests session:

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# Access internal session
client._session.proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'http://proxy.company.com:8080',
}
```

---

## Verification Script

Use this script to verify your setup:

```python
#!/usr/bin/env python3
"""
Dataiku API Setup Verification Script
Run this to verify your connection and permissions
"""

import os
import sys
from dataikuapi import DSSClient
from dataikuapi.utils import DataikuException

def verify_setup():
    """Verify Dataiku API connection and basic permissions"""

    # Step 1: Check environment variables
    print("=" * 60)
    print("STEP 1: Checking environment variables...")
    print("=" * 60)

    api_key = os.environ.get('DATAIKU_API_KEY')
    host = os.environ.get('DATAIKU_HOST')

    if not api_key:
        print("❌ DATAIKU_API_KEY not set")
        print("   Set it with: export DATAIKU_API_KEY='your-key'")
        return False
    else:
        print(f"✓ DATAIKU_API_KEY found (length: {len(api_key)})")

    if not host:
        print("❌ DATAIKU_HOST not set")
        print("   Set it with: export DATAIKU_HOST='https://dss.company.com'")
        return False
    else:
        print(f"✓ DATAIKU_HOST found: {host}")

    # Step 2: Test connection
    print("\n" + "=" * 60)
    print("STEP 2: Testing connection...")
    print("=" * 60)

    try:
        client = DSSClient(host, api_key)
        print(f"✓ Client created successfully")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False

    # Step 3: Test authentication
    print("\n" + "=" * 60)
    print("STEP 3: Testing authentication...")
    print("=" * 60)

    try:
        projects = client.list_project_keys()
        print(f"✓ Authentication successful")
        print(f"  Found {len(projects)} accessible projects")
        if projects:
            print(f"  Sample projects: {projects[:5]}")
    except DataikuException as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your API key and permissions")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Step 4: Check permissions
    print("\n" + "=" * 60)
    print("STEP 4: Checking permissions...")
    print("=" * 60)

    # Try to get general settings (admin only)
    try:
        settings = client.get_general_settings()
        print("✓ Admin access: YES (can access general settings)")
    except:
        print("ℹ Admin access: NO (normal user - this is usually fine)")

    # Try to list users (admin only)
    try:
        users = client.list_users()
        print(f"✓ Can list users: YES ({len(users)} users)")
    except:
        print("ℹ Can list users: NO (requires admin)")

    # Try to list connections (requires some permissions)
    try:
        connections = client.list_connections()
        print(f"✓ Can list connections: YES ({len(connections)} connections)")
    except:
        print("ℹ Can list connections: NO (limited permissions)")

    # Step 5: Summary
    print("\n" + "=" * 60)
    print("SETUP VERIFICATION COMPLETE")
    print("=" * 60)
    print("✓ Your Dataiku API client is configured correctly!")
    print("\nNext steps:")
    print("  - Read 02-authentication-and-connection.md for connection patterns")
    print("  - Read 03-project-operations.md to start working with projects")

    return True

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
```

Save as `verify_setup.py` and run:

```bash
python verify_setup.py
```

---

## Common Setup Issues

### Issue: "Connection refused" or timeout

**Causes:**
- DSS instance not running
- Wrong host/port
- Firewall blocking connection
- Network connectivity issue

**Solutions:**
1. Verify DSS is running: `https://dss.yourcompany.com` in browser
2. Check port (default 11200)
3. Test with curl: `curl -I https://dss.yourcompany.com/`
4. Check firewall rules
5. Try from same network as DSS

### Issue: "401 Unauthorized" or "403 Forbidden"

**Causes:**
- Invalid API key
- Expired API key
- API key lacks required permissions
- User account disabled

**Solutions:**
1. Regenerate API key in DSS UI
2. Check user account is active
3. Verify key has correct permissions
4. Try with admin key to rule out permission issues

### Issue: "SSL Certificate Verification Failed"

**Causes:**
- Self-signed certificate
- Expired certificate
- Certificate chain issue

**Solutions:**
1. For dev/testing only: `no_check_certificate=True`
2. For production: Install proper CA certificate
3. Update system certificate store
4. Use client certificate authentication

### Issue: Import error "No module named 'dataikuapi'"

**Causes:**
- Package not installed
- Wrong Python environment
- Wrong pip/python version

**Solutions:**
```bash
# Check which Python
which python
which pip

# Check installed packages
pip list | grep dataiku

# Install in correct environment
pip install dataiku-api-client

# Or for specific Python version
python3.9 -m pip install dataiku-api-client
```

---

## Best Practices

1. **Use Environment Variables** for credentials
2. **Never commit API keys** to version control (add to .gitignore)
3. **Use HTTPS** in production (not HTTP)
4. **Rotate API keys** regularly (every 90 days recommended)
5. **Use service accounts** for automation (not personal keys)
6. **Set key descriptions** so you know what each key is for
7. **Delete unused keys** regularly
8. **Monitor API usage** through DSS audit logs
9. **Use the minimum permissions** needed (principle of least privilege)
10. **Test with read-only operations** first before making changes

---

## Next Steps

Once setup is verified:

1. **02-authentication-and-connection.md** - Learn about scope hierarchy and connection patterns
2. **03-project-operations.md** - Start working with projects
3. **99-quick-reference.md** - Quick lookup for common operations

---

## Resources

- **Official Docs:** https://doc.dataiku.com/dss/latest/python-api/
- **API Reference:** https://developer.dataiku.com/latest/api-reference/python/
- **GitHub:** https://github.com/dataiku/dataiku-api-client-python
- **PyPI:** https://pypi.org/project/dataiku-api-client/

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
