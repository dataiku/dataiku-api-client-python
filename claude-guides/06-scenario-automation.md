# 06 - Scenario Automation

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Creating, configuring, and running Dataiku scenarios for workflow automation

---

## Scenarios in Dataiku

**Scenarios** are automation workflows that orchestrate data pipelines. They can:
- Build datasets
- Run recipes
- Execute Python/R code
- Send notifications
- Make API calls
- Run on schedules or triggers

**Key Concept:** Scenarios are the primary automation tool in Dataiku.

---

## Listing Scenarios

### List All Scenarios

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")

# List scenarios
scenarios = project.list_scenarios()

print(f"Found {len(scenarios)} scenarios:")
for scenario in scenarios:
    print(f"  - {scenario['name']} ({'Active' if scenario.get('active') else 'Inactive'})")
    print(f"    Type: {scenario.get('type', 'N/A')}")
    print(f"    Triggers: {len(scenario.get('triggers', []))}")
```

### Filter Active Scenarios

```python
def get_active_scenarios(project):
    """Get all active scenarios"""
    all_scenarios = project.list_scenarios()
    return [s for s in all_scenarios if s.get('active', False)]

# Usage
active = get_active_scenarios(project)
print(f"Found {len(active)} active scenarios")
```

---

## Getting a Scenario

```python
project = client.get_project("MY_PROJECT")

# Get scenario handle
scenario = project.get_scenario("daily_refresh")

# Get scenario settings
settings = scenario.get_settings()
print(f"Scenario: {settings.settings.get('name')}")
print(f"Active: {settings.settings.get('active')}")
```

---

## Running Scenarios

### Run and Wait (Synchronous)

```python
scenario = project.get_scenario("daily_refresh")

# Run and wait for completion
scenario_run = scenario.run_and_wait()

# Check result
if scenario_run.get_outcome() == 'SUCCESS':
    print("✓ Scenario succeeded")
else:
    print(f"❌ Scenario failed: {scenario_run.get_outcome()}")
```

### Run Asynchronously

**IMPORTANT:** This is a two-step process!

```python
import time

scenario = project.get_scenario("daily_refresh")

# Step 1: Trigger the scenario (returns trigger fire)
trigger_fire = scenario.run()

print(f"Scenario triggered, fire ID: {trigger_fire.get_trigger_fire()['runId']}")

# Step 2: Wait for actual scenario run to start
scenario_run = trigger_fire.wait_for_scenario_run()

print(f"Scenario run started: {scenario_run.get_id()}")

# Monitor progress
while scenario_run.running:
    scenario_run.refresh()
    print(f"Status: {scenario_run.get_state()}", end='\r')
    time.sleep(5)

print()  # Newline
print(f"Final outcome: {scenario_run.get_outcome()}")
```

### Run with Parameters

```python
# Scenarios can accept parameters
scenario = project.get_scenario("parameterized_scenario")

# Run with custom parameters
trigger_fire = scenario.run(params={
    "date": "2023-11-21",
    "region": "US",
    "batch_size": "1000"
})

scenario_run = trigger_fire.wait_for_scenario_run()
scenario_run.wait_for_completion()

print(f"Scenario completed with outcome: {scenario_run.get_outcome()}")
```

---

## Scenario History and Runs

### Get Last Run

```python
scenario = project.get_scenario("daily_refresh")

# Get most recent run
last_run = scenario.get_last_finished_run()

if last_run:
    print(f"Last run ID: {last_run.get_id()}")
    print(f"Start time: {last_run.get_start_time()}")
    print(f"End time: {last_run.get_end_time()}")
    print(f"Outcome: {last_run.get_outcome()}")
    print(f"Duration: {last_run.get_duration()} ms")
else:
    print("No runs found")
```

### Get Run History

```python
scenario = project.get_scenario("daily_refresh")

# Get last N runs
last_runs = scenario.get_last_runs(limit=10)

