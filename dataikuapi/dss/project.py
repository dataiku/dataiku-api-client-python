import warnings, os.path as osp

from ..dss_plugin_mlflow import MLflowHandle

from .dataset import DSSDataset, DSSDatasetListItem, DSSManagedDatasetCreationHelper
from .modelcomparison import DSSModelComparison
from .jupyternotebook import DSSJupyterNotebook, DSSJupyterNotebookListItem
from .notebook import DSSNotebook
from .streaming_endpoint import DSSStreamingEndpoint, DSSStreamingEndpointListItem, DSSManagedStreamingEndpointCreationHelper
from .recipe import DSSRecipeListItem, DSSRecipe
from . import recipe
from .managedfolder import DSSManagedFolder
from .savedmodel import DSSSavedModel
from .modelevaluationstore import DSSModelEvaluationStore
from .mlflow import DSSMLflowExtension
from .job import DSSJob, DSSJobWaiter
from .scenario import DSSScenario, DSSScenarioListItem
from .continuousactivity import DSSContinuousActivity
from .apiservice import DSSAPIService
from .future import DSSFuture
from .macro import DSSMacro
from .wiki import DSSWiki
from .discussion import DSSObjectDiscussions
from .ml import DSSMLTask, DSSMLTaskQueues
from .analysis import DSSAnalysis
from .flow import DSSProjectFlow
from .app import DSSAppManifest
from .codestudio import DSSCodeStudioObject, DSSCodeStudioObjectListItem

