# 00 - Project Planning Guide

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** How to plan and structure Dataiku projects to avoid getting lost or confused

---

## WHY PLANNING MATTERS FOR CLAUDE CODE

**CRITICAL:** Claude Code sessions can easily get confused or lost without a clear plan. Always create a detailed project plan BEFORE writing any code.

### Common Problems Without Planning:
- ❌ Forgetting what datasets/recipes were already created
- ❌ Creating circular dependencies
- ❌ Inconsistent naming conventions
- ❌ Missing critical steps
- ❌ Having to backtrack and refactor
- ❌ Losing track of the flow structure

### Benefits of Planning:
- ✓ Clear roadmap to follow
- ✓ Consistent naming
- ✓ Proper dependency order
- ✓ Complete functionality
- ✓ Easy to review progress
- ✓ Can resume if interrupted

---

## PLANNING WORKFLOW

### Step 1: Understand Requirements

Before any code, clarify:

```markdown
## Project Goal
What is this project supposed to do?

## Input Data Sources
- What data sources? (databases, files, APIs, etc.)
- Connection details needed?
- Schema/format of inputs?

## Transformations Needed
- Data cleaning steps?
- Joins required?
- Aggregations?
- Business logic?

## Output Requirements
- Final outputs needed?
- Format/destination?
- Update frequency?

## Automation Needs
- Should it run on schedule?
- Triggers needed?
- Notifications?
```

### Step 2: Create Flow Diagram

Draw the data flow on paper or in markdown:

```
[Source DB] → [raw_customers] → [clean_customers] ┐
                                                    ├→ [customer_orders] → [customer_summary]
[Orders API] → [raw_orders] → [clean_orders] ──────┘
```

### Step 3: Define Naming Convention

**CRITICAL:** Establish naming rules upfront!

#### Recommended Convention:

```python
# Project key: UPPERCASE with underscores
PROJECT_KEY = "CUSTOMER_ANALYTICS"

# Datasets: lowercase_with_underscores
"raw_customers"
"clean_customers"
"customer_orders"
"customer_summary"

# Recipes: action_description
"clean_customers"
"join_customer_orders"
"aggregate_summary"

# Scenarios: purpose_frequency (if applicable)
"daily_refresh"
"weekly_report"
```

**WHY UPPERCASE FOR SOME ELEMENTS:**
- Snowflake datasets REQUIRE uppercase table/column names
- Many SQL databases are case-sensitive
- Mixing cases causes confusing errors
- Consistency prevents mistakes

**Recommendation:** Use UPPERCASE for:
- Project keys
- Dataset names when using Snowflake
- Column names in schemas
- Any SQL identifiers

Use lowercase for:
- Python code
- Recipe names (optional)
- Scenario names (optional)

### Step 4: Create Detailed Plan Document

**THIS IS CRITICAL - Create this BEFORE coding!**

```markdown
# Project Plan: Customer Analytics

## Project Setup
- [ ] Project key: CUSTOMER_ANALYTICS
- [ ] Owner: data_team
- [ ] Variables needed:
  - db_connection: "snowflake_prod"
  - batch_size: "1000"
  - email_recipient: "team@company.com"

## Phase 1: Data Ingestion

### Dataset: RAW_CUSTOMERS
- Type: Snowflake
- Connection: snowflake_prod
- Table: ANALYTICS.RAW.CUSTOMERS
- Schema: ID (bigint), NAME (string), EMAIL (string), CREATED_AT (timestamp)

### Dataset: RAW_ORDERS
- Type: Snowflake
- Connection: snowflake_prod
- Table: ANALYTICS.RAW.ORDERS
- Schema: ORDER_ID (bigint), CUSTOMER_ID (bigint), AMOUNT (double), ORDER_DATE (date)

## Phase 2: Data Cleaning

### Recipe: clean_customers (Python)
- Input: RAW_CUSTOMERS
- Output: CLEAN_CUSTOMERS
- Logic:
  - Remove null IDs
  - Validate email format
  - Deduplicate by ID
  - Standardize name format

### Recipe: clean_orders (Python)
- Input: RAW_ORDERS
- Output: CLEAN_ORDERS
- Logic:
  - Remove null ORDER_IDs
  - Validate AMOUNT > 0
  - Filter out future dates

## Phase 3: Data Integration

### Recipe: join_customer_orders (Join)
- Inputs: CLEAN_CUSTOMERS, CLEAN_ORDERS
- Output: CUSTOMER_ORDERS
- Join type: LEFT JOIN
- Join key: CLEAN_CUSTOMERS.ID = CLEAN_ORDERS.CUSTOMER_ID

## Phase 4: Aggregation

### Recipe: aggregate_summary (Group)
- Input: CUSTOMER_ORDERS
- Output: CUSTOMER_SUMMARY
- Group by: CUSTOMER_ID
- Aggregations:
  - COUNT(ORDER_ID) as TOTAL_ORDERS
  - SUM(AMOUNT) as TOTAL_SPENT
  - AVG(AMOUNT) as AVG_ORDER_VALUE
  - MAX(ORDER_DATE) as LAST_ORDER_DATE

## Phase 5: Automation

### Scenario: daily_refresh
- Trigger: Daily at 2 AM UTC
- Steps:
  1. Build RAW_CUSTOMERS
  2. Build RAW_ORDERS
  3. Build CUSTOMER_SUMMARY (recursive)
  4. Validate: Check row count > 0
  5. Notify: Email on success/failure

## Testing Plan
- [ ] Verify each dataset builds successfully
- [ ] Check schema matches expectations
- [ ] Validate data quality (no nulls in key columns)
- [ ] Test scenario end-to-end
- [ ] Verify notifications work

## Rollback Plan
- [ ] Keep exports of each phase
- [ ] Document any manual steps
- [ ] Note connection dependencies
```

