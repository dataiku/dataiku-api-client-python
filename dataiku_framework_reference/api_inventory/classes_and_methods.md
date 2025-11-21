# DATAIKU PYTHON API CLIENT - COMPREHENSIVE INVENTORY

## Executive Summary

The Dataiku Python API client provides comprehensive programmatic access to Dataiku DSS (Data Science Studio), Govern, and Fleet Management (FM) platforms. The API is organized into multiple client classes with clear separation of concerns:

- **DSSClient**: Main entry point for DSS (Design/Automation Node) operations
- **GovernClient**: Access to Dataiku Govern governance and compliance features  
- **FMClient (AWS/Azure/GCP)**: Fleet Management for cloud infrastructure
- **APINodeClient**: Client for managed API services
- **APINodeAdminClient**: Administrative operations for API nodes

---

## PART 1: MAIN CLIENT CLASSES AND CAPABILITIES

### 1.1 DSSClient - Core DSS Operations (114 public methods)

**Entry Point**: `from dataikuapi import DSSClient`

**Initialization**:
```python
client = DSSClient(
    host="http://localhost:11200",
    api_key="YOUR_API_KEY",
    internal_ticket=None,
    extra_headers=None,
    no_check_certificate=False,
    client_certificate=None
)
```

**Key Capabilities**:

#### Project Management (8 methods)
- `list_project_keys()` → List[str]
- `list_projects()` → List[dict]
- `get_project(project_key)` → DSSProject
- `get_default_project()` → DSSProject
- `create_project(project_key, name, owner, description, settings, project_folder_id)` → DSSProject
- `get_root_project_folder()` → DSSProjectFolder
- `get_project_folder(project_folder_id)` → DSSProjectFolder

#### Users & Groups Management (15 methods)
- `list_users(as_objects)` → List[DSSUser | dict]
- `get_user(login)` → DSSUser
- `create_user(login, password, display_name, source_type, groups, profile, email)` → DSSUser
- `list_groups()` → List[dict]
- `get_group(name)` → DSSGroup
- `create_group(name, description, source_type)` → DSSGroup
- `get_own_user()` → DSSOwnUser
- `list_users_info()` → List[DSSUserInfo]
- `list_groups_info()` → List[DSSGroupInfo]
- `list_users_activity(enabled_users_only)` → List[DSSUserActivity]
- `start_resync_users_from_supplier(logins)` → DSSFuture
- `start_resync_all_users_from_supplier()` → DSSFuture
- `start_fetch_external_groups(user_source_type)` → DSSFuture
- `start_fetch_external_users(user_source_type, login, email, group_name)` → DSSFuture
- `start_provision_users(user_source_type, users)` → DSSFuture

#### API Keys Management (10 methods)
- `list_global_api_keys(as_type)` → List[DSSGlobalApiKeyListItem | DSSGlobalApiKey]
- `get_global_api_key(key)` → DSSGlobalApiKey
- `get_global_api_key_by_id(id_)` → DSSGlobalApiKey
- `create_global_api_key(label, description, admin)` → DSSGlobalApiKey
- `list_personal_api_keys(as_type)` → List[DSSPersonalApiKeyListItem | DSSPersonalApiKey]
- `get_personal_api_key(id)` → DSSPersonalApiKey
- `create_personal_api_key(label, description, as_type)` → DSSPersonalApiKey | dict
- `list_all_personal_api_keys(as_type)` → List[DSSPersonalApiKeyListItem | DSSPersonalApiKey]
- `create_personal_api_key_for_user(user, label, description, as_type)` → DSSPersonalApiKey | dict

#### Connections Management (6 methods)
- `list_connections(as_type)` → dict | List[DSSConnectionListItem | DSSConnection]
- `list_connections_names(connection_type)` → List[str]
- `get_connection(name)` → DSSConnection
- `create_connection(name, type, params, usable_by, allowed_groups)` → DSSConnection

#### Code Environments (8 methods)
- `list_code_envs(as_objects)` → List[DSSCodeEnv | dict]
- `get_code_env(env_lang, env_name)` → DSSCodeEnv
- `create_code_env(env_lang, env_name, deployment_mode, params)` → DSSCodeEnv
- `create_internal_code_env(internal_env_type, python_interpreter, code_env_version)` → DSSCodeEnv
- `create_code_env_from_python_preset(preset_name, allow_update, interpreter, prefix)` → dict
- `list_code_env_usages()` → dict

#### Clusters & Infrastructure (4 methods)
- `list_clusters()` → List[dict]
- `get_cluster(cluster_id)` → DSSCluster
- `create_cluster(cluster_name, cluster_type, params, cluster_architecture)` → DSSCluster

#### Code Studio Templates (3 methods)
- `list_code_studio_templates(as_type)` → List[DSSCodeStudioTemplateListItem | DSSCodeStudioTemplate]
- `get_code_studio_template(template_id)` → DSSCodeStudioTemplate

#### Long-Running Tasks (3 methods)
- `list_futures(as_objects, all_users)` → List[DSSFuture | dict]
- `list_running_scenarios(all_users)` → List[dict]
- `get_future(job_id)` → DSSFuture

#### Notebooks (1 method)
- `list_running_notebooks(as_objects)` → List[DSSNotebook | dict]

#### Apps (3 methods)
- `list_apps(as_type)` → List[DSSAppListItem | DSSApp]
- `get_app(app_id)` → DSSApp