print("Last 10 runs:")
for run in last_runs:
    print(f"  {run.get_start_time()}: {run.get_outcome()}")
```

### Get Runs by Date Range

```python
from datetime import datetime, timedelta

scenario = project.get_scenario("daily_refresh")

# Get runs from last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

runs = scenario.get_runs_by_date(
    from_time=int(start_date.timestamp() * 1000),
    to_time=int(end_date.timestamp() * 1000)
)

print(f"Runs in last 7 days: {len(runs)}")
for run in runs:
    print(f"  {run.get_start_time()}: {run.get_outcome()}")
```

---

## Scenario Run Details

### Get Run Logs

```python
scenario = project.get_scenario("daily_refresh")
last_run = scenario.get_last_finished_run()

if last_run:
    # Get full details
    details = last_run.get_details()

    # Print step outcomes
    for step in details.get('stepRuns', []):
        print(f"Step: {step.get('stepName')}")
        print(f"  Outcome: {step.get('result', {}).get('outcome')}")
        print(f"  Duration: {step.get('duration')} ms")

        # Get step logs if failed
        if step.get('result', {}).get('outcome') == 'FAILED':
            print(f"  Error: {step.get('result', {}).get('errorDetails')}")
```

### Check Specific Run Status

```python
# Get specific run by ID
scenario = project.get_scenario("daily_refresh")
run_id = "scenario_run_12345"

scenario_run = scenario.get_run(run_id)

print(f"Run ID: {scenario_run.get_id()}")
print(f"State: {scenario_run.get_state()}")
print(f"Outcome: {scenario_run.get_outcome()}")
print(f"Running: {scenario_run.running}")
```

---

## Creating Scenarios

### Create Basic Scenario

```python
project = client.get_project("MY_PROJECT")

# Create new scenario
scenario = project.create_scenario(
    scenario_name="new_automation",
    type="step_based",
    definition={}
)

print(f"✓ Created scenario: new_automation")
```

### Configure Scenario Settings

```python
scenario = project.get_scenario("new_automation")

# Get settings
settings = scenario.get_settings()

# Configure basic settings
settings.settings['name'] = "Daily Data Refresh"
settings.settings['active'] = True
settings.settings['creationTag'] = {
    "versionNumber": 0,
    "lastModifiedBy": {"login": "admin"},
    "lastModifiedOn": int(time.time() * 1000)
}

# Save
settings.save()

print("✓ Scenario settings updated")
```

---

## Scenario Steps

### Add Build Dataset Step

```python
scenario = project.get_scenario("new_automation")
settings = scenario.get_settings()

# Add step to build a dataset
build_step = {
    "id": "build_dataset_1",
    "type": "build_flowitem",
    "name": "Build Customer Data",
    "params": {
        "builds": [{
            "type": "DATASET",
            "itemId": "customers",
            "partitionsSpec": ""
        }]
    },
    "runConditionEnabled": False,
    "runConditionExpression": ""
}

# Add step to scenario
if 'params' not in settings.settings:
    settings.settings['params'] = {}
if 'steps' not in settings.settings['params']:
    settings.settings['params']['steps'] = []

settings.settings['params']['steps'].append(build_step)

# Save
settings.save()

print("✓ Added build step")
```

### Add Python Step

```python
scenario = project.get_scenario("new_automation")
settings = scenario.get_settings()

# Add Python code step
python_step = {
    "id": "python_1",
    "type": "custom_python",
    "name": "Custom Logic",
    "params": {
        "envSelection": {
            "envMode": "INHERIT"
        },
        "script": """
# Python code runs in DSS
import dataiku

client = dataiku.api_client()
project = client.get_default_project()

# Your automation code here
print("Running custom logic...")

# Example: Check dataset status
dataset = project.get_dataset("customers")
schema = dataset.get_schema()
print(f"Dataset has {len(schema['columns'])} columns")
"""
    },
    "runConditionEnabled": False
}

settings.settings['params']['steps'].append(python_step)
settings.save()