---

## EXECUTION WORKFLOW

### Phase-by-Phase Implementation

**DO NOT try to build everything at once!** Follow phases:

#### Phase 1: Project Setup

```python
# 1. Create plan document (markdown file)
# 2. Review plan with user
# 3. Get approval to proceed

# 4. Create project
from dataikuapi import DSSClient
import os

client = DSSClient(
    os.getenv('DATAIKU_HOST'),
    os.getenv('DATAIKU_API_KEY')
)

project = client.create_project(
    project_key="CUSTOMER_ANALYTICS",
    name="Customer Analytics",
    owner="data_team",
    description="Customer order analytics pipeline"
)

# 5. Set variables
project.set_variables({
    "db_connection": "snowflake_prod",
    "batch_size": "1000",
    "email_recipient": "team@company.com"
})

print("✓ Phase 1 complete: Project created")
```

#### Phase 2: Create Datasets

```python
# Create datasets in dependency order

# 1. Source datasets first
raw_customers = project.create_dataset(
    "RAW_CUSTOMERS",
    "Snowflake",
    params={
        "connection": "snowflake_prod",
        "mode": "table",
        "schema": "RAW",
        "table": "CUSTOMERS"
    }
)

raw_orders = project.create_dataset(
    "RAW_ORDERS",
    "Snowflake",
    params={
        "connection": "snowflake_prod",
        "mode": "table",
        "schema": "RAW",
        "table": "ORDERS"
    }
)

# 2. Test source datasets
raw_customers.build(wait=True)
raw_orders.build(wait=True)

print("✓ Phase 2 complete: Source datasets accessible")
```

#### Phase 3: Create Intermediate Datasets

```python
# Create output datasets (empty, will be filled by recipes)

clean_customers = project.create_dataset(
    "CLEAN_CUSTOMERS",
    "Snowflake",
    params={
        "connection": "snowflake_prod",
        "mode": "table",
        "schema": "STAGING",
        "table": "CLEAN_CUSTOMERS"
    }
)

clean_orders = project.create_dataset(
    "CLEAN_ORDERS",
    "Snowflake",
    params={
        "connection": "snowflake_prod",
        "mode": "table",
        "schema": "STAGING",
        "table": "CLEAN_ORDERS"
    }
)

print("✓ Phase 3 complete: Intermediate datasets created")
```

#### Phase 4: Create Recipes

```python
# Create recipes in dependency order

# Recipe 1: clean_customers
recipe1 = project.new_recipe(
    type="python",
    name="clean_customers"
).with_input("RAW_CUSTOMERS").with_output("CLEAN_CUSTOMERS").create()

# Set code
definition = recipe1.get_definition_and_payload()
definition['payload']['script'] = """
import dataiku
import pandas as pd

# Read raw data
df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()

# Cleaning logic
df = df.dropna(subset=['ID'])
df = df[df['EMAIL'].str.contains('@', na=False)]
df = df.drop_duplicates(subset=['ID'])

# Write clean data
dataiku.Dataset("CLEAN_CUSTOMERS").write_with_schema(df)
"""
recipe1.set_definition_and_payload(definition)

# Update schema
recipe1.compute_schema_updates().apply()

# Test recipe
job = recipe1.run(wait=True)
print(f"✓ Recipe 1 complete: {job.id}")

# Repeat for other recipes...
```

