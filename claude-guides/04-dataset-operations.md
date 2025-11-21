# 04 - Dataset Operations

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Creating, reading, updating, and managing Dataiku datasets

---

## Dataset Basics

Datasets in Dataiku are the core data objects. They can be:
- **SQL tables** (PostgreSQL, MySQL, Snowflake, etc.)
- **Files** (CSV, Parquet, JSON, Excel, etc.)
- **Cloud storage** (S3, GCS, Azure Blob, etc.)
- **NoSQL** (MongoDB, Cassandra, Elasticsearch, etc.)
- **Streaming** (Kafka, etc.)
- **Custom** (via plugins)

**Key Concept:** Datasets have **settings** (configuration) and **data** (content). Most operations work with one or both.

---

## Listing Datasets

### List All Datasets in Project

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")

# Get list of dataset objects (lightweight)
datasets = project.list_datasets()

print(f"Found {len(datasets)} datasets:")
for ds in datasets:
    print(f"  - {ds['name']} ({ds['type']})")
    print(f"    Schema: {len(ds.get('schema', {}).get('columns', []))} columns")
```

### Filter Datasets by Type

```python
def get_datasets_by_type(project, dataset_type):
    """Get all datasets of specific type (e.g., 'PostgreSQL', 'Filesystem', 'S3')"""
    all_datasets = project.list_datasets()
    return [ds for ds in all_datasets if ds['type'] == dataset_type]

# Usage
sql_datasets = get_datasets_by_type(project, "PostgreSQL")
file_datasets = get_datasets_by_type(project, "Filesystem")
s3_datasets = get_datasets_by_type(project, "S3")
```

---

## Getting a Dataset

### Basic Dataset Access

```python
project = client.get_project("MY_PROJECT")

# Get dataset handle
dataset = project.get_dataset("my_dataset")

# Now you can work with the dataset
schema = dataset.get_schema()
metadata = dataset.get_metadata()
```

### Check if Dataset Exists

```python
def dataset_exists(project, dataset_name):
    """Check if dataset exists in project"""
    try:
        project.get_dataset(dataset_name)
        return True
    except:
        return False

# Usage
if dataset_exists(project, "customers"):
    dataset = project.get_dataset("customers")
else:
    print("Dataset does not exist")
```

---

## Creating Datasets

### Create SQL Dataset

```python
# Create PostgreSQL dataset
dataset = project.create_dataset(
    dataset_name="customers",
    type="PostgreSQL",
    params={
        "connection": "my_postgres_connection",
        "mode": "table",
        "table": "public.customers",
        "schema": "public"
    },
    formatType=None,  # Not needed for SQL
    formatParams=None
)

print(f"✓ Created SQL dataset: customers")
```

### Create Filesystem (CSV) Dataset

```python
# Create CSV dataset in managed folder
dataset = project.create_dataset(
    dataset_name="sales_data",
    type="Filesystem",
    params={
        "connection": "filesystem_managed",
        "path": "/sales/sales_data.csv"
    },
    formatType="csv",
    formatParams={
        "separator": ",",
        "quoteChar": "\"",
        "escapeChar": "\\",
        "skipRowsBeforeHeader": 0,
        "parseHeaderRow": True,
        "encoding": "utf8"
    }
)

print(f"✓ Created CSV dataset: sales_data")
```

### Create S3 Dataset

```python
# Create dataset from S3
dataset = project.create_dataset(
    dataset_name="s3_orders",
    type="S3",
    params={
        "connection": "my_s3_connection",
        "path": "/bucket-name/orders/*.parquet",
        "bucket": "my-bucket"
    },
    formatType="parquet",
    formatParams={}
)

print(f"✓ Created S3 dataset: s3_orders")
```

### Create Upload Dataset (Manual Upload)

```python
# Create empty upload dataset
dataset = project.create_upload_dataset("uploaded_data")

# Upload file to it
with open("local_file.csv", "rb") as f:
    dataset.upload_file(f, "data.csv")

