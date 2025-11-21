# 03 - Project Operations

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Creating, configuring, and managing Dataiku projects

---

## Projects in Dataiku

A **Project** is the top-level container in Dataiku that holds:
- Datasets
- Recipes
- Scenarios
- ML Tasks
- Dashboards
- Notebooks
- Flow/DAG
- Settings and variables

**Key Concept:** Almost everything you do in Dataiku happens within a project scope.

---

## Listing Projects

### List Project Keys Only

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# Get list of project keys (strings)
project_keys = client.list_project_keys()
print(f"Found {len(project_keys)} projects")
print(project_keys)  # ['PROJECT1', 'PROJECT2', 'PROJECT3']
```

**When to use:** Quick check of what projects exist or if you can access a project.

### List Project Summaries

```python
# Get detailed project information
projects = client.list_projects()

for project in projects:
    print(f"Key: {project['projectKey']}")
    print(f"Name: {project['name']}")
    print(f"Owner: {project['owner']}")
    print(f"Created: {project['creationTag']['lastModifiedOn']}")
    print(f"Description: {project.get('shortDesc', 'N/A')}")
    print("-" * 40)
```

**When to use:** When you need metadata about projects (names, owners, descriptions).

### Filter Projects

```python
# Find projects by criteria
def find_projects_by_owner(client, owner_login):
    """Find all projects owned by specific user"""
    all_projects = client.list_projects()
    return [p for p in all_projects if p['owner'] == owner_login]

def find_projects_by_tag(client, tag):
    """Find projects with specific tag"""
    all_projects = client.list_projects()
    return [p for p in all_projects if tag in p.get('tags', [])]

# Usage
my_projects = find_projects_by_owner(client, "john.doe")
tagged_projects = find_projects_by_tag(client, "production")
```

---

## Getting a Project

### Basic Project Access

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# Get project handle
project = client.get_project("MY_PROJECT")

# Now you can access project resources
datasets = project.list_datasets()
recipes = project.list_recipes()
scenarios = project.list_scenarios()
```

### Check if Project Exists

```python
def project_exists(client, project_key):
    """Check if project exists and is accessible"""
    try:
        client.get_project(project_key)
        return True
    except:
        return False

# Usage
if project_exists(client, "MY_PROJECT"):
    project = client.get_project("MY_PROJECT")
else:
    print("Project does not exist or is not accessible")
```

---

## Creating Projects

### Basic Project Creation

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)

# Create new project
project_key = "NEW_PROJECT"
project_name = "My New Project"
owner = "john.doe"  # DSS username

project = client.create_project(
    project_key=project_key,
    name=project_name,
    owner=owner,
    description="Project created via API",
    settings=None  # Use default settings
)

print(f"Created project: {project_key}")
```

**GOTCHA:**
- Requires admin rights or permission to create projects
- `project_key` must be uppercase letters, numbers, and underscores only
- `project_key` must be unique across the instance
- `owner` must be an existing DSS user

### Project Creation with Settings

```python
# Create project with custom settings
project = client.create_project(
    project_key="CUSTOM_PROJECT",
    name="Custom Project",
    owner="john.doe",
    description="Project with custom settings",
    settings={
        "tags": ["production", "etl"],
        "checklists": {
            "checklists": []
        }
    }
)
```

### Create Project from Template

```python
def create_project_from_template(client, template_key, new_key, new_name, owner):
    """Create new project based on existing project as template"""

    # Export template project
    template_project = client.get_project(template_key)
    export_stream = template_project.get_export_stream(
        options={
            "exportUploads": False,  # Don't export uploaded files
            "exportManagedFS": False,  # Don't export managed folder contents
            "exportAnalysisModels": True,
            "exportSavedModels": True,
            "exportManagedFolders": True,
            "exportAllInputDatasets": False,
            "exportAllDatasets": False,
            "exportAllInputManagedFolders": False
        }
    )

    # Import as new project
    import_result = client.prepare_project_import(export_stream)
    import_result = import_result.execute(
        new_project_key=new_key,
        new_project_name=new_name
    )

    # Get the new project
    new_project = client.get_project(new_key)

    # Update owner
    settings = new_project.get_settings()
    settings.settings['owner'] = owner
    settings.save()

    return new_project