print("✓ Added Python step")
```

### Add SQL Step

```python
# Add SQL query step
sql_step = {
    "id": "sql_1",
    "type": "exec_sql",
    "name": "Run SQL Maintenance",
    "params": {
        "connection": "my_postgres",
        "script": """
-- SQL commands
VACUUM ANALYZE customers;
UPDATE stats SET last_refresh = NOW();
"""
    }
}

settings.settings['params']['steps'].append(sql_step)
settings.save()
```

### Add Conditional Step

```python
# Add step with run condition
conditional_step = {
    "id": "conditional_build",
    "type": "build_flowitem",
    "name": "Build if Updated",
    "params": {
        "builds": [{
            "type": "DATASET",
            "itemId": "output_data",
            "partitionsSpec": ""
        }]
    },
    "runConditionEnabled": True,
    "runConditionExpression": "outcome['build_dataset_1'] == 'SUCCESS'"
}

settings.settings['params']['steps'].append(conditional_step)
settings.save()
```

---

## Scenario Triggers

### Add Time Trigger (Schedule)

```python
scenario = project.get_scenario("daily_refresh")
settings = scenario.get_settings()

# Add time-based trigger (daily at 2 AM)
trigger = {
    "id": "time_trigger_1",
    "type": "temporal",
    "name": "Daily at 2 AM",
    "active": True,
    "params": {
        "frequency": "Daily",
        "startOn": int(time.time() * 1000),
        "timezone": "UTC",
        "daysOfWeek": [],
        "minute": 0,
        "hour": 2,
        "repeatFrequency": 0
    }
}

if 'triggers' not in settings.settings:
    settings.settings['triggers'] = []

settings.settings['triggers'].append(trigger)
settings.save()

print("✓ Added daily trigger")
```

### Add Dataset Update Trigger

```python
# Trigger when dataset is updated
trigger = {
    "id": "dataset_trigger_1",
    "type": "dataset_modified",
    "name": "On Source Data Update",
    "active": True,
    "params": {
        "datasetId": "source_data",
        "type": "ALL"  # ALL, ANY_PARTITION, SPECIFIC_PARTITION
    }
}

settings.settings['triggers'].append(trigger)
settings.save()

print("✓ Added dataset update trigger")
```

### Add Manual Trigger

```python
# Manual trigger (run on demand)
trigger = {
    "id": "manual_trigger_1",
    "type": "manual",
    "name": "Manual Run",
    "active": True,
    "params": {}
}

settings.settings['triggers'].append(trigger)
settings.save()
```

---

## Scenario Notifications

### Add Email Reporter

```python
scenario = project.get_scenario("daily_refresh")
settings = scenario.get_settings()

# Add email notification on failure
reporter = {
    "messaging": {
        "type": "mail-scenario",
        "configuration": {
            "recipient": "data-team@company.com",
            "subject": "Scenario Failed: Daily Refresh",
            "message": """
Scenario: ${scenarioName}
Project: ${projectKey}
Outcome: ${outcome}
Start Time: ${startTime}
End Time: ${endTime}

Please check the logs for details.
"""
        }
    },
    "runConditionEnabled": True,
    "runConditionExpression": "outcome == 'FAILED'"
}

if 'reporters' not in settings.settings['params']:
    settings.settings['params']['reporters'] = []

settings.settings['params']['reporters'].append(reporter)
settings.save()