#### Phase 5: Create Automation

```python
# Create scenario
scenario = project.create_scenario(
    scenario_name="daily_refresh",
    type="step_based",
    definition={}
)

settings = scenario.get_settings()

# Configure steps (see 06-scenario-automation.md for details)
settings.settings['params'] = {
    "steps": [
        # Build sources
        {
            "id": "build_sources",
            "type": "build_flowitem",
            "name": "Build Source Data",
            "params": {
                "builds": [
                    {"type": "DATASET", "itemId": "RAW_CUSTOMERS"},
                    {"type": "DATASET", "itemId": "RAW_ORDERS"}
                ]
            }
        },
        # Build final output recursively
        {
            "id": "build_final",
            "type": "build_flowitem",
            "name": "Build Final Output",
            "params": {
                "builds": [{
                    "type": "RECURSIVE",
                    "itemId": "CUSTOMER_SUMMARY"
                }]
            },
            "runConditionEnabled": True,
            "runConditionExpression": "outcome['build_sources'] == 'SUCCESS'"
        }
    ]
}

settings.save()
print("✓ Phase 5 complete: Automation configured")
```

#### Phase 6: Testing

```python
# Test end-to-end
print("Testing scenario...")
scenario_run = scenario.run_and_wait()

if scenario_run.get_outcome() == 'SUCCESS':
    print("✓ Phase 6 complete: End-to-end test passed")
else:
    print("❌ Test failed, review logs")
    details = scenario_run.get_details()
    for step in details.get('stepRuns', []):
        print(f"  {step['stepName']}: {step.get('result', {}).get('outcome')}")
```

---

## CHECKPOINT PATTERN

After each phase, create a checkpoint:

```python
def create_checkpoint(phase_name, status):
    """Save progress checkpoint"""
    checkpoint = {
        "phase": phase_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "objects_created": []  # List what was created
    }

    # Save to file or project metadata
    with open(f"checkpoint_{phase_name}.json", "w") as f:
        json.dump(checkpoint, f, indent=2)

    print(f"✓ Checkpoint saved: {phase_name}")

# After each phase
create_checkpoint("01_project_setup", "complete")
create_checkpoint("02_source_datasets", "complete")
# etc.
```

---

## NAMING CONVENTIONS GUIDE

### Why Naming Matters

**Inconsistent naming causes:**
- SQL errors (case sensitivity)
- Cannot find datasets/recipes
- Confusion in large projects
- Merge conflicts
- Debugging nightmares

### Recommended Conventions

#### Project Keys
```python
# ✓ GOOD
"CUSTOMER_ANALYTICS"
"SALES_REPORTING"
"DATA_QUALITY"

# ❌ BAD
"customer_analytics"  # Inconsistent
"Sales-Reporting"     # Uses dash
"DataQuality"         # Camel case
```

#### Dataset Names (Snowflake)
```python
# ✓ GOOD - UPPERCASE for Snowflake
"RAW_CUSTOMERS"
"CLEAN_ORDERS"
"CUSTOMER_SUMMARY"

# ❌ BAD - Will cause issues
"raw_customers"  # Snowflake may reject
"Raw_Customers"  # Inconsistent
"rawCustomers"   # Camel case
```

#### Dataset Names (Non-Snowflake)
```python
# ✓ GOOD - lowercase_with_underscores
"raw_customers"
"clean_orders"
"customer_summary"

# ❌ BAD
"rawCustomers"   # Camel case
"raw-customers"  # Dashes
"Raw_Customers"  # Mixed case
```

#### Recipe Names
```python
# ✓ GOOD - descriptive action
"clean_customers"
"join_customer_orders"
"aggregate_by_region"

# ❌ BAD
"recipe1"        # Not descriptive
"customer"       # Unclear
"transformation" # Too vague
```

#### Column Names (IMPORTANT for Snowflake)
```python
# ✓ GOOD - UPPERCASE for Snowflake
schema = {
    "columns": [
        {"name": "CUSTOMER_ID", "type": "bigint"},
        {"name": "ORDER_DATE", "type": "date"},
        {"name": "TOTAL_AMOUNT", "type": "double"}
    ]
}

# ❌ BAD - Snowflake issues
{"name": "customer_id", "type": "bigint"}  # May not match
{"name": "customerId", "type": "bigint"}    # Camel case
```

