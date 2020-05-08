import time
from .dataset import DSSDataset, DSSManagedDatasetCreationHelper
from .recipe import DSSRecipe
from .managedfolder import DSSManagedFolder
from .savedmodel import DSSSavedModel
from .job import DSSJob, DSSJobWaiter
from .scenario import DSSScenario
from .apiservice import DSSAPIService
import sys
import os.path as osp
from .future import DSSFuture
from .notebook import DSSNotebook
from .macro import DSSMacro
from .wiki import DSSWiki
from .discussion import DSSObjectDiscussions
from .ml import DSSMLTask
from .analysis import DSSAnalysis
from ..utils import DataikuException


class DSSProject(object):
    """
    A handle to interact with a project on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_project``
    """
    def __init__(self, client, project_key):
       self.client = client
       self.project_key = project_key

    ########################################################
    # Project deletion
    ########################################################

    def delete(self, drop_data=False):
        """
        Delete the project

        This call requires an API key with admin rights

        :param bool drop_data: Should the data of managed datasets be dropped
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s" % self.project_key, params = {
                "dropData": drop_data
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
            * exportManagedFolders (boolean): Exports the data of managed folders - default False
            * exportAllInputDatasets (boolean): Exports the data of all input datasets - default False
            * exportAllDatasets (boolean): Exports the data of all datasets - default False
            * exportAllInputManagedFolders (boolean): Exports the data of all input managed folders - default False
            * exportGitRepositoy (boolean): Exports the Git repository history - default False
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

    ########################################################
    # Datasets
    ########################################################

    def list_datasets(self):
        """
        List the datasets in this project
        
        :returns: The list of the datasets, each one as a dictionary. Each dataset dict contains at least a `name` field which is the name of the dataset
        :rtype: list of dicts
        """
        return self.client._perform_json(
            "GET", "/projects/%s/datasets/" % self.project_key)

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

    def new_managed_dataset_creation_helper(self, dataset_name):
        """
        Creates a helper class to create a managed dataset in the project

        :param string dataset_name: Name of the new dataset - must be unique in the project
        :return: A :class:`dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper` object to create the managed dataset
        """
        return DSSManagedDatasetCreationHelper(self, dataset_name)

    ########################################################
    # ML
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
                                   guess_policy = "KMEANS"):


        """Creates a new clustering task in a new visual analysis lab
        for a dataset.


        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and ANOMALY_DETECTION
        """

        obj = {
            "inputDataset" : input_dataset,
            "taskType" : "CLUSTERING",
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        ref = self.client._perform_json("POST", "/projects/%s/models/lab/" % self.project_key, body=obj)
        return DSSMLTask(self.client, self.project_key, ref["analysisId"], ref["mlTaskId"])

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
        
        Args:
            definition: the definition for the job to create. The definition must contain the type of job (RECURSIVE_BUILD, 
            NON_RECURSIVE_FORCED_BUILD, RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD) and a list of outputs to build.
            Optionally, a refreshHiveMetastore field can specify whether to re-synchronize the Hive metastore for recomputed
            HDFS datasets.
        
        Returns:
            A :class:`dataikuapi.dss.job.DSSJob` job handle
        """
        job_def = self.client._perform_json("POST", "/projects/%s/jobs/" % self.project_key, body = definition)
        return DSSJob(self.client, self.project_key, job_def['id'])

    def start_job_and_wait(self, definition, no_fail=False):
        """
        Create a new job. Wait the end of the job to complete.
        
        Args:
            definition: the definition for the job to create. The definition must contain the type of job (RECURSIVE_BUILD, 
            NON_RECURSIVE_FORCED_BUILD, RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD) and a list of outputs to build.
            Optionally, a refreshHiveMetastore field can specify whether to re-synchronize the Hive metastore for recomputed
            HDFS datasets.
        """
        job_def = self.client._perform_json("POST", "/projects/%s/jobs/" % self.project_key, body = definition)
        job = DSSJob(self.client, self.project_key, job_def['id'])
        waiter = DSSJobWaiter(job)
        return waiter.wait(no_fail)

    def new_job_definition_builder(self, job_type='NON_RECURSIVE_FORCED_BUILD'):
        return JobDefinitionBuilder(self.project_key, job_type)

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

        @param dict obj: must be a modified version of the object returned by get_variables
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
    # Bundles / Export (Design node)
    ########################################################

    def list_exported_bundles(self):
        return self.client._perform_json("GET",
                "/projects/%s/bundles/exported" % self.project_key)

    def export_bundle(self, bundle_id):
        return self.client._perform_json("PUT",
                "/projects/%s/bundles/exported/%s" % (self.project_key, bundle_id))

    def get_exported_bundle_archive_stream(self, bundle_id):
        """
        Download a bundle archive that can be deployed in a DSS automation Node, as a binary stream.
        Warning: this stream will monopolize the DSSClient until closed.
        """
        return self.client._perform_raw("GET",
                "/projects/%s/bundles/exported/%s/archive" % (self.project_key, bundle_id))

    def download_exported_bundle_archive_to_file(self, bundle_id, path):
        """
        Download a bundle archive that can be deployed in a DSS automation Node into the given output file.
        @param path if "-", will write to /dev/stdout
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


    ########################################################
    # Bundles / Import (Automation node)
    ########################################################

    def list_imported_bundles(self):
        return self.client._perform_json("GET",
                "/projects/%s/bundles/imported" % self.project_key)

    def import_bundle_from_archive(self, archive_path):
        return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/actions/importFromArchive" % (self.project_key),
                 params = { "archivePath" : osp.abspath(archive_path) })

    def import_bundle_from_stream(self, fp):
        files = {'file': fp }
        return self.client._perform_empty("POST",
                "/projects/%s/bundles/imported/actions/importFromStream" % (self.project_key),
                files=files)

    def activate_bundle(self, bundle_id):
         return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/%s/actions/activate" % (self.project_key, bundle_id))

    def preload_bundle(self, bundle_id):
         return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/%s/actions/preload" % (self.project_key, bundle_id))


    ########################################################
    # Scenarios
    ########################################################

    def list_scenarios(self):
        """
        List the scenarios in this project.

        This method returns a list of Python dictionaries. Each dictionary represents
        a scenario. Each dictionary contains at least a "id" field, that you can then pass
        to the :meth:`get_scenario`

        :returns: the list of scenarios, each one as a Python dictionary
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/" % self.project_key)

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

    def list_recipes(self):
        """
        List the recipes in this project
        
        Returns:
            the list of the recipes, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/recipes/" % self.project_key)

    def get_recipe(self, recipe_name):
        """
        Get a handle to interact with a specific recipe
       
        Args:
            recipe_name: the name of the desired recipe
        
        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
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
        List the currently-running notebooks

        Returns:
            list of notebooks. Each object contains at least a 'name' field
        """
        list = self.client._perform_json("GET", "/projects/%s/notebooks/active" % self.project_key)
        if as_objects:
            return [DSSNotebook(self.client, notebook['projectKey'], notebook['name'], notebook) for notebook in list]
        else:
            return list

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
                params = {"connectionName": connection_name} )

        def to_schema_table_pair(x):
            return {"schema":x.get("databaseName", None), "table":x["table"]}
        return [to_schema_table_pair(x) for x in DSSFuture.get_result_wait_if_needed(self.client, ret)['tables']]

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
        else:
            self.settings["settings"]["codeEnvs"]["python"]["useBuiltinEnv"] = False
            self.settings["settings"]["codeEnvs"]["python"]["envName"] = code_env_name

    def set_r_code_env(self, code_env_name):
        """Sets the default R code env used by this project

        :param str code_env_name: Identifier of the code env to use. If None, sets the project to use the builtin R env
        """
        if code_env_name is None:
            self.settings["settings"]["codeEnvs"]["r"]["useBuiltinEnv"] = True
        else:
            self.settings["settings"]["codeEnvs"]["r"]["useBuiltinEnv"] = False
            self.settings["settings"]["codeEnvs"]["r"]["envName"] = code_env_name

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

    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_empty("PUT", "/projects/%s/settings" % (self.project_key),
                body = self.settings)

class JobDefinitionBuilder(object):
    def __init__(self, project_key, job_type="NON_RECURSIVE_FORCED_BUILD"):
        """
        Create a helper to build a job definition

        :param project_key: the project in which the job is launched
        :param job_type: the build type for the job  RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD, 
                            RECURSIVE_FORCED_BUILD, RECURSIVE_MISSING_ONLY_BUILD

        """
        self.project_key = project_key
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
        Adds an item to build in the definition
        """
        self.definition['outputs'].append({'type':object_type, 'id':name, 'projectKey':object_project_key, 'partition':partition})
        return self

    def get_definition(self):
        return self.definition
