# Dataiku Framework Reference Documentation

**Purpose:** Comprehensive reference documentation for building framework wrappers around the Dataiku Python API.

**Audience:**
- Developers building frameworks/wrappers
- Claude Code sessions doing deep API work
- Anyone needing complete API reference

---

## Structure

### `/documentation` - Numbered Reference Guides

Sequential guides for understanding the entire API:

1. **[01-prerequisites-and-setup.md](documentation/01-prerequisites-and-setup.md)**
   - Project structure recommendations
   - API key setup and security
   - File naming conventions
   - Configuration patterns

2. **[02-api-overview.md](documentation/02-api-overview.md)**
   - API architecture and design
   - Main modules and their purposes
   - Package organization
   - Entry points and client types

3. **[03-client-authentication.md](documentation/03-client-authentication.md)**
   - Authentication methods
   - Client initialization patterns
   - Connection management
   - Multi-instance scenarios

4. **[04-project-operations.md](documentation/04-project-operations.md)**
   - Complete project API reference
   - All project-level operations
   - Project settings and metadata
   - Project contents access

5. **[05-dataset-operations.md](documentation/05-dataset-operations.md)**
   - Dataset types and creation
   - Schema management
   - Data access patterns
   - Build and partition operations

6. **[06-recipe-operations.md](documentation/06-recipe-operations.md)**
   - Recipe types reference
   - Recipe creation patterns
   - Execution and monitoring
   - Schema propagation

7. **[07-scenario-operations.md](documentation/07-scenario-operations.md)**
   - Scenario structure
   - Steps and triggers
   - Execution patterns
   - Monitoring and logging

8. **[08-job-operations.md](documentation/08-job-operations.md)**
   - Job lifecycle
   - Status monitoring
   - Log access
   - Async patterns with futures

9. **[09-ml-operations.md](documentation/09-ml-operations.md)**
   - ML task reference
   - Model training and evaluation
   - Saved model management
   - Deployment patterns

10. **[10-admin-operations.md](documentation/10-admin-operations.md)**
    - User and group management
    - Connection management
    - Code environments
    - Instance settings

### `/api_inventory` - Complete API Reference

Deep technical reference:

- **[classes_and_methods.md](api_inventory/classes_and_methods.md)** - Complete class/method inventory (1,162 lines)
- **[class_index.md](api_inventory/class_index.md)** - Quick reference organized by category (500 lines)
- **[common_patterns.md](api_inventory/common_patterns.md)** - Workflow patterns and examples
- **[coverage_analysis.md](api_inventory/coverage_analysis.md)** - Gap analysis and recommendations
- **[README.md](api_inventory/README.md)** - How to use the inventory

---

## Quick Navigation

### I want to...

**Build a framework wrapper:**
1. Start with `documentation/01-prerequisites-and-setup.md`
2. Read `documentation/02-api-overview.md` for architecture
3. Use `api_inventory/classes_and_methods.md` as complete reference
4. Check `api_inventory/common_patterns.md` for implementation patterns

**Find a specific class/method:**
1. Use `api_inventory/class_index.md` for quick lookup
2. Check `api_inventory/classes_and_methods.md` for details

**Understand workflows:**
1. Read relevant `documentation/0X-*.md` guide
2. Check `api_inventory/common_patterns.md` for code examples

**Assess what's possible:**
1. Skim `api_inventory/class_index.md` for categories
2. Review `api_inventory/coverage_analysis.md` for completeness

---

## Key Differences from claude-guides/

| `claude-guides/` | `dataiku_framework_reference/` |
|------------------|--------------------------------|
| Usage-focused workflow guides | Complete API reference |
| How to accomplish tasks | What exists in the API |
| Best practices and gotchas | Technical specifications |
| Quick project building | Framework development |
| ~6,600 lines | ~10,000+ lines |

**Use both together:**
- `claude-guides/` - For building Dataiku projects quickly
- `dataiku_framework_reference/` - For building wrappers/frameworks

---

## Documentation Statistics

**API Inventory:**
- 150+ classes documented
- 1,000+ methods cataloged
- 7 client types covered
- 15 functional categories
- 50+ workflow examples

**Reference Guides:**
- 10 comprehensive sections
- Complete method signatures
- Parameter documentation
- Return type specifications
- Example code throughout

---

## Project Structure Recommendation

When building with this reference:

```
your_project/
├── config/
│   ├── APIKEY.txt                    # Your API key (never commit!)
│   └── config.json                   # Environment config
├── dataiku_framework_reference/      # This documentation (read-only)
│   ├── documentation/
│   ├── api_inventory/
│   └── README.md
├── claude-guides/                    # Usage guides (read-only)
├── your_framework/                   # Your wrapper code
│   ├── __init__.py
│   ├── client.py
│   ├── projects.py
│   └── ...
├── tests/                            # Your tests
├── examples/                         # Usage examples
└── {PROJECT_KEY}_script.py          # Project-specific scripts
```

---

## Getting Started

### For Framework Development:

1. **Read prerequisites:**
   ```bash
   cat documentation/01-prerequisites-and-setup.md
   ```

2. **Understand API architecture:**
   ```bash
   cat documentation/02-api-overview.md
   ```

3. **Explore what's available:**
   ```bash
   cat api_inventory/class_index.md
   ```

4. **Dive into specific areas:**
   ```bash
   cat documentation/04-project-operations.md  # For project wrappers
   cat documentation/05-dataset-operations.md  # For dataset wrappers
   # etc.
   ```

### For Quick Reference:

1. **Find a class:**
   ```bash
   grep "class DSSDataset" api_inventory/classes_and_methods.md -A 20
   ```

2. **Find a method:**
   ```bash
   grep "def build" api_inventory/classes_and_methods.md
   ```

3. **Find patterns:**
   ```bash
   cat api_inventory/common_patterns.md | grep -A 10 "Dataset Processing"
   ```

---

## Contributing to This Reference

When updating:
1. Keep `api_inventory/` as pure technical reference
2. Put workflow guidance in `documentation/`
3. Include method signatures and return types
4. Add examples for complex patterns
5. Update coverage analysis when finding gaps

---

## Version Info

- **API Version:** 14.1.3+
- **Last Updated:** 2025-11-21
- **Python:** 3.7+
- **Total Lines:** ~10,000+

---

## Related Resources

- **Usage Guides:** `../claude-guides/` (for building projects)
- **Official Docs:** https://doc.dataiku.com/
- **API Reference:** https://developer.dataiku.com/latest/api-reference/python/
- **GitHub:** https://github.com/dataiku/dataiku-api-client-python

---

**Ready to build? Start with `documentation/01-prerequisites-and-setup.md`**
