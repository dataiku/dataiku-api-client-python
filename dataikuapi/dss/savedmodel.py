import os
import shutil
import tempfile

from dataikuapi.dss.utils import DSSDatasetSelectionBuilder
from .discussion import DSSObjectDiscussions
from .managedfolder import DSSManagedFolder
from .metrics import ComputedMetrics
from .ml import DSSMLTask, DSSTrainedTimeseriesForecastingModelDetails
from .ml import DSSTrainedClusteringModelDetails
from .ml import DSSTrainedPredictionModelDetails
from ..utils import _make_zipfile, dku_basestring_type

try:
    basestring
except NameError:
    basestring = str


class DatabricksRepositoryContextManager(object):
    def __init__(self, connection_info, use_unity_catalog):
        self.connection_info = connection_info
        self.use_unity_catalog = use_unity_catalog

    def __enter__(self):
        self._setup_mlflow_for_databricks_registry()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._restore_previous_mlflow_setup()

    def _setup_mlflow_for_databricks_registry(self):
        params = self.connection_info.get("params")
        auth_type = params.get("authType")
        if auth_type == "OAUTH2_APP":
            token = self.connection_info.get("resolvedOAuth2Credential").get("accessToken")
        elif auth_type == "PERSONAL_ACCESS_TOKEN":
            token = params.get("personalAccessToken")
        else:
            raise Exception("Unhandled auth method: " + auth_type)
        databricks_host = "https://" if params.get("ssl") else "http://"
        host = params.get("host")
        port = params.get("port")
        if not host:
            raise Exception("Host undefined for Databricks connection")
        if not port:
            raise Exception("Port undefined for Databricks connection")
        databricks_host += host + ":" + str(port)
        http_path = params.get("httpPath")
        if http_path:
            if http_path.endswith("/"):
                http_path = http_path[:-1]
            if not http_path.startswith("/"):
                http_path = "/" + http_path
            databricks_host += http_path
        self.previous_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", None)
        self.previous_databricks_host = os.environ.get("DATABRICKS_HOST", None)
        self.previous_databricks_token = os.environ.get("DATABRICKS_TOKEN", None)
        proxy_as_string = self.connection_info.get("proxySettingsAsString")
        if proxy_as_string:
            self.previous_http_proxy = os.environ.get("HTTP_PROXY", None)
            self.previous_https_proxy = os.environ.get("HTTPS_PROXY", None)
            os.environ["http_proxy"] = "http://" + proxy_as_string
            os.environ["https_proxy"] = "http://" + proxy_as_string
        else:
            self.previous_http_proxy = None
            self.previous_https_proxy = None

        import mlflow
        self.previous_registry_uri = mlflow.get_registry_uri()
        if self.use_unity_catalog:
            mlflow.set_registry_uri("databricks-uc")
        else:
            mlflow.set_registry_uri(None)

        os.environ["MLFLOW_TRACKING_URI"] = "databricks"
        os.environ["DATABRICKS_HOST"] = databricks_host
        os.environ["DATABRICKS_TOKEN"] = token

    def _restore_previous_mlflow_setup(self):
        if self.previous_tracking_uri:
            os.environ["MLFLOW_TRACKING_URI"] = self.previous_tracking_uri
        else:
            os.environ.pop("MLFLOW_TRACKING_URI")
        if self.previous_databricks_host:
            os.environ["DATABRICKS_HOST"] = self.previous_databricks_host
        else:
            os.environ.pop("DATABRICKS_HOST")
        if self.previous_databricks_token:
            os.environ["DATABRICKS_TOKEN"] = self.previous_databricks_token
        else:
            os.environ.pop("DATABRICKS_TOKEN")
        import mlflow
        mlflow.set_registry_uri(self.previous_registry_uri)
        if self.previous_http_proxy:
            os.environ["http_proxy"] = self.previous_http_proxy
        if self.previous_https_proxy:
            os.environ["https_proxy"] = self.previous_https_proxy