#### Plugins (5 methods)
- `list_plugins()` → List[dict]
- `get_plugin(plugin_id)` → DSSPlugin
- `download_plugin_stream(plugin_id)` → stream
- `download_plugin_to_file(plugin_id, path)` → None
- `install_plugin_from_archive(fp)` → None
- `start_install_plugin_from_archive(fp)` → DSSFuture
- `install_plugin_from_store(plugin_id)` → DSSFuture
- `install_plugin_from_git(repository_url, checkout, subpath)` → DSSFuture

#### Meanings (3 methods)
- `list_meanings()` → List[dict]
- `get_meaning(id)` → DSSMeaning
- `create_meaning(id, label, type, description, values, mappings, pattern, normalizationMode, detectable)` → DSSMeaning

#### SQL Queries (1 method)
- `sql_query(query, connection, database, dataset_full_name, ...)` → DSSSQLQuery

#### Messaging & Notifications (4 methods)
- `get_messaging_channel(channel_id)` → DSSMessagingChannel | DSSMailMessagingChannel
- `list_messaging_channels(as_type, channel_type, channel_family)` → List
- `new_messaging_channel(type)` → DSSMessagingChannelCreator (or subclass)
- `create_messaging_channel(channel_type, channel_id, channel_configuration, permissions)` → DSSMessagingChannel

#### Workspaces (3 methods)
- `list_workspaces(as_objects)` → List[dict | DSSWorkspace]
- `get_workspace(workspace_key)` → DSSWorkspace
- `create_workspace(workspace_key, name, permissions, description, color)` → DSSWorkspace

#### Data Collections (3 methods)
- `list_data_collections(as_type)` → List[DSSDataCollectionListItem | DSSDataCollection | dict]
- `get_data_collection(id)` → DSSDataCollection
- `create_data_collection(displayName, id, tags, description, color, permissions)` → DSSDataCollection

#### Feature Store (1 method)
- `get_feature_store()` → DSSFeatureStore

#### Deployer & Monitoring (6 methods)
- `get_apideployer()` → DSSAPIDeployer
- `get_projectdeployer()` → DSSProjectDeployer
- `get_unified_monitoring()` → DSSUnifiedMonitoring
- `get_project_standards()` → DSSProjectStandards

#### Global Settings & Config (10 methods)
- `get_general_settings()` → DSSGeneralSettings
- `get_variables()` → [DEPRECATED] Use get_global_variables()
- `get_global_variables()` → DSSInstanceVariables
- `set_variables(variables)` → [DEPRECATED]
- `get_resolved_variables(project_key, typed)` → dict
- `get_meaning(id)` → DSSMeaning
- `list_meanings()` → List[dict]
- `get_llm_cost_limiting_counters()` → DSSLLMCostLimitingCounters

#### Logging & Audit (3 methods)
- `list_logs()` → List[str]
- `get_log(name)` → str
- `log_custom_audit(custom_type, custom_params)` → None

#### Licensing & Monitoring (6 methods)
- `get_global_usage_summary(with_per_project)` → DSSGlobalUsageSummary
- `get_licensing_status()` → dict
- `set_license(license)` → None
- `perform_instance_sanity_check(exclusion_list, wait)` → DSSInfoMessages | DSSFuture
- `get_sanity_check_codes()` → List[str]

#### Authentication & Security (4 methods)
- `get_auth_info(with_secrets)` → dict
- `get_auth_info_from_browser_headers(headers_dict, with_secrets)` → dict
- `get_ticket_from_browser_headers(headers_dict)` → str
- `get_sso_settings()` → DSSSSOSettings
- `get_ldap_settings()` → DSSLDAPSettings
- `get_azure_ad_settings()` → DSSAzureADSettings

#### Container Execution (3 methods)
- `push_base_images()` → DSSFuture
- `apply_kubernetes_namespaces_policies()` → DSSFuture
- `build_cde_plugins_image()` → DSSFuture

#### Bundle & Import (3 methods)
- `create_project_from_bundle_local_archive(archive_path, project_folder, permissions_propagation_policy)` → dict
- `create_project_from_bundle_archive(fp, project_folder)` → dict
- `prepare_project_import(f)` → TemporaryImportHandle

#### Data Catalog (1 method)
- `catalog_index_connections(connection_names, all_connections, indexing_mode)` → None

#### Resources (1 method)
- `get_scoring_libs_stream()` → stream

#### Discussions & Govern (3 methods)
- `get_object_discussions(project_key, object_type, object_id)` → DSSObjectDiscussions
- `get_govern_client()` → GovernClient | None

#### Permissions (1 method)
- `new_permission_check()` → DSSPermissionsCheckRequest

#### Instance Info (1 method)
- `get_instance_info()` → DSSInstanceInfo

---

### 1.2 GovernClient - Govern/Compliance Features (48 public methods)

**Entry Point**: `from dataikuapi import GovernClient` or `dss_client.get_govern_client()`

**Key Capabilities**:

#### Artifact Management (4 methods)
- `get_artifact(artifact_id)` → GovernArtifact
- `get_artifacts(criteria)` → List[GovernArtifact]
- `create_artifact(artifact)` → GovernArtifact
- `search_artifacts(search_request)` → GovernArtifactSearchResponse

#### Blueprints & Workflows (6 methods)
- `get_blueprint(blueprint_id)` → GovernBlueprint
- `list_blueprints()` → List[GovernBlueprintListItem]
- `get_blueprint_version(blueprint_id, version_id)` → GovernBlueprintVersion
- `get_blueprint_designer()` → GovernAdminBlueprintDesigner

#### Custom Pages (3 methods)
- `get_custom_page(custom_page_id)` → GovernCustomPage
- `list_custom_pages()` → List[GovernCustomPageListItem]
- `get_custom_pages_handler()` → GovernAdminCustomPagesHandler

#### Users & Groups (8 methods)
- `list_users(as_objects)` → List[GovernUser | dict]
- `get_user(login)` → GovernUser
- `create_user(login, password, display_name, source_type, groups, profile, email)` → GovernUser
- `get_own_user()` → GovernOwnUser
- `list_users_info()` → List[GovernUserInfo]
- `list_groups()` → List[dict]
- `get_group(name)` → GovernGroup
- `create_group(name, description, source_type)` → GovernGroup

#### API Keys (4 methods)
- `list_global_api_keys(as_type)` → List[GovernGlobalApiKeyListItem | GovernGlobalApiKey]
- `get_global_api_key_by_id(id_)` → GovernGlobalApiKey
- `create_global_api_key(label, description, admin)` → GovernGlobalApiKey

#### Time Series (1 method)
- `create_time_series(datapoints)` → GovernTimeSeries

#### Settings & Configuration (5 methods)
- `get_general_settings()` → GovernGeneralSettings
- `get_authorization_matrix()` → GovernAuthorizationMatrix
- `get_sso_settings()` → GovernSSOSettings
- `get_ldap_settings()` → GovernLDAPSettings
- `get_azure_ad_settings()` → GovernAzureADSettings

#### Other Operations (3 methods)
- `get_future(job_id)` → GovernFuture
- `get_auth_info(with_secrets)` → dict
- `get_instance_info()` → GovernInstanceInfo

---

### 1.3 FMClient Variants - Fleet Management

Three platform-specific clients: **FMClientAWS**, **FMClientAzure**, **FMClientGCP**

Each supports these capabilities:

#### Cloud Infrastructure (5 methods)
- `get_instance(instance_id)` → FMAWSInstance (or Azure/GCP equivalent)
- `list_instances()` → List[dict]
- `new_instance_creator(label, instance_settings_template_id, virtual_network_id, image_id)` → FMAWSInstanceCreator
- `list_images()` → List[dict]
- `get_image(image_id)` → dict

#### Virtual Networks (1 method)
- `new_virtual_network_creator(label)` → FMAWSVirtualNetworkCreator
- `get_virtual_network(virtual_network_id)` → FMAWSVirtualNetwork
- `list_virtual_networks()` → List[dict]

#### Load Balancers (1 method)
- `new_load_balancer_creator(name, virtual_network_id)` → FMAWSLoadBalancerCreator
- `get_load_balancer(load_balancer_id)` → FMAWSLoadBalancer
- `list_load_balancers()` → List[dict]

#### Cloud Credentials (4 methods)
- `get_cloud_credentials()` → FMCloudCredentials
- `get_cloud_account(cloud_account_id)` → FMAWSCloudAccount
- `list_cloud_accounts()` → List[dict]
- `new_cloud_account_creator(label)` → FMAWSCloudAccountCreator

#### Templates & Configuration (3 methods)
- `get_instance_settings_template(instance_settings_template_id)` → FMInstanceSettingsTemplate
- `list_instance_settings_templates()` → List[dict]
- `new_instance_template_creator(label)` → FMAWSInstanceSettingsTemplateCreator

#### Tenant Config (3 methods)
- `get_cloud_tags()` → FMCloudTags
- `get_azure_ad_settings()` → AzureADSettings
- `get_ldap_settings()` → LDAPSettings

---

### 1.4 APINodeClient - API Service Operations (9 methods)

**Capabilities**:
- `predict_record(endpoint_id, features, forced_generation, dispatch_key, context, with_explanations, ...)` → dict
- `predict_records(endpoint_id, records, forced_generation, dispatch_key, with_explanations, ...)` → List[dict]
- `predict_effect(endpoint_id, features, forced_generation, dispatch_key)` → dict
- `predict_effects(endpoint_id, records, forced_generation, dispatch_key)` → List[dict]
- `forecast(endpoint_id, records, forced_generation, dispatch_key)` → dict
- `lookup_record(endpoint_id, record, context)` → dict
- `lookup_records(endpoint_id, records)` → List[dict]
- `sql_query(endpoint_id, parameters)` → dict
- `run_function(endpoint_id)` → dict

---

### 1.5 APINodeAdminClient - API Node Administration (11 methods)

**Capabilities**:
- `list_services()` → List[dict]
- `service(service_id)` → APINodeService
- `create_service(service_id)` → APINodeService
- `clear_model_cache()` → None
- `clean_code_env_cache()` → None
- `import_code_env_in_cache(file_dir, language)` → dict
- `register_code_env_in_cache(exported_env_dir, built_env_dir, language)` → dict
- `import_model_archive_in_cache(model_archive_path)` → dict
- `clean_unused_services_and_generations()` → dict
- `get_metrics()` → dict
- `auth()` → APINodeAuth

---

## PART 2: PROJECT-LEVEL CLASSES (DSSProject)

### 2.1 DSSProject - Primary Project Handle (154 public methods)

**Access**: `client.get_project(project_key)` → DSSProject