class DSSProject(object):
    """
    A handle to interact with a project on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_project`
    """
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def get_summary(self):
        """
        Returns a summary of the project. The summary is a read-only view of some of the state of the project.
        You cannot edit the resulting dict and use it to update the project state on DSS, you must use the other more
        specific methods of this :class:`dataikuapi.dss.project.DSSProject` object

        :returns: a dict containing a summary of the project. Each dict contains at least a 'projectKey' field
        :rtype: dict
        """
        return self.client._perform_json("GET", "/projects/%s" % self.project_key)

    def get_project_folder(self):
        """
        Returns the :class:`dataikuapi.dss.projectfolder.DSSProjectFolder` containing this project
        :rtype: :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        root = self.client.get_root_project_folder()

        def rec(pf):
            if self.project_key in pf.list_project_keys():
                return pf
            else:
                for spf in pf.list_child_folders():
                    found_in_child = rec(spf)
                    if found_in_child:
                        return found_in_child
            return None

        found_in = rec(root)
        if found_in:
            return found_in
        else:
            return root

    def move_to_folder(self, folder):
        """
        Moves this project to a project folder
        :param folder :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        current_folder = self.get_project_folder()
        current_folder.move_project_to(self.project_key, folder)

    ########################################################
    # Project deletion
    ########################################################

    def delete(self, clear_managed_datasets=False, clear_output_managed_folders=False, clear_job_and_scenario_logs=True, **kwargs):
        """
        Delete the project

        This call requires an API key with admin rights

        :param bool clear_managed_datasets: Should the data of managed datasets be cleared
        :param bool clear_output_managed_folders: Should the data of managed folders used as outputs of recipes be cleared
        :param bool clear_job_and_scenario_logs: Should the job and scenario logs be cleared
        """
        # For backwards compatibility
        if 'drop_data' in kwargs and kwargs['drop_data']:
            clear_managed_datasets = True

        return self.client._perform_empty(
            "DELETE", "/projects/%s" % self.project_key, params={
                "clearManagedDatasets": clear_managed_datasets,
                "clearOutputManagedFolders": clear_output_managed_folders,
                "clearJobAndScenarioLogs": clear_job_and_scenario_logs
            })

    ########################################################
    # Project export
    ########################################################

    def get_export_stream(self, options=None):
        """
        Return a stream of the exported project
        You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param dict options: Dictionary of export options (defaults to `{}`). The following options are available:

            * exportUploads (boolean): Exports the data of Uploaded datasets - default False
            * exportManagedFS (boolean): Exports the data of managed Filesystem datasets - default False
            * exportAnalysisModels (boolean): Exports the models trained in analysis - default False
            * exportSavedModels (boolean): Exports the models trained in saved models - default False
            * exportManagedFolders (boolean): Exports the data of managed folders - default False
            * exportAllInputDatasets (boolean): Exports the data of all input datasets - default False
            * exportAllDatasets (boolean): Exports the data of all datasets - default False
            * exportAllInputManagedFolders (boolean): Exports the data of all input managed folders - default False
            * exportGitRepositoy (boolean): Exports the Git repository history - default False
            * exportInsightsData (boolean): Exports the data of static insights - default False

        :returns: a file-like obbject that is a stream of the export archive
        :rtype: file-like
        """
        if options is None:
            options = {}
        return self.client._perform_raw(
            "POST", "/projects/%s/export" % self.project_key, body=options).raw

    def export_to_file(self, path, options=None):
        """
        Export the project to a file
        
        :param str path: the path of the file in which the exported project should be saved
        :param dict options: Dictionary of export options (defaults to `{}`). The following options are available:

            * exportUploads (boolean): Exports the data of Uploaded datasets - default False
            * exportManagedFS (boolean): Exports the data of managed Filesystem datasets - default False
            * exportAnalysisModels (boolean): Exports the models trained in analysis - default False
            * exportSavedModels (boolean): Exports the models trained in saved models - default False
            * exportModelEvaluationStores (boolean): Exports the evaluation stores - default False
            * exportManagedFolders (boolean): Exports the data of managed folders - default False
            * exportAllInputDatasets (boolean): Exports the data of all input datasets - default False
            * exportAllDatasets (boolean): Exports the data of all datasets - default False
            * exportAllInputManagedFolders (boolean): Exports the data of all input managed folders - default False
            * exportGitRepository (boolean): Exports the Git repository history - default False
            * exportInsightsData (boolean): Exports the data of static insights - default False
        """
        if options is None:
            options = {}
        with open(path, 'wb') as f:
            export_stream = self.client._perform_raw(
                "POST", "/projects/%s/export" % self.project_key, body=options)
            for chunk in export_stream.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
            f.flush()

    ########################################################
    # Project duplicate
    ########################################################

    def duplicate(self, target_project_key,
                  target_project_name,
                  duplication_mode="MINIMAL",
                  export_analysis_models=True,
                  export_saved_models=True,
                  export_git_repository=True,
                  export_insights_data=True,
                  remapping=None,
                  target_project_folder=None):
        """
        Duplicate the project

        :param string target_project_key: The key of the new project
        :param string target_project_name: The name of the new project
        :param string duplication_mode: can be one of the following values: MINIMAL, SHARING, FULL, NONE
        :param bool export_analysis_models:
        :param bool export_saved_models:
        :param bool export_git_repository:
        :param bool export_insights_data:
        :param dict remapping: dict of connections to be remapped for the new project (defaults to `{}`)
        :param target_project_folder: the project folder where to put the duplicated project
        :type target_project_folder: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder
        :returns: A dict containing the original and duplicated project's keys
        :rtype: :class:`ProjectDuplicateResult`
        """
        if remapping is None:
            remapping = {}
        obj = {
            "targetProjectName": target_project_name,
            "targetProjectKey": target_project_key,
            "duplicationMode": duplication_mode,
            "exportAnalysisModels": export_analysis_models,
            "exportSavedModels": export_saved_models,
            "exportGitRepository": export_git_repository,
            "exportInsightsData": export_insights_data,
            "remapping": remapping
        }
        if target_project_folder is not None:
            obj["targetProjectFolderId"] = target_project_folder.project_folder_id

        ref = self.client._perform_json("POST", "/projects/%s/duplicate/" % self.project_key, body = obj)
        return ref

    ########################################################
    # Project infos
    ########################################################

    def get_metadata(self):
        """
        Get the metadata attached to this project. The metadata contains label, description
        checklists, tags and custom metadata of the project.

        For more information on available metadata, please see https://doc.dataiku.com/dss/api/6.0/rest/
        
        :returns: a dict object containing the project metadata.
        :rtype: dict
        """
        return self.client._perform_json("GET", "/projects/%s/metadata" % self.project_key)

    def set_metadata(self, metadata):
        """
        Set the metadata on this project.
        
        :param metadata dict: the new state of the metadata for the project. You should only set a metadata object that has been retrieved using the :meth:`get_metadata` call.
        """
        return self.client._perform_empty(
            "PUT", "/projects/%s/metadata" % self.project_key, body = metadata)

    def get_settings(self):
        """
        Gets the settings of this project. This does not contain permissions. See :meth:`get_permissions`

        :returns a handle to read, modify and save the settings
        :rtype: :class:`DSSProjectSettings`
        """
        ret = self.client._perform_json("GET", "/projects/%s/settings" % self.project_key)
        return DSSProjectSettings(self.client, self.project_key, ret)

    def get_permissions(self):
       """
       Get the permissions attached to this project

        :returns: A dict containing the owner and the permissions, as a list of pairs of group name and permission type
       """
       return self.client._perform_json(
          "GET", "/projects/%s/permissions" % self.project_key)

    def set_permissions(self, permissions):
        """
        Sets the permissions on this project
        
        :param permissions dict: a permissions object with the same structure as the one returned by :meth:`get_permissions` call
        """
        return self.client._perform_empty(
            "PUT", "/projects/%s/permissions" % self.project_key, body = permissions)

    def get_interest(self):
        """
        Get the interest of this project. The interest means the number of watchers and the number of stars.

        :returns: a dict object containing the interest of the project with two fields:
           - starCount: number of stars for this project
           - watchCount: number of users watching this project
        :rtype: dict
        """
        return self.client._perform_json("GET","/projects/%s/interest" % self.project_key)

    def get_timeline(self, item_count=100):
        """
        Get the timeline of this project. The timeline consists of information about the creation of this project
        (by whom, and when), the last modification of this project (by whom and when), a list of contributors,
        and a list of modifications. This list of modifications contains a maximum of `item_count` elements (default: 100).
        If `item_count` is greater than the real number of modification, `item_count` is adjusted.

        :return: a dict object containing a timeline where the top-level fields are :
          - allContributors: all contributors who have been involve in this project
          - items: a history of the modifications of the project
          - createdBy: who created this project
          - createdOn: when the project was created
          - lastModifiedBy: who modified this project for the last time
          - lastModifiedOn: when this modification took place
        :rtype: dict
        """
        return self.client._perform_json("GET", "/projects/%s/timeline" % self.project_key, params = {
            "itemCount": item_count
        })

    ########################################################
    # Datasets
    ########################################################

    def list_datasets(self, as_type="listitems"):
        """
        List the datasets in this project.

        :param str as_type: How to return the list. Supported values are "listitems" and "objects".
        :returns: The list of the datasets. If "as_type" is "listitems", each one as a :class:`dataset.DSSDatasetListItem`.
                  If "as_type" is "objects", each one as a :class:`dataset.DSSDataset`
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/datasets/" % self.project_key)
        if as_type == "listitems" or as_type == "listitem":
            return [DSSDatasetListItem(self.client, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSDataset(self.client, self.project_key, item["name"]) for item in items]
        else:
            raise ValueError("Unknown as_type")

    def get_dataset(self, dataset_name):
        """
        Get a handle to interact with a specific dataset
       
        :param string dataset_name: the name of the desired dataset
        
        :returns: A :class:`dataikuapi.dss.dataset.DSSDataset` dataset handle
        """
        return DSSDataset(self.client, self.project_key, dataset_name)

    def create_dataset(self, dataset_name, type,
                params=None, formatType=None, formatParams=None):
        """
        Create a new dataset in the project, and return a handle to interact with it.

        The precise structure of ``params`` and ``formatParams`` depends on the specific dataset 
        type and dataset format type. To know which fields exist for a given dataset type and format type,
        create a dataset from the UI, and use :meth:`get_dataset` to retrieve the configuration
        of the dataset and inspect it. Then reproduce a similar structure in the :meth:`create_dataset` call.

        Not all settings of a dataset can be set at creation time (for example partitioning). After creation,
        you'll have the ability to modify the dataset
        
        :param string dataset_name: the name for the new dataset
        :param string type: the type of the dataset
        :param dict params: the parameters for the type, as a JSON object (defaults to `{}`)
        :param string formatType: an optional format to create the dataset with (only for file-oriented datasets)
        :param dict formatParams: the parameters to the format, as a JSON object (only for file-oriented datasets, default to `{}`)
        
        Returns:
            A :class:`dataikuapi.dss.dataset.DSSDataset` dataset handle
        """
        if params is None:
            params = {}
        if formatParams is None:
            formatParams = {}
        obj = {
            "name" : dataset_name,
            "projectKey" : self.project_key,
            "type" : type,
            "params" : params,
            "formatType" : formatType,
            "formatParams" : formatParams
        }
        self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key,
                       body = obj)
        return DSSDataset(self.client, self.project_key, dataset_name)

    def create_upload_dataset(self, dataset_name, connection=None):
        obj = {
            "name" : dataset_name,
            "projectKey" : self.project_key,
            "type" : "UploadedFiles",
            "params" : {}
        }
        if connection is not None:
            obj["params"]["uploadConnection"] = connection
        self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key,
                       body = obj)
        return DSSDataset(self.client, self.project_key, dataset_name)

    def create_filesystem_dataset(self, dataset_name, connection, path_in_connection):
        return self.create_fslike_dataset(dataset_name, "Filesystem", connection, path_in_connection)

    def create_s3_dataset(self, dataset_name, connection, path_in_connection, bucket=None):
        """
        Creates a new external S3 dataset in the project and returns a :class:`~dataikuapi.dss.dataset.DSSDataset` to interact with it.

        The created dataset doesn not have its format and schema initialized, it is recommend to use 
        :meth:`~dataikuapi.dss.dataset.DSSDataset.autodetect_settings` on the returned object

        :param dataset_name: Name of the dataset to create. Must not already exist
        :rtype: `~dataikuapi.dss.dataset.DSSDataset`
        """
        extra_params = {}
        if bucket is not None:
            extra_params["bucket"] = bucket
        return self.create_fslike_dataset(dataset_name, "S3", connection, path_in_connection, extra_params)

    def create_fslike_dataset(self, dataset_name, dataset_type, connection, path_in_connection, extra_params=None):
        body = {
            "name" : dataset_name,
            "projectKey" : self.project_key,
            "type" : dataset_type,
            "params" : {
                "connection" : connection,
                "path": path_in_connection
            }
        }
        if extra_params is not None:
            body["params"].update(extra_params)
        self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key, body = body)
        return DSSDataset(self.client, self.project_key, dataset_name)

    def create_sql_table_dataset(self, dataset_name, type, connection, table, schema):
        obj = {
            "name" : dataset_name,
            "projectKey" : self.project_key,
            "type" : type,
            "params" : {
                "connection" : connection,
                "mode": "table",
                "table" : table,
                "schema" : schema
            }
        }
        self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key,
                       body = obj)
        return DSSDataset(self.client, self.project_key, dataset_name)

    def new_managed_dataset_creation_helper(self, dataset_name):
        """Deprecated. Please use :meth:`new_managed_dataset`"""
        warnings.warn("new_managed_dataset_creation_helper is deprecated, please use new_managed_dataset", DeprecationWarning)
        return DSSManagedDatasetCreationHelper(self, dataset_name)

    def new_managed_dataset(self, dataset_name):
        """
        Initializes the creation of a new managed dataset. Returns a :class:`dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper`
        or one of its subclasses to complete the creation of the managed dataset.

        Usage example:

        .. code-block:: python

            builder = project.new_managed_dataset("my_dataset")
            builder.with_store_into("target_connection")
            dataset = builder.create()

        :param str dataset_name: Name of the dataset to create
        :rtype: :class:`dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper`
        :return: A :class:`dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper` object to create the managed dataset
        """
        return DSSManagedDatasetCreationHelper(self, dataset_name)

    ########################################################
    # Streaming endpoints
    ########################################################

    def list_streaming_endpoints(self, as_type="listitems"):
        """
        List the streaming endpoints in this project.

        :param str as_type: How to return the list. Supported values are "listitems" and "objects".
        :returns: The list of the streaming endpoints. If "as_type" is "listitems", each one as a :class:`streaming_endpoint.DSSStreamingEndpointListItem`.
                  If "as_type" is "objects", each one as a :class:`streaming_endpoint.DSSStreamingEndpoint`
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/streamingendpoints/" % self.project_key)
        if as_type == "listitems" or as_type == "listitem":
            return [DSSStreamingEndpointListItem(self.client, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSStreamingEndpoint(self.client, self.project_key, item["id"]) for item in items]
        else:
            raise ValueError("Unknown as_type")

    def get_streaming_endpoint(self, streaming_endpoint_name):
        """
        Get a handle to interact with a specific streaming endpoint
       
        :param string streaming_endpoint_name: the name of the desired streaming endpoint
        
        :returns: A :class:`dataikuapi.dss.streaming_endpoint.DSSStreamingEndpoint` streaming endpoint handle
        """
        return DSSStreamingEndpoint(self.client, self.project_key, streaming_endpoint_name)

    def create_streaming_endpoint(self, streaming_endpoint_name, type, params=None):
        """
        Create a new streaming endpoint in the project, and return a handle to interact with it.

        The precise structure of ``params`` depends on the specific streaming endpoint 
        type. To know which fields exist for a given streaming endpoint type,
        create a streaming endpoint from the UI, and use :meth:`get_streaming_endpoint` to retrieve the configuration
        of the streaming endpoint and inspect it. Then reproduce a similar structure in the :meth:`create_streaming_endpoint` call.

        Not all settings of a streaming endpoint can be set at creation time (for example partitioning). After creation,
        you'll have the ability to modify the streaming endpoint
        
        :param string streaming_endpoint_name: the name for the new streaming endpoint
        :param string type: the type of the streaming endpoint
        :param dict params: the parameters for the type, as a JSON object (defaults to `{}`)
        
        Returns:
            A :class:`dataikuapi.dss.streaming_endpoint.DSSStreamingEndpoint` streaming endpoint handle
        """
        if params is None:
            params = {}
        obj = {
            "id" : streaming_endpoint_name,
            "projectKey" : self.project_key,
            "type" : type,
            "params" : params
        }
        self.client._perform_json("POST", "/projects/%s/streamingendpoints/" % self.project_key,
                       body = obj)
        return DSSStreamingEndpoint(self.client, self.project_key, streaming_endpoint_name)

    def create_kafka_streaming_endpoint(self, streaming_endpoint_name, connection=None, topic=None):
        obj = {
            "id" : streaming_endpoint_name,
            "projectKey" : self.project_key,
            "type" : "kafka",
            "params" : {}
        }
        if connection is not None:
            obj["params"]["connection"] = connection
        if topic is not None:
            obj["params"]["topic"] = topic
        self.client._perform_json("POST", "/projects/%s/streamingendpoints/" % self.project_key,
                       body = obj)
        return DSSStreamingEndpoint(self.client, self.project_key, streaming_endpoint_name)

    def create_httpsse_streaming_endpoint(self, streaming_endpoint_name, url=None):
        obj = {
            "id" : streaming_endpoint_name,
            "projectKey" : self.project_key,
            "type" : "httpsse",
            "params" : {}
        }
        if url is not None:
            obj["params"]["url"] = url
        self.client._perform_json("POST", "/projects/%s/streamingendpoints/" % self.project_key,
                       body = obj)
        return DSSStreamingEndpoint(self.client, self.project_key, streaming_endpoint_name)

    def new_managed_streaming_endpoint(self, streaming_endpoint_name, streaming_endpoint_type=None):
        """
        Initializes the creation of a new streaming endpoint. Returns a :class:`dataikuapi.dss.streaming_endpoint.DSSManagedStreamingEndpointCreationHelper`
        to complete the creation of the streaming endpoint

        :param string streaming_endpoint_name: Name of the new streaming endpoint - must be unique in the project
        :param string streaming_endpoint_type: Type of the new streaming endpoint (optional if it can be inferred from a connection type)
        :return: A :class:`dataikuapi.dss.streaming_endpoint.DSSManagedStreamingEndpointCreationHelper` object to create the streaming endpoint
        """
        return DSSManagedStreamingEndpointCreationHelper(self, streaming_endpoint_name, streaming_endpoint_type)

    ########################################################
    # Lab and ML
    # Don't forget to synchronize with DSSDataset.*
    ########################################################

    def create_prediction_ml_task(self, input_dataset, target_variable,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="DEFAULT",
                                  prediction_type=None,
                                  wait_guess_complete=True):

        """Creates a new prediction task in a new visual analysis lab
        for a dataset.

        :param string input_dataset: the dataset to use for training/testing the model
        :param string target_variable: the variable to predict
        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: DEFAULT, SIMPLE_FORMULA, DECISION_TREE, EXPLANATORY and PERFORMANCE
        :param string prediction_type: The type of prediction problem this is. If not provided the prediction type will be guessed. Valid values are: BINARY_CLASSIFICATION, REGRESSION, MULTICLASS
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """
        obj = {
            "inputDataset": input_dataset,
            "taskType": "PREDICTION",
            "targetVariable": target_variable,
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        if prediction_type is not None:
            obj["predictionType"] = prediction_type

        ref = self.client._perform_json("POST", "/projects/%s/models/lab/" % self.project_key, body=obj)
        ret = DSSMLTask(self.client, self.project_key, ref["analysisId"], ref["mlTaskId"])

        if wait_guess_complete:
            ret.wait_guess_complete()
        return ret

    def create_clustering_ml_task(self, input_dataset,
                                  ml_backend_type = "PY_MEMORY",
                                  guess_policy = "KMEANS",
                                  wait_guess_complete=True):

        """Creates a new clustering task in a new visual analysis lab
        for a dataset.


        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and ANOMALY_DETECTION
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """

        obj = {
            "inputDataset" : input_dataset,
            "taskType" : "CLUSTERING",
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        ref = self.client._perform_json("POST", "/projects/%s/models/lab/" % self.project_key, body=obj)
        mltask = DSSMLTask(self.client, self.project_key, ref["analysisId"], ref["mlTaskId"])

        if wait_guess_complete:
            mltask.wait_guess_complete()
        return mltask

    def list_ml_tasks(self):
        """
        List the ML tasks in this project
        
        Returns:
            the list of the ML tasks summaries, each one as a JSON object
        """
        return self.client._perform_json("GET", "/projects/%s/models/lab/" % self.project_key)

    def get_ml_task(self, analysis_id, mltask_id):
        """
        Get a handle to interact with a specific ML task
       
        Args:
            analysis_id: the identifier of the visual analysis containing the desired ML task
            mltask_id: the identifier of the desired ML task 
        
        Returns:
            A :class:`dataikuapi.dss.ml.DSSMLTask` ML task handle
        """
        return DSSMLTask(self.client, self.project_key, analysis_id, mltask_id)

    def list_mltask_queues(self):
        """
        List non-empty ML task queues in this project 
        
        :returns: an iterable :class:`DSSMLTaskQueues` listing of MLTask queues (each a dict)
        :rtype: :class:`DSSMLTaskQueues`
        """ 
        data = self.client._perform_json("GET", "/projects/%s/models/labs/mltask-queues" % self.project_key)
        return DSSMLTaskQueues(data)

    def create_analysis(self, input_dataset):
        """
        Creates a new visual analysis lab for a dataset.

        """

        obj = {
            "inputDataset" : input_dataset
        }

        ref = self.client._perform_json("POST", "/projects/%s/lab/" % self.project_key, body=obj)
        return DSSAnalysis(self.client, self.project_key, ref["id"])

    def list_analyses(self):
        """
        List the visual analyses in this project
        
        Returns:
            the list of the visual analyses summaries, each one as a JSON object
        """
        return self.client._perform_json("GET", "/projects/%s/lab/" % self.project_key)

    def get_analysis(self, analysis_id):
        """
        Get a handle to interact with a specific visual analysis
       
        Args:
            analysis_id: the identifier of the desired visual analysis
        
        Returns:
            A :class:`dataikuapi.dss.analysis.DSSAnalysis` visual analysis handle
        """
        return DSSAnalysis(self.client, self.project_key, analysis_id)

    ########################################################
    # Saved models
    ########################################################

    def list_saved_models(self):
        """
        List the saved models in this project
        
        Returns:
            the list of the saved models, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/savedmodels/" % self.project_key)

    def get_saved_model(self, sm_id):
        """
        Get a handle to interact with a specific saved model
       
        Args:
            sm_id: the identifier of the desired saved model
        
        Returns:
            A :class:`dataikuapi.dss.savedmodel.DSSSavedModel` saved model handle
        """
        return DSSSavedModel(self.client, self.project_key, sm_id)

    def create_mlflow_pyfunc_model(self, name, prediction_type = None):
        """
        Creates a new external saved model for storing and managing MLFlow models

        :param string name: Human readable name for the new saved model in the flow
        :param string prediction_type: Optional (but needed for most operations). One of BINARY_CLASSIFICATION, MULTICLASS or REGRESSION
        """
        model = {
            "savedModelType" : "MLFLOW_PYFUNC",
            "predictionType" : prediction_type,
            "name": name
        }

        id = self.client._perform_json("POST", "/projects/%s/savedmodels/" % self.project_key, body = model)["id"]
        return self.get_saved_model(id)

    ########################################################
    # Managed folders
    ########################################################

    def list_managed_folders(self):
        """
        List the managed folders in this project
        
        Returns:
            the list of the managed folders, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/managedfolders/" % self.project_key)

    def get_managed_folder(self, odb_id):
        """
        Get a handle to interact with a specific managed folder
       
        Args:
            odb_id: the identifier of the desired managed folder
        
        Returns:
            A :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` managed folder handle
        """
        return DSSManagedFolder(self.client, self.project_key, odb_id)

    def create_managed_folder(self, name, folder_type=None, connection_name="filesystem_folders"):
        """
        Create a new managed folder in the project, and return a handle to interact with it
        
        Args:
            name: the name of the managed folder
        
        Returns:
            A :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` managed folder handle
        """
        obj = {
            "name" : name,
            "projectKey" : self.project_key,
            "type" : folder_type,
            "params" : {
                "connection" : connection_name,
                "path" : "/${projectKey}/${odbId}"
            }
        }
        res = self.client._perform_json("POST", "/projects/%s/managedfolders/" % self.project_key,
                       body = obj)
        odb_id = res['id']
        return DSSManagedFolder(self.client, self.project_key, odb_id)


    ########################################################
    # Model evaluation stores
    ########################################################

    def list_model_evaluation_stores(self):
        """
        List the model evaluation stores in this project.

        :returns: The list of the model evaluation stores
        :rtype: list of :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationStore`
        """
        items = self.client._perform_json("GET", "/projects/%s/modelevaluationstores/" % self.project_key)
        return [DSSModelEvaluationStore(self.client, self.project_key, item["id"]) for item in items]

    def get_model_evaluation_store(self, mes_id):
        """
        Get a handle to interact with a specific model evaluation store
       
        :param string mes_id: the id of the desired model evaluation store
        
        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationStore` model evaluation store handle
        """
        return DSSModelEvaluationStore(self.client, self.project_key, mes_id)

    def create_model_evaluation_store(self, name):
        """
        Create a new model evaluation store in the project, and return a handle to interact with it.
        
        :param string name: the name for the new model evaluation store

        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationStore` model evaluation store handle
        """
        obj = {
            "projectKey" : self.project_key,
            "name" : name
        }
        res = self.client._perform_json("POST", "/projects/%s/modelevaluationstores/" % self.project_key,
                       body = obj)
        mes_id = res['id']
        return DSSModelEvaluationStore(self.client, self.project_key, mes_id)

    ########################################################
    # Model comparisons
    ########################################################

    def list_model_comparisons(self):
        """
        List the model comparisons in this project.

        :returns: The list of the model comparisons
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/modelcomparisons/" % self.project_key)
        return [DSSModelComparison(self.client, self.project_key, item["id"]) for item in items]

    def get_model_comparison(self, mec_id):
        """
        Get a handle to interact with a specific model comparison

        :param string mec_id: the id of the desired model comparison

        :returns: A handle on a model comparison
        :rtype: :class:`dataikuapi.dss.modelcomparison.DSSModelComparison`
        """
        return DSSModelComparison(self.client, self.project_key, mec_id)

    def create_model_comparison(self, name, prediction_type):
        """
        Create a new model comparison in the project, and return a handle to interact with it.

        :param string name: the name for the new model comparison
        :param string prediction_type: one of BINARY_CLASSIFICATION, REGRESSION and MULTICLASS

        :returns: A handle on a new model comparison
        :rtype: :class:`dataikuapi.dss.modelcomparison.DSSModelComparison`
        """
        obj = {
            "projectKey": self.project_key,
            "displayName": name,
            "predictionType": prediction_type
        }
        res = self.client._perform_json("POST", "/projects/%s/modelcomparisons/" % self.project_key,
                                        body = obj)
        mec_id = res['id']
        return DSSModelComparison(self.client, self.project_key, mec_id)

    ########################################################
    # Jobs
    ########################################################

    def list_jobs(self):
        """
        List the jobs in this project
        
        Returns:
            a list of the jobs, each one as a JSON object, containing both the definition and the state
        """
        return self.client._perform_json(
            "GET", "/projects/%s/jobs/" % self.project_key)

    def get_job(self, id):
        """
        Get a handler to interact with a specific job
        
        Returns:
            A :class:`dataikuapi.dss.job.DSSJob` job handle
        """
        return DSSJob(self.client, self.project_key, id)

    def start_job(self, definition):
        """
        Create a new job, and return a handle to interact with it
        
        :param dict definition: The definition should contain: 
            
            * the type of job (RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD, RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD)
            * a list of outputs to build from the available types: (DATASET, MANAGED_FOLDER, SAVED_MODEL, STREAMING_ENDPOINT)
            * (Optional) a refreshHiveMetastore field (True or False) to specify whether to re-synchronize the Hive metastore for recomputed HDFS datasets.
        
        :returns: A :class:`dataikuapi.dss.job.DSSJob` job handle
        """
        job_def = self.client._perform_json("POST", "/projects/%s/jobs/" % self.project_key, body = definition)
        return DSSJob(self.client, self.project_key, job_def['id'])

    def start_job_and_wait(self, definition, no_fail=False):
        """
        Starts a new job and waits for it to complete.
        
        :param dict definition: The definition should contain:
            
            * the type of job (RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD, RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD)
            * a list of outputs to build from the available types: (DATASET, MANAGED_FOLDER, SAVED_MODEL, STREAMING_ENDPOINT)
            * (Optional) a refreshHiveMetastore field (True or False) to specify whether to re-synchronize the Hive metastore for recomputed HDFS datasets.
        """
        job_def = self.client._perform_json("POST", "/projects/%s/jobs/" % self.project_key, body = definition)
        job = DSSJob(self.client, self.project_key, job_def['id'])
        waiter = DSSJobWaiter(job)
        return waiter.wait(no_fail)

    def new_job(self, job_type='NON_RECURSIVE_FORCED_BUILD'):
        """
        Create a job to be run

        You need to add outputs to the job (i.e. what you want to build) before running it.

        .. code-block:: python

            job_builder = project.new_job()
            job_builder.with_output("mydataset")
            complete_job = job_builder.start_and_wait()
            print("Job %s done" % complete_job.id)

        :rtype: :class:`JobDefinitionBuilder`
        """
        return JobDefinitionBuilder(self, job_type)

    def new_job_definition_builder(self, job_type='NON_RECURSIVE_FORCED_BUILD'):
        """Deprecated. Please use :meth:`new_job`"""
        warnings.warn("new_job_definition_builder is deprecated, please use new_job", DeprecationWarning)
        return JobDefinitionBuilder(self, job_type)

    ########################################################
    # Jupyter Notebooks
    ########################################################
    
    def list_jupyter_notebooks(self, active=False, as_type="object"):
        """
        List the jupyter notebooks of a project.

        :param bool as_type: How to return the list. Supported values are "listitems" and "objects".
        :param bool active: if True, only return currently running jupyter notebooks.

        :returns: The list of the notebooks. If "as_type" is "listitems", each one as a :class:`dataikuapi.dss.notebook.DSSJupyterNotebookListItem`, if "as_type" is "objects", each one as a :class:`dataikuapi.dss.notebook.DSSJupyterNotebook`
        
        :rtype: list of :class:`dataikuapi.dss.notebook.DSSJupyterNotebook` or list of :class:`dataikuapi.dss.notebook.DSSJupyterNotebookListItem`
        """
        notebook_items = self.client._perform_json("GET", "/projects/%s/jupyter-notebooks/" % self.project_key, params={"active": active})
        if as_type == "listitems" or as_type == "listitem":
            return [DSSJupyterNotebookListItem(self.client, notebook_item) for notebook_item in notebook_items]
        elif as_type == "objects" or as_type == "object":
            return [DSSJupyterNotebook(self.client, self.project_key, notebook_item["name"]) for notebook_item in notebook_items]
        else:
            raise ValueError("Unknown as_type")


    def get_jupyter_notebook(self, notebook_name):
        """
        Get a handle to interact with a specific jupyter notebook

        :param str notebook_name: The name of the jupyter notebook to retrieve
        :returns: A handle to interact with this jupyter notebook
        :rtype: :class:`~dataikuapi.dss.notebook.DSSNotebook` jupyter notebook handle
        """
        return DSSJupyterNotebook(self.client, self.project_key, notebook_name)

    def create_jupyter_notebook(self, notebook_name, notebook_content):
        """
        Create a new jupyter notebook and get a handle to interact with it

        :param str notebook_name: the name of the notebook to create
        :param dict notebook_content: the data of the notebook to create, as a dict.
            The data will be converted to a JSON string internally.
            Use ``get_content()`` on a similar existing ``DSSNotebook`` object in order to get a sample definition object
        :returns: A handle to interact with the newly created jupyter notebook
        :rtype: :class:`~dataikuapi.dss.notebook.DSSNotebook` jupyter notebook handle
        """
        self.client._perform_json("POST", "/projects/%s/jupyter-notebooks/%s" % (self.project_key, notebook_name), body=notebook_content)
        return self.get_jupyter_notebook(notebook_name)

    ########################################################
    # Continuous activities
    ########################################################

    def list_continuous_activities(self, as_objects=True):
        """
        List the continuous activities in this project
        
        Returns:
            a list of the continuous activities, each one as a JSON object, containing both the definition and the state
        """
        list = self.client._perform_json("GET", "/projects/%s/continuous-activities/" % self.project_key)
        if as_objects:
            return [DSSContinuousActivity(self.client, a['projectKey'], a['recipeId']) for a in list]
        else:
            return list

    def get_continuous_activity(self, recipe_id):
        """
        Get a handler to interact with a specific continuous activities
        
        Returns:
            A :class:`dataikuapi.dss.continuousactivity.DSSContinuousActivity` job handle
        """
        return DSSContinuousActivity(self.client, self.project_key, recipe_id)

    ########################################################
    # Variables
    ########################################################

    def get_variables(self):
        """
        Gets the variables of this project.

        Returns:
            a dictionary containing two dictionaries : "standard" and "local".
            "standard" are regular variables, exported with bundles.
            "local" variables are not part of the bundles for this project
        """
        return self.client._perform_json(
            "GET", "/projects/%s/variables/" % self.project_key)

    def set_variables(self, obj):
        """
        Sets the variables of this project.
        WARNING: if executed from a python recipe, the changes made by `set_variables` will not be "seen" in that recipe.
                 Use the internal API dataiku.get_custom_variables() instead if this behavior is needed

        :param dict obj: must be a modified version of the object returned by get_variables
        """
        if not "standard" in obj:
            raise ValueError("Missing 'standard' key in argument")
        if not "local" in obj:
            raise ValueError("Missing 'local' key in argument")

        self.client._perform_empty(
            "PUT", "/projects/%s/variables/" % self.project_key, body=obj)


    def update_variables(self, variables, type="standard"):
        """
        Updates a set of variables for this project

        :param variables dict: a dict of variable name -> value to set. Keys of the dict must be strings.
                    Values in the dict can be strings, numbers, booleans, lists or dicts
        :param type str: Can be "standard" to update regular variables or "local" to update local-only
                    variables that are not part of bundles for this project
        """

        current_variables = self.get_variables()
        current_variables[type].update(variables)
        self.set_variables(current_variables)

    ########################################################
    # API Services
    ########################################################

    def list_api_services(self):
        """
        List the API services in this project

        Returns:
            the list of API services, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/apiservices/" % self.project_key)

    def create_api_service(self, service_id):
        """
        Create a new API service, and returns a handle to interact with it. The newly-created
        service does not have any endpoint.

        :param str service_id: the ID of the API service to create
        :returns: A :class:`~dataikuapi.dss.dataset.DSSAPIService` API Service handle
        """
        self.client._perform_empty(
            "POST", "/projects/%s/apiservices/%s" % (self.project_key, service_id))
        return DSSAPIService(self.client, self.project_key, service_id)


    def get_api_service(self, service_id):
        """
        Get a handle to interact with a specific API Service from the API Designer

        :param str service_id: The identifier of the API Designer API Service to retrieve
        :returns: A handle to interact with this API Service
        :rtype: :class:`~dataikuapi.dss.dataset.DSSAPIService` API Service handle
        """
        return DSSAPIService(self.client, self.project_key, service_id)

    ########################################################
    # Bundles / Export and Publish (Design node)
    ########################################################

    def list_exported_bundles(self):
        """
        :returns: A dictionary of all bundles for a project on the Design node.
        """
        return self.client._perform_json("GET",
                "/projects/%s/bundles/exported" % self.project_key)

    def export_bundle(self, bundle_id):
        """
        Creates a new project bundle on the Design node 
        
        :param str bundle_id: bundle id tag 
        """
        return self.client._perform_json("PUT",
                "/projects/%s/bundles/exported/%s" % (self.project_key, bundle_id))

    def get_exported_bundle_archive_stream(self, bundle_id):
        """
        Download a bundle archive that can be deployed in a DSS automation Node, as a binary stream.
        
        .. warning::
            
            The stream must be closed after use. Use a ``with`` statement to handle closing the stream at the end of the block by default. For example:
            
            .. code-block:: python 
        
                    with project.get_exported_bundle_archive_stream('v1') as fp:
                        # use fp 
                    
                    # or explicitly close the stream after use
                    fp = project.get_exported_bundle_archive_stream('v1')
                    # use fp, then close 
                    fp.close()
                    
        """
        return self.client._perform_raw("GET",
                "/projects/%s/bundles/exported/%s/archive" % (self.project_key, bundle_id))

    def download_exported_bundle_archive_to_file(self, bundle_id, path):
        """
        Download a bundle archive that can be deployed in a DSS automation Node into the given output file.
        
        :param string path: if "-", will write to /dev/stdout
        """
        if path == "-":
            path= "/dev/stdout"
        stream = self.get_exported_bundle_archive_stream(bundle_id)

        with open(path, 'wb') as f:
            for chunk in stream.iter_content(chunk_size=10000):
                if chunk:
                    f.write(chunk)
                    f.flush()
        stream.close()

    def publish_bundle(self, bundle_id, published_project_key=None):
        """
        Publish a bundle on the Project Deployer.

        :param string bundle_id: The identifier of the bundle
        :param string published_project_key: The key of the project on the Project Deployer where the bundle will be published.
            A new published project will be created if none matches the key.
            If the parameter is not set, the key from the current :class:`DSSProject` is used.

        :rtype: dict
        :return: a dict with info on the bundle state once published. It contains the keys "publishedOn" for the publish date,
        "publishedBy" for the user who published the bundle, and "publishedProjectKey" for the key of the Project Deployer project used.
        """
        params = None
        if published_project_key is not None:
            params = {"publishedProjectKey": published_project_key}
        return self.client._perform_json("POST", "/projects/%s/bundles/%s/publish" % (self.project_key, bundle_id), params=params)

    ########################################################
    # Bundles / Import (Automation node)
    ########################################################

    def list_imported_bundles(self):
        """
        :returns: a dict containing bundle imports for a project, on the Automation node.
        """
        return self.client._perform_json("GET",
                "/projects/%s/bundles/imported" % self.project_key)

    def import_bundle_from_archive(self, archive_path):
        """
        Imports a bundle from a zip archive path on the Automation node.
        
        :param str archive_path: A full path to a zip archive, for example `/home/dataiku/my-bundle-v1.zip`
        """
        return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/actions/importFromArchive" % (self.project_key),
                 params = { "archivePath" : osp.abspath(archive_path) })

    def import_bundle_from_stream(self, fp):
        """
        Imports a bundle from a file stream, on the Automation node. 
        
        :param file-like fp: file handler. Usage example: 
        
        .. code-block:: python

            project = client.get_project('MY_PROJECT')
            with open('/home/dataiku/my-bundle-v1.zip', 'rb') as f:
                project.import_bundle_from_stream(f)
        """
        files = {'file': fp}
        return self.client._perform_empty("POST",
                "/projects/%s/bundles/imported/actions/importFromStream" % (self.project_key),
                files=files)

    def activate_bundle(self, bundle_id, scenarios_to_enable=None):
        """
        Activates a bundle in this project.

        :param str bundle_id: The ID of the bundle to activate
        :param dict scenarios_to_enable: An optional dict of scenarios to enable or disable upon bundle activation. The
               format of the dict should be scenario IDs as keys with values of True or False.
        :returns: A report containing any error or warning messages that occurred during bundle activation
        :rtype: dict
        """
        options = {"scenariosActiveOnActivation": scenarios_to_enable} if scenarios_to_enable else {}

        return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/%s/actions/activate" % (self.project_key, bundle_id), body=options)

    def preload_bundle(self, bundle_id):
        """
        Preloads a bundle that has been imported on the Automation node 
        
        :param str bundle_id: the bundle_id for an existing imported bundle
        """
        return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/%s/actions/preload" % (self.project_key, bundle_id))


    ########################################################
    # Scenarios
    ########################################################

    def list_scenarios(self, as_type="listitems"):
        """
        List the scenarios in this project.

        :param str as_type: How to return the list. Supported values are "listitems" and "objects".
        :returns: The list of the datasets. If "rtype" is "listitems", each one as a :class:`scenario.DSSScenarioListItem`.
                  If "rtype" is "objects", each one as a :class:`scenario.DSSScenario`
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/scenarios/" % self.project_key)
        if as_type == "listitems":
            return [DSSScenarioListItem(self.client, item) for item in items]
        elif as_type == "objects":
            return [DSSScenario(self.client, self.project_key, item["id"]) for item in items]
        else:
            raise ValueError("Unknown as_type")

    def get_scenario(self, scenario_id):
        """
        Get a handle to interact with a specific scenario

        :param str: scenario_id: the ID of the desired scenario

        :returns: a :class:`dataikuapi.dss.scenario.DSSScenario` scenario handle
        """
        return DSSScenario(self.client, self.project_key, scenario_id)
        
    def create_scenario(self, scenario_name, type, definition=None):
        """
        Create a new scenario in the project, and return a handle to interact with it

        :param str scenario_name: The name for the new scenario. This does not need to be unique
                                (although this is strongly recommended)
        :param str type: The type of the scenario. MUst be one of 'step_based' or 'custom_python'
        :param dict definition: the JSON definition of the scenario. Use ``get_definition(with_status=False)`` on an
                existing ``DSSScenario`` object in order to get a sample definition object (defaults to `{'params': {}}`)

        :returns: a :class:`.scenario.DSSScenario` handle to interact with the newly-created scenario
        """
        if definition is None:
            definition = {'params': {}}
        definition['type'] = type
        definition['name'] = scenario_name
        scenario_id = self.client._perform_json("POST", "/projects/%s/scenarios/" % self.project_key,
                       body = definition)['id']
        return DSSScenario(self.client, self.project_key, scenario_id)
        
    ########################################################
    # Recipes
    ########################################################

    def list_recipes(self, as_type="listitems"):
        """
        List the recipes in this project

        :param str as_type: How to return the list. Supported values are "listitems" and "objects".
        :returns: The list of the recipes. If "as_type" is "listitems", each one as a :class:`recipe.DSSRecipeListItem`.
                  If "as_type" is "objects", each one as a :class:`recipe.DSSRecipe`
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/recipes/" % self.project_key)
        if as_type == "listitems" or as_type == "listitem":
            return [DSSRecipeListItem(self.client, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSRecipe(self.client, self.project_key, item["name"]) for item in items]
        else:
            raise ValueError("Unknown as_type")


    def get_recipe(self, recipe_name):
        """
        Gets a :class:`dataikuapi.dss.recipe.DSSRecipe` handle to interact with a recipe
        
        :param str recipe_name: The name of the recipe
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipe`
        """
        return DSSRecipe(self.client, self.project_key, recipe_name)

    def create_recipe(self, recipe_proto, creation_settings):
        """
        Create a new recipe in the project, and return a handle to interact with it.
        We strongly recommend that you use the creator helpers instead of calling this directly.

        Some recipe types require additional parameters in creation_settings:

        * 'grouping' : a 'groupKey' column name
        * 'python', 'sql_query', 'hive', 'impala' : the code of the recipe as a 'payload' string

        Args:
            recipe_proto: a prototype for the recipe object. Must contain at least 'type' and 'name'
            creation_settings: recipe-specific creation settings

        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
        """
        recipe_proto["projectKey"] = self.project_key
        definition = {'recipePrototype': recipe_proto, 'creationSettings' : creation_settings}
        recipe_name = self.client._perform_json("POST", "/projects/%s/recipes/" % self.project_key,
                       body = definition)['name']
        return DSSRecipe(self.client, self.project_key, recipe_name)

    def new_recipe(self, type, name=None):
        """
        Initializes the creation of a new recipe. Returns a :class:`dataikuapi.dss.recipe.DSSRecipeCreator`
        or one of its subclasses to complete the creation of the recipe.

        Usage example:

        .. code-block:: python

            grouping_recipe_builder = project.new_recipe("grouping")
            grouping_recipe_builder.with_input("dataset_to_group_on")
            # Create a new managed dataset for the output in the "filesystem_managed" connection
            grouping_recipe_builder.with_new_output("grouped_dataset", "filesystem_managed")                                    
            grouping_recipe_builder.with_group_key("column")
            recipe = grouping_recipe_builder.build()

            # After the recipe is created, you can edit its settings
            recipe_settings = recipe.get_settings()
            recipe_settings.set_column_aggregations("value", sum=True)
            recipe_settings.save()

            # And you may need to apply new schemas to the outputs
            recipe.compute_schema_updates().apply()

        :param str type: Type of the recipe
        :param str name: Optional, base name for the new recipe.
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipeCreator`
        """

        if type == "grouping":
            return recipe.GroupingRecipeCreator(name, self)
        elif type == "window":
            return recipe.WindowRecipeCreator(name, self)
        elif type == "sync":
            return recipe.SyncRecipeCreator(name, self)
        elif type == "sort":
            return recipe.SortRecipeCreator(name, self)
        elif type == "topn":
            return recipe.TopNRecipeCreator(name, self)
        elif type == "distinct":
            return recipe.DistinctRecipeCreator(name, self)
        elif type == "join":
            return recipe.JoinRecipeCreator(name, self)
        elif type == "vstack":
            return recipe.StackRecipeCreator(name, self)
        elif type == "sampling":
            return recipe.SamplingRecipeCreator(name, self)
        elif type == "split":
            return recipe.SplitRecipeCreator(name, self)
        elif type == "prepare" or type == "shaker":
            return recipe.PrepareRecipeCreator(name, self)
        elif type == "prediction_scoring":
            return recipe.PredictionScoringRecipeCreator(name, self)
        elif type == "evaluation":
            return recipe.EvaluationRecipeCreator(name, self)
        elif type == "standalone_evaluation":
            return recipe.StandaloneEvaluationRecipeCreator(name, self)
        elif type == "clustering_scoring":
            return recipe.ClusteringScoringRecipeCreator(name, self)
        elif type == "download":
            return recipe.DownloadRecipeCreator(name, self)
        elif type == "sql_query":
            return recipe.SQLQueryRecipeCreator(name, self)
        elif type in ["python", "r", "sql_script", "pyspark", "sparkr", "spark_scala", "shell"]:
            return recipe.CodeRecipeCreator(name, type, self)

    ########################################################
    # Flow
    ########################################################

    def get_flow(self):
        """
        :rtype: A :class:`dataikuapi.dss.flow.DSSProjectFlow`
        """
        return DSSProjectFlow(self.client, self)

    ########################################################
    # Security
    ########################################################
    
    def sync_datasets_acls(self):
        """
        Resync permissions on HDFS datasets in this project
        
        Returns:
            a DSSFuture handle to the task of resynchronizing the permissions
        
        Note: this call requires an API key with admin rights
        """
        future_response = self.client._perform_json(
            "POST", "/projects/%s/actions/sync" % (self.project_key))
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

    ########################################################
    # Notebooks
    ########################################################

    def list_running_notebooks(self, as_objects=True):
        """
        Deprecated. Use :meth:`DSSProject.list_jupyter_notebooks`
        List the currently-running notebooks

        Returns:
            list of notebooks. Each object contains at least a 'name' field
        """
        notebook_list = self.client._perform_json("GET", "/projects/%s/notebooks/active" % self.project_key)
        if as_objects:
            return [DSSNotebook(self.client, notebook['projectKey'], notebook['name'], notebook) for notebook in notebook_list]
        else:
            return notebook_list

    ########################################################
    # Tags
    ########################################################

    def get_tags(self):
        """
        List the tags of this project.

        Returns:
            a dictionary containing the tags with a color
        """
        return self.client._perform_json("GET", "/projects/%s/tags" % self.project_key)

    def set_tags(self, tags=None):
        """
        Set the tags of this project.
        :param dict tags: must be a modified version of the object returned by list_tags (defaults to `{}`)
        """
        if tags is None:
            tags = {}
        return self.client._perform_empty("PUT", "/projects/%s/tags" % self.project_key, body=tags)


    ########################################################
    # Macros
    ########################################################

    def list_macros(self, as_objects=False):
        """
        List the macros accessible in this project
        
        :param as_objects: if True, return the macros as :class:`dataikuapi.dss.macro.DSSMacro` 
                        macro handles instead of raw JSON
        :returns: the list of the macros
        """
        macros = self.client._perform_json(
            "GET", "/projects/%s/runnables/" % self.project_key)
        if as_objects:
            return [DSSMacro(self.client, self.project_key, m["runnableType"], m) for m in macros]
        else:
            return macros

    def get_macro(self, runnable_type):
        """
        Get a handle to interact with a specific macro
       
        :param runnable_type: the identifier of a macro        
        :returns: A :class:`dataikuapi.dss.macro.DSSMacro` macro handle
        """
        return DSSMacro(self.client, self.project_key, runnable_type)

    ########################################################
    # Wiki
    ########################################################
    def get_wiki(self):
        """
        Get the wiki

        :returns: the wiki associated to the project
        :rtype: :class:`dataikuapi.dss.wiki.DSSWiki`
        """
        return DSSWiki(self.client, self.project_key)

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the project

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "PROJECT", self.project_key)

    ########################################################
    # Tables import
    ########################################################

    def init_tables_import(self):
        """
        Start an operation to import Hive or SQL tables as datasets into this project

        :returns: a :class:`TablesImportDefinition` to add tables to import
        :rtype: :class:`TablesImportDefinition`
        """
        return TablesImportDefinition(self.client, self.project_key)

    def list_sql_schemas(self, connection_name):
        """
        Lists schemas from which tables can be imported in a SQL connection

        :returns: an array of schemas names
        """
        return self._list_schemas(connection_name)

    def list_hive_databases(self):
        """
        Lists Hive databases from which tables can be imported

        :returns: an array of databases names
        """
        return self._list_schemas("@virtual(hive-jdbc):default")

    def _list_schemas(self, connection_name):
        return self.client._perform_json("GET", "/projects/%s/datasets/tables-import/actions/list-schemas" % (self.project_key),
                params = {"connectionName": connection_name} )

    def list_sql_tables(self, connection_name, schema_name=None):
        """
        Lists tables to import in a SQL connection

        :returns: an array of tables
        """
        ret = self.client._perform_json("GET", "/projects/%s/datasets/tables-import/actions/list-tables" % (self.project_key),
                params = {"connectionName": connection_name, "schemaName": schema_name} )

        def to_schema_table_pair(x):
            return {"schema":x.get("schema", None), "table":x["table"]}
        return [to_schema_table_pair(x) for x in DSSFuture.get_result_wait_if_needed(self.client, ret)['tables']]

    def list_hive_tables(self, hive_database):
        """
        Lists tables to import in a Hive database

        :returns: an array of tables
        """
        connection_name = "@virtual(hive-jdbc):" + hive_database
        ret = self.client._perform_json("GET", "/projects/%s/datasets/tables-import/actions/list-tables" % (self.project_key),
                params={"connectionName": connection_name} )

        def to_schema_table_pair(x):
            return {"schema":x.get("databaseName", None), "table":x["table"]}
        return [to_schema_table_pair(x) for x in DSSFuture.get_result_wait_if_needed(self.client, ret)['tables']]

    ########################################################
    # App designer
    ########################################################
    def get_app_manifest(self):
        raw_data = self.client._perform_json("GET", "/projects/%s/app-manifest" % self.project_key)
        return DSSAppManifest(self.client, raw_data, self.project_key)

    ########################################################
    # MLflow experiment tracking
    ########################################################
    def setup_mlflow(self, managed_folder, host=None):
        """
        Setup the dss-plugin for MLflow

        :param object managed_folder: the managed folder where MLflow artifacts should be stored.
                                      Can be either a managed folder id as a string,
                                      a :class:`dataikuapi.dss.DSSManagedFolder`, or a :class:`dataiku.Folder`
        :param str host: setup a custom host if the backend used is not DSS.
        """
        return MLflowHandle(client=self.client, project=self, managed_folder=managed_folder, host=host)

    def get_mlflow_extension(self):
        """
        Get a handle to interact with the extension of MLflow provided by DSS

        :returns: A :class:`dataikuapi.dss.mlflow.DSSMLflowExtension` Mlflow Extension handle

        """
        return DSSMLflowExtension(client=self.client, project_key=self.project_key)



    ########################################################
    # Code studios
    ########################################################
    def list_code_studios(self, as_type="listitems"):
        """
        List the code studio objects in this project
        
        :returns: the list of the code studio objects, each one as a JSON object
        """
        items = self.client._perform_json(
            "GET", "/projects/%s/code-studios/" % self.project_key)
        if as_type == "listitems" or as_type == "listitem":
            return [DSSCodeStudioObjectListItem(self.client, self.project_key, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSCodeStudioObject(self.client, self.project_key, item["id"]) for item in items]
        else:
            raise ValueError("Unknown as_type") 

    def get_code_studio(self, code_studio_id):
        """
        Get a handle to interact with a specific code studio object
       
        :param str code_studio_id: the identifier of the desired code studio object
        
        :returns: A :class:`dataikuapi.dss.codestudio.DSSCodeStudioObject` code studio object handle
        """
        return DSSCodeStudioObject(self.client, self.project_key, code_studio_id)

    def create_code_studio(self, name, template_id):
        """
        Create a new code studio object in the project, and return a handle to interact with it
        
        :param str name: the name of the code studio object
        :param str template_id: the identifier of a code studio template
        
        :returns: A :class:`dataikuapi.dss.codestudio.DSSCodeStudioObject` code studio object handle
        """
        obj = {
            "name" : name,
            "templateId" : template_id
        }
        res = self.client._perform_json("POST", "/projects/%s/code-studios/" % self.project_key, body = obj)
        code_studio_id = res['codeStudio']['id']
        return DSSCodeStudioObject(self.client, self.project_key, code_studio_id)



class TablesImportDefinition(object):
    """
    Temporary structure holding the list of tables to import
    """

    def __init__(self, client, project_key):
        """Do not call this directly, use :meth:`DSSProject.init_tables_import`"""
        self.client = client
        self.project_key = project_key
        self.keys = []

    def add_hive_table(self, hive_database, hive_table):
        """Add a Hive table to the list of tables to import"""
        self.keys.append({
            "connectionName" : "@virtual(hive-jdbc):" + hive_database,
            "name" : hive_table
        })

    def add_sql_table(self, connection, schema, table):
        """Add a SQL table to the list of table to import"""
        self.keys.append({
            "connectionName" : connection,
            "schema": schema,
            "name" : table
        })

    def prepare(self):
        """
        Run the first step of the import process. In this step, DSS will check
        the tables whose import you have requested and prepare dataset names and 
        target connections

        :returns: a :class:`TablesPreparedImport` object that allows you to finalize the import process
        :rtype: :class:`TablesPreparedImport`

        """
        ret = self.client._perform_json("POST", "/projects/%s/datasets/tables-import/actions/prepare-from-keys" % (self.project_key),
                body = {"keys": self.keys} )

        future = self.client.get_future(ret["jobId"])
        future.wait_for_result()
        return TablesPreparedImport(self.client, self.project_key, future.get_result())

class TablesPreparedImport(object):
    """Result of preparing a tables import. Import can now be finished"""
    
    def __init__(self, client, project_key, candidates):
        """Do not call this directly, use :meth:`DSSProject.init_tables_import` and then prepare"""
        self.client = client
        self.project_key = project_key
        self.candidates = candidates

    def execute(self):
        """
        Starts executing the import in background and returns a :class:`dataikuapi.dss.future.DSSFuture` to wait on the result

        :returns: a future to wait on the result
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/datasets/tables-import/actions/execute-from-candidates" % (self.project_key),
                body = self.candidates)
        return self.client.get_future(ret["jobId"])

class DSSProjectSettings(object):
    """Settings of a DSS project"""

    def __init__(self, client, project_key, settings):
        """Do not call directly, use :meth:`DSSProject.get_settings`"""
        self.client = client
        self.project_key = project_key
        self.settings = settings

    def get_raw(self):
        """Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def set_python_code_env(self, code_env_name):
        """Sets the default Python code env used by this project

        :param str code_env_name: Identifier of the code env to use. If None, sets the project to use the builtin Python env
        """
        if code_env_name is None:
            self.settings["settings"]["codeEnvs"]["python"]["useBuiltinEnv"] = True
            self.settings["settings"]["codeEnvs"]["python"]["mode"] = "USE_BUILTIN_MODE"
        else:
            self.settings["settings"]["codeEnvs"]["python"]["useBuiltinEnv"] = False
            self.settings["settings"]["codeEnvs"]["python"]["envName"] = code_env_name
            self.settings["settings"]["codeEnvs"]["python"]["mode"] = "EXPLICIT_ENV"

    def set_r_code_env(self, code_env_name):
        """Sets the default R code env used by this project

        :param str code_env_name: Identifier of the code env to use. If None, sets the project to use the builtin R env
        """
        if code_env_name is None:
            self.settings["settings"]["codeEnvs"]["r"]["useBuiltinEnv"] = True
            self.settings["settings"]["codeEnvs"]["r"]["mode"] = "USE_BUILTIN_MODE"
        else:
            self.settings["settings"]["codeEnvs"]["r"]["useBuiltinEnv"] = False
            self.settings["settings"]["codeEnvs"]["r"]["envName"] = code_env_name
            self.settings["settings"]["codeEnvs"]["r"]["mode"] = "EXPLICIT_ENV"

    def set_container_exec_config(self, config_name):
        """Sets the default containerized execution config used by this project

        :param str config_name: Identifier of the containerized execution config to use. If None, sets the project to use local execution
        """
        if config_name is None:
            self.settings["settings"]["container"]["containerMode"] = "NONE"
        else:
            self.settings["settings"]["container"]["containerMode"] = "EXPLICIT_CONTAINER"
            self.settings["settings"]["container"]["containerConf"] = config_name

    def set_k8s_cluster(self, cluster, fallback_cluster=None):
        """Sets the Kubernetes cluster used by this project

        :param str cluster: Identifier of the cluster to use. May use variables expansion. If None, sets the project 
                            to use the globally-defined cluster
        :param str fallback_cluster: Identifier of the cluster to use if the variable used for "cluster" does not exist
        """
        if cluster is None:
            self.settings["settings"]["k8sCluster"]["clusterMode"] = "INHERIT"
        else:
            self.settings["settings"]["k8sCluster"]["clusterMode"] = "EXPLICIT_CLUSTER"
            self.settings["settings"]["k8sCluster"]["clusterId"] = cluster
            self.settings["settings"]["k8sCluster"]["defaultClusterId"] = fallback_cluster

    def set_cluster(self, cluster, fallback_cluster=None):
        """Sets the Hadoop/Spark cluster used by this project

        :param str cluster: Identifier of the cluster to use. May use variables expansion. If None, sets the project 
                            to use the globally-defined cluster
        :param str fallback_cluster: Identifier of the cluster to use if the variable used for "cluster" does not exist
        """
        if cluster is None:
            self.settings["settings"]["cluster"]["clusterMode"] = "INHERIT"
        else:
            self.settings["settings"]["cluster"]["clusterMode"] = "EXPLICIT_CLUSTER"
            self.settings["settings"]["cluster"]["clusterId"] = cluster
            self.settings["settings"]["cluster"]["defaultClusterId"] = fallback_cluster

    def add_exposed_object(self, object_type, object_id, target_project):
        """
        Exposes an object from this project to another project.
        Does nothing if the object was already exposed to the target project
        """
        found_eo = None
        for eo in self.settings["exposedObjects"]["objects"]:
            if eo["type"] == object_type and eo["localName"] == object_id:
                found_eo = eo
                break

        if found_eo is None:
            found_eo = {"type" : object_type, "localName" : object_id, "rules" : []}
            self.settings["exposedObjects"]["objects"].append(found_eo)

        already_exists = False
        for rule in found_eo["rules"]:
            if rule["targetProject"] == target_project:
                already_exists = True
                break

        if not already_exists:
            found_eo["rules"].append({"targetProject": target_project})


    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_empty("PUT", "/projects/%s/settings" % (self.project_key),
                body = self.settings)

class JobDefinitionBuilder(object):
    """
    Helper to run a job. Do not create this class directly, use :meth:`DSSProject.new_job`
    """
    def __init__(self, project, job_type="NON_RECURSIVE_FORCED_BUILD"):
        self.project = project
        self.definition = {'type':job_type, 'refreshHiveMetastore':False, 'outputs':[]}

    def with_type(self, job_type):
        """
        Sets the build type

        :param job_type: the build type for the job  RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD, 
                            RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD
        """
        self.definition['type'] = job_type
        return self

    def with_refresh_metastore(self, refresh_metastore):
        """
        Sets whether the hive tables built by the job should have their definitions
        refreshed after the corresponding dataset is built
        """
        self.definition['refreshHiveMetastore'] = refresh_metastore
        return self

    def with_output(self, name, object_type=None, object_project_key=None, partition=None):
        """
        Adds an item to build in this job
        
        :param name: name of the output object
        :param object_type: type of object to build from: DATASET, MANAGED_FOLDER, SAVED_MODEL, STREAMING_ENDPOINT
        :param object_project_key: PROJECT_KEY for the project that contains the object to build 
        :param partition: specify partition to build
        """
        self.definition['outputs'].append({'type':object_type, 'id':name, 'projectKey':object_project_key, 'partition':partition})
        return self

    def get_definition(self):
        """Gets the internal definition for this job"""
        return self.definition

    def start(self):
        """
        Starts the job, and return a :doc:`dataikuapi.dss.job.DSSJob` handle to interact with it.

        You need to wait for the returned job to complete
        
        :return: the :class:`dataikuapi.dss.job.DSSJob` job handle
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        job_def = self.project.client._perform_json("POST", 
                            "/projects/%s/jobs/" % self.project.project_key, body = self.definition)
        return DSSJob(self.project.client, self.project.project_key, job_def['id'])

    def start_and_wait(self, no_fail=False):
        """
        Starts the job, waits for it to complete and returns a a :doc:`dataikuapi.dss.job.DSSJob` handle to interact with it

        Raises if the job failed.

        :param no_fail: if True, does not raise if the job failed.
        :return: the :class:`dataikuapi.dss.job.DSSJob` job handle
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        job = self.start()
        waiter = DSSJobWaiter(job)
        waiter.wait(no_fail)
        return job