class DSSSavedModel(object):
    """
    Handle to interact with a saved model on the DSS instance.

    .. important::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSProject.get_saved_model`

    :param client: an api client to connect to the DSS backend
    :type client: :class:`dataikuapi.dssclient.DSSClient`
    :param str project_key: identifier of the project containing the model
    :param str sm_id: identifier of the saved model
    """
    def __init__(self, client, project_key, sm_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.sm_id = sm_id

    @property
    def id(self):
        """
        Returns the identifier of the saved model

        :rtype: str
        """
        return self.sm_id

    def get_settings(self):
        """
        Returns the settings of this saved model.

        :return: settings of this saved model
        :rtype: :class:`dataikuapi.dss.savedmodel.DSSSavedModelSettings`
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))
        return DSSSavedModelSettings(self, data)

    ########################################################
    # Versions
    ########################################################

    def list_versions(self):
        """
        Gets the versions of this saved model.

        This returns each version as a dict of object. Each object contains at least an "id" parameter, which
        can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`.

        :return: The list of the versions
        :rtype: list[dict]
        """
        return self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions" % (self.project_key, self.sm_id))

    def get_active_version(self):
        """
        Gets the active version of this saved model.

        The returned dict contains at least an "id" parameter, which can be passed to :meth:`get_metric_values`,
        :meth:`get_version_details` and :meth:`set_active_version`.

        :return: A dict representing the active version or None if no version is active.
        :rtype: Union[dict, None]
        """
        filtered = [x for x in self.list_versions() if x["active"]]
        if len(filtered) == 0:
            return None
        else:
            return filtered[0]

    def get_version_details(self, version_id):
        """
        Gets details for a version of a saved model

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :return: details of this trained model
        :rtype: :class:`dataikuapi.dss.ml.DSSTrainedPredictionModelDetails`
        """
        details = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s/versions/%s/details" % (self.project_key, self.sm_id, version_id))
        snippet = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s/versions/%s/snippet" % (self.project_key, self.sm_id, version_id))

        if "facts" in details:
            return DSSTrainedClusteringModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)
        if snippet.get("predictionType", "") == "TIMESERIES_FORECAST":
            return DSSTrainedTimeseriesForecastingModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)
        return DSSTrainedPredictionModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)

    def set_active_version(self, version_id):
        """
        Sets a particular version of the saved model as the active one.

        :param str version_id: Identifier of the version, as returned by :meth:`list_versions`
        """
        self.client._perform_empty(
            "POST", "/projects/%s/savedmodels/%s/versions/%s/actions/setActive" % (self.project_key, self.sm_id, version_id))

    def delete_versions(self, versions, remove_intermediate=True):
        """
        Deletes version(s) of the saved model.

        :param list[str] versions: list of versions to delete
        :param bool remove_intermediate: If True, also removes intermediate versions. In the case of a partitioned model,
            an intermediate version is created every time a partition has finished training. (defaults to **True**)
        """
        if not isinstance(versions, list):
            versions = [versions]
        body = {
            "versions": versions,
            "removeIntermediate": remove_intermediate
        }
        self.client._perform_empty(
            "POST", "/projects/%s/savedmodels/%s/actions/delete-versions" % (self.project_key, self.sm_id),
            body=body)

    def get_origin_ml_task(self):
        """
        Fetches the last ML task that has been exported to this saved model.

        :return: origin ML task or None if the saved model does not have an origin ml task
        :rtype: Union[:class:`dataikuapi.dss.ml.DSSMLTask`, None]
        """
        fmi = self.get_settings().get_raw().get("lastExportedFrom")
        if fmi is not None:
            return DSSMLTask.from_full_model_id(self.client, fmi, project_key=self.project_key)

    def import_mlflow_version_from_path(self, version_id, path, code_env_name="INHERIT",
                                        container_exec_config_name="NONE", set_active=True,
                                        binary_classification_threshold=0.5):
        """
        Creates a new version for this saved model from a path containing a MLFlow model.

        .. important::
            Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_mlflow_pyfunc_model`.

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :param str path: absolute path on the local filesystem - must be a folder, and must contain a MLFlow model
        :param str code_env_name: Name of the code env to use for this model version. The code env must contain at least
            mlflow and the package(s) corresponding to the used MLFlow-compatible frameworks.

            * If value is "INHERIT", the default active code env of the project will be used.

            (defaults to **INHERIT**)
        :param str container_exec_config_name: Name of the containerized execution configuration to use for reading
            the metadata of the model

            * If value is "INHERIT", the container execution configuration of the project will be used.
            * If value is "NONE", local execution will be used (no container)

            (defaults to **INHERIT**)
        :param bool set_active: sets this new version as the active version of the saved model (defaults to **True**)
        :param float binary_classification_threshold: for binary classification, defines the actual threshold for the
            imported version (defaults to **0.5**)
        :return: external model version handler in order to interact with the new MLFlow model version
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        # TODO: Add a check that it's indeed a MLFlow model folder
        import shutil
        import os

        archive_temp_dir = tempfile.mkdtemp()
        try:
            archive_filename = _make_zipfile(os.path.join(archive_temp_dir, "tmpmodel.zip"), path)

            with open(archive_filename, "rb") as fp:
                self.client._perform_empty(
                    "POST", "/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}".format(
                        project_id=self.project_key, saved_model_id=self.sm_id, version_id=version_id
                    ),
                    params={"codeEnvName": code_env_name, "containerExecConfigName": container_exec_config_name,
                            "setActive": set_active, "binaryClassificationThreshold": binary_classification_threshold},
                    files={"file": (archive_filename, fp)})
            return self.get_external_model_version_handler(version_id)
        finally:
            shutil.rmtree(archive_temp_dir)

    def import_mlflow_version_from_managed_folder(self, version_id, managed_folder, path, code_env_name="INHERIT",
                                                  container_exec_config_name="INHERIT", set_active=True,
                                                  binary_classification_threshold=0.5):
        """
        Creates a new version for this saved model from a managed folder.

        .. important::
            Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_mlflow_pyfunc_model`.

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :param managed_folder: managed folder, or identifier of the managed folder
        :type managed_folder: :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` or str
        :param str path: path of the MLflow folder in the managed folder
        :param str code_env_name: Name of the code env to use for this model version. The code env must contain at least
            mlflow and the package(s) corresponding to the used MLFlow-compatible frameworks.

            * If value is "INHERIT", the default active code env of the project will be used.

            (defaults to **INHERIT**)
        :param str container_exec_config_name: Name of the containerized execution configuration to use for reading the
            metadata of the model

            * If value is "INHERIT", the container execution configuration of the project will be used.
            * If value is "NONE", local execution will be used (no container)

            (defaults to **INHERIT**)
        :param bool set_active: sets this new version as the active version of the saved model (defaults to **True**)
        :param float binary_classification_threshold: for binary classification, defines the actual threshold for the
            imported version (defaults to **0.5**)
        :return: external model version handler in order to interact with the new MLFlow model version
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        # TODO: Add a check that it's indeed a MLflow model folder
        folder_ref = None
        if isinstance(managed_folder, DSSManagedFolder):
            folder_ref = "{}.{}".format(managed_folder.project_key, managed_folder.id)
        elif isinstance(managed_folder, dku_basestring_type):
            folder_ref = managed_folder
        else:
            raise Exception("managed_folder should either be a string representing the identifier of the managed folder"
                            " or an instance of dataikuapi.dss.managedfolder.DSSManagedFolder")

        self.client._perform_empty(
            "POST", "/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}".format(
                project_id=self.project_key, saved_model_id=self.sm_id, version_id=version_id
            ),
            params={
                "folderRef": folder_ref,
                "path": path,
                "codeEnvName": code_env_name,
                "containerExecConfigName": container_exec_config_name,
                "setActive": set_active,
                "binaryClassificationThreshold": binary_classification_threshold
            },
            files={"file": (None, None)}  # required for backend-mandated multipart request
        )
        return self.get_external_model_version_handler(version_id)

    def import_mlflow_version_from_databricks(self, version_id, connection_name, use_unity_catalog, model_name,
                                              model_version, code_env_name="INHERIT",
                                              container_exec_config_name="INHERIT",
                                              set_active=True, binary_classification_threshold=0.5):
        connection = self.client.get_connection(connection_name)
        connection_info = connection.get_info(self.project_key)
        if connection_info is None or connection_info["type"] != "DatabricksModelDeployment":
            raise ValueError("The connection " + connection_name + " is not a Databricks connection")
        if "params" not in connection_info:
            raise Exception("Permission to view details of the connection " + connection_name + "required")
        temp_folder = tempfile.mktemp()
        os.mkdir(temp_folder)
        try:
            with DatabricksRepositoryContextManager(connection_info, use_unity_catalog):
                self._download_from_databricks_registry(model_name, model_version, temp_folder)
            return self.import_mlflow_version_from_path(version_id, os.path.join(temp_folder),
                                                        code_env_name=code_env_name,
                                                        container_exec_config_name=container_exec_config_name,
                                                        set_active=set_active,
                                                        binary_classification_threshold=binary_classification_threshold)
        finally:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)

    @staticmethod
    def _download_from_databricks_registry(model_name, model_version, target_directory):
        from mlflow.store.artifact.models_artifact_repo import ModelsArtifactRepository
        mar = ModelsArtifactRepository("models:/{model_name}/{model_version}".format(model_name=model_name,
                                                                                     model_version=model_version))
        mar.download_artifacts("", dst_path=target_directory)

    def create_external_model_version(self, version_id, configuration, target_column_name=None,
                                      class_labels=None, set_active=True, binary_classification_threshold=0.5,
                                      input_dataset=None, selection=None, use_optimal_threshold=True,
                                      skip_expensive_reports=True, features_list=None, container_exec_config_name="NONE",
                                      input_format="GUESS", output_format="GUESS", evaluate=True):
        """
        Creates a new version of an external model.

        .. important::
            Requires the saved model to have been created using
            :meth:`dataikuapi.dss.project.DSSProject.create_external_model`.

        :param version_id: Identifier of the version, as returned by :meth:`list_versions`
        :type version_id: str
        :param configuration: A dictionary containing the desired saved model version configuration.

          * For SageMaker, syntax is:

            .. code-block:: python

                configuration = {
                    "protocol": "sagemaker",
                    "endpoint_name": "<endpoint-name>"
                }
  
          * For AzureML, syntax is:

            .. code-block:: python

                configuration = {
                    "protocol": "azure-ml",
                    "endpoint_name": "<endpoint-name>"
                }
  
          * For Vertex AI, syntax is:
  
            .. code-block:: python
            
                configuration = {
                    "protocol": "vertex-ai",
                    "endpoint_id": "<endpoint-id>"
                }
                
          * For Databricks, syntax is:
  
            .. code-block:: python
            
                configuration = {
                    "protocol": "databricks",
                    "endpointName": "<endpoint-id>"
                }
  
        :type configuration: dict
        :param target_column_name: Name of the target column. Mandatory if model performance will be evaluated
        :type target_column_name: str
        :param class_labels: List of strings, ordered class labels. Mandatory for evaluation of classification models
        :type class_labels: list or None
        :param set_active: (optional) Sets this new version as the active version of the saved model (defaults to **True**)
        :type set_active: bool
        :param binary_classification_threshold: (optional) For binary classification, defines the actual threshold for the
            imported version (defaults to **0.5**). Overwritten during evaluation if an evaluation dataset
            is specified and `use_optimal_threshold` is True
        :type binary_classification_threshold: float
        :param input_dataset: (mandatory if either evaluate=True, input_format=GUESS, output_format=GUESS, features_list is None)
            Dataset to use to infer the features names and types (if features_list is not set), evaluate the model, populate interpretation tabs,
            and guess input/output formats (if input_format=GUESS or output_format=GUESS).
        :type input_dataset: str or :class:`dataikuapi.dss.dataset.DSSDataset` or :class:`dataiku.Dataset`
        :param selection: (optional) Sampling parameter for input_dataset during evaluation.

            * Example 1: head 100 lines ``DSSDatasetSelectionBuilder().with_head_sampling(100)``
            * Example 2: random 500 lines ``DSSDatasetSelectionBuilder().with_random_fixed_nb_sampling(500)``
            * Example 3: head 100 lines ``{"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": 100}``

            Defaults to head 100 lines
        :type selection: dict or :class:`DSSDatasetSelectionBuilder` or None
        :param use_optimal_threshold: (optional) Set as threshold for this model version the threshold that has been computed
            during evaluation according to the metric set on the saved model setting
            (i.e. ``prediction_metrics_settings['thresholdOptimizationMetric']``)
        :type use_optimal_threshold: bool
        :param skip_expensive_reports: (optional) Skip computation of expensive/slow reports (e.g. feature importance).
        :type skip_expensive_reports: bool
        :param features_list: (optional) List of features, in JSON. Used if input_dataset is not defined
        :type features_list: list of ``{"name": "feature_name", "type": "feature_type"}`` or None

        :param container_exec_config_name: (optional) name of the containerized execution configuration to use for running the
            evaluation process.

            * If value is "INHERIT", the container execution configuration of the project will be used.
            * If value is "NONE", local execution will be used (no container)

        :type container_exec_config_name: str

        :param input_format: (optional) Input format to use when querying the underlying endpoint.
            For the 'azure-ml' and 'sagemaker' protocols, this option must be set if input_dataset is not set.
            Supported values are:

            * For all protocols:
                - GUESS (default): Guess the input format by cycling through supported input formats and making requests using data from input_dataset.

            * For Amazon SageMaker:
                - INPUT_SAGEMAKER_CSV
                - INPUT_SAGEMAKER_JSON
                - INPUT_SAGEMAKER_JSON_EXTENDED
                - INPUT_SAGEMAKER_JSONLINES
                - INPUT_DEPLOY_ANYWHERE_ROW_ORIENTED_JSON

            * For Vertex AI:
                - INPUT_VERTEX_DEFAULT

            * For Azure Machine Learning:
                - INPUT_AZUREML_JSON_INPUTDATA
                - INPUT_AZUREML_JSON_WRITER
                - INPUT_AZUREML_JSON_INPUTDATA_DATA
                - INPUT_DEPLOY_ANYWHERE_ROW_ORIENTED_JSON

            * For Databricks:
                - INPUT_RECORD_ORIENTED_JSON
                - INPUT_SPLIT_ORIENTED_JSON
                - INPUT_TF_INPUTS_JSON
                - INPUT_TF_INSTANCES_JSON
                - INPUT_DATABRICKS_CSV
        :type input_format: str

        :param output_format: (optional) Output format to use to parse the underlying endpoint's response.
            For the 'azure-ml' and 'sagemaker' protocols, this option must be set if input_dataset is not set.
            Supported values are:

            * For all protocols:
                - GUESS (default): Guess the output format by cycling through supported output formats and making requests using data from input_dataset.

            * For Amazon SageMaker:
                - OUTPUT_SAGEMAKER_CSV
                - OUTPUT_SAGEMAKER_ARRAY_AS_STRING
                - OUTPUT_SAGEMAKER_JSON
                - OUTPUT_DEPLOY_ANYWHERE_JSON

            * For Vertex AI:
                - OUTPUT_VERTEX_DEFAULT

            * For Azure Machine Learning:
                - OUTPUT_AZUREML_JSON_OBJECT
                - OUTPUT_AZUREML_JSON_ARRAY
                - OUTPUT_DEPLOY_ANYWHERE_JSON

            * For Databricks:
                - OUTPUT_DATABRICKS_JSON
        :type output_format: str

        :param evaluate: (optional) True (default) if this model should be evaluated using input_dataset, False to disable evaluation.
        :type evaluate: bool

        * Example: create a SageMaker Saved Model and add an endpoint as a version, evaluated on a dataset:

          .. code-block:: python
  
              import dataiku
              client = dataiku.api_client()
              project = client.get_default_project()
              # create a SageMaker saved model, whose endpoints are hosted in region eu-west-1
              sm = project.create_external_model("SaveMaker External Model", "BINARY_CLASSIFICATION", {"protocol": "sagemaker", "region": "eu-west-1"})
  
              # configuration to add endpoint
              configuration = {
                "protocol": "sagemaker",
                "endpoint_name": "titanic-survived-endpoint"
              }
              smv = sm.create_external_model_version("v0",
                                                configuration,
                                                target_column_name="Survived",
                                                class_labels=["0", "1"],
                                                input_dataset="evaluation_dataset")
  
          A dataset named "evaluation_dataset" must exist in the current project. Its schema and content should
          match the endpoint expectations. Depending on the way the model deployed on the endpoint was created,
          it may require a certain schema and not accept extra columns, it may not deal with missing features, etc.
  
        * Example: create a Vertex AI Saved Model and add an endpoint as a version, without evaluating it:

          .. code-block:: python

              import dataiku
              client = dataiku.api_client()
              project = client.get_default_project()
              # create a VertexAI saved model, whose endpoints are hosted in region europe-west-1
              sm = project.create_external_model("Vertex AI Proxy Model", "BINARY_CLASSIFICATION", {"protocol":"vertex-ai", "region":"europe-west1"})
              configuration = {
                  "protocol":"vertex-ai",
                  "project_id": "my-project",
                  "endpoint_id": "123456789012345678"
              }

              smv = sm.create_external_model_version("v1",
                                                  configuration,
                                                  target_column_name="Survived",
                                                  class_labels=["0", "1"],
                                                  input_dataset="titanic")

          A dataset named "my_dataset" must exist in the current project. It will be used to infer the schema of the
          data to submit to the endpoint. As there is no evaluation dataset specified, the interpretation tabs
          of this model version will be for the most empty. But the model still can be used to score datasets. It can also
          be evaluated on a dataset by an Evaluation Recipe.
        * Example: create an AzureML Saved Model

          .. code-block:: python

              import dataiku
              client = dataiku.api_client()
              project = client.get_default_project()
              # create an Azure ML saved model. No region specified, as this notion does not exist for Azure ML
              sm = project.create_external_model("Azure ML Proxy Model", "BINARY_CLASSIFICATION", {"protocol": "azure-ml"})
              configuration = {
                  "protocol": "azure-ml",
                  "subscription_id": "<subscription-id>>",
                  "resource_group": "<your.resource.group-rg>",
                  "workspace": "<your-workspace>",
                  "endpoint_name": "<endpoint-name>"
              }

              features_list = [{'name': 'Pclass', 'type': 'bigint'},
                               {'name': 'Age', 'type': 'double'},
                               {'name': 'SibSp', 'type': 'bigint'},
                               {'name': 'Parch', 'type': 'bigint'},
                               {'name': 'Fare', 'type': 'double'}]


              smv = sm.create_external_model_version("20230324-in-prod",
                                                  configuration,
                                                  target_column_name="Survived",
                                                  class_labels=["0", "1"],
                                                  features_list=features_list)
        * Example: minimalistic creation of a VertexAI model binary classification model

          .. code-block:: python

              import dataiku
              client = dataiku.api_client()
              project = client.get_default_project()

              sm = project.create_external_model("Raw Vertex AI Proxy Model", "BINARY_CLASSIFICATION", {"protocol": "vertex-ai", "region": "europe-west1"})
              configuration = {
                  "protocol": "vertex-ai",
                  "project_id": "my-project",
                  "endpoint_id": "123456789012345678"
              }

              smv = sm.create_external_model_version("legacy-model",
                                                  configuration,
                                                  class_labels=["0", "1"])

          This model will have empty interpretation tabs and can not be evaluated later by an Evaluation Recipe, as its
          target is not defined, but it can be scored.


        * Example: create a Databricks Saved Model

          .. code-block:: python

              import dataiku
              client = dataiku.api_client()
              project = client.get_default_project()

              sm = project.create_external_model("Databricks External Model", "BINARY_CLASSIFICATION", {"protocol": "databricks","connection": "db"})

              smv = sm.create_external_model_version("vX",
                                {"protocol": "databricks", "endpointName": "<endpoint-name>"},
                                target_column_name="Survived",
                                class_labels=["0", "1"],
                                input_dataset="train_titanic_prepared")

        """
        model_version = self._create_external_model_version(version_id, configuration, set_active,
                                                         binary_classification_threshold)
        model_version._set_core_external_metadata(target_column_name, class_labels, features_list, input_dataset,
                                        container_exec_config_name=container_exec_config_name,
                                        input_format=input_format,
                                        output_format=output_format)
        if evaluate:
            if input_dataset is None:
                raise ValueError("You must provide an input_dataset to evaluate this model, or set evaluate to False")
            model_version.evaluate(input_dataset, container_exec_config_name, selection, use_optimal_threshold, skip_expensive_reports)

    def _create_external_model_version(self, version_id, configuration, set_active=True,
                                   binary_classification_threshold=0.5):
        """
        .. important::
            Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_external_model`.

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :param dict configuration: A dictionary containing the required params for the selected protocol
        :param bool set_active: sets this new version as the active version of the saved model (defaults to **True**)
        :param float binary_classification_threshold: for binary classification, defines the actual threshold for the
            imported version (defaults to **0.5**)
        :return: external model version handler in order to interact with the new Proxy model version
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        import json

        # Set the type in configuration
        assert isinstance(configuration, dict), "configuration should be a dictionary containing the required params for the selected protocol"
        self.client._perform_empty(
            "POST", "/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}".format(
                project_id=self.project_key, saved_model_id=self.sm_id, version_id=version_id
            ),
            params={
                "setActive": set_active,
                "proxyModelVersionConfiguration": json.dumps(configuration),
                "binaryClassificationThreshold": binary_classification_threshold
            },
            files={"file": (None, None)}  # required for backend-mandated multipart request
        )
        return self.get_external_model_version_handler(version_id)

    def get_external_model_version_handler(self, version_id):
        """
        Returns a handler to interact with an external model version (MLflow or Proxy model)

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :return: external model version handler
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        return ExternalModelVersionHandler(self, version_id)

    ########################################################
    # Metrics
    ########################################################

    def get_metric_values(self, version_id):
        """
        Gets the values of the metrics on the specified version of this saved model

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :return: a list of metric objects and their value
        :rtype: list
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/metrics/%s" % (self.project_key, self.sm_id, version_id)))

    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this saved model

        :return: the saved model's flow zone
        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Moves this object to a flow zone

        :param object zone: flow zone where the object should be moved
        :type zone: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        if isinstance(zone, basestring):
           zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Shares this object to a flow zone

        :param object zone: flow zone where the object should be shared
        :type zone: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshares this object from a flow zone

        :param object zone: flow zone from which the object shouldn't be shared
        :type zone: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Gets the recipes referencing this model

        :return: a list of usages
        :rtype: list
        """
        return self.client._perform_json("GET", "/projects/%s/savedmodels/%s/usages" % (self.project_key, self.sm_id))

    def get_object_discussions(self):
        """
        Gets a handle to manage discussions on the saved model

        :return: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SAVED_MODEL", self.sm_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """Deletes the saved model"""
        return self.client._perform_empty("DELETE", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))


class MLFlowVersionSettings:
    """
    Handle for the settings of an imported MLFlow model version.

    .. important::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler.get_settings`

    :param version_handler: handler to interact with an external model version
    :type version_handler: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
    :param dict data: raw settings of the imported MLFlow model version
    """

    def __init__(self, version_handler, data):
        self.version_handler = version_handler
        self.data = data

    @property
    def raw(self):
        """
        :return: The raw settings of the imported MLFlow model version
        :rtype: dict
        """
        return self.data

    def save(self):
        """Saves the settings of this MLFlow model version"""
        self.version_handler.saved_model.client._perform_empty("PUT",
            "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.version_handler.saved_model.project_key, self.version_handler.saved_model.sm_id, self.version_handler.version_id),
            body=self.data)


class ExternalModelVersionHandler:
    """
    Handler to interact with an External model version (MLflow import of Proxy model).

    .. important::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.savedmodel.DSSSavedModel.get_external_model_version_handler`

    :param saved_model: the saved model object
    :type saved_model: :class:`dataikuapi.dss.savedmodel.DSSSavedModel`
    :param str version_id: identifier of the version, as returned by :meth:`dataikuapi.dss.savedmodel.DSSSavedModel.list_versions`
    """

    def __init__(self, saved_model, version_id):
        self.saved_model = saved_model
        self.version_id = version_id

    def get_settings(self):
        """
        Returns the settings of the MLFlow model version

        :return: settings of the MLFlow model version
        :rtype: :class:`dataikuapi.dss.savedmodel.MLFlowVersionSettings`
        """
        metadata = self.saved_model.client._perform_json("GET", "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id))
        return MLFlowVersionSettings(self, metadata)

    def _init_model_version_info(self, target_column_name, class_labels=None,
                                 get_features_from_dataset=None, features_list=None):
        if features_list is not None and get_features_from_dataset is not None:
            raise Exception("The information of the features should come either from the features_list or get_features_from_dataset, but not both.")

        metadata = self.saved_model.client._perform_json("GET", "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id))

        if target_column_name is not None:
            metadata["targetColumnName"] = target_column_name

        if class_labels is not None:
            metadata["classLabels"] = [{"label": label} for label in class_labels]

        if get_features_from_dataset is not None:
            metadata["gatherFeaturesFromDataset"] = get_features_from_dataset

        # TODO: add support for get_features_from_signature=False,
        # if get_features_from_signature:
        #    raise Exception("Get features from signature is not yet implemented")

        if features_list is not None:
            for feature in features_list:
                if not ("name" in feature and "type" in feature):
                    raise Exception("The features_list should be a list of {'name': 'feature_name', 'type': 'feature_type'}")
            metadata["features"] = features_list
        return metadata

    def _set_core_external_metadata(self,
            target_column_name, class_labels=None,
            features_list=None, input_dataset=None, container_exec_config_name="NONE",
            input_format="GUESS", output_format="GUESS"):
        """
            Sets core metadata of external models, see :meth:`DSSSavedModel.create_external_model_version` for details about parameters.
        """
        if features_list is not None:
            model_version_info = self._init_model_version_info(target_column_name, class_labels, None, features_list)
        else:
            model_version_info = self._init_model_version_info(target_column_name, class_labels, input_dataset, None)
        protocol = model_version_info["proxyModelVersionConfiguration"]["protocol"]
        if protocol == "vertex-ai":
            model_version_info["inputFormat"] = "INPUT_VERTEX_DEFAULT"
            model_version_info["outputFormat"] = "OUTPUT_VERTEX_DEFAULT"
        elif protocol in ["azure-ml", "sagemaker", "databricks"]:
            model_version_info["inputFormat"] = input_format
            model_version_info["outputFormat"] = output_format
            if input_dataset is not None:
                model_version_info["signatureAndFormatsGuessingDataset"] = input_dataset

        self.saved_model.client._perform_empty(
            "PUT",
            "/projects/{project_key}/savedmodels/{sm_id}/versions/{version_id}/external-ml/metadata?containerExecConfigName={container_exec_config_name}".format(
                project_key=self.saved_model.project_key,
                sm_id=self.saved_model.sm_id,
                version_id=self.version_id,
                container_exec_config_name=container_exec_config_name),
            body=model_version_info)

    def set_core_metadata(self,
            target_column_name, class_labels=None,
            get_features_from_dataset=None, features_list=None,
            container_exec_config_name="NONE"):
        """
        Sets metadata for this MLFlow model version

        In addition to ``target_column_name``, one of ``get_features_from_dataset`` or ``features_list`` must be passed in order
        to be able to evaluate performance

        :param str target_column_name: name of the target column. Mandatory in order to be able to evaluate performance
        :param class_labels: List of strings, ordered class labels. Mandatory in order to be able to evaluate performance on classification models
        :type class_labels: list or None
        :param get_features_from_dataset: name of a dataset to get feature names from
        :type get_features_from_dataset: str or None
        :param features_list: list of ``{"name": "feature_name", "type": "feature_type"}``
        :type features_list: list or None
        :param str container_exec_config_name: name of the containerized execution configuration to use for running the
            evaluation process.

            * If value is "INHERIT", the container execution configuration of the project will be used.
            * If value is "NONE", local execution will be used (no container)

            (defaults to **None**)
        """
        model_version_info = self._init_model_version_info(target_column_name, class_labels, get_features_from_dataset, features_list)
        self.saved_model.client._perform_empty(
            "PUT",
            "/projects/{project_key}/savedmodels/{sm_id}/versions/{version_id}/external-ml/metadata?containerExecConfigName={container_exec_config_name}".format(
                project_key=self.saved_model.project_key,
                sm_id=self.saved_model.sm_id,
                version_id=self.version_id,
                container_exec_config_name=container_exec_config_name
            ),
            body=model_version_info
        )

    def evaluate(self, dataset_ref, container_exec_config_name="INHERIT", selection=None, use_optimal_threshold=True,
                 skip_expensive_reports=True):
        """
        Evaluates the performance of this model version on a particular dataset.
        After calling this, the "result screens" of the MLFlow model version will be available
        (confusion matrix, error distribution, performance metrics, ...)
        and more information will be available when calling:
        :meth:`dataikuapi.dss.savedmodel.DSSSavedModel.get_version_details`

        Evaluation is available only for models having BINARY_CLASSIFICATION, MULTICLASS or REGRESSION as prediction type. See :meth:`DSSProject.create_mlflow_pyfunc_model`.

        .. important::
            :meth:`set_core_metadata` must be called before you can evaluate a dataset

        :param dataset_ref: Evaluation dataset to use
        :type dataset_ref: str or :class:`dataikuapi.dss.dataset.DSSDataset` or :class:`dataiku.Dataset`
        :param str container_exec_config_name: Name of the containerized execution configuration to use for running the
            evaluation process.

            * If value is "INHERIT", the container execution configuration of the project will be used.
            * If value is "NONE", local execution will be used (no container)

            (defaults to **INHERIT**)
        :param selection:
            Sampling parameter for the evaluation.

            * Example 1: ``DSSDatasetSelectionBuilder().with_head_sampling(100)``
            * Example 2: ``{"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": 100}``

            (defaults to **None**)
        :type selection: dict or :class:`DSSDatasetSelectionBuilder` or None
        :param bool use_optimal_threshold: Choose between optimized or actual threshold.
            Optimized threshold has been computed according to the metric set on the saved model setting
            (i.e. ``prediction_metrics_settings['thresholdOptimizationMetric']``)
            (defaults to **True**)
        :param boolean skip_expensive_reports: Skip expensive/slow reports (e.g. feature importance).
        """
        sampling_param = selection.build() if isinstance(
            selection, DSSDatasetSelectionBuilder) else selection

        if hasattr(dataset_ref, 'name'):
            dataset_ref = dataset_ref.name
        req = {
            "datasetRef": dataset_ref,
            "containerExecConfigName": container_exec_config_name,
            "samplingParam": sampling_param
        }
        post = ("/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}/external-ml/actions/evaluate"
                "?useOptimalThreshold={use_optimal_threshold}&skipExpensiveReports={skip_expensive_reports}").format(
            project_id=self.saved_model.project_key, saved_model_id=self.saved_model.sm_id, version_id=self.version_id,
            use_optimal_threshold=use_optimal_threshold, skip_expensive_reports=skip_expensive_reports)
        self.saved_model.client._perform_empty("POST", post, body=req)


class DSSSavedModelSettings:
    """
    Handle on the settings of a saved model.

    .. important::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSSavedModel.get_settings`

    :param saved_model: the saved model object
    :type saved_model: :class:`dataikuapi.dss.savedmodel.DSSSavedModel`
    :param dict settings: the settings of the saved model
    """

    def __init__(self, saved_model, settings):
        self.saved_model = saved_model
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw settings of the saved model

        :return: the raw settings of the saved model
        :rtype: dict
        """
        return self.settings

    @property
    def prediction_metrics_settings(self):
        """
        Returns the metrics-related settings

        :rtype: dict
        """
        return self.settings["miniTask"]["modeling"]["metrics"]

    def save(self):
        """Saves the settings of this saved model"""
        self.saved_model.client._perform_empty("PUT", "/projects/%s/savedmodels/%s" % (self.saved_model.project_key, self.saved_model.sm_id),
                                               body=self.settings)
