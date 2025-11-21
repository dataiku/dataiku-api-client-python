# DATAIKU PYTHON API - QUICK CLASS REFERENCE

## Main Entry Point Classes (7 classes)

| Class | Module | Purpose |
|-------|--------|---------|
| `DSSClient` | dssclient.py | Main DSS instance client (114 methods) |
| `GovernClient` | govern_client.py | Govern governance & compliance (48 methods) |
| `FMClientAWS` | fmclient.py | AWS Fleet Management (5 methods + inherited) |
| `FMClientAzure` | fmclient.py | Azure Fleet Management (5 methods + inherited) |
| `FMClientGCP` | fmclient.py | GCP Fleet Management (4 methods + inherited) |
| `APINodeClient` | apinode_client.py | API endpoint predictions (9 methods) |
| `APINodeAdminClient` | apinode_admin_client.py | API node administration (11 methods) |

---

## Project-Level Classes (1 major class)

| Class | Methods | Purpose |
|-------|---------|---------|
| `DSSProject` | 154 | Main project handle; access all project objects |

---

## Dataset & Data Classes (15 classes)

| Class | Purpose |
|-------|---------|
| `DSSDataset` | Access dataset definition, schema, data read/write |
| `DSSDatasetListItem` | Lightweight dataset list item |
| `DSSDatasetSettings` | Dataset configuration wrapper |
| `DSSManagedDatasetCreationHelper` | Helper for creating managed datasets |
| `DSSDatasetInfo` | Metadata about dataset |
| `DSSManagedFolder` | File/folder storage in DSS |
| `DSSManagedFolderListItem` | Lightweight managed folder item |
| `FSLikeDatasetSettings` | Settings for filesystem datasets |
| `SQLDatasetSettings` | Settings for SQL datasets |
| `DSSDataCollection` | Data collection grouping |
| `DSSDataCollectionListItem` | Lightweight data collection item |
| `DSSDataCollectionSettings` | Data collection configuration |
| `DSSDataCollectionItem` | Item within collection |
| `DSSDataCollectionPermissionItem` | Permission for collection |

---

## Workflow & Automation Classes (18 classes)

| Class | Purpose |
|-------|---------|
| `DSSRecipe` | Data transformation recipe |
| `DSSRecipeListItem` | Lightweight recipe item |
| `DSSRecipeSettings` | Recipe configuration |
| `DSSScenario` | Workflow scenario orchestration |
| `DSSScenarioListItem` | Lightweight scenario item |
| `DSSScenarioSettings` | Scenario configuration |
| `DSSScenarioRun` | Single scenario execution |
| `DSSTestingStatus` | Scenario testing status |
| `DSSJob` | Scheduled/running job |
| `DSSJobWaiter` | Wait for job completion |
| `DSSFuture` | Long-running async operation |
| `DSSContinuousActivity` | Continuous data activity |
| `JobDefinitionBuilder` | Builder for job definitions |
| `TablesImportDefinition` | Builder for table imports |
| `TablesPreparedImport` | Prepared table import |

---

## Analytics & Visualization Classes (12 classes)

| Class | Purpose |
|-------|---------|
| `DSSDashboard` | Analytics dashboard |
| `DSSDashboardListItem` | Lightweight dashboard item |
| `DSSDashboardSettings` | Dashboard configuration |
| `DSSInsight` | Single visualization/insight |
| `DSSInsightListItem` | Lightweight insight item |
| `DSSAnalysis` | Data analysis workspace |
| `DSSWebApp` | Interactive web application |
| `DSSWebAppListItem` | Lightweight webapp item |
| `DSSWebAppBackend` | Webapp backend handler |
| `DSSWebAppSettings` | Webapp configuration |

---

## Machine Learning Classes (20 classes)

| Class | Purpose |
|-------|---------|
| `DSSMLTask` | Machine learning task |
| `DSSMLTaskListItem` | Lightweight ML task item |
| `DSSMLTaskSettings` | ML task configuration |
| `DSSMLTaskQueues` | ML task queue management |
| `DSSTrainedModel` | Trained ML model version |
| `DSSSavedModel` | Deployed saved model |
| `DSSSavedModelListItem` | Lightweight saved model item |
| `DSSSavedModelSettings` | Saved model configuration |
| `DSSSavedModelVersion` | Specific model version |
| `DSSModelComparison` | Model comparison interface |
| `DSSModelEvaluationStore` | Model evaluation storage |
| `DSSModelEvaluationStoreListItem` | Lightweight eval store item |
| `DSSMLflowExtension` | MLflow integration |
| `PluginDSSManagedFolderArtifactRepository` | MLflow artifact storage |

---

## Agent & Knowledge Classes (10 classes)

| Class | Purpose |
|-------|---------|
| `DSSAgent` | AI agent definition |
| `DSSAgentListItem` | Lightweight agent item |
| `DSSAgentTool` | Tool available to agents |
| `DSSAgentToolListItem` | Lightweight tool item |
| `DSSAgentToolCreator` | Builder for agent tools |
| `DSSAgentToolSettings` | Tool configuration |
| `DSSKnowledgeBank` | Knowledge base for LLMs |
| `DSSKnowledgeBankListItem` | Lightweight KB item |
| `DSSKnowledgeBankSettings` | KB configuration |
| `DSSRetrievalAugmentedLLM` | RAG LLM configuration |

---

## LLM & Language Classes (6 classes)

| Class | Purpose |
|-------|---------|
| `DSSLLM` | LLM configuration |
| `DSSLLMListItem` | Lightweight LLM item |
| `DSSRetrievalAugmentedLLM` | RAG LLM setup |
| `DSSRetrievalAugmentedLLMSettings` | RAG LLM config |
| `DSSRetrievalAugmentedLLMVersionSettings` | RAG version config |

---

## Notebook Classes (5 classes)

| Class | Purpose |
|-------|---------|
| `DSSNotebook` | Jupyter notebook in project |
| `DSSJupyterNotebook` | Full jupyter notebook handle |
| `DSSJupyterNotebookListItem` | Lightweight notebook item |
| `DSSSQLNotebook` | SQL notebook for queries |
| `DSSSQLNotebookListItem` | Lightweight SQL notebook item |

---

## API Service Classes (10 classes)

| Class | Purpose |
|-------|---------|
| `DSSAPIService` | Deployed API service |
| `DSSAPIServiceListItem` | Lightweight API service item |
| `DSSAPIServiceSettings` | API service configuration |
| `DSSAPIServiceVersion` | API service version |
| `DSSAPIDeployer` | API deployment manager |
| `DSSAPIDeployerInfra` | API infra configuration |
| `DSSAPIDeployerDeployment` | Single API deployment |
| `DSSAPIDeployerDeploymentStatus` | Deployment status |
| `DSSStreamingEndpoint` | Streaming API endpoint |
| `DSSStreamingEndpointListItem` | Lightweight endpoint item |

---

## Administration Classes (35 classes)

### User & Group Management
| Class | Purpose |
|-------|---------|
| `DSSUser` | User account handle |
| `DSSOwnUser` | Current user |
| `DSSUserSettings` | User configuration |
| `DSSUserSettingsBase` | Base user settings |
| `DSSUserPreferences` | User preferences |
| `DSSUserInfo` | User information (read-only) |
| `DSSUserActivity` | User activity log |
| `DSSGroup` | User group |
| `DSSGroupInfo` | Group information |
| `DSSUserImpersonationRule` | User impersonation config |
| `DSSGroupImpersonationRule` | Group impersonation config |

### API Keys
| Class | Purpose |
|-------|---------|
| `DSSGlobalApiKey` | Global API key |
| `DSSGlobalApiKeyListItem` | Lightweight API key item |
| `DSSPersonalApiKey` | Personal API key |
| `DSSPersonalApiKeyListItem` | Lightweight personal key item |

### Connections & Resources
| Class | Purpose |
|-------|---------|
| `DSSConnection` | Database/data source connection |
| `DSSConnectionListItem` | Lightweight connection item |
| `DSSConnectionSettings` | Connection configuration |
| `DSSConnectionDetailsReadability` | Connection access control |
| `DSSConnectionInfo` | Connection metadata |

### Code Environments
| Class | Purpose |
|-------|---------|
| `DSSCodeEnv` | Python/R code environment |
| `DSSCodeEnvSettings` | Code env configuration |
| `DSSDesignCodeEnvSettings` | Design node code env |
| `DSSAutomationCodeEnvSettings` | Automation node code env |
| `DSSCodeEnvContainerConfsBearer` | Container configuration |
| `DSSCodeEnvPackageListBearer` | Package list access |

### Clusters & Infrastructure
| Class | Purpose |
|-------|---------|
| `DSSCluster` | Compute cluster |
| `DSSClusterSettings` | Cluster configuration |
| `DSSClusterStatus` | Cluster status |
| `DSSCodeStudioTemplate` | Code studio template |
| `DSSCodeStudioTemplateListItem` | Lightweight template item |
| `DSSCodeStudioTemplateSettings` | Template configuration |

### Global Configuration
| Class | Purpose |
|-------|---------|
| `DSSGeneralSettings` | Instance general settings |
| `DSSInstanceVariables` | Instance-level variables |
| `DSSMeaning` | Custom data meaning |
| `DSSAuthorizationMatrix` | Permissions matrix |
| `DSSGlobalUsageSummary` | Instance usage statistics |
| `DSSLLMCostLimitingCounters` | LLM cost tracking |

---

## Governance Classes (40+ classes)

### Govern Clients
| Class | Purpose |
|-------|---------|
| `GovernClient` | Main Govern instance client |
| `GovernInstanceInfo` | Govern instance information |

### Govern Artifacts & Workflows
| Class | Purpose |
|-------|---------|
| `GovernArtifact` | Governed artifact |
| `GovernArtifactDefinition` | Artifact definition |
| `GovernArtifactSignoff` | Approval/signoff |
| `GovernArtifactSignoffDefinition` | Signoff definition |
| `GovernArtifactSignoffRecurrenceConfiguration` | Recurrence config |
| `GovernArtifactSignoffDetails` | Signoff details |
| `GovernArtifactSignoffFeedback` | Feedback on signoff |
| `GovernArtifactSignoffApproval` | Approval record |
| `GovernBlueprint` | Workflow blueprint |
| `GovernBlueprintVersion` | Blueprint version |

### Govern Administration
| Class | Purpose |
|-------|---------|
| `GovernUser` | Govern user |
| `GovernOwnUser` | Current Govern user |
| `GovernUserSettings` | User settings |
| `GovernUserInfo` | User info |
| `GovernUserActivity` | User activity |
| `GovernGroup` | Govern group |
| `GovernGroupInfo` | Group info |
| `GovernGlobalApiKey` | Govern API key |
| `GovernGeneralSettings` | Govern settings |
| `GovernAuthorizationMatrix` | Permissions |

---

## Fleet Management Classes (40+ classes)

### FMClient Base
| Class | Purpose |
|-------|---------|
| `FMClient` | Base FM client |
| `FMCloudCredentials` | Cloud credentials config |
| `FMCloudTags` | Cloud resource tags |

### Instances (VM) Classes
| Class | Purpose |
|-------|---------|
| `FMInstance` | Cloud VM instance |
| `FMAWSInstance` | AWS EC2 instance |
| `FMAzureInstance` | Azure VM instance |
| `FMGCPInstance` | GCP Compute instance |
| `FMInstanceCreator` | VM creation builder |
| `FMAWSInstanceCreator` | AWS VM creator |
| `FMAzureInstanceCreator` | Azure VM creator |
| `FMGCPInstanceCreator` | GCP VM creator |
| `FMSnapshot` | VM snapshot |
| `FMInstanceStatus` | VM status info |
| `FMNodeType` | DSS node type enum |
| `FMInstanceEncryptionMode` | Encryption enum |

### Virtual Networks
| Class | Purpose |
|-------|---------|
| `FMVirtualNetwork` | Virtual network |
| `FMAWSVirtualNetwork` | AWS VPC |
| `FMAzureVirtualNetwork` | Azure vnet |
| `FMGCPVirtualNetwork` | GCP network |
| `FMVirtualNetworkCreator` | Network creator |
| `FMAWSVirtualNetworkCreator` | AWS VPC creator |
| `FMAzureVirtualNetworkCreator` | Azure vnet creator |
| `FMGCPVirtualNetworkCreator` | GCP network creator |
| `FMHTTPSStrategy` | HTTPS configuration |

### Load Balancers
| Class | Purpose |
|-------|---------|
| `FMLoadBalancer` | Load balancer |
| `FMAWSLoadBalancer` | AWS load balancer |
| `FMAzureLoadBalancer` | Azure load balancer |
| `FMLoadBalancerCreator` | LB creator |
| `FMAWSLoadBalancerCreator` | AWS LB creator |
| `FMAzureLoadBalancerCreator` | Azure LB creator |
| `FMLoadBalancerPhysicalStatus` | LB status |

### Cloud Accounts & Templates
| Class | Purpose |
|-------|---------|
| `FMCloudAccount` | Cloud account credentials |
| `FMAWSCloudAccount` | AWS account |
| `FMAzureCloudAccount` | Azure account |
| `FMGCPCloudAccount` | GCP account |
| `FMCloudAccountCreator` | Account creator |
| `FMInstanceSettingsTemplate` | VM template |
| `FMInstanceSettingsTemplateCreator` | Template creator |
| `FMSetupAction` | Setup action config |
| `FMSnapshot` | VM snapshot |

---

## Utility Classes (20+ classes)

