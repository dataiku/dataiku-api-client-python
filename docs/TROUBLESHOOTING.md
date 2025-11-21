# Troubleshooting Guide

Common errors, solutions, and debugging tips. See [`../claude-guides/08-common-gotchas.md`](../claude-guides/08-common-gotchas.md) for comprehensive details.

---

## Table of Contents

1. [Critical Gotchas](#critical-gotchas)
2. [Authentication Errors](#authentication-errors)
3. [Connection Errors](#connection-errors)
4. [Dataset Errors](#dataset-errors)
5. [Recipe Errors](#recipe-errors)
6. [Scenario Errors](#scenario-errors)
7. [Common Mistakes](#common-mistakes)
8. [Debugging Checklist](#debugging-checklist)

---

## Critical Gotchas

### 1. Scope Hierarchy (MUST Follow)

**Error:** `AttributeError: 'DSSClient' object has no attribute 'get_dataset'`

**Cause:** Skipped scope hierarchy

**Fix:**
```python
# ❌ WRONG
dataset = client.get_dataset("my_dataset")

# ✓ CORRECT
project = client.get_project("MY_PROJECT")
dataset = project.get_dataset("my_dataset")
```

### 2. Settings Not Saved

**Problem:** Changes disappear

**Cause:** Forgot `.save()`

**Fix:**
```python
# ❌ WRONG
settings = dataset.get_settings()
settings.settings['description'] = "New"
# Changes lost!

# ✓ CORRECT
settings = dataset.get_settings()
settings.settings['description'] = "New"
settings.save()  # CRITICAL!
```

### 3. Uppercase Naming (Snowflake)

**Problem:** SQL errors with Snowflake

**Cause:** Lowercase table/column names

**Fix:**
```python
# ⚠️ May cause Snowflake errors
dataset_name = "raw_customers"
column_name = "customer_id"

# ✓ RECOMMENDED for Snowflake
dataset_name = "RAW_CUSTOMERS"
column_name = "CUSTOMER_ID"
```

### 4. Scenario Two-Step

**Error:** `AttributeError: 'DSSScenarioTriggerFireHandle' has no attribute 'get_outcome'`

**Cause:** Skipped second step

**Fix:**
```python
# ❌ WRONG
trigger_fire = scenario.run()
outcome = trigger_fire.get_outcome()  # Fails!

# ✓ CORRECT
trigger_fire = scenario.run()
scenario_run = trigger_fire.wait_for_scenario_run()
outcome = scenario_run.get_outcome()
```

---

## Authentication Errors

### 401 Unauthorized

**Cause:** Invalid API key

**Solutions:**
1. Verify API key: `echo $DATAIKU_API_KEY`
2. Regenerate key in DSS
3. Check key is not expired

### 403 Forbidden

**Cause:** Insufficient permissions

**Solutions:**
1. Check user permissions in DSS
2. Use admin key if needed
3. Verify project access

---

## Connection Errors

### Connection Refused / Timeout

**Causes:**
- DSS not running
- Wrong host/port
- Firewall blocking

**Solutions:**
```bash
# Test connectivity
curl -I $DATAIKU_HOST

# Check firewall
ping dss.company.com
```

---

## Dataset Errors

### "Dataset is already being built"

**Cause:** Another job is building it

**Solution:**
```python
import time

def wait_for_available(dataset, max_wait=300):
    start = time.time()
    while time.time() - start < max_wait:
        try:
            return dataset.build(wait=False)
        except Exception as e:
            if "already being built" in str(e):
                time.sleep(10)
            else:
                raise
    raise TimeoutError("Dataset still busy")
```

### "Source dataset not ready"

**Cause:** Input datasets not built

**Solution:** Build dependencies first:
```python
# Build sources first
source1.build(wait=True)
source2.build(wait=True)

# Then build target
target.build(wait=True)
```

---

## Recipe Errors

### "Cannot compute schema updates"

**Cause:** Recipe configuration invalid

**Solution:**
```python
# Validate recipe first
def validate_recipe(recipe):
    definition = recipe.get_definition()
    
    # Check inputs exist
    for input_list in definition.get('inputs', {}).values():
        for inp in input_list:
            try:
                project.get_dataset(inp['ref'])
            except:
                print(f"❌ Input {inp['ref']} not found")
                return False
    return True

if validate_recipe(recipe):
    recipe.compute_schema_updates().apply()
```

---

## Scenario Errors

### "Trigger fire cancelled"

**Cause:** Scenario running too frequently

**Solution:**
```python
import time

trigger_fire = scenario.run()
try:
    scenario_run = trigger_fire.wait_for_scenario_run()
except Exception as e:
    if "cancelled" in str(e).lower():
        time.sleep(60)  # Wait before retry
        trigger_fire = scenario.run()
        scenario_run = trigger_fire.wait_for_scenario_run()
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip scope hierarchy | Go through project |
| Forget `.save()` | Always save settings |
| Lowercase with Snowflake | Use UPPERCASE |
| Assume sync operations | Check for async, wait for completion |
| Single scenario step | Two steps: `run()` → `wait_for_scenario_run()` |
| Commit API keys | Add to `.gitignore` |
| Variables as numbers | Convert: `int(variables["batch_size"])` |

---

## Debugging Checklist

When something fails:

**Connection:**
- [ ] Can ping the DSS host?
- [ ] Is DSS running?
- [ ] Is API key valid?

**Permissions:**
- [ ] Can list projects?
- [ ] Can access specific project?
- [ ] User has required permissions?

**Resources:**
- [ ] Dataset/recipe/scenario exists?
- [ ] In correct project?
- [ ] Names spelled correctly?

**Dependencies:**
- [ ] Input datasets built?
- [ ] Schemas up to date?
- [ ] Connections configured?

**State:**
- [ ] Job already running?
- [ ] Scenario active?
- [ ] Conflicting operations?

**Configuration:**
- [ ] Called `.save()` on settings?
- [ ] Updated schemas after recipe changes?
- [ ] Variable types correct?

---

## Getting Help

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Full Guide:**
- [`../claude-guides/08-common-gotchas.md`](../claude-guides/08-common-gotchas.md) - Comprehensive gotchas
- [`../claude-guides/99-quick-reference.md`](../claude-guides/99-quick-reference.md) - Quick patterns

**API Reference:**
- [`../dataiku_framework_reference/`](../dataiku_framework_reference/) - Complete API docs

---

**Back to:** [`../CLAUDE.md`](../CLAUDE.md)
