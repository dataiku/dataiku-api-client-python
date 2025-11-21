# 07 - ML Workflows

**Audience:** Claude Code sessions working with Dataiku Python API
**Purpose:** Working with machine learning tasks, models, and deployments

---

## Machine Learning in Dataiku

Dataiku provides:
- **Visual ML** - AutoML interface for classification, regression, clustering
- **ML Tasks** - Configurable training tasks
- **Saved Models** - Versioned trained models
- **API Services** - Deploy models as REST endpoints

**Key Objects:**
- `DSSMLTask` - ML training configuration and execution
- `DSSSavedModel` - Saved model versions
- `DSSModelEvaluationStore` - Model performance tracking

---

## Listing ML Tasks

```python
from dataikuapi import DSSClient

client = DSSClient(host, api_key)
project = client.get_project("MY_PROJECT")

# List ML tasks
ml_tasks = project.list_ml_tasks()

print(f"Found {len(ml_tasks)} ML tasks:")
for task in ml_tasks:
    print(f"  - {task['name']} ({task['taskType']})")
```

---

## Getting an ML Task

```python
# Get ML task
ml_task = project.get_ml_task("predict_churn")

# Get settings
settings = ml_task.get_settings()
print(f"Task type: {settings.settings.get('taskType')}")
print(f"Target variable: {settings.settings.get('targetVariable')}")
```

---

## Training Models

### Train a Model

```python
ml_task = project.get_ml_task("predict_churn")

# Start training
train_result = ml_task.train()

print(f"Training started: {train_result}")

# Wait for training to complete (may take a while)
# Training runs asynchronously
```

### Check Training Status

```python
# Get trained models
trained_models = ml_task.get_trained_models_details()

print(f"Found {len(trained_models)} trained models:")
for model in trained_models:
    print(f"  - {model['userMeta']['name']}")
    print(f"    Algorithm: {model['algorithm']}")
    print(f"    Score: {model.get('perf', {})}")
```

---

## Saved Models

### List Saved Models

```python
# List all saved models in project
saved_models = project.list_saved_models()

print(f"Found {len(saved_models)} saved models:")
for sm in saved_models:
    print(f"  - {sm['id']}")
```

### Get Saved Model

```python
saved_model = project.get_saved_model("saved_model_id")

# List versions
versions = saved_model.list_versions()

print(f"Model has {len(versions)} versions:")
for version in versions:
    print(f"  - {version['id']} (created: {version.get('snippet', {}).get('created')})")
```

### Get Active Version

```python
saved_model = project.get_saved_model("saved_model_id")

# Get active version details
active_version = saved_model.get_active_version()

print(f"Active version: {active_version.get('versionId')}")
print(f"Algorithm: {active_version.get('algorithm')}")
```

---

## Model Deployment

### Deploy to API Service

```python
# Create API service from saved model
saved_model = project.get_saved_model("churn_model")

# Create service
service = project.create_api_service("churn_prediction_api")

# Get service settings
settings = service.get_settings()

# Configure to use the saved model
settings.settings['endpoints'] = [{
    "id": "predict_churn",
    "type": "STD_PREDICTION",
    "modelRef": "churn_model"
}]

settings.save()

print("✓ API service created and configured")
```

---

## Working with Analysis

### Create Visual Analysis

```python
# Create analysis (for visual ML)
analysis = project.create_analysis(
    "customer_analysis",
    "customers_dataset"
)

print("✓ Analysis created")
```

### Get Analysis

```python
analysis = project.get_analysis("customer_analysis")

# Get ML tasks in the analysis
ml_tasks = analysis.list_ml_tasks()
print(f"Analysis has {len(ml_tasks)} ML tasks")
```

---

## Model Evaluation Store

### List Evaluation Stores

```python
# Model evaluation stores track model performance
stores = project.list_model_evaluation_stores()

print(f"Found {len(stores)} evaluation stores:")
for store in stores:
    print(f"  - {store['id']}")
```

### Get Evaluation Metrics

```python
# Get evaluation store
eval_store = project.get_model_evaluation_store("mes_id")

# Get evaluations
evaluations = eval_store.list_evaluations()

for ev in evaluations:
    print(f"Evaluation: {ev.get('id')}")
    print(f"  Model: {ev.get('modelRef')}")
    print(f"  Metrics: {ev.get('metrics')}")
```