| Class | Purpose |
|-------|---------|
| `DSSBaseClient` | Base HTTP client |
| `DSSFuture` | Async operation handle |
| `DSSPermissionsCheckRequest` | Permission checker |
| `TemporaryImportHandle` | Temporary import handle |
| `DSSInstanceInfo` | Instance metadata |
| `DSSObjectDiscussions` | Comment threads |
| `DSSProjectFolder` | Project folder |
| `DSSProjectFolderSettings` | Folder settings |
| `DSSProjectSettings` | Project settings |
| `DSSProjectGit` | Git integration |
| `DSSProjectFlow` | Project data flow |
| `DSSWiki` | Project wiki |
| `DSSWorkspace` | Workspace container |
| `DSSMacro` | Code macro |
| `DSSPlugin` | Plugin handle |
| `DSSApp` | DSS App/template |
| `DSSSQLQuery` | SQL query builder |
| `DSSLabelingTask` | Labeling task |
| `DSSDocumentExtractor` | Document extraction |
| `DSSUnifiedMonitoring` | Monitoring dashboard |
| `DSSProjectDeployer` | Project deployment |
| `DSSProjectStandards` | Project standards |
| `DSSInfoMessages` | Messages container |
| `DSSFeatureStore` | Feature store manager |
| `HTTPBearerAuth` | Bearer auth handler |

---

## Taggable Objects (Have tag/owner/description methods)

- `DSSDataset`
- `DSSRecipe`
- `DSSSavedModel`
- `DSSManagedFolder`
- `DSSScenario`
- `DSSDashboard`
- `DSSInsight`
- `DSSMLTask`
- `DSSWebApp`
- `DSSJupyterNotebook`
- `DSSKnowledgeBank`
- `DSSLLM`
- `DSSAgent`
- `DSSAgentTool`
- `DSSRetrievalAugmentedLLM`
- `DSSSQLNotebook`
- `DSSStreamingEndpoint`

---

## Total Classes Summary

| Category | Count |
|----------|-------|
| Main Clients | 7 |
| Project-Level | 1 |
| Dataset Classes | 15 |
| Workflow Classes | 18 |
| Analytics Classes | 12 |
| ML Classes | 20 |
| Agent/Knowledge Classes | 10 |
| LLM Classes | 6 |
| Notebook Classes | 5 |
| API Service Classes | 10 |
| Administration Classes | 35 |
| Governance Classes | 40+ |
| Fleet Management Classes | 40+ |
| Utility Classes | 20+ |
| **TOTAL** | **150+** |

---

## Quick Navigation by Use Case

### I want to work with datasets
Start with: `DSSClient.get_project() → DSSProject.get_dataset()`
Classes: DSSDataset, DSSDatasetSettings, DSSDatasetListItem, DSSManagedDatasetCreationHelper

### I want to create a data pipeline
Start with: `DSSClient.get_project() → DSSProject.create_recipe()`
Classes: DSSRecipe, DSSScenario, DSSFuture, JobDefinitionBuilder

### I want to train ML models
Start with: `DSSClient.get_project() → DSSProject.get_ml_task()`
Classes: DSSMLTask, DSSTrainedModel, DSSSavedModel, DSSModelEvaluationStore

### I want to create dashboards
Start with: `DSSClient.get_project() → DSSProject.get_dashboard()` or `.create_dashboard()`
Classes: DSSDashboard, DSSInsight, DSSInsightListItem, DSSDashboardSettings

### I want to manage users
Start with: `DSSClient.create_user()` or `.get_user()`
Classes: DSSUser, DSSUserSettings, DSSGroup, DSSAuthorizationMatrix

### I want to manage connections
Start with: `DSSClient.get_connection()` or `.create_connection()`
Classes: DSSConnection, DSSConnectionSettings, DSSConnectionInfo

### I want to manage code environments
Start with: `DSSClient.get_code_env()` or `.create_code_env()`
Classes: DSSCodeEnv, DSSCodeEnvSettings, DSSCodeEnvContainerConfsBearer

### I want to deploy models to API
Start with: `DSSClient.get_apideployer()`
Classes: DSSAPIDeployer, DSSAPIDeployerDeployment, DSSAPIService, DSSStreamingEndpoint

### I want to manage projects
Start with: `DSSClient.get_project()` or `.create_project()`
Classes: DSSProject, DSSProjectSettings, DSSProjectFolder, DSSProjectGit

### I want to use governance features
Start with: `DSSClient.get_govern_client()` → `GovernClient`
Classes: GovernArtifact, GovernBlueprint, GovernArtifactSignoff

### I want to manage cloud infrastructure
Start with: `FMClientAWS()` or `FMClientAzure()` or `FMClientGCP()`
Classes: FMInstance, FMVirtualNetwork, FMLoadBalancer, FMCloudAccount