# Usage
new_project = create_project_from_template(
    client,
    template_key="TEMPLATE_PROJECT",
    new_key="NEW_FROM_TEMPLATE",
    new_name="New Project from Template",
    owner="jane.doe"
)
```

---

## Project Settings

### Get and Modify Settings

```python
project = client.get_project("MY_PROJECT")

# Get settings object
settings = project.get_settings()

# View current settings (raw dict)
print(settings.settings)

# Modify settings
settings.settings['shortDesc'] = "Updated description"
settings.settings['tags'].append('new-tag')

# Save changes
settings.save()
```

### Common Settings Operations

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")
settings = project.get_settings()

# Add tags
if 'production' not in settings.settings.get('tags', []):
    settings.settings.setdefault('tags', []).append('production')

# Set description
settings.settings['shortDesc'] = "This project handles customer data ETL"

# Change owner
settings.settings['owner'] = 'new.owner'

# Add contributor
if 'contributors' not in settings.settings:
    settings.settings['contributors'] = []
settings.settings['contributors'].append('contributor.user')

# Save all changes
settings.save()

print("✓ Project settings updated")
```

### Project Variables

```python
# Get project variables
variables = project.get_variables()
print("Current variables:", variables)

# Set project variables
project.set_variables({
    "db_host": "postgres.company.com",
    "db_name": "production",
    "api_endpoint": "https://api.company.com",
    "batch_size": "1000"
})

# Update specific variable
current = project.get_variables()
current["batch_size"] = "2000"
project.set_variables(current)

print("✓ Project variables updated")
```

**IMPORTANT:** Project variables are strings. Convert types when using:

```python
variables = project.get_variables()
batch_size = int(variables.get("batch_size", "1000"))
```

---

## Project Metadata

### Get Project Information

```python
project = client.get_project("MY_PROJECT")

# Get project metadata (comprehensive info)
metadata = project.get_metadata()

print(f"Project Key: {metadata['projectKey']}")
print(f"Name: {metadata['name']}")
print(f"Owner: {metadata['owner']}")
print(f"Created: {metadata['creationTag']['lastModifiedOn']}")
print(f"Contributors: {metadata.get('contributors', [])}")
print(f"Tags: {metadata.get('tags', [])}")

# Get permissions info
print(f"Permissions: {metadata.get('permissions', [])}")
```

### Get Project Summary

```python
# Lightweight project info
summary = project.get_summary()

print(f"Key: {summary['projectKey']}")
print(f"Name: {summary['name']}")
print(f"# Datasets: {summary.get('nbDatasets', 0)}")
print(f"# Recipes: {summary.get('nbRecipes', 0)}")
print(f"# Scenarios: {summary.get('nbRunningScenarios', 0)} running")
```

---

## Project Contents

### List All Resources in Project

```python
project = client.get_project("MY_PROJECT")

# List datasets
datasets = project.list_datasets()
print(f"Datasets ({len(datasets)}):")
for ds in datasets:
    print(f"  - {ds['name']} ({ds['type']})")

# List recipes
recipes = project.list_recipes()
print(f"\nRecipes ({len(recipes)}):")
for r in recipes:
    print(f"  - {r['name']} ({r['type']})")

# List scenarios
scenarios = project.list_scenarios()
print(f"\nScenarios ({len(scenarios)}):")
for s in scenarios:
    print(f"  - {s['name']} (active: {s.get('active', False)})")

# List managed folders
folders = project.list_managed_folders()
print(f"\nManaged Folders ({len(folders)}):")
for f in folders:
    print(f"  - {f['name']}")

# List ML tasks
ml_tasks = project.list_ml_tasks()
print(f"\nML Tasks ({len(ml_tasks)}):")
for t in ml_tasks:
    print(f"  - {t['name']}")

# List saved models
saved_models = project.list_saved_models()
print(f"\nSaved Models ({len(saved_models)}):")
for m in saved_models:
    print(f"  - {m['id']}")

# List dashboards
dashboards = project.list_dashboards()
print(f"\nDashboards ({len(dashboards)}):")
for d in dashboards:
    print(f"  - {d['name']}")
```

