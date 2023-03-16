
import tempfile

from dataikuapi.dss.utils import DSSDatasetSelectionBuilder
from .discussion import DSSObjectDiscussions
from .managedfolder import DSSManagedFolder
from .metrics import ComputedMetrics
from .ml import DSSMLTask
from .ml import DSSTrainedClusteringModelDetails
from .ml import DSSTrainedPredictionModelDetails
from ..utils import _make_zipfile, dku_basestring_type

try:
    basestring
except NameError:
    basestring = str


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

        :return: a list of the versions, as a dict of object. Each object contains at least an "id" parameter, which
            can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`
        :rtype: list
        """
        return self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions" % (self.project_key, self.sm_id))

    def get_active_version(self):
        """
        Gets the active version of this saved model.

        :return: a dict representing the active version or None if no version is active.
            The dict contains at least an "id" parameter, which can be passed to :meth:`get_metric_values`,
            :meth:`get_version_details` and :meth:`set_active_version`.
        :rtype: dict or None
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
        else:
            return DSSTrainedPredictionModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)

    def set_active_version(self, version_id):
        """
        Sets a particular version of the saved model as the active one.

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
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
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTask` or None
        """
        fmi = self.get_settings().get_raw().get("lastExportedFrom")
        if fmi is not None:
            return DSSMLTask.from_full_model_id(self.client, fmi, project_key=self.project_key)

    def import_mlflow_version_from_path(self, version_id, path, code_env_name="INHERIT", container_exec_config_name="NONE", set_active=True,
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
        :param str container_exec_config_name: Name of the containerized execution configuration to use for running the
            evaluation process.

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
                    params={"codeEnvName": code_env_name, "containerExecConfigName": container_exec_config_name, "setActive": set_active,
                            "binaryClassificationThreshold": binary_classification_threshold},
                    files={"file": (archive_filename, fp)})
            return self.get_external_model_version_handler(version_id)
        finally:
            shutil.rmtree(archive_temp_dir)

    def import_mlflow_version_from_managed_folder(self, version_id, managed_folder, path, code_env_name="INHERIT", container_exec_config_name="INHERIT",
                                                  set_active=True, binary_classification_threshold=0.5):
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
        :param str container_exec_config_name: Name of the containerized execution configuration to use for running the
            evaluation process.

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

    def create_proxy_model_version(self, version_id, protocol, configuration):
        """
        EXPERIMENTAL. Creates a new version of a proxy model.

        This is an experimental API, subject to change.

        .. important::
            Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_proxy_model`.

        :param str version_id: identifier of the version, as returned by :meth:`list_versions`
        :param str protocol: one of ["KServe", "DSS_API_NODE"]
        :param dict configuration: A dictionary containing the required params for the selected protocol
        :return: external model version handler in order to interact with the new Proxy model version
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        import json

        # Set the type in configuration
        assert isinstance(configuration, dict), "configuration should be a dictionary containing the required params for the selected protocol"
        configuration["protocol"] = protocol
        self.client._perform_empty(
            "POST", "/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}?containerExecConfigName={containerExecConfigName}".format(
                project_id=self.project_key, saved_model_id=self.sm_id, version_id=version_id, containerExecConfigName="NONE"
            ),
            params={"configuration": json.dumps(configuration)},
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
        Gets the values of the metrics on the version of this saved model

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
        """The raw settings of the imported MLFlow model version"""
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

    def set_core_metadata(self,
            target_column_name, class_labels=None,
            get_features_from_dataset=None, features_list=None,
            output_style="AUTO_DETECT", container_exec_config_name="NONE"):
        """
        Sets metadata for this MLFlow model version

        In addition to ``target_column_name``, one of ``get_features_from_dataset`` or ``features_list`` must be passed in order
        to be able to evaluate performance

        :param str target_column_name: name of the target column. Mandatory in order to be able to evaluate performance
        :param class_labels: List of strings, ordered class labels. Mandatory in order to be able to evaluate performance on classification models
        :type class_labels: list or None
        :param get_features_from_dataset: mame of a dataset to get feature names from
        :type get_features_from_dataset: str or None
        :param features_list: list of ``{"name": "feature_name", "type": "feature_type"}``
        :type features_list: list or None
        :param str container_exec_config_name: name of the containerized execution configuration to use for running the
            evaluation process.

                * If value is "INHERIT", the container execution configuration of the project will be used.
                * If value is "NONE", local execution will be used (no container)

            (defaults to **None**)
        """

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

        self.saved_model.client._perform_empty(
            "PUT",
            "/projects/{project_key}/savedmodels/{sm_id}/versions/{version_id}/external-ml/metadata?containerExecConfigName={container_exec_config_name}".format(
                project_key=self.saved_model.project_key,
                sm_id=self.saved_model.sm_id,
                version_id=self.version_id,
                container_exec_config_name=container_exec_config_name),
            body=metadata)

    def evaluate(self, dataset_ref, container_exec_config_name="INHERIT", selection=None, use_optimal_threshold=True):
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
                "?useOptimalThreshold={use_optimal_threshold}").format(
            project_id=self.saved_model.project_key, saved_model_id=self.saved_model.sm_id, version_id=self.version_id,
            use_optimal_threshold=use_optimal_threshold)
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