print(f"✓ Created and uploaded to dataset: uploaded_data")
```

### Comprehensive Dataset Creator

```python
def create_dataset_from_config(project, config):
    """
    Create dataset from configuration dict

    Config example:
    {
        "name": "my_dataset",
        "type": "PostgreSQL",
        "connection": "my_postgres",
        "table": "public.users",
        "schema": "public"
    }
    """

    dataset_type = config['type']

    if dataset_type in ['PostgreSQL', 'MySQL', 'Snowflake', 'Redshift']:
        # SQL dataset
        params = {
            "connection": config['connection'],
            "mode": "table",
            "table": config['table']
        }
        if 'schema' in config:
            params['schema'] = config['schema']

        dataset = project.create_dataset(
            dataset_name=config['name'],
            type=dataset_type,
            params=params
        )

    elif dataset_type == 'Filesystem':
        # File dataset
        params = {
            "connection": config.get('connection', 'filesystem_managed'),
            "path": config['path']
        }

        dataset = project.create_dataset(
            dataset_name=config['name'],
            type="Filesystem",
            params=params,
            formatType=config.get('format', 'csv'),
            formatParams=config.get('format_params', {})
        )

    elif dataset_type == 'S3':
        # S3 dataset
        params = {
            "connection": config['connection'],
            "path": config['path'],
            "bucket": config['bucket']
        }

        dataset = project.create_dataset(
            dataset_name=config['name'],
            type="S3",
            params=params,
            formatType=config.get('format', 'csv'),
            formatParams=config.get('format_params', {})
        )
    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")

    return dataset

# Usage
config = {
    "name": "customers",
    "type": "PostgreSQL",
    "connection": "my_postgres",
    "table": "public.customers",
    "schema": "public"
}

dataset = create_dataset_from_config(project, config)
```

---

## Dataset Schema

### Get Dataset Schema

```python
dataset = project.get_dataset("customers")

# Get schema
schema = dataset.get_schema()

print(f"Columns in {dataset.name}:")
for col in schema['columns']:
    print(f"  - {col['name']}: {col['type']}")
    if col.get('comment'):
        print(f"    Comment: {col['comment']}")
```

### Set Dataset Schema

```python
# Define new schema
new_schema = {
    "columns": [
        {"name": "id", "type": "bigint"},
        {"name": "customer_name", "type": "string", "maxLength": 100},
        {"name": "email", "type": "string"},
        {"name": "created_at", "type": "date"},
        {"name": "total_orders", "type": "int"},
        {"name": "lifetime_value", "type": "double"}
    ],
    "userModified": True
}

# Set schema
dataset.set_schema(new_schema)

print("✓ Schema updated")
```

### Add Column to Schema

```python
def add_column_to_schema(dataset, column_name, column_type, comment=None):
    """Add a new column to dataset schema"""

    # Get current schema
    schema = dataset.get_schema()

    # Check if column already exists
    existing_cols = [c['name'] for c in schema['columns']]
    if column_name in existing_cols:
        print(f"Column {column_name} already exists")
        return

    # Add new column
    new_col = {"name": column_name, "type": column_type}
    if comment:
        new_col['comment'] = comment

    schema['columns'].append(new_col)
    schema['userModified'] = True

    # Save schema
    dataset.set_schema(schema)
    print(f"✓ Added column {column_name}")

# Usage
add_column_to_schema(dataset, "last_purchase_date", "date", "Date of most recent purchase")
```

---

## Reading Data

### Iterate Rows (Recommended for Large Datasets)

```python
dataset = project.get_dataset("customers")

# Iterate through rows (memory efficient)
count = 0
for row in dataset.iter_rows():
    count += 1
    print(f"Row {count}: {row}")

    if count >= 10:  # Limit for demo
        break

print(f"Dataset has at least {count} rows")
```

### Get Data as Pandas DataFrame

```python
import pandas as pd

dataset = project.get_dataset("customers")

# Get all data as DataFrame (use with caution on large datasets!)
df = dataset.get_dataframe()

print(f"Loaded {len(df)} rows")
print(df.head())
print(df.info())
```

### Get Limited Rows

```python
# Get first N rows
dataset = project.get_dataset("customers")

rows = []
for i, row in enumerate(dataset.iter_rows()):
    rows.append(row)
    if i >= 999:  # Get first 1000 rows
        break