---

## Complete ML Pipeline Example

```python
def create_ml_pipeline(project, dataset_name, target_column, model_name):
    """
    Create complete ML pipeline:
    1. Create analysis
    2. Create ML task
    3. Train model
    4. Save model
    5. Deploy as API service
    """

    print("Step 1: Creating analysis...")
    analysis = project.create_analysis(
        f"{model_name}_analysis",
        dataset_name
    )

    print("Step 2: Creating ML task...")
    # ML tasks are created through the visual interface or
    # by configuring analysis settings

    # For programmatic creation, you typically:
    # - Create analysis
    # - Configure via UI or complex settings
    # - Train via API

    print("Step 3: Training model...")
    # Assuming ML task exists
    ml_task = project.get_ml_task(f"{model_name}_task")

    # Get settings
    settings = ml_task.get_settings()

    # Configure target
    settings.settings['targetVariable'] = target_column
    settings.settings['taskType'] = 'PREDICTION'
    settings.settings['predictionType'] = 'BINARY_CLASSIFICATION'

    # Configure train/test split
    settings.settings['splitParams'] = {
        "ttPolicy": "SPLIT_SINGLE_DATASET",
        "kfold": False,
        "ssdSplitMode": "RANDOM",
        "ssdTrainingRatio": 0.8,
        "ssdSelection": {
            "filter": {},
            "samplingMethod": "HEAD_SEQUENTIAL"
        }
    }

    # Save settings
    settings.save()

    # Train
    train_result = ml_task.train()
    print(f"  Training started: {train_result}")

    # Note: Training is async, need to wait/check later

    print("✓ ML pipeline configured")

# Usage
create_ml_pipeline(
    project,
    dataset_name="customers",
    target_column="will_churn",
    model_name="churn_prediction"
)
```

---

## Common Patterns

### Model Versioning

```python
def deploy_new_model_version(project, saved_model_id, new_version_id):
    """Deploy a new version of a model"""

    saved_model = project.get_saved_model(saved_model_id)

    # Set new active version
    saved_model.set_active_version(new_version_id)

    print(f"✓ Activated version {new_version_id}")

# Usage
deploy_new_model_version(project, "churn_model", "v_20231121_001")
```

### Model A/B Testing

```python
def setup_ab_test(project, model_a_id, model_b_id, traffic_split=0.5):
    """
    Setup A/B test for two models
    Note: Actual A/B testing requires API node configuration
    """

    # Get both models
    model_a = project.get_saved_model(model_a_id)
    model_b = project.get_saved_model(model_b_id)

    print(f"Setting up A/B test:")
    print(f"  Model A: {model_a_id} ({traffic_split * 100}% traffic)")
    print(f"  Model B: {model_b_id} ({(1-traffic_split) * 100}% traffic)")

    # Actual implementation requires API node configuration
    # This would be done through deployment settings
```

---

## Common Gotchas

### 1. Training is Asynchronous

```python
# ❌ Model not immediately available
ml_task.train()
trained_models = ml_task.get_trained_models_details()  # May be empty!

# ✓ Need to wait for training to complete
ml_task.train()
# Wait some time, then check
import time
time.sleep(60)  # Wait for training
trained_models = ml_task.get_trained_models_details()
```

### 2. Saved Model ID vs ML Task Name

```python
# These are different!
ml_task = project.get_ml_task("my_task")  # ML Task name
saved_model = project.get_saved_model("sm_123")  # Saved Model ID (generated)
```

### 3. Must Configure Before Training

```python
# ❌ Training may fail without proper configuration
ml_task.train()

# ✓ Configure settings first
settings = ml_task.get_settings()
settings.settings['targetVariable'] = 'target'
settings.settings['taskType'] = 'PREDICTION'
settings.save()
ml_task.train()
```

---

## Next Steps

- **08-common-gotchas.md** - Comprehensive troubleshooting guide
- **99-quick-reference.md** - Quick lookup for common operations

---

**Last Updated:** 2025-11-21
**API Version:** 14.1.3+
