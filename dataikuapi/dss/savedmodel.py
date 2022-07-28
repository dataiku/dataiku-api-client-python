import tempfile

from .metrics import ComputedMetrics
from .ml import DSSMLTask
from .ml import DSSTrainedClusteringModelDetails
from .ml import DSSTrainedPredictionModelDetails
from .managedfolder import DSSManagedFolder

from ..utils import _make_zipfile, dku_basestring_type

try:
    basestring
except NameError:
    basestring = str

class DSSSavedModel(object):
    """
    A handle to interact with a saved model on the DSS instance.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_saved_model`
    """
    def __init__(self, client, project_key, sm_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.sm_id = sm_id
  
    @property
    def id(self):
        return self.sm_id

    def get_settings(self):
        """
        Returns the settings of this saved model.

        :rtype: DSSSavedModelSettings
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))
        return DSSSavedModelSettings(self, data)

        
    ########################################################
    # Versions
    ########################################################

    def list_versions(self):
        """
        Get the versions of this saved model
        
        :return: a list of the versions, as a dict of object. Each object contains at least a "id" parameter, which can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`
        :rtype: list
        """
        return self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions" % (self.project_key, self.sm_id))

    def get_active_version(self):
        """
        Gets the active version of this saved model
        
        :return: a dict representing the active version or None if no version is active. The dict contains at least a "id" parameter, which can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`
        :rtype: dict
        """
        filtered = [x for x in self.list_versions() if x["active"]]
        if len(filtered) == 0:
            return None
        else:
            return filtered[0]

    def get_version_details(self, version_id):
        """
        Gets details for a version of a saved model
        
        :param str version_id: Identifier of the version, as returned by :meth:`list_versions`

        :return: A :class:`DSSTrainedPredictionModelDetails` representing the details of this trained model id
        :rtype: :class:`DSSTrainedPredictionModelDetails`
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
        """Sets a particular version of the saved model as the active one"""
        self.client._perform_empty(
            "POST", "/projects/%s/savedmodels/%s/versions/%s/actions/setActive" % (self.project_key, self.sm_id, version_id))

    def delete_versions(self, versions, remove_intermediate=True):
        """
        Delete version(s) of the saved model

        :param versions: list of versions to delete
        :type versions: list[str]
        :param remove_intermediate: also remove intermediate versions (default: True). In the case of a partitioned
        model, an intermediate version is created every time a partition has finished training.
        :type remove_intermediate: bool
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
        Fetch the last ML task that has been exported to this saved model. Returns None if the saved model
        does not have an origin ml task.

        :rtype: DSSMLTask | None
        """
        fmi = self.get_settings().get_raw().get("lastExportedFrom")
        if fmi is not None:
            return DSSMLTask.from_full_model_id(self.client, fmi, project_key=self.project_key)

    def import_mlflow_version_from_path(self, version_id, path, code_env_name="INHERIT", container_exec_config_name="INHERIT"):
        """
        Create a new version for this saved model from a path containing a MLFlow model.

        Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_mlflow_pyfunc_model`.

        :param str version_id: Identifier of the version to create
        :param str path: An absolute path on the local filesystem. Must be a folder, and must contain a MLFlow model
        :param str code_env_name: Name of the code env to use for this model version. The code env must contain at least
                                  mlflow and the package(s) corresponding to the used MLFlow-compatible frameworks.
                                  If value is "INHERIT", the default active code env of the project will be used
        :param str container_exec_config_name: Name of the containerized execution configuration to use while creating
                                  this model version.
                                  If value is "INHERIT", the container execution configuration of the project will be used.
                                  If value is "NONE", local execution will be used (no container)
        :return a :class:MLFlowVersionHandler in order to interact with the new MLFlow model version
        """
        # TODO: Add a check that it's indeed a MLFlow model folder
        import shutil
        import os

        archive_temp_dir = tempfile.mkdtemp()
        try:
            archive_filename = _make_zipfile(os.path.join(archive_temp_dir, "tmpmodel.zip"), path)

            with open(archive_filename, "rb") as fp:
                self.client._perform_empty("POST", "/projects/%s/savedmodels/%s/versions/%s?codeEnvName=%s&containerExecConfigName=%s" % (self.project_key, self.sm_id, version_id, code_env_name, container_exec_config_name),
                                           files={"file": (archive_filename, fp)})
            return self.get_mlflow_version_handler(version_id)
        finally:
            shutil.rmtree(archive_temp_dir)

    def import_mlflow_version_from_managed_folder(self, version_id, managed_folder, path, code_env_name="INHERIT", container_exec_config_name="INHERIT"):
        """
        Create a new version for this saved model from a path containing a MLFlow model in a managed folder.

        Requires the saved model to have been created using :meth:`dataikuapi.dss.project.DSSProject.create_mlflow_pyfunc_model`.

        :param str version_id: Identifier of the version to create
        :param str managed_folder: Identifier of the managed folder or `dataikuapi.dss.managedfolder.DSSManagedFolder`
        :param str path: Path of the MLflow folder in the managed folder
        :param str code_env_name: Name of the code env to use for this model version. The code env must contain at least
                                  mlflow and the package(s) corresponding to the used MLFlow-compatible frameworks.
                                  If value is "INHERIT", the default active code env of the project will be used
        :param str container_exec_config_name: Name of the containerized execution configuration to use for evaluating
                                  this model version.
                                  If value is "INHERIT", the container execution configuration of the project will be used.
                                  If value is "NONE", local execution will be used (no container)
        :return a :class:MLFlowVersionHandler in order to interact with the new MLFlow model version
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
            "POST", "/projects/{project_id}/savedmodels/{saved_model_id}/versions/{version_id}?codeEnvName={codeEnvName}&containerExecConfigName={containerExecConfigName}".format(
                project_id=self.project_key, saved_model_id=self.sm_id, version_id=version_id, codeEnvName=code_env_name, containerExecConfigName=container_exec_config_name
            ),
            params={"folderRef": folder_ref, "path": path},
            files={"file": (None, None)}  # required for backend-mandated multipart request
        )
        return self.get_mlflow_version_handler(version_id)

    def get_mlflow_version_handler(self, version_id):
        """
        Returns a :class:MLFlowVersionHandler to interact with a MLFlow model version
        """
        return MLFlowVersionHandler(self, version_id)

    ########################################################
    # Metrics
    ########################################################

    def get_metric_values(self, version_id):
        """
        Get the values of the metrics on the version of this saved model
        
        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/metrics/%s" % (self.project_key, self.sm_id, version_id)))

                
    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this saved model

        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Moves this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object
        """
        if isinstance(zone, basestring):
           zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Share this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to share the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshare this object from a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` from where to unshare the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Get the recipes referencing this model

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/savedmodels/%s/usages" % (self.project_key, self.sm_id))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the saved model

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SAVED_MODEL", self.sm_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the saved model

        """
        return self.client._perform_empty("DELETE", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))