**Hierarchical Navigation**:
```
DSSClient
  └── DSSProject (project_key)
      ├── DSSDataset
      ├── DSSRecipe
      ├── DSSManagedFolder
      ├── DSSSavedModel
      ├── DSSScenario
      ├── DSSDashboard
      ├── DSSInsight
      ├── DSSAnalysis
      ├── DSSMLTask
      ├── DSSWebApp
      ├── DSSJupyterNotebook
      └── ... (and many others)
```

#### Dataset Operations (12 methods)
- `list_datasets()` → List[dict]
- `list_datasets_with_filter(filter)` → List[dict]
- `get_dataset(dataset_name)` → DSSDataset
- `create_dataset(dataset_name, connection, database, table, ...)` → DSSDataset
- `create_dataiku_dataset(dataset_name)` → DSSDataset
- `create_sql_dataset(dataset_name, connection, database, table)` → DSSDataset
- `create_hive_dataset(dataset_name, database, table)` → DSSDataset
- `create_gs_dataset(dataset_name, connection, path)` → DSSDataset
- `create_azure_blob_dataset(dataset_name, connection, path_in_connection, container)` → DSSDataset
- `create_postgresql_dataset(dataset_name, connection, database, schema_table)` → DSSDataset
- `prepare_import_tables()` → TablesImportDefinition

#### Recipe Operations (3 methods)
- `list_recipes()` → List[dict]
- `get_recipe(recipe_name)` → DSSRecipe
- `create_recipe(recipe_name, recipe_type, inputs, outputs)` → DSSRecipe

**Recipe Creation Helpers**:
- `create_grouping_recipe(recipe_name, input_dataset, outputs)` → GroupingRecipeCreator
- `create_distinct_recipe(recipe_name, input_dataset, output_dataset)` → DistinctRecipeCreator
- `create_sort_recipe(recipe_name, input_dataset, output_dataset)` → SortRecipeCreator
- `create_topn_recipe(recipe_name, input_dataset, output_dataset)` → TopNRecipeCreator
- `create_join_recipe(recipe_name, outputs)` → JoinRecipeCreator
- `create_split_recipe(recipe_name, input_dataset, outputs)` → SplitRecipeCreator
- `create_sampling_recipe(recipe_name, input_dataset, output_dataset)` → SamplingRecipeCreator
- `create_sync_recipe(recipe_name, input_dataset, output_dataset)` → SyncRecipeCreator
- `create_download_recipe(recipe_name, output_dataset)` → DownloadRecipeCreator
- `create_sql_query_recipe(recipe_name, output_dataset)` → SQLQueryRecipeCreator
- `create_code_recipe(recipe_name, recipe_type, outputs)` → CodeRecipeCreator
- `create_window_recipe(recipe_name, input_dataset, output_dataset)` → WindowRecipeCreator
- `create_stack_recipe(recipe_name, outputs)` → StackRecipeCreator
- `create_upsert_recipe(recipe_name, input_dataset, output_dataset)` → UpsertRecipeCreator

#### Managed Folder Operations (3 methods)
- `list_managed_folders()` → List[dict]
- `get_managed_folder(name)` → DSSManagedFolder
- `create_managed_folder(name, connection, path_in_connection)` → DSSManagedFolder

#### Saved Model Operations (5 methods)
- `list_saved_models()` → List[dict]
- `get_saved_model(sm_id)` → DSSSavedModel
- `create_prediction_saved_model_from_trained_model(sm_id, mlflow_handle, mlflow_run_id, name, ...)` → DSSSavedModel
- `create_custom_saved_model(sm_id, object_type)` → DSSSavedModel

#### Scenario Operations (3 methods)
- `list_scenarios()` → List[dict]
- `get_scenario(name)` → DSSScenario
- `create_scenario(name)` → DSSScenario

#### Dashboard Operations (3 methods)
- `list_dashboards()` → List[dict]
- `get_dashboard(dashboard_id)` → DSSDashboard
- `create_dashboard(dashboard_name)` → DSSDashboard

#### Insight Operations (3 methods)
- `list_insights()` → List[dict]
- `get_insight(insight_id)` → DSSInsight
- `create_insight(insight_id, dataset_name)` → DSSInsight

#### Analysis Operations (2 methods)
- `list_analyses()` → List[dict]
- `create_analysis(input_dataset)` → DSSAnalysis

#### ML Task Operations (3 methods)
- `list_ml_tasks()` → List[dict]
- `get_ml_task(task_id)` → DSSMLTask
- `create_ml_task(task_id, input_dataset, target_variable, task_type)` → DSSMLTask

#### Model Evaluation Store (2 methods)
- `list_model_evaluation_stores()` → List[dict]
- `get_model_evaluation_store(store_id)` → DSSModelEvaluationStore

#### WebApp & UI (3 methods)
- `list_webapps()` → List[dict]
- `get_webapp(webapp_id)` → DSSWebApp
- `create_webapp(webapp_id)` → DSSWebApp

#### Notebook Operations (3 methods)
- `list_jupyter_notebooks()` → List[dict]
- `get_jupyter_notebook(notebook_id)` → DSSJupyterNotebook
- `create_jupyter_notebook(notebook_name)` → DSSJupyterNotebook

#### SQL Notebook Operations (2 methods)
- `list_sql_notebooks()` → List[dict]
- `get_sql_notebook(notebook_id)` → DSSSQLNotebook

#### Documentation & Wiki (2 methods)
- `get_wiki()` → DSSWiki
- `get_object_discussions(object_type, object_id)` → DSSObjectDiscussions

#### Agents & LLM (4 methods)
- `list_agents()` → List[dict]
- `get_agent(agent_id)` → DSSAgent
- `create_agent(name, type, plugin_agent_type)` → DSSAgent

#### Knowledge Banks (2 methods)
- `list_knowledge_banks()` → List[dict]
- `get_knowledge_bank(kb_id)` → DSSKnowledgeBank

#### Streaming Endpoints (2 methods)
- `list_streaming_endpoints()` → List[dict]
- `get_streaming_endpoint(endpoint_id)` → DSSStreamingEndpoint

#### APIs & Services (3 methods)
- `list_api_services()` → List[dict]
- `get_api_service(service_id)` → DSSAPIService
- `create_api_service(service_id)` → DSSAPIService

#### Code Studio (3 methods)
- `list_code_studio_objects()` → List[dict]
- `get_code_studio_object(object_id)` → DSSCodeStudioObject

#### Settings & Configuration (3 methods)
- `get_settings()` → DSSProjectSettings
- `get_variables()` → dict
- `get_resolved_variables(typed)` → dict

#### Project Flow & Execution (3 methods)
- `get_flow()` → DSSProjectFlow
- `list_jobs()` → List[dict]
- `get_job(job_id)` → DSSJob

#### Git Integration (2 methods)
- `get_git()` → DSSProjectGit

#### Data Quality (2 methods)
- `list_data_quality_checks()` → List[dict]
- `get_data_quality_status()` → dict

#### Bundles & Deployment (3 methods)
- `get_bundles()` → List[dict]
- `create_bundle()` → dict
- `activate_bundle(bundle_id, scenarios_to_enable)` → None

#### Export/Import (2 methods)
- `export_to_file(path, ...)` → None
- `validate_export_plan(export_config)` → dict

#### Labeling Tasks (1 method)
- `list_labeling_tasks()` → List[dict]

#### Code Macros (2 methods)
- `list_macros()` → List[dict]
- `get_macro(macro_id)` → DSSMacro

#### MLflow Integration (1 method)
- `get_mlflow()` → DSSMLflowExtension

---

## PART 3: OBJECT-LEVEL CLASSES

### 3.1 DSSDataset - Dataset Operations

**Access**: `project.get_dataset(dataset_name)` → DSSDataset

**Key Methods** (100+ methods):
- `get_definition()` → dict (full schema/config)
- `set_definition(definition)` → None
- `get_settings()` → DSSDatasetSettings
- `list_partitions()` → List[str]
- `delete()` → None
- `get_info()` → DSSDatasetInfo
- `read_dataframe(limit, infer_with_pandas, ...)` → DataFrame
- `get_distinct_values(column, process_securely)` → List
- `read_column(column_name, limit)` → List
- `get_schema()` → dict
- `synchronize_hive_metastore()` → DSSFuture
- `init_hive_metastore()` → None
- `compute_statistics()` → dict

**Nested Objects**:
- `get_comments()` → DSSObjectDiscussions
- `get_column_comments(column_name)` → DSSObjectDiscussions

### 3.2 DSSRecipe - Recipe Operations

**Access**: `project.get_recipe(recipe_name)` → DSSRecipe