print("✓ Added email reporter")
```

---

## Complete Scenario Example

### Full Scenario Setup

```python
def create_complete_scenario(project, scenario_name):
    """Create a complete scenario with steps and triggers"""

    # Create scenario
    scenario = project.create_scenario(
        scenario_name=scenario_name,
        type="step_based",
        definition={}
    )

    # Get settings
    settings = scenario.get_settings()

    # Basic info
    settings.settings['name'] = "Complete ETL Pipeline"
    settings.settings['active'] = True

    # Add steps
    settings.settings['params'] = {
        "steps": [
            # Step 1: Build source dataset
            {
                "id": "build_source",
                "type": "build_flowitem",
                "name": "Build Source Data",
                "params": {
                    "builds": [{
                        "type": "DATASET",
                        "itemId": "source_data",
                        "partitionsSpec": ""
                    }]
                }
            },
            # Step 2: Run transformation
            {
                "id": "run_recipe",
                "type": "build_flowitem",
                "name": "Run Transformations",
                "params": {
                    "builds": [{
                        "type": "RECURSIVE",
                        "itemId": "final_output",
                        "partitionsSpec": ""
                    }]
                },
                "runConditionEnabled": True,
                "runConditionExpression": "outcome['build_source'] == 'SUCCESS'"
            },
            # Step 3: Validate results
            {
                "id": "validate",
                "type": "custom_python",
                "name": "Validate Results",
                "params": {
                    "envSelection": {"envMode": "INHERIT"},
                    "script": """
import dataiku

client = dataiku.api_client()
project = client.get_default_project()

# Check row count
dataset = project.get_dataset("final_output")
metadata = dataset.get_metadata()
record_count = metadata.get('recordCount', 0)

print(f"Final output has {record_count} records")

if record_count == 0:
    raise Exception("No records in output!")
"""
                },
                "runConditionEnabled": True,
                "runConditionExpression": "outcome['run_recipe'] == 'SUCCESS'"
            }
        ],
        "reporters": [
            # Success notification
            {
                "messaging": {
                    "type": "mail-scenario",
                    "configuration": {
                        "recipient": "team@company.com",
                        "subject": "Pipeline Success: ${scenarioName}",
                        "message": "Pipeline completed successfully."
                    }
                },
                "runConditionEnabled": True,
                "runConditionExpression": "outcome == 'SUCCESS'"
            },
            # Failure notification
            {
                "messaging": {
                    "type": "mail-scenario",
                    "configuration": {
                        "recipient": "team@company.com",
                        "subject": "Pipeline FAILED: ${scenarioName}",
                        "message": "Pipeline failed. Check logs."
                    }
                },
                "runConditionEnabled": True,
                "runConditionExpression": "outcome == 'FAILED'"
            }
        ]
    }

    # Add trigger (daily at 2 AM)
    settings.settings['triggers'] = [
        {
            "id": "daily_trigger",
            "type": "temporal",
            "name": "Daily at 2 AM",
            "active": True,
            "params": {
                "frequency": "Daily",
                "startOn": int(time.time() * 1000),
                "timezone": "UTC",
                "hour": 2,
                "minute": 0
            }
        }
    ]

    # Save
    settings.save()

    print(f"✓ Created complete scenario: {scenario_name}")
    return scenario

# Usage
scenario = create_complete_scenario(project, "etl_pipeline")
```

---

## Scenario Control

### Abort Running Scenario

```python
scenario = project.get_scenario("long_running")

# Get current run
last_run = scenario.get_last_runs(limit=1)[0]

if last_run.running:
    # Abort it
    last_run.abort()
    print("✓ Scenario aborted")
else:
    print("Scenario not running")
```

### Enable/Disable Scenario

```python
scenario = project.get_scenario("daily_refresh")
settings = scenario.get_settings()

# Disable
settings.settings['active'] = False
settings.save()
print("✓ Scenario disabled")

# Enable
settings.settings['active'] = True
settings.save()
print("✓ Scenario enabled")
```

---

## Bulk Operations

### Run Multiple Scenarios

```python
def run_scenarios_sequentially(project, scenario_names):
    """Run multiple scenarios in sequence"""

    results = []

    for scenario_name in scenario_names:
        try:
            print(f"Running {scenario_name}...")
            scenario = project.get_scenario(scenario_name)

            scenario_run = scenario.run_and_wait()

            outcome = scenario_run.get_outcome()
            results.append({
                "scenario": scenario_name,
                "outcome": outcome,
                "run_id": scenario_run.get_id()
            })

            print(f"✓ {scenario_name}: {outcome}")

            # Stop on first failure
            if outcome != 'SUCCESS':
                print(f"Stopping due to failure in {scenario_name}")
                break

        except Exception as e:
            print(f"❌ {scenario_name} error: {e}")
            results.append({
                "scenario": scenario_name,
                "outcome": "ERROR",
                "error": str(e)
            })
            break

    return results

