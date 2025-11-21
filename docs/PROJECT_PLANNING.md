# Project Planning Guide

**CRITICAL: Plan before coding to avoid getting lost!**

This guide is extracted from [`../claude-guides/00-project-planning-guide.md`](../claude-guides/00-project-planning-guide.md) - see that file for complete details.

---

## Why Planning Matters

Without a plan, you will:
- ❌ Forget what datasets/recipes were created
- ❌ Create circular dependencies
- ❌ Use inconsistent naming
- ❌ Miss critical steps
- ❌ Have to backtrack and refactor

With a plan, you get:
- ✓ Clear roadmap
- ✓ Consistent naming
- ✓ Proper dependency order
- ✓ Complete functionality
- ✓ Easy progress tracking

---

## Quick Planning Workflow

### 1. Understand Requirements

```markdown
## Project Goal
[What is this project doing?]

## Input Sources
- [List data sources]

## Transformations
- [What cleaning/processing?]

## Outputs
- [Final deliverables]

## Automation
- [Schedule? Triggers?]
```

### 2. Draw Flow Diagram

```
[Source DB] → [raw_customers] → [clean_customers] ┐
                                                   ├→ [customer_orders] → [final_output]
[Orders API] → [raw_orders] → [clean_orders] ─────┘
```

### 3. Establish Naming Convention

**UPPERCASE for Snowflake (CRITICAL!):**

```python
PROJECT_KEY = "CUSTOMER_ANALYTICS"
dataset = "RAW_CUSTOMERS"  # UPPERCASE
column = "CUSTOMER_ID"     # UPPERCASE
recipe = "clean_customers"  # lowercase (optional)
```

**Why:** Snowflake REQUIRES uppercase table/column names

See: [`NAMING_CONVENTIONS.md`](NAMING_CONVENTIONS.md)

### 4. Break Into Phases

```markdown
## Phase 1: Project Setup
- [ ] Create project
- [ ] Set variables

## Phase 2: Source Datasets
- [ ] Create RAW_CUSTOMERS
- [ ] Create RAW_ORDERS
- [ ] Test connectivity

## Phase 3: Cleaning
- [ ] Create clean_customers recipe
- [ ] Create clean_orders recipe
- [ ] Test transformations

## Phase 4: Integration
- [ ] Create join recipe
- [ ] Test join results

## Phase 5: Automation
- [ ] Create scenario
- [ ] Test end-to-end
```

---

## Implementation Pattern

**Work phase-by-phase. Test after each phase.**

```python
# Phase 1: Create project
project = client.create_project("CUSTOMER_ANALYTICS", ...)
print("✓ Phase 1 complete")

# Phase 2: Create source datasets
raw_customers = project.create_dataset("RAW_CUSTOMERS", ...)
raw_customers.build(wait=True)
print("✓ Phase 2 complete")

# Phase 3: Create recipes
# ... (continue phase by phase)
```

**Checkpoint after each phase!**

---

## Complete Planning Template

See [`../claude-guides/00-project-planning-guide.md`](../claude-guides/00-project-planning-guide.md) for:
- Complete planning template
- Detailed examples
- Visual flow planning
- Checkpoint patterns
- Common mistakes to avoid

---

## Example Plan

```markdown
# Project Plan: Customer Analytics

## Phase 1: Setup
- [ ] Project: CUSTOMER_ANALYTICS
- [ ] Variables: db_connection, email

## Phase 2: Ingestion (Datasets)
- [ ] RAW_CUSTOMERS (Snowflake: ANALYTICS.RAW.CUSTOMERS)
- [ ] RAW_ORDERS (Snowflake: ANALYTICS.RAW.ORDERS)

## Phase 3: Cleaning (Recipes + Datasets)
- [ ] clean_customers recipe → CLEAN_CUSTOMERS
- [ ] clean_orders recipe → CLEAN_ORDERS

## Phase 4: Integration (Recipe + Dataset)
- [ ] join_customer_orders → CUSTOMER_ORDERS

## Phase 5: Aggregation (Recipe + Dataset)
- [ ] aggregate_summary → CUSTOMER_SUMMARY

## Phase 6: Automation (Scenario)
- [ ] daily_refresh scenario (runs at 2 AM)
```

---

## Next Steps

1. **Create your plan** using the template
2. **Get approval** from stakeholders
3. **Start implementation** phase by phase
4. **Use patterns** from [`PATTERNS.md`](PATTERNS.md)
5. **Reference guides** in [`WORKFLOW_GUIDES.md`](WORKFLOW_GUIDES.md)

---

**Full detailed guide:** [`../claude-guides/00-project-planning-guide.md`](../claude-guides/00-project-planning-guide.md)