class MLFlowVersionSettings:
    """Handle for the settings of an imported MLFlow model version"""

    def __init__(self, version_handler, data):
        self.version_handler = version_handler
        self.data = data

    @property
    def raw(self):
        return self.data

    def save(self):
        self.version_handler.saved_model.client._perform_empty("PUT", 
            "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.version_handler.saved_model.project_key, self.version_handler.saved_model.sm_id, self.version_handler.version_id),
            body=self.data)

class MLFlowVersionHandler:
    """Handler to interact with an imported MLFlow model version"""
    def __init__(self, saved_model, version_id):
        """Do not call this, use :meth:`DSSSavedModel.get_mlflow_version_handler`"""
        self.saved_model = saved_model
        self.version_id = version_id

    def get_settings(self):
        metadata = self.saved_model.client._perform_json("GET", "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id))
        return MLFlowVersionSettings(self, metadata)

    def set_core_metadata(self,
        target_column_name, class_labels = None,
        get_features_from_dataset=None, features_list = None,
        output_style="AUTO_DETECT"):
        """
        Sets metadata for this MLFlow model version

        In addition to target_column_name, one of get_features_from_dataset or features_list must be passed in order
        to be able to evaluate performance

        :param str target_column_name: name of the target column. Mandatory in order to be able to evaluate performance
        :param list class_labels: List of strings, ordered class labels. Mandatory in order to be able to evaluate performance on classification models
        :param str get_features_from_dataset: Name of a dataset to get feature names from
        :param list features_list: List of {"name": "feature_name", "type": "feature_type"}
        """

        if features_list is not None and get_features_from_dataset is not None:
            raise Exception("The information of the features should come either from the features_list or get_features_from_dataset, but not both.")

        metadata = self.saved_model.client._perform_json("GET", "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id))

        if target_column_name is not None:
            metadata["targetColumnName"] = target_column_name

        if class_labels is not None:
            metadata["classLabels"] = [{"label": l} for l in class_labels]

        if get_features_from_dataset is not None:
            metadata["gatherFeaturesFromDataset"] = get_features_from_dataset

        # TODO: add support for get_features_from_signature=False,
        #if get_features_from_signature:
        #    raise Exception("Get features from signature is not yet implemented")

        if features_list is not None:
            for feature in features_list:
                if not ("name" in feature and "type" in feature):
                    raise Exception("The features_list should be a list of {'name': 'feature_name', 'type': 'feature_type'}")
            metadata["features"] = features_list

        self.saved_model.client._perform_empty("PUT",
            "/projects/%s/savedmodels/%s/versions/%s/external-ml/metadata" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id),
            body=metadata)

    def evaluate(self, dataset_ref, container_exec_config_name="INHERIT"):
        """
        Evaluates the performance of this model version on a particular dataset.
        After calling this, the "result screens" of the MLFlow model version will be available
        (confusion matrix, error distribution, performance metrics, ...)
        and more information will be available when calling :meth:`DSSSavedModel.get_version_details`

        :meth:`set_core_metadata` must be called before you can evaluate a dataset
        :param str dataset_ref: Evaluation dataset to use (either a dataset name, "PROJECT.datasetName", :class:`DSSDataset` instance or :class:`dataiku.Dataset` instance)
        :param str container_exec_config_name: Name of the containerized execution configuration to use for running the evaluation process.
                                  If value is "INHERIT", the container execution configuration of the project will be used.
                                  If value is "NONE", local execution will be used (no container)
        """
        if hasattr(dataset_ref, 'name'):
            dataset_ref = dataset_ref.name
        req = {
            "datasetRef": dataset_ref,
            "containerExecConfigName": container_exec_config_name
        }
        self.saved_model.client._perform_empty("POST",
            "/projects/%s/savedmodels/%s/versions/%s/external-ml/actions/evaluate" % (self.saved_model.project_key, self.saved_model.sm_id, self.version_id),
            body=req)


class DSSSavedModelSettings:
    """
    A handle on the settings of a saved model

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSSavedModel.get_settings`
    """

    def __init__(self, saved_model, settings):
        self.saved_model = saved_model
        self.settings = settings

    def get_raw(self):
        return self.settings

    @property
    def prediction_metrics_settings(self):
        """The settings of evaluation metrics for a prediction saved model"""
        return self.settings["miniTask"]["modeling"]["metrics"]

    def save(self):
        """Saves the settings of this saved model"""
        self.saved_model.client._perform_empty("PUT", "/projects/%s/savedmodels/%s" % (self.saved_model.project_key, self.saved_model.sm_id),
                    body=self.settings)