### Project Inventory Function

```python
def get_project_inventory(client, project_key):
    """Get comprehensive inventory of project contents"""

    project = client.get_project(project_key)

    inventory = {
        "project_key": project_key,
        "datasets": len(project.list_datasets()),
        "recipes": len(project.list_recipes()),
        "scenarios": len(project.list_scenarios()),
        "ml_tasks": len(project.list_ml_tasks()),
        "saved_models": len(project.list_saved_models()),
        "managed_folders": len(project.list_managed_folders()),
        "dashboards": len(project.list_dashboards()),
        "web_apps": len(project.list_web_apps() if hasattr(project, 'list_web_apps') else []),
        "notebooks": len(project.list_jupyter_notebooks() if hasattr(project, 'list_jupyter_notebooks') else [])
    }

    return inventory

# Usage
inventory = get_project_inventory(client, "MY_PROJECT")
print(f"Project Inventory:")
for resource, count in inventory.items():
    print(f"  {resource}: {count}")
```

---

## Project Flow

### Get Flow Graph

```python
project = client.get_project("MY_PROJECT")

# Get flow handle
flow = project.get_flow()

# Get flow graph
graph = flow.get_graph()

# Explore graph
print(f"Zones: {len(graph.get('zones', []))}")
print(f"Computablens: {graph.get('nodes', [])}")

# Get all nodes
nodes = graph.get('nodes', [])
for node in nodes:
    print(f"Node: {node.get('id')} (type: {node.get('type')})")
```

### Flow Zones

```python
flow = project.get_flow()

# List zones
zones = flow.list_zones()
print(f"Found {len(zones)} zones")
for zone in zones:
    print(f"  - {zone['name']}")

# Create new zone
new_zone = flow.create_zone(
    name="Data Ingestion",
    color="#FF5733"
)

# Get specific zone
zone = flow.get_zone("zone_id")
zone_settings = zone.get_settings()
zone_settings.settings['name'] = "Updated Zone Name"
zone_settings.save()
```

---

## Project Jobs

### List Recent Jobs

```python
project = client.get_project("MY_PROJECT")

# List all jobs (recent first)
jobs = project.list_jobs()

print(f"Recent Jobs ({len(jobs)}):")
for job in jobs[:10]:  # Show last 10
    print(f"Job {job['def']['id']}:")
    print(f"  Type: {job['def'].get('type', 'N/A')}")
    print(f"  State: {job['state']}")
    print(f"  Start: {job.get('startTime', 'N/A')}")
    print("-" * 40)
```

### Get Specific Job

```python
# Get job by ID
job_id = "JOB_20231121_123456_ABC"
job = project.get_job(job_id)

# Get job status
status = job.get_status()
print(f"Job Status: {status['baseStatus']['state']}")

# Get job log
log = job.get_log()
print("Job Log:")
print(log)
```

### Start New Job

```python
# Create and run a job to build a dataset
dataset = project.get_dataset("my_dataset")

# Start build job
job = dataset.build(wait=False)

print(f"Started job: {job.id}")

# Monitor job
while True:
    status = job.get_status()
    state = status['baseStatus']['state']
    print(f"Job state: {state}")

    if state in ['DONE', 'FAILED', 'ABORTED']:
        break

    time.sleep(2)

if state == 'DONE':
    print("✓ Job completed successfully")
else:
    print(f"❌ Job failed with state: {state}")
    print(job.get_log())
```

---

## Project Export/Import

### Export Project