df = pd.DataFrame(rows)
print(f"Sampled {len(df)} rows")
```

### Read Partitioned Data

```python
# Get specific partition
dataset = project.get_dataset("sales_by_date")

# List partitions
partitions = dataset.list_partitions()
print(f"Available partitions: {partitions}")

# Read specific partition
partition_id = "2023-11-21"
df = dataset.get_dataframe(partition=partition_id)

print(f"Partition {partition_id}: {len(df)} rows")
```

---

## Writing Data

### Write Pandas DataFrame

```python
import pandas as pd

# Create sample data
df = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "value": [100.5, 200.3, 150.7]
})

# Get dataset
dataset = project.get_dataset("output_data")

# Write DataFrame
with dataset.get_writer() as writer:
    writer.write_dataframe(df)

print("✓ Data written to dataset")
```

### Append vs Overwrite

```python
# Overwrite dataset (clear and write)
dataset.clear()
with dataset.get_writer() as writer:
    writer.write_dataframe(df)

# Or write with schema inference
dataset.write_with_schema(df)
```

### Write with Partitioning

```python
# Write to specific partition
partition_id = "2023-11-21"

with dataset.get_writer(partition=partition_id) as writer:
    writer.write_dataframe(df)

print(f"✓ Written to partition {partition_id}")
```

### Bulk Upload from File

```python
# Upload CSV file
with open("data.csv", "rb") as f:
    dataset.upload_file(f, "data.csv")

# Trigger data detection (for upload datasets)
dataset.autodetect_settings()
```

---

## Dataset Settings

### Get and Modify Settings

```python
dataset = project.get_dataset("customers")

# Get settings object
settings = dataset.get_settings()

# View raw settings
print(settings.settings)

# Modify settings
settings.settings['description'] = "Customer master data"

# Save
settings.save()
```

### Configure Partitioning

```python
dataset = project.get_dataset("sales_by_date")
settings = dataset.get_settings()

# Add time partitioning
settings.add_discrete_partitioning_dimension("date")

# Save
settings.save()

print("✓ Partitioning configured")
```

### Set Format Parameters (CSV)

```python
dataset = project.get_dataset("csv_data")
settings = dataset.get_settings()

# Get format params
format_params = settings.get_raw()['params'].get('formatParams', {})

# Modify CSV settings
format_params['separator'] = '|'
format_params['quoteChar'] = '"'
format_params['escapeChar'] = '\\'

# Save
settings.save()
```

---

## Building Datasets

### Simple Build (Synchronous)

```python
dataset = project.get_dataset("output_dataset")

# Build and wait for completion
job = dataset.build(wait=True)

print(f"✓ Build complete. Job ID: {job.id}")
```

### Build Asynchronously

```python
dataset = project.get_dataset("large_dataset")

# Start build (non-blocking)
job = dataset.build(wait=False)

print(f"Started job {job.id}")

# Do other work...

# Check status later
status = job.get_status()
if status['baseStatus']['state'] == 'DONE':
    print("✓ Build complete")
else:
    print(f"Build status: {status['baseStatus']['state']}")
```

### Build with Job Monitoring

```python
import time

dataset = project.get_dataset("output_dataset")

# Start build
job = dataset.build(wait=False)

print(f"Building dataset... Job ID: {job.id}")

# Monitor progress
while True:
    status = job.get_status()
    state = status['baseStatus']['state']

    print(f"Status: {state}", end='\r')

    if state in ['DONE', 'FAILED', 'ABORTED']:
        break

    time.sleep(2)

print()  # New line

if state == 'DONE':
    print("✓ Build successful")
else:
    print(f"❌ Build {state}")
    # Get logs
    log = job.get_log()
    print("Error log:")
    print(log)
```

### Build Specific Partition

```python
# Build single partition
dataset = project.get_dataset("partitioned_data")

job = dataset.build(
    partition="2023-11-21",
    wait=True
)

print("✓ Partition built")
```

### Force Rebuild

```python
# Force rebuild (ignore up-to-date checks)
job = dataset.build(
    job_type="NON_RECURSIVE_FORCED_BUILD",
    wait=True
)
```

---

## Dataset Metadata

### Get Metadata

```python
dataset = project.get_dataset("customers")

# Get metadata
metadata = dataset.get_metadata()