# Usage
scenarios = ["prepare_data", "process_data", "export_results"]
results = run_scenarios_sequentially(project, scenarios)
```

### Disable All Scenarios

```python
def disable_all_scenarios(project):
    """Disable all scenarios in project"""

    scenarios = project.list_scenarios()

    for scenario_info in scenarios:
        scenario = project.get_scenario(scenario_info['name'])
        settings = scenario.get_settings()

        if settings.settings.get('active', False):
            settings.settings['active'] = False
            settings.save()
            print(f"✓ Disabled {scenario_info['name']}")

# Usage
disable_all_scenarios(project)
```

---

## Monitoring Scenarios

### Check Scenario Health

```python
from datetime import datetime, timedelta

def check_scenario_health(scenario, expected_frequency_hours=24):
    """Check if scenario is running as expected"""

    # Get last successful run
    runs = scenario.get_last_runs(limit=10)
    successful_runs = [r for r in runs if r.get_outcome() == 'SUCCESS']

    if not successful_runs:
        return {
            "healthy": False,
            "issue": "No successful runs found",
            "last_run": None
        }

    last_success = successful_runs[0]
    last_success_time = datetime.fromtimestamp(
        last_success.get_start_time() / 1000
    )

    # Check if run is recent enough
    hours_since = (datetime.now() - last_success_time).total_seconds() / 3600

    if hours_since > expected_frequency_hours:
        return {
            "healthy": False,
            "issue": f"Last success was {hours_since:.1f} hours ago",
            "last_run": last_success_time
        }

    return {
        "healthy": True,
        "issue": None,
        "last_run": last_success_time
    }

# Usage
scenario = project.get_scenario("daily_refresh")
health = check_scenario_health(scenario, expected_frequency_hours=24)

if health['healthy']:
    print(f"✓ Scenario healthy. Last run: {health['last_run']}")
else:
    print(f"❌ Scenario issue: {health['issue']}")
```

---

## Common Gotchas

### 1. Two-Step Run Process

```python
# ❌ WRONG - trigger_fire is NOT the scenario run!
trigger_fire = scenario.run()
outcome = trigger_fire.get_outcome()  # AttributeError!

# ✓ CORRECT - Must wait for scenario run
trigger_fire = scenario.run()
scenario_run = trigger_fire.wait_for_scenario_run()
outcome = scenario_run.get_outcome()
```

### 2. Scenario Settings Need Save

```python
# ❌ WRONG - Changes not saved
settings = scenario.get_settings()
settings.settings['active'] = True
# Forgot settings.save()!

# ✓ CORRECT
settings = scenario.get_settings()
settings.settings['active'] = True
settings.save()
```

### 3. Step IDs Must Be Unique

```python
# Each step needs unique ID
step1 = {"id": "step_1", ...}
step2 = {"id": "step_1", ...}  # ❌ Duplicate ID!

# Use unique IDs
step1 = {"id": "step_1", ...}
step2 = {"id": "step_2", ...}  # ✓ Unique
```

### 4. Run Conditions Use Previous Step Outcomes

```python
# Reference previous steps by their ID
conditional_step = {
    "runConditionEnabled": True,
    "runConditionExpression": "outcome['build_source'] == 'SUCCESS'"
    # 'build_source' must match a previous step's ID
}
```

---

## Next Steps

- **07-ml-workflows.md** - Machine learning automation
- **08-common-gotchas.md** - Comprehensive troubleshooting
- **99-quick-reference.md** - Quick lookup

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