```python
project = client.get_project("MY_PROJECT")

# Get export stream
export_stream = project.get_export_stream(
    options={
        "exportUploads": False,
        "exportManagedFS": False,
        "exportAnalysisModels": True,
        "exportSavedModels": True,
        "exportManagedFolders": True,
        "exportAllInputDatasets": False,
        "exportAllDatasets": False,
        "exportAllInputManagedFolders": False,
        "exportGitRepository": False,
        "exportInsightsData": False
    }
)

# Save to file
with open(f"{project.project_key}_export.zip", "wb") as f:
    for chunk in export_stream:
        f.write(chunk)

print(f"✓ Project exported to {project.project_key}_export.zip")
```

### Import Project

```python
# Import from file
with open("PROJECT_export.zip", "rb") as f:
    import_handle = client.prepare_project_import(f)

    # Execute import
    result = import_handle.execute(
        new_project_key="IMPORTED_PROJECT",
        new_project_name="Imported Project"
    )

print("✓ Project imported successfully")
```

### Duplicate Project

```python
def duplicate_project(client, source_key, target_key, target_name):
    """Create a duplicate of an existing project"""

    source = client.get_project(source_key)

    # Export source
    export_stream = source.get_export_stream()

    # Import as new project
    import_handle = client.prepare_project_import(export_stream)
    import_handle.execute(
        new_project_key=target_key,
        new_project_name=target_name
    )

    print(f"✓ Duplicated {source_key} to {target_key}")
    return client.get_project(target_key)

# Usage
duplicate_project(
    client,
    source_key="TEMPLATE",
    target_key="NEW_INSTANCE",
    target_name="New Instance from Template"
)
```

---

## Project Deletion

### Delete Project

```python
# ⚠️  WARNING: This permanently deletes the project and all its contents!

project = client.get_project("PROJECT_TO_DELETE")

# Optional: Export backup first
export_stream = project.get_export_stream()
with open("backup.zip", "wb") as f:
    for chunk in export_stream:
        f.write(chunk)

# Delete project
project.delete()

print("✓ Project deleted")
```

### Safe Delete with Confirmation

```python
def safe_delete_project(client, project_key, confirmation_string):
    """Delete project with confirmation and backup"""

    if confirmation_string != f"DELETE {project_key}":
        raise ValueError(
            f"Confirmation failed. Must provide exactly: 'DELETE {project_key}'"
        )

    project = client.get_project(project_key)

    # Create backup
    backup_file = f"{project_key}_backup_{int(time.time())}.zip"
    export_stream = project.get_export_stream()

    with open(backup_file, "wb") as f:
        for chunk in export_stream:
            f.write(chunk)

    print(f"✓ Backup saved to {backup_file}")

    # Delete
    project.delete()
    print(f"✓ Project {project_key} deleted")

    return backup_file

# Usage - requires exact confirmation string
backup = safe_delete_project(
    client,
    "OLD_PROJECT",
    "DELETE OLD_PROJECT"  # Must match exactly
)
```

---

## Project Permissions

### View Project Permissions

```python
project = client.get_project("MY_PROJECT")
settings = project.get_settings()

# Get owner
owner = settings.settings.get('owner')
print(f"Owner: {owner}")

# Get contributors
contributors = settings.settings.get('contributors', [])
print(f"Contributors: {contributors}")

# Get permissions (if you have admin rights)
try:
    permissions = settings.settings.get('permissions', [])
    for perm in permissions:
        print(f"Group: {perm.get('group', perm.get('user'))}")
        print(f"  Read: {perm.get('read', False)}")
        print(f"  Write: {perm.get('write', False)}")
        print(f"  Admin: {perm.get('admin', False)}")
except:
    print("Cannot view detailed permissions (requires admin)")
```

### Add Project Contributor