print(f"Name: {metadata.get('name')}")
print(f"Label: {metadata.get('label')}")
print(f"Description: {metadata.get('description')}")
print(f"Tags: {metadata.get('tags', [])}")
print(f"Custom metadata: {metadata.get('custom', {})}")
```

### Set Metadata

```python
# Set description and tags
dataset.set_metadata({
    "label": "Customer Master Data",
    "description": "Contains all customer information from CRM",
    "tags": ["customer", "master-data", "production"],
    "custom": {
        "data_owner": "sales_team",
        "refresh_frequency": "daily",
        "pii_data": "true"
    }
})

print("✓ Metadata updated")
```

### Add Tags

```python
def add_tags(dataset, *tags):
    """Add tags to dataset"""
    metadata = dataset.get_metadata()
    current_tags = set(metadata.get('tags', []))
    current_tags.update(tags)
    metadata['tags'] = list(current_tags)
    dataset.set_metadata(metadata)

# Usage
add_tags(dataset, "production", "verified", "customer-data")
```

---

## Dataset Statistics

### Get Last Build Info

```python
dataset = project.get_dataset("customers")

# Get last build info
try:
    metadata = dataset.get_metadata()
    last_build = metadata.get('lastBuild', {})

    print(f"Last built: {last_build.get('endTime', 'Never')}")
    print(f"Build state: {last_build.get('state', 'Unknown')}")
    print(f"Record count: {metadata.get('recordCount', 'Unknown')}")
except:
    print("No build information available")
```

### Compute Metrics

```python
# Compute dataset metrics
dataset.compute_metrics()

# Get metrics
metrics = dataset.get_last_metric_values()

for metric_id, metric_value in metrics.get('metrics', {}).items():
    print(f"{metric_id}: {metric_value.get('lastValues', [{}])[0].get('value')}")
```

---

## Copying and Clearing Datasets

### Copy Dataset

```python
source = project.get_dataset("source_data")
target = project.get_dataset("target_data")

# Copy data from source to target
job = source.copy_to(target.name)
job_result = job.wait_for_result()

print(f"✓ Copied {source.name} to {target.name}")
```

### Clear Dataset

```python
dataset = project.get_dataset("temp_data")

# Clear all data
dataset.clear()

print("✓ Dataset cleared")
```

### Clear Specific Partition

```python
dataset = project.get_dataset("partitioned_data")

# Clear one partition
dataset.clear(partition="2023-11-21")

print("✓ Partition cleared")
```

---

## Dataset Deletion

### Delete Dataset

```python
project = client.get_project("MY_PROJECT")

# Get dataset
dataset = project.get_dataset("old_dataset")

# Delete it
dataset.delete()

print("✓ Dataset deleted")
```

### Safe Delete with Dependency Check

```python
def safe_delete_dataset(project, dataset_name):
    """Delete dataset after checking dependencies"""

    dataset = project.get_dataset(dataset_name)

    # Check if dataset is used in flow
    flow = project.get_flow()
    graph = flow.get_graph()

    # Find datasets that depend on this one
    downstream = []
    for node in graph.get('nodes', []):
        if node.get('type') == 'COMPUTABLE_DATASET':
            # Check if this dataset is an input
            recipe_inputs = node.get('predecessors', [])
            if dataset_name in [i.get('ref') for i in recipe_inputs]:
                downstream.append(node.get('id'))

    if downstream:
        print(f"❌ Cannot delete {dataset_name}")
        print(f"   Used by: {downstream}")
        return False

    # No dependencies, safe to delete
    dataset.delete()
    print(f"✓ Deleted {dataset_name}")
    return True

# Usage
safe_delete_dataset(project, "old_dataset")
```

---

## Working with Managed Folders

Managed folders are like datasets but for unstructured data (files).

### Create Managed Folder

```python
# Create managed folder
folder = project.create_managed_folder("my_folder")

print(f"✓ Created managed folder: my_folder")
```

### Upload File to Managed Folder

```python
folder = project.get_managed_folder("my_folder")

# Upload file
with open("local_file.txt", "rb") as f:
    folder.put_file("/remote_path/file.txt", f)

