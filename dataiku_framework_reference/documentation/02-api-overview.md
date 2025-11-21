# 02 - API Overview

**Purpose:** Understanding Dataiku Python API architecture and design

**Status:** See `../api_inventory/classes_and_methods.md` for complete class reference

---

## Quick Overview

The Dataiku Python API (`dataikuapi`) provides programmatic access to all Dataiku DSS functionality.

### Main Client Classes

- **DSSClient** - Primary entry point for Dataiku DSS
- **GovernClient** - For Dataiku Govern operations
- **FMClient** - Fleet Management (AWS/Azure/GCP variants)
- **APINodeClient** - For deployed API services
- **APINodeAdminClient** - API Node administration

### Key Modules

- `dataikuapi.dss.*` - DSS operations (150+ classes)
- `dataikuapi.govern.*` - Govern operations
- `dataikuapi.fm.*` - Fleet management
- `dataikuapi.apinode_admin.*` - API Node admin

---

## For Complete Details

**See:**
- `../api_inventory/classes_and_methods.md` - Full API inventory (1,162 lines)
- `../api_inventory/class_index.md` - Quick reference by category (500 lines)
- `../../claude-guides/02-authentication-and-connection.md` - Usage guide

---

**Last Updated:** 2025-11-21