```python
def add_project_contributor(project, username):
    """Add a user as project contributor"""

    settings = project.get_settings()

    contributors = settings.settings.get('contributors', [])
    if username not in contributors:
        contributors.append(username)
        settings.settings['contributors'] = contributors
        settings.save()
        print(f"✓ Added {username} as contributor")
    else:
        print(f"{username} is already a contributor")

# Usage
project = client.get_project("MY_PROJECT")
add_project_contributor(project, "jane.doe")
```

---

## Advanced: Bulk Project Operations

### Create Multiple Projects from Config

```python
import yaml

def create_projects_from_config(client, config_file):
    """Create multiple projects from YAML config"""

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    results = []

    for project_def in config['projects']:
        try:
            project = client.create_project(
                project_key=project_def['key'],
                name=project_def['name'],
                owner=project_def['owner'],
                description=project_def.get('description', ''),
                settings={"tags": project_def.get('tags', [])}
            )

            # Set variables if defined
            if 'variables' in project_def:
                project.set_variables(project_def['variables'])

            results.append({
                "key": project_def['key'],
                "status": "success"
            })
            print(f"✓ Created {project_def['key']}")

        except Exception as e:
            results.append({
                "key": project_def['key'],
                "status": "failed",
                "error": str(e)
            })
            print(f"❌ Failed to create {project_def['key']}: {e}")

    return results

# Example config.yaml:
# projects:
#   - key: PROJECT1
#     name: First Project
#     owner: john.doe
#     description: Project 1 description
#     tags: [production, etl]
#     variables:
#       db_host: postgres.company.com
#       batch_size: "1000"
#
#   - key: PROJECT2
#     name: Second Project
#     owner: jane.doe
#     tags: [development]

results = create_projects_from_config(client, "projects_config.yaml")
```

### Audit All Projects

```python
def audit_all_projects(client):
    """Generate audit report of all projects"""

    projects = client.list_projects()

    audit_data = []

    for proj_summary in projects:
        try:
            project = client.get_project(proj_summary['projectKey'])
            inventory = get_project_inventory(client, proj_summary['projectKey'])

            audit_data.append({
                "key": proj_summary['projectKey'],
                "name": proj_summary['name'],
                "owner": proj_summary['owner'],
                "created": proj_summary['creationTag']['lastModifiedOn'],
                "tags": proj_summary.get('tags', []),
                **inventory
            })
        except Exception as e:
            print(f"Failed to audit {proj_summary['projectKey']}: {e}")

    return audit_data

# Usage
import json

audit = audit_all_projects(client)

# Save to file
with open('project_audit.json', 'w') as f:
    json.dump(audit, f, indent=2)

print(f"✓ Audited {len(audit)} projects")
```

---

## Common Gotchas

### 1. Project Keys Must Be Uppercase

```python
# ❌ WRONG
client.create_project("my_project", "My Project", "owner")  # Will fail!

# ✓ CORRECT
client.create_project("MY_PROJECT", "My Project", "owner")
```

### 2. Owner Must Be Valid User

```python
# Check if user exists first
try:
    user = client.get_user("john.doe")
    # User exists, can use as owner
    project = client.create_project("NEW_PROJECT", "New Project", "john.doe")
except:
    print("User doesn't exist, cannot create project")
```

### 3. Settings Must Be Saved

```python
# ❌ WRONG - Changes not saved!
settings = project.get_settings()
settings.settings['shortDesc'] = "New description"
# Forgot to save!

# ✓ CORRECT
settings = project.get_settings()
settings.settings['shortDesc'] = "New description"
settings.save()  # Must call save()
```

### 4. Project Variables Are Strings

```python
# Setting variables
project.set_variables({
    "batch_size": "1000",  # Store as string
    "enabled": "true"      # Store as string
})

# Using variables - convert types!
variables = project.get_variables()
batch_size = int(variables["batch_size"])  # Convert to int
enabled = variables["enabled"].lower() == "true"  # Convert to bool
```

---

## Next Steps

- **04-dataset-operations.md** - Working with datasets
- **05-recipe-workflows.md** - Creating and running recipes
- **06-scenario-automation.md** - Automating workflows

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