### Prefixes for Organization

Use prefixes to group related items:

```python
# Raw data layer
"RAW_CUSTOMERS"
"RAW_ORDERS"
"RAW_PRODUCTS"

# Cleaned data layer
"CLEAN_CUSTOMERS"
"CLEAN_ORDERS"
"CLEAN_PRODUCTS"

# Intermediate
"INT_CUSTOMER_ORDERS"
"INT_PRODUCT_SALES"

# Final outputs
"FINAL_CUSTOMER_SUMMARY"
"FINAL_SALES_REPORT"
```

---

## VISUAL FLOW PLANNING

### Create Flow Diagram First

Before coding, draw the flow:

```
┌─────────────┐     ┌──────────────┐
│RAW_CUSTOMERS│     │ RAW_ORDERS   │
└──────┬──────┘     └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│clean_customers│    │ clean_orders │
│   (Python)    │    │   (Python)   │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│CLEAN_CUSTOMER│    │ CLEAN_ORDERS │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └────────┬──────────┘
                │
                ▼
       ┌─────────────────┐
       │join_customer_    │
       │    orders        │
       │   (Join)         │
       └────────┬─────────┘
                │
                ▼
       ┌─────────────────┐
       │CUSTOMER_ORDERS   │
       └────────┬─────────┘
                │
                ▼
       ┌─────────────────┐
       │aggregate_summary │
       │    (Group)       │
       └────────┬─────────┘
                │
                ▼
       ┌─────────────────┐
       │CUSTOMER_SUMMARY  │
       └─────────────────┘
```

### Dependencies Matter

**Build in this order:**
1. Source datasets (no dependencies)
2. First-level transformations
3. Joins that combine cleaned data
4. Aggregations on joined data
5. Final outputs

**NEVER create circular dependencies:**
```
❌ BAD: Dataset A → Recipe X → Dataset B → Recipe Y → Dataset A
✓ GOOD: Linear or tree-structured flow
```

---

## PROGRESS TRACKING

### Use TODO List

```python
"""
PROJECT: Customer Analytics

PLAN:
☐ Phase 1: Project setup
☐ Phase 2: Source datasets
☐ Phase 3: Cleaning recipes
☐ Phase 4: Join recipe
☐ Phase 5: Aggregation recipe
☐ Phase 6: Scenario automation
☐ Phase 7: Testing

CURRENT PHASE: Phase 2 - Creating source datasets

COMPLETED:
✓ Phase 1: Project created
  - Created project CUSTOMER_ANALYTICS
  - Set project variables

IN PROGRESS:
→ Phase 2: Creating RAW_CUSTOMERS dataset

NEXT:
- Create RAW_ORDERS dataset
- Test source data access
"""
```

### Document As You Go

```python
# Add comments explaining decisions
project = client.create_project(
    "CUSTOMER_ANALYTICS",
    "Customer Analytics",
    "data_team"
)
print("✓ Created project CUSTOMER_ANALYTICS")

# Reason: Using Snowflake, so UPPERCASE required
raw_customers = project.create_dataset(
    "RAW_CUSTOMERS",  # UPPERCASE for Snowflake compatibility
    "Snowflake",
    params={"connection": "snowflake_prod", "table": "CUSTOMERS"}
)
print("✓ Created dataset RAW_CUSTOMERS")
```

---

## COMMON PLANNING MISTAKES

### 1. Starting Without a Plan

```
❌ "Let me just start coding and figure it out..."
✓ "Let me write a complete plan first, then code phase by phase"
```

### 2. Inconsistent Naming

```
❌ "raw_customers", "CleanOrders", "customer-summary"
✓ "RAW_CUSTOMERS", "CLEAN_ORDERS", "CUSTOMER_SUMMARY"
```

### 3. Building Everything at Once

```
❌ Create all datasets → Create all recipes → Hope it works
✓ Create dataset → Test → Create recipe → Test → Repeat
```

### 4. Ignoring Dependencies

```
❌ Creating recipes before output datasets exist
✓ Create datasets first, then recipes that use them
```

### 5. Not Testing Incrementally

```
❌ Build entire pipeline, test at end
✓ Test after each phase
```

---

## PLANNING TEMPLATE

Use this template for every project:

```markdown
# Project Plan: [PROJECT_NAME]

## 1. Requirements
- Goal: [What is this project doing?]
- Inputs: [What data sources?]
- Outputs: [What are the final deliverables?]
- Schedule: [How often does it run?]

## 2. Naming Convention
- Project key: [UPPERCASE_WITH_UNDERSCORES]
- Dataset pattern: [chosen_pattern]
- Recipe pattern: [chosen_pattern]
- Why: [Snowflake / other requirements]

## 3. Flow Diagram
[ASCII or description of data flow]

## 4. Phase Breakdown

### Phase 1: Project Setup
- [ ] Task 1
- [ ] Task 2

### Phase 2: [Next Phase]
- [ ] Task 1
- [ ] Task 2

[Continue for all phases]

## 5. Testing Plan
- [ ] Test item 1
- [ ] Test item 2

## 6. Rollback Plan
- [ ] Backup strategy
- [ ] Recovery steps
```

---

## WORKING WITH CLAUDE CODE

### Before Starting

1. **Ask clarifying questions** about requirements
2. **Create detailed plan** and get approval
3. **Establish naming conventions** upfront
4. **Draw flow diagram** or describe flow clearly

### During Implementation

1. **Work phase by phase** - Don't jump ahead
2. **Test after each phase** - Verify before continuing
3. **Document progress** - Update plan as you go
4. **Save checkpoints** - So you can resume if interrupted

### If Getting Confused

1. **Stop coding** immediately
2. **Review the plan** - Where are you in the plan?
3. **List what's been created** - What exists already?
4. **Identify next step** - What's the next phase?
5. **Resume systematically** - Follow the plan

---

## EXAMPLE: Complete Planning Session

### User Request
"I need a pipeline that pulls customer data from Snowflake, cleans it, joins with orders, and creates a summary table."

### Planning Response

```markdown
I'll create a detailed plan for your customer analytics pipeline.

## PROPOSED PLAN: Customer Analytics Pipeline

### Requirements Summary
- **Input 1**: Snowflake table ANALYTICS.RAW.CUSTOMERS
- **Input 2**: Snowflake table ANALYTICS.RAW.ORDERS
- **Output**: Aggregated customer summary table
- **Connection**: Snowflake (requires UPPERCASE naming)

### Naming Convention
Since you're using Snowflake, I'll use UPPERCASE for all dataset and column names.

- Project: CUSTOMER_ANALYTICS
- Datasets: RAW_CUSTOMERS, CLEAN_CUSTOMERS, etc.
- Recipes: clean_customers, join_customer_orders, etc.

### Data Flow
```
RAW_CUSTOMERS → clean_customers → CLEAN_CUSTOMERS ┐
                                                   ├→ join → CUSTOMER_ORDERS → aggregate → CUSTOMER_SUMMARY
RAW_ORDERS → clean_orders → CLEAN_ORDERS ────────┘
```

### Implementation Phases

**Phase 1**: Project Setup
- Create project CUSTOMER_ANALYTICS
- Set variables (connection name, etc.)

**Phase 2**: Source Datasets
- Create RAW_CUSTOMERS dataset (Snowflake)
- Create RAW_ORDERS dataset (Snowflake)
- Test connectivity

**Phase 3**: Cleaning Layer
- Create CLEAN_CUSTOMERS dataset
- Create clean_customers recipe (Python)
- Create CLEAN_ORDERS dataset
- Create clean_orders recipe (Python)
- Test cleaning logic

**Phase 4**: Integration Layer
- Create CUSTOMER_ORDERS dataset
- Create join_customer_orders recipe (Join)
- Test join results

**Phase 5**: Aggregation Layer
- Create CUSTOMER_SUMMARY dataset
- Create aggregate_summary recipe (Group)
- Test aggregation

**Phase 6**: Automation
- Create daily_refresh scenario
- Configure triggers and notifications
- Test end-to-end

### Approval Needed
Does this plan match your requirements? Should I proceed with Phase 1?
```

---

## KEY TAKEAWAYS

1. **ALWAYS plan before coding** - Never start without a plan
2. **Use UPPERCASE for Snowflake** - Prevents many SQL errors
3. **Work phase by phase** - Test incrementally
4. **Document progress** - Track what's done
5. **Get plan approval** - Verify requirements before building

---

## Next Steps

- Once you have a plan approved, start with `01-prerequisites-and-setup.md`
- Follow the guides phase by phase
- Use `99-quick-reference.md` for quick code lookups

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
