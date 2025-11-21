# Naming Conventions

Quick reference for naming conventions. See [`../claude-guides/00-project-planning-guide.md#naming-conventions-guide`](../claude-guides/00-project-planning-guide.md#naming-conventions-guide) for complete details.

---

## Why Naming Matters

**Critical for Snowflake:** Snowflake REQUIRES uppercase table/column names

**Other reasons:**
- SQL databases are case-sensitive
- Prevents confusing errors
- Maintains consistency

---

## Recommended Conventions

### Project Keys: UPPERCASE

```python
# ✓ RECOMMENDED
"CUSTOMER_ANALYTICS"
"SALES_REPORTING"
"DATA_QUALITY"

# ⚠️ Works but may cause Snowflake issues
"customer_analytics"
```

### Dataset Names

**With Snowflake: UPPERCASE**
```python
"RAW_CUSTOMERS"
"CLEAN_ORDERS"
"CUSTOMER_SUMMARY"
```

**Without Snowflake: lowercase_with_underscores**
```python
"raw_customers"
"clean_orders"
"customer_summary"
```

### Column Names (CRITICAL for Snowflake!)

```python
# ✓ UPPERCASE for Snowflake
schema = {
    "columns": [
        {"name": "CUSTOMER_ID", "type": "bigint"},
        {"name": "ORDER_DATE", "type": "date"},
        {"name": "TOTAL_AMOUNT", "type": "double"}
    ]
}

# ❌ May not work with Snowflake
{"name": "customer_id", "type": "bigint"}
```

### Recipe Names: descriptive_action

```python
# ✓ GOOD
"clean_customers"
"join_customer_orders"
"aggregate_by_region"

# ❌ BAD
"recipe1"           # Not descriptive
"customer"          # Unclear
"transformation"    # Too vague
```

### File Names: {PROJECT_KEY}_filename.py

```python
# ✓ RECOMMENDED
"customer_analytics_create_project.py"
"customer_analytics_build_pipeline.py"
"sales_reporting_daily_refresh.py"

# ❌ BAD
"create_project.py"      # Which project?
"pipeline.py"            # Not descriptive
"my_script_final_v2.py"  # Unclear
```

**Why:** Groups files by project alphabetically

---

## Prefixes for Organization

```python
# Raw data layer
"RAW_CUSTOMERS"
"RAW_ORDERS"
"RAW_PRODUCTS"

# Cleaned data layer
"CLEAN_CUSTOMERS"
"CLEAN_ORDERS"

# Intermediate
"INT_CUSTOMER_ORDERS"

# Final outputs
"FINAL_CUSTOMER_SUMMARY"
```

---

## Examples

### Good Example (Snowflake Project)

```python
# Project
PROJECT_KEY = "CUSTOMER_ANALYTICS"

# Datasets
RAW_CUSTOMERS = "RAW_CUSTOMERS"
CLEAN_CUSTOMERS = "CLEAN_CUSTOMERS"
CUSTOMER_SUMMARY = "CUSTOMER_SUMMARY"

# Columns in schema
{"name": "CUSTOMER_ID", "type": "bigint"}
{"name": "TOTAL_ORDERS", "type": "int"}

# Recipes
clean_recipe = "clean_customers"
join_recipe = "join_customer_orders"

# Files
"customer_analytics_create_project.py"
"customer_analytics_run_pipeline.py"
```

### Bad Example (Inconsistent)

```python
# ❌ Inconsistent naming
PROJECT_KEY = "customer_analytics"  # Lowercase
RAW_DATA = "raw_customers"          # Will cause Snowflake errors
cleaned = "Clean_Customers"         # Mixed case
final = "customerSummary"           # Camel case

# Files
"create.py"                         # Not descriptive
"Script1.py"                        # Not grouped
```

---

## Quick Reference

| Item | Convention | Example |
|------|------------|---------|
| **Project Key** | UPPERCASE | `CUSTOMER_ANALYTICS` |
| **Dataset (Snowflake)** | UPPERCASE | `RAW_CUSTOMERS` |
| **Dataset (other)** | lowercase | `raw_customers` |
| **Column (Snowflake)** | UPPERCASE | `CUSTOMER_ID` |
| **Recipe** | lowercase | `clean_customers` |
| **Scenario** | lowercase | `daily_refresh` |
| **File** | {PROJECT_KEY}_name.py | `customer_analytics_setup.py` |

---

**Full Guide:** [`../claude-guides/00-project-planning-guide.md`](../claude-guides/00-project-planning-guide.md)

**Back to:** [`../CLAUDE.md`](../CLAUDE.md)