print("✓ File uploaded")
```

### Download File from Managed Folder

```python
folder = project.get_managed_folder("my_folder")

# Download file
with folder.get_file("/remote_path/file.txt") as remote_file:
    with open("downloaded_file.txt", "wb") as local_file:
        local_file.write(remote_file.read())

print("✓ File downloaded")
```

### List Files in Managed Folder

```python
folder = project.get_managed_folder("my_folder")

# List all files
files = folder.list_contents()

print("Files in folder:")
for file in files:
    print(f"  - {file['path']} ({file.get('size', 0)} bytes)")
```

---

## Common Dataset Patterns

### Pattern: ETL - Extract, Transform, Load

```python
def etl_pipeline(project, source_name, target_name, transform_func):
    """Simple ETL pattern"""

    # Extract
    source = project.get_dataset(source_name)
    df = source.get_dataframe()
    print(f"Extracted {len(df)} rows from {source_name}")

    # Transform
    df_transformed = transform_func(df)
    print(f"Transformed to {len(df_transformed)} rows")

    # Load
    target = project.get_dataset(target_name)
    target.clear()
    with target.get_writer() as writer:
        writer.write_dataframe(df_transformed)

    print(f"✓ Loaded {len(df_transformed)} rows to {target_name}")

# Usage
def my_transform(df):
    # Example transformation
    return df[df['value'] > 100]

etl_pipeline(project, "raw_data", "processed_data", my_transform)
```

### Pattern: Incremental Load

```python
import pandas as pd
from datetime import datetime, timedelta

def incremental_load(project, source_name, target_name, date_column):
    """Load only new/updated records"""

    source = project.get_dataset(source_name)
    target = project.get_dataset(target_name)

    # Get last load timestamp
    try:
        target_metadata = target.get_metadata()
        last_load = target_metadata.get('custom', {}).get('last_load_timestamp')
        if last_load:
            last_load = pd.to_datetime(last_load)
        else:
            last_load = datetime(1900, 1, 1)
    except:
        last_load = datetime(1900, 1, 1)

    # Get new/updated records
    source_df = source.get_dataframe()
    source_df[date_column] = pd.to_datetime(source_df[date_column])
    new_records = source_df[source_df[date_column] > last_load]

    if len(new_records) == 0:
        print("No new records to load")
        return

    # Append to target
    target_df = target.get_dataframe()
    combined = pd.concat([target_df, new_records], ignore_index=True)

    # Write back
    target.clear()
    with target.get_writer() as writer:
        writer.write_dataframe(combined)

    # Update last load timestamp
    target.set_metadata({
        "custom": {
            "last_load_timestamp": datetime.now().isoformat()
        }
    })

    print(f"✓ Loaded {len(new_records)} new records")

# Usage
incremental_load(project, "source_orders", "target_orders", "order_date")
```

---

## Common Gotchas

### 1. Large Datasets and Memory

```python
# ❌ WRONG - Will load entire dataset into memory!
df = dataset.get_dataframe()

# ✓ BETTER - Iterate for large datasets
for row in dataset.iter_rows():
    process_row(row)

# ✓ BEST - Use recipes for large transformations (let DSS handle it)
# Create a recipe instead of loading into Python
```

### 2. Schema Must Be Set Before Writing

```python
# ❌ May fail if schema doesn't match
with dataset.get_writer() as writer:
    writer.write_dataframe(df)

# ✓ Better - Set schema first or use write_with_schema
dataset.write_with_schema(df)
```

### 3. Always Save Settings

```python
# ❌ WRONG - Changes not saved
settings = dataset.get_settings()
settings.settings['description'] = "New description"

# ✓ CORRECT
settings = dataset.get_settings()
settings.settings['description'] = "New description"
settings.save()
```

### 4. Build May Fail if Source Not Ready

```python
# Always check dependencies first
def safe_build(dataset):
    try:
        job = dataset.build(wait=True)
        return True
    except Exception as e:
        print(f"Build failed: {e}")
        # Check if source datasets are ready
        # Fix issues and retry
        return False
```

---

## Next Steps

- **05-recipe-workflows.md** - Creating and managing recipes
- **06-scenario-automation.md** - Automating dataset builds
- **08-common-gotchas.md** - More troubleshooting

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