**Key Methods** (50+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `get_settings()` → DSSRecipeSettings
- `delete()` → None
- `get_json()` → dict
- `get_inputs()` → List[str]
- `get_outputs()` → List[str]
- `run(parameters, wait, no_fail, ...)` → DSSFuture | DSSJob
- `get_last_modification_info()` → dict

### 3.3 DSSSavedModel - Trained Model Operations

**Access**: `project.get_saved_model(sm_id)` → DSSSavedModel

**Key Methods** (40+ methods):
- `get_definition()` → dict
- `get_settings()` → DSSSavedModelSettings
- `delete()` → None
- `list_versions()` → List[dict]
- `get_version(version_id)` → DSSSavedModelVersion
- `get_active_version()` → DSSSavedModelVersion
- `set_active_version(version_id)` → None
- `import_mlflow_model(mlflow_handle, run_id, ...)` → DSSFuture

### 3.4 DSSManagedFolder - File Storage Operations

**Access**: `project.get_managed_folder(name)` → DSSManagedFolder

**Key Methods** (30+ methods):
- `get_definition()` → dict
- `get_path()` → str (local filesystem path)
- `delete()` → None
- `upload_file(local_path, target_path)` → None
- `download_file(target_path, local_path)` → None
- `list_contents()` → List[dict]
- `read_stream(path)` → stream

### 3.5 DSSScenario - Workflow Orchestration

**Access**: `project.get_scenario(name)` → DSSScenario

**Key Methods** (40+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `get_settings()` → DSSScenarioSettings
- `delete()` → None
- `run(...)` → DSSFuture
- `enable()` → None
- `disable()` → None
- `get_status()` → dict
- `list_runs()` → List[dict]
- `get_last_run()` → dict

### 3.6 DSSDashboard - Analytics Dashboards

**Access**: `project.get_dashboard(dashboard_id)` → DSSDashboard

**Key Methods** (30+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `get_settings()` → DSSDashboardSettings
- `delete()` → None
- `get_insights()` → List[DSSInsight]
- `list_shares()` → List[dict]

### 3.7 DSSMLTask - Machine Learning Tasks

**Access**: `project.get_ml_task(task_id)` → DSSMLTask

**Key Methods** (40+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `get_settings()` → DSSMLTaskSettings
- `delete()` → None
- `list_trainable_prediction_models()` → List[dict]
- `list_trainable_clustering_models()` → List[dict]
- `list_trained_models()` → List[dict]
- `train(model_type, ...)` → DSSFuture
- `get_trained_model(model_id)` → DSSTrainedModel

### 3.8 DSSAnalysis - Data Analysis

**Access**: `project.create_analysis(input_dataset)` → DSSAnalysis

**Key Methods** (30+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `delete()` → None
- `list_analyses()` → List[dict]

### 3.9 DSSWebApp - Interactive Web Applications

**Access**: `project.get_webapp(webapp_id)` → DSSWebApp

**Key Methods** (30+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `get_settings()` → DSSWebAppSettings
- `delete()` → None
- `get_backend()` → DSSWebAppBackend

### 3.10 DSSInsight - Insights & Visualizations

**Access**: `project.get_insight(insight_id)` → DSSInsight

**Key Methods** (30+ methods):
- `get_definition()` → dict
- `set_definition(definition)` → None
- `delete()` → None
- `export_to_png(output_file, width, height)` → None

---

## PART 4: SETTINGS & CONFIGURATION PATTERN

### 4.1 Common Settings Pattern

All major objects follow this pattern:

```python
# Get settings
settings = object.get_settings()

# Modify settings (settings is mutable dict-like)
settings.raw['some_property'] = new_value

# Save changes
settings.save()
```

**Settings Classes**:
- DSSDatasetSettings
- DSSRecipeSettings
- DSSSavedModelSettings
- DSSScenarioSettings
- DSSDashboardSettings
- DSSMLTaskSettings
- DSSWebAppSettings
- DSSProjectSettings
- DSSConnectionSettings
- DSSCodeEnvSettings
- DSSClusterSettings

### 4.2 Getter vs Setter Methods

**Common naming pattern**:
- `list_*()` - Returns list of items (dicts)
- `get_*()` - Returns single object handle (class instance)
- `create_*()` - Creates and returns new object handle
- `delete()` - Deletes the object
- `save()` - Saves changes to settings
- `get_definition()` - Gets raw dict configuration
- `set_definition(definition)` - Sets raw dict configuration
- `get_settings()` - Gets settings object wrapper
- `*_raw` - Access to underlying dict data

---

## PART 5: ASYNCHRONOUS OPERATIONS & FUTURES

### 5.1 DSSFuture - Long-Running Operations

**Access**: Various operations return `DSSFuture` objects

**Key Methods**:
- `wait_for_result(timeout, no_fail)` → dict (waits until complete)
- `get_result()` → dict (result if available)
- `abort()` → None
- `get_state()` → dict (current progress)
- `has_result()` → bool

**Operations Returning Futures**:
- `client.list_futures()` - Get list of running operations
- `scenario.run()` - Execute scenario
- `recipe.run()` - Execute recipe  
- `client.start_resync_users_from_supplier()` - User sync
- `client.start_fetch_external_users()` - User import
- Plugin install operations
- Sanity checks
- Many job scheduling operations

---

## PART 6: DATA IMPORT/EXPORT PATTERNS

### 6.1 Dataset Import Pattern

```python
# Step 1: Prepare import
builder = project.prepare_import_tables()
builder.add_hive_table(hive_database, hive_table)
builder.add_sql_table(connection, schema, table)

# Step 2: Execute import
prepared_import = builder.prepare()
result = prepared_import.execute()
```

### 6.2 Project Bundle Export/Import

```python
# Export project to file
project.export_to_file("path/to/bundle.zip")

# Import from file (automation node only)
result = client.create_project_from_bundle_local_archive("path/to/bundle.zip")

# Or with file object
with open("bundle.zip", "rb") as f:
    result = client.create_project_from_bundle_archive(f)

# From design node: prepare import
handle = client.prepare_project_import(file_object)
result = handle.execute(settings={"targetProjectKey": "NEW_KEY"})
```

---

## PART 7: CLASS HIERARCHY & INHERITANCE

### 7.1 Base Classes

```
object
├── DSSClient
├── DSSBaseClient
│   ├── APINodeClient
│   └── APINodeAdminClient
├── FMClient
│   ├── FMClientAWS
│   ├── FMClientAzure
│   └── FMClientGCP
├── GovernClient
│
├── DSSProject
├── DSSDataset
├── DSSRecipe
├── DSSSavedModel
└── ... (many more object classes)
```

### 7.2 Taggable Objects Hierarchy

Many DSS objects inherit from `DSSTaggableObjectListItem` and `DSSTaggableObjectSettings`:

- DSSDashboard
- DSSInsight
- DSSDataset
- DSSManagedFolder
- DSSRecipe
- DSSSavedModel
- DSSMLTask
- DSSWebApp
- DSSJupyterNotebook
- DSSKnowledgeBank
- DSSLLM
- DSSAgent
- DSSAgentTool
- DSSRetrievalAugmentedLLM
- DSSSQLNotebook
- DSSStreamingEndpoint

**Shared Methods**:
- Tags management
- Name/description editing
- Owner/permission management
- List items with filter support

---

## PART 8: COMPOSITION PATTERNS

### 8.1 Settings Composition

Many classes have nested settings with specialized configurations:

```
Project
├── DSSDataset
│   └── DSSDatasetSettings
│       ├── FSLikeDatasetSettings (for filesystem datasets)
│       └── SQLDatasetSettings (for SQL datasets)
├── DSSSavedModel
│   └── DSSSavedModelSettings
├── DSSMLTask
│   └── DSSMLTaskSettings
│       ├── PredictionMLTaskSettings
│       ├── ClusteringMLTaskSettings
│       └── TextAnalysisMLTaskSettings
└── DSSScenario
    └── DSSScenarioSettings
```

### 8.2 List Item Pattern

Many list operations return "ListItem" objects with minimal data:

```
Client.list_dashboards() → List[DSSDashboardListItem]
  ├── item.to_dashboard() → DSSDashboard (fetch full object)
  └── item.get_raw() → dict (access raw data)
```

---

## PART 9: COMMON WORKFLOWS & METHOD CHAINS

### 9.1 Dataset Processing Workflow

```python
client = DSSClient(host, api_key)
project = client.get_project("PROJECT_KEY")

# Access dataset
dataset = project.get_dataset("input_data")
info = dataset.get_info()
schema = dataset.get_schema()
df = dataset.read_dataframe(limit=1000)

# Create recipe
recipe = project.create_recipe(
    "new_recipe",
    "grouping",
    inputs=["input_data"],
    outputs=["output_data"]
)
recipe_def = recipe.get_definition()
recipe_def['params']['customParams']['doNotKeepGroupingColumns'] = False
recipe.set_definition(recipe_def)

# Execute recipe
future = recipe.run()
future.wait_for_result()

# Access output
output = project.get_dataset("output_data")
result_df = output.read_dataframe()
```

### 9.2 Model Training Workflow

```python
# Get ML task
ml_task = project.get_ml_task("task_id")

# List available algorithms
models = ml_task.list_trainable_prediction_models()

# Train model
future = ml_task.train("model_type", params={...})
future.wait_for_result()

# Get trained model
trained_model = ml_task.get_trained_model("model_id")
version_data = trained_model.get_version("v1")

# Deploy to saved model
saved_model = project.get_saved_model("sm_id")
trained_model.deploy(saved_model)
```

### 9.3 Scenario Execution Workflow

```python
scenario = project.get_scenario("scenario_name")

# Check current status
status = scenario.get_status()
is_enabled = status.get('enabled', False)

# Enable if needed
if not is_enabled:
    scenario.enable()

# Execute scenario
future = scenario.run(triggers={"type": "manual"})
result = future.wait_for_result()

# Get last run info
last_run = scenario.get_last_run()
run_id = last_run['runId']
```

### 9.4 User & Permission Management Workflow

```python
# Create user
user = client.create_user(
    login="newuser",
    password="temppass",
    display_name="New User",
    groups=["team1", "team2"],
    profile="FULL_DESIGNER"
)

# Configure user settings
settings = user.get_settings()
settings.set_connection_credential("db_conn", "user", "pass")
settings.save()

# Check user activity
activity = user.get_activity()
last_login = activity.last_successful_login()

# Get authorization matrix
auth_matrix = client.get_authorization_matrix()
```

### 9.5 API Deployment Workflow

```python
deployer = client.get_apideployer()

# Get infra configuration
infra = deployer.get_infra("infra_name")
infra_settings = infra.get_settings()

# Get deployment
deployment = infra.get_deployment("api_name")
deployment_settings = deployment.get_settings()

# List API services
services = deployment.list_api_services()

# Get service version
service = deployment.get_api_service("service_id")
versions = service.list_deployed_generations()
```

---

## PART 10: KEY DESIGN PATTERNS

### 10.1 Handle Pattern

Many methods return "Handle" objects that combine data + actions:

```python
dataset = project.get_dataset("name")  # Returns handle
dataset.get_definition()  # Query current state
dataset.set_definition(def)  # Modify state
dataset.delete()  # Perform action
```

### 10.2 Builder Pattern

Create complex objects with builder classes:

```python
creator = project.create_grouping_recipe("name", "input")
creator.with_output("output", "DATASET")
creator.with_custom_params({...})
recipe = creator.create()
```

### 10.3 List + Get Pattern

Listing operations return dicts, individual gets return handles:

```python
# List returns dicts
datasets = project.list_datasets()  # List[dict]

# Individual access returns handle
dataset = project.get_dataset("name")  # DSSDataset handle
```

### 10.4 Settings Wrapper Pattern

Settings objects provide both dict access and typed properties:

```python
settings = dataset.get_settings()
settings.raw  # Dict access
settings.get_raw()  # Get as dict
settings.save()  # Persist changes
```

### 10.5 Creator Helper Pattern

Specialized creation for recipe types:

```python
# Generic recipe creation
recipe = project.create_recipe("name", "sql_query", ...)

# Specialized creator
creator = project.create_sql_query_recipe("name", "output")
creator.with_connection("pg_conn")
recipe = creator.create()
```

---

## PART 11: COMMON METHOD NAMING CONVENTIONS

| Pattern | Usage | Example |
|---------|-------|---------|
| `list_*()` | Returns list of dicts | `list_datasets()` |
| `get_*(id)` | Returns object handle | `get_dataset(name)` |
| `create_*(...)` | Creates object, returns handle | `create_dataset(...)` |
| `*_to_file(path)` | Export to filesystem | `export_to_file(path)` |
| `*_from_file(path)` | Import from filesystem | `import_from_file(path)` |
| `delete()` | Delete object | `dataset.delete()` |
| `get_definition()` | Get raw dict config | `recipe.get_definition()` |
| `set_definition(def)` | Set raw dict config | `recipe.set_definition(def)` |
| `get_settings()` | Get settings wrapper | `dataset.get_settings()` |
| `get_raw()` | Get as dict | `settings.get_raw()` |
| `save()` | Persist changes | `settings.save()` |
| `*_info()` | Get detailed info | `dataset.get_info()` |
| `run()` | Execute async operation | `scenario.run()` |
| `wait_for_result()` | Block until future complete | `future.wait_for_result()` |
| `enable()` / `disable()` | Toggle state | `scenario.enable()` |
| `list_*()` | Multiple items | `list_recipes()` |
| `start_*()` | Start async, return future | `start_resync_users()` |
| `prepare_*()` | Prepare for operation | `prepare_import_tables()` |
| `new_*()` | Create builder object | `new_messaging_channel()` |

---

## PART 12: ERROR HANDLING & EXCEPTIONS

**Common Exception Types**:
- `DataikuException` - Base exception class
- HTTP exceptions handled via `handle_http_exception()`
- Validation errors from settings

**Common Error Scenarios**:
- Invalid API key → 401 Unauthorized
- Insufficient permissions → 403 Forbidden
- Object not found → 404 Not Found
- Invalid configuration → 400 Bad Request

**Best Practices**:
```python
try:
    result = dataset.read_dataframe()
except Exception as e:
    logger.error(f"Failed to read dataset: {e}")
    # Handle gracefully
```

---

## PART 13: AUTHENTICATION METHODS

### 13.1 API Key Authentication
```python
client = DSSClient(
    host="http://localhost:11200",
    api_key="YOUR_API_KEY"
)
```

### 13.2 Internal Ticket Authentication
```python
client = DSSClient(
    host="http://localhost:11200",
    internal_ticket="INTERNAL_TICKET"
)
```

### 13.3 Browser Header Authentication
```python
auth_info = client.get_auth_info_from_browser_headers(headers_dict)
ticket = client.get_ticket_from_browser_headers(headers_dict)
```

### 13.4 SSL/Certificate Configuration
```python
client = DSSClient(
    host="https://dss.company.com",
    api_key="KEY",
    no_check_certificate=False,  # Default: verify SSL
    client_certificate=("cert.pem", "key.pem")  # Client cert auth
)
```

---

## PART 14: SUMMARY TABLE OF ALL PUBLIC CLASSES

**Core Clients (7)**:
DSSClient, GovernClient, FMClient, FMClientAWS, FMClientAzure, FMClientGCP, APINodeClient, APINodeAdminClient

**Project & Objects (40+)**:
DSSProject, DSSDataset, DSSRecipe, DSSSavedModel, DSSScenario, DSSDashboard, DSSInsight, DSSAnalysis, DSSMLTask, DSSWebApp, DSSManagedFolder, DSSJupyterNotebook, DSSSQLNotebook, DSSAgent, DSSAgentTool, DSSKnowledgeBank, DSSRetrievalAugmentedLLM, DSSLLM, DSSStreamingEndpoint, DSSAPIService, DSSCodeStudioObject, DSSContinuousActivity, DSSAppManifest, DSSDocumentExtractor, DSSModelEvaluationStore, DSSModelComparison, DSSSQLQuery, DSSLabelingTask, DSSMacro, DSSNotebook, DSSPlugin, DSSWiki, DSSWorkspace, DSSDataCollection

**Settings Classes (30+)**:
DSSDatasetSettings, DSSRecipeSettings, DSSSavedModelSettings, DSSScenarioSettings, DSSDashboardSettings, DSSMLTaskSettings, DSSWebAppSettings, DSSProjectSettings, DSSConnectionSettings, DSSCodeEnvSettings, DSSClusterSettings, and many more...

**Admin Classes (40+)**:
DSSUser, DSSGroup, DSSConnection, DSSCodeEnv, DSSCluster, DSSMeaning, DSSGeneralSettings, DSSInstanceVariables, and corresponding Govern equivalents...

**Governance & Monitoring (30+)**:
GovernArtifact, GovernBlueprint, GovernCustomPage, GovernTimeSeries, DSSUnifiedMonitoring, DSSProjectDeployer, DSSAPIDeployer, DSSProjectStandards

**Total Public Classes**: 150+

---

## SUMMARY

The Dataiku Python API client provides a comprehensive, well-structured interface for:

1. **Project Management** - Create, list, configure DSS projects
2. **Data Operations** - Manage datasets, connections, imports/exports
3. **Data Processing** - Create and execute recipes, scenarios, jobs
4. **ML/AI** - Train models, manage saved models, run ML tasks
5. **Analytics** - Create dashboards, insights, analyses
6. **Automation** - Schedule and execute scenarios, manage workflows
7. **Administration** - User/group management, security, configuration
8. **Governance** - Artifact tracking, compliance, signoffs (via GovernClient)
9. **Cloud Infrastructure** - VM provisioning, networking, LB management (via FMClient)
10. **API Services** - Deploy and manage served models and functions (via APINodeClient)

All classes follow consistent patterns for:
- Object access (get vs list)
- Settings management (get_settings + save)
- Async operations (futures with wait_for_result)
- Configuration (dict-based definitions)

