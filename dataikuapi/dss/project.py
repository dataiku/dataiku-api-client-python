from dataset import DSSDataset
from recipe import DSSRecipe
from managedfolder import DSSManagedFolder
from savedmodel import DSSSavedModel
from job import DSSJob
from scenario import DSSScenario
from apiservice import DSSAPIService
import sys

class DSSProject(object):
    """
    A project on the DSS instance
    """
    def __init__(self, client, project_key):
       self.client = client
       self.project_key = project_key

    ########################################################
    # Project deletion
    ########################################################

    def delete(self):
        """
        Delete the project

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s" % self.project_key)

    ########################################################
    # Project export
    ########################################################

    def get_export_stream(self, options = {}):
        """
        Return a stream of the exported project

        Warning: this stream will monopolize the DSSClient until closed
        """
        return self.client._perform_raw(
            "POST", "/projects/%s/export" % self.project_key, body=options).raw

    def export_to_file(self, path, options={}):
        """
        Export the project to a file
        Args:
            path: the path of the file in which the exported project should be saved
        """
        with open(path, 'w') as f:
            export_stream = self.client._perform_raw(
                "POST", "/projects/%s/export" % self.project_key, body=options)
            for chunk in export_stream.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
            f.flush()

    ########################################################
    # Project infos
    ########################################################

    def get_metadata(self):
        """
        Get the metadata attached to this project. The metadata contains label, description
        checklists, tags and custom metadata of the project
        
        Returns:
            a dict object. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/latest
        """
        return self.client._perform_json(
            "GET", "/projects/%s/metadata" % self.project_key)

    def set_metadata(self, metadata):
        """
        Set the metadata on this project.
        
        Args:
            metadata: the new state of the metadata for the project. You should only set a metadata object 
            that has been retrieved using the get_metadata call.
        """
        return self.client._perform_empty(
            "PUT", "/projects/%s/metadata" % self.project_key, body = metadata)

    def get_permissions(self):
       """
       Get the permissions attached to this project

        Returns:
            a JSON object, containing the owner and the permissions, as a list of pairs of group name
            and permission type
       """
       return self.client._perform_json(
          "GET", "/projects/%s/permissions" % self.project_key)

    def set_permissions(self, permissions):
        """
        Set the permissions on this project
        
        Args:
            permissions: a JSON object of the same structure as the one returned by get_permissions call
        """
        return self.client._perform_empty(
            "PUT", "/projects/%s/permissions" % self.project_key, body = permissions)

    ########################################################
    # Datasets
    ########################################################

    def list_datasets(self):
        """
        List the datasets in this project
        
        Returns:
            the list of the datasets, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/datasets/" % self.project_key)

    def get_dataset(self, dataset_name):
        """
        Get a handle to interact with a specific dataset
       
        Args:
            dataset_name: the name of the desired dataset
        
        Returns:
            A :class:`dataikuapi.dss.dataset.DSSDataset` dataset handle
        """
        return DSSDataset(self.client, self.project_key, dataset_name)

    def create_dataset(self, dataset_name, type,
                params={}, formatType=None, formatParams={}):
        """
        Create a new dataset in the project, and return a handle to interact with it
        
        Args:
            dataset_name: the name for the new dataset
            type: the type of the dataset
            params: the parameters for the type, as a JSON object
            formatType: an optional format to create the dataset with
            formatParams: the parameters to the format, as a JSON object
        
        Returns:
            A :class:`dataikuapi.dss.dataset.DSSDataset` dataset handle
        """
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

    def create_managed_folder(self, name):
        """
        Create a new managed folder in the project, and return a handle to interact with it
        
        Args:
            name: the name of the managed folder
        
        Returns:
            A :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` managed folder handle
        """
        obj = {
            "name" : name,
            "projectKey" : self.project_key
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
        @param obj: must be a modified version of the object returned by get_variables
        """
        if not "standard" in obj:
            raise ValueError("Missing 'standard' key in argument")
        if not "local" in obj:
            raise ValueError("Missing 'local' key in argument")

        self.client._perform_empty(
            "PUT", "/projects/%s/variables/" % self.project_key, body=obj)

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

    def get_api_service(self, service_id):
        """
        Get a handle to interact with a specific API service

        Args:
            service_id: the ID of the desired API service

        Returns:
            A :class:`dataikuapi.dss.dataset.DSSAPIService` API Service handle
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

    def activate_bundle(self, bundle_id):
         return self.client._perform_json("POST",
                "/projects/%s/bundles/imported/%s/actions/activate" % (self.project_key, bundle_id))


    ########################################################
    # Scenarios
    ########################################################

    def list_scenarios(self):
        """
        List the scenarios in this project

        Returns:
            the list of scenarios, each one as a JSON object.
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/" % self.project_key)

    def get_scenario(self, scenario_id):
        """
        Get a handle to interact with a specific scenario

        Args:
            scenario_id: the ID of the desired scenario

        Returns:
            A :class:`dataikuapi.dss.scenario.DSSScenario` scenario handle
        """
        return DSSScenario(self.client, self.project_key, scenario_id)
        
    def create_scenario(self, scenario_name, type, definition={}):
        """
        Create a new scenario in the project, and return a handle to interact with it
        
        Args:
            scenario_name: the name for the new scenario
            type: the type of the scenario ('step_based' or 'custom_python')
            definition: the definition of the scenario, as a JSON object
        
        Returns:
            A :class:`dataikuapi.dss.scenario.DSSScenario` scenario handle
        """
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

    def create_recipe(self, recipe_name, type, recipe_inputs=[], recipe_outputs=[], recipe_params={}):
        """
        Create a new recipe in the project, and return a handle to interact with it. Some recipe
        types take additional parameters in recipe_params:
        
        * 'grouping' : a 'groupKey' column name
        * 'python', 'sql_query', 'hive', 'impala' : the code of the recipe as a 'payload' string
        
        Args:
            recipe_name: the name for the new recipe
            type: the type of the scenario ('sync', 'grouping', 'join', 'vstack', 'python', 'sql_query', 'hive', 'impala')
            recipe_inputs: an array of recipes inputs, as objects {'ref':'...', 'deps':[...]}
            recipe_outputs: an array of recipes outputs, as objects {'ref':'...', 'appendMode':True/False}
            recipe_params: additional parameters for the recipe creation
        
        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
        """
        definition = {'type' : type, 'name' : recipe_name, 'inputs' : {'items':recipe_inputs}, 'outputs' : {'items':recipe_outputs}}
        definition['params'] = recipe_params
        recipe_name = self.client._perform_json("POST", "/projects/%s/recipes/" % self.project_key,
                       body = definition)['name']
        return DSSRecipe(self.client, self.project_key, recipe_name)
        