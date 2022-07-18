from ..utils import DataikuException
from .utils import DSSTaggableObjectSettings
from .discussion import DSSObjectDiscussions
import json, logging, warnings
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings
try:
    basestring
except NameError:
    basestring = str

class DSSRecipeListItem(DSSTaggableObjectListItem):
    """An item in a list of recipes. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_recipes`"""
    def __init__(self, client, data):
        super(DSSRecipeListItem, self).__init__(data)
        self.client = client

    def to_recipe(self):
        """Gets the :class:`DSSRecipe` corresponding to this dataset"""
        return  DSSRecipe(self.client, self._data["projectKey"], self._data["name"])

    @property
    def name(self):
        return self._data["name"]
    @property
    def id(self):
        return self._data["name"]
    @property
    def type(self):
        return self._data["type"]

class DSSRecipe(object):
    """
    A handle to an existing recipe on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_recipe`
    """
    def __init__(self, client, project_key, recipe_name):
        self.client = client
        self.project_key = project_key
        self.recipe_name = recipe_name

    @property
    def id(self):
        """The id of the recipe"""
        return self.recipe_name

    @property
    def name(self):
        """The name of the recipe"""
        return self.recipe_name

    def compute_schema_updates(self):
        """
        Computes which updates are required to the outputs of this recipe.
        The required updates are returned as a :class:`RequiredSchemaUpdates` object, which then
        allows you to :meth:`~RequiredSchemaUpdates.apply` the changes.

        Usage example:

        .. code-block:: python

            required_updates = recipe.compute_schema_updates()
            if required_updates.any_action_required():
                print("Some schemas will be updated")

            # Note that you can call apply even if no changes are required. This will be noop
            required_updates.apply()
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/recipes/%s/schema-update" % (self.project_key, self.recipe_name))
        return RequiredSchemaUpdates(self, data)

    def run(self, job_type="NON_RECURSIVE_FORCED_BUILD", partitions=None, wait=True, no_fail=False):
        """
        Starts a new job to run this recipe and wait for it to complete.
        Raises if the job failed.

        .. code-block:: python

            job = recipe.run()
            print("Job %s done" % job.id)

        :param job_type: The job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param partitions: If the outputs are partitioned, a list of partition ids to build
        :param no_fail: if True, does not raise if the job failed.
        :return: the :class:`dataikuapi.dss.job.DSSJob` job handle corresponding to the built job
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        project = self.client.get_project(self.project_key)
        outputs = project.get_flow().get_graph().get_successor_computables(self)

        if len(outputs) == 0:
            raise Exception("recipe has no outputs, can't run it")

        first_output = outputs[0]

        object_type_map = {
            "COMPUTABLE_DATASET": "DATASET",
            "COMPUTABLE_FOLDER": "MANAGED_FOLDER",
            "COMPUTABLE_SAVED_MODEL": "SAVED_MODEL",
            "COMPUTABLE_STREAMING_ENDPOINT": "STREAMING_ENDPOINT",
            "COMPUTABLE_MODEL_EVALUATION_STORE": "MODEL_EVALUATION_STORE"
        }
        if first_output["type"] in object_type_map:
            jd = project.new_job(job_type)
            jd.with_output(first_output["ref"], object_type=object_type_map[first_output["type"]], partition=partitions)
        else:
            raise Exception("Recipe has unsupported output type {}, can't run it".format(first_output["type"]))

        if wait:
            return jd.start_and_wait(no_fail)
        else:
            return jd.start()

    def delete(self):
        """
        Delete the recipe
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))

    def get_settings(self):
        """
        Gets the settings of the recipe, as a :class:`DSSRecipeSettings` or one of its subclasses.

        Some recipes have a dedicated class for the settings, with additional helpers to read and modify the settings

        Once you are done modifying the returned settings object, you can call :meth:`~DSSRecipeSettings.save` on it
        in order to save the modifications to the DSS recipe
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        type = data["recipe"]["type"]

        if type == "grouping":
            return GroupingRecipeSettings(self, data)
        elif type == "window":
            return WindowRecipeSettings(self, data)
        elif type == "sync":
            return SyncRecipeSettings(self, data)
        elif type == "sort":
            return SortRecipeSettings(self, data)
        elif type == "topn":
            return TopNRecipeSettings(self, data)
        elif type == "distinct":
            return DistinctRecipeSettings(self, data)
        elif type == "join":
            return JoinRecipeSettings(self, data)
        elif type == "vstack":
            return StackRecipeSettings(self, data)
        elif type == "sampling":
            return SamplingRecipeSettings(self, data)
        elif type == "split":
            return SplitRecipeSettings(self, data)
        elif type == "prepare" or type == "shaker":
            return PrepareRecipeSettings(self, data)
        #elif type == "prediction_scoring":
        #elif type == "clustering_scoring":
        elif type == "download":
            return DownloadRecipeSettings(self, data)
        #elif type == "sql_query":
        #    return WindowRecipeSettings(self, data)
        elif type in ["python", "r", "sql_script", "pyspark", "sparkr", "spark_scala", "shell"]:
            return CodeRecipeSettings(self, data)
        else:
            return DSSRecipeSettings(self, data)

    def get_definition_and_payload(self):
        """
        Deprecated. Use :meth:`get_settings`
        """
        warnings.warn("Recipe.get_definition_and_payload is deprecated, please use get_settings", DeprecationWarning)

        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        return DSSRecipeDefinitionAndPayload(self, data)

    def set_definition_and_payload(self, definition):
        """
        Deprecated. Use :meth:`get_settings` and :meth:`DSSRecipeSettings.save`
        """
        warnings.warn("Recipe.set_definition_and_payload is deprecated, please use get_settings", DeprecationWarning)
        definition._payload_to_str()
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name),
                body=definition.data)

    def get_status(self):
        """
        Gets the status of this recipe (status messages, engines status, ...)

        :return: a :class:`dataikuapi.dss.recipe.DSSRecipeStatus` object to interact with the status
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipeStatus`
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/status" % (self.project_key, self.recipe_name))
        return DSSRecipeStatus(self.client, data)


    def get_metadata(self):
        """
        Get the metadata attached to this recipe. The metadata contains label, description
        checklists, tags and custom metadata of the recipe

        :returns: a dict. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/8.0/rest/
        :rtype dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this recipe.
        :params dict metadata: the new state of the metadata for the recipe. You should only set a metadata object
            that has been retrieved using the get_metadata call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name),
                body=metadata)

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the recipe

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "RECIPE", self.recipe_name)

    def get_continuous_activity(self):
        """
        Return a handle on the associated recipe
        """
        from .continuousactivity import DSSContinuousActivity
        return DSSContinuousActivity(self.client, self.project_key, self.recipe_name)

    def move_to_zone(self, zone):
        """
        Moves this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object
        """
        if isinstance(zone, basestring):
           zone = self.client.get_project(self.project_key).get_flow().get_zone(zone)
        zone.add_item(self)

class DSSRecipeStatus(object):
    """Status of a recipce.
    Do not create that directly, use :meth:`DSSRecipe.get_status`"""

    def __init__(self, client, data):
        """Do not call that directly, use :meth:`dataikuapi.dss.recipe.DSSRecipe.get_status`"""
        self.client = client
        self.data = data

    def get_selected_engine_details(self):
        """
        Gets the selected engine for this recipe (for recipes that support engines)

        :returns: a dict of the details of the selected recipe. The dict will contain at least fields 'type' indicating
             which engine it is, "statusWarnLevel" which indicates whether the engine is OK / WARN / ERROR
        :rtype: dict
        """
        if not "selectedEngine" in self.data:
            raise ValueError("This recipe doesn't have a selected engine")
        return self.data["selectedEngine"]

    def get_engines_details(self):
        """
        Gets details about all possible engines for this recipe (for recipes that support engines)

        :returns: a list of dict of the details of each possible engine. The dict for each engine
             will contain at least fields 'type' indicating
             which engine it is, "statusWarnLevel" which indicates whether the engine is OK / WARN / ERROR
        :rtype: list
        """
        if not "engines" in self.data:
            raise ValueError("This recipe doesn't have engines")
        return self.data["engines"]

    def get_status_severity(self):
        """Returns whether the recipe is in SUCCESS, WARNING or ERROR status

        :rtype: string
        """
        return self.data["allMessagesForFrontend"]["maxSeverity"]

    def get_status_messages(self):
        """
        Returns status messages for this recipe.

        :returns: a list of dict, for each status message. Each dict represents a single message,
            and contains at least a "severity" field (SUCCESS, WARNING or ERROR)
            and a "message" field
        :rtype: list
        """
        return self.data["allMessagesForFrontend"]["messages"]


class DSSRecipeSettings(DSSTaggableObjectSettings):
    """
    Settings of a recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    def __init__(self, recipe, data):
        super(DSSRecipeSettings, self).__init__(data["recipe"])
        self.recipe = recipe
        self.data = data
        self.recipe_settings = self.data["recipe"]
        self._str_payload = self.data.get("payload", None)
        self._obj_payload = None

    def save(self):
        """
        Saves back the recipe in DSS.
        """
        self._payload_to_str()
        return self.recipe.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.recipe.project_key, self.recipe.recipe_name),
                body=self.data)

    @property
    def type(self):
        return self.recipe_settings["type"]

    @property
    def str_payload(self):
        """The raw "payload" of the recipe, as a string"""
        self._payload_to_str()
        return self._str_payload
    @str_payload.setter
    def str_payload(self, payload):
        self._str_payload = payload
        self._obj_payload = None

    @property
    def obj_payload(self):
        """The raw "payload" of the recipe, as a dict"""
        self._payload_to_obj()
        return self._obj_payload

    @property
    def raw_params(self):
        """The raw 'params' field of the recipe settings, as a dict"""
        return self.recipe_settings["params"]

    def _payload_to_str(self):
        if self._obj_payload is not None:
            self._str_payload = json.dumps(self._obj_payload)
            self._obj_payload = None
        if self._str_payload is not None:
            self.data["payload"] = self._str_payload

    def _payload_to_obj(self):
        if self._str_payload is not None:
            self._obj_payload = json.loads(self._str_payload)
            self._str_payload = None

    def get_recipe_raw_definition(self):
        """
        Get the recipe definition as a raw dict
        :rtype dict
        """
        return self.recipe_settings

    def get_recipe_inputs(self):
        """
        Get a structured dict of inputs to this recipe
        :rtype dict
        """
        return self.recipe_settings.get('inputs')

    def get_recipe_outputs(self):
        """
        Get a structured dict of outputs of this recipe
        :rtype dict
        """
        return self.recipe_settings.get('outputs')

    def get_recipe_params(self):
        """
        Get the parameters of this recipe, as a dict
        :rtype dict
        """
        return self.recipe_settings.get('params')

    def get_payload(self):
        """
        Get the payload or script of this recipe, as a string
        :rtype string
        """
        self._payload_to_str()
        return self._str_payload

    def get_json_payload(self):
        """
        Get the payload or script of this recipe, parsed from JSON, as a dict
        :rtype dict
        """
        self._payload_to_obj()
        return self._obj_payload

    def set_payload(self, payload):
        """
        Set the payload of this recipe
        :param str payload: the payload, as a string
        """
        self._str_payload = payload
        self._obj_payload = None

    def set_json_payload(self, payload):
        """
        Set the payload of this recipe
        :param dict payload: the payload, as a dict. The payload will be converted to a JSON string internally
        """
        self._str_payload = None
        self._obj_payload = payload

    def has_input(self, input_ref):
        """Returns whether this recipe has a given ref as input"""
        inputs = self.get_recipe_inputs()
        for (input_role_name, input_role) in inputs.items():
            for item in input_role.get("items", []):
                if item.get("ref", None) == input_ref:
                    return True
        return False

    def has_output(self, output_ref):
        """Returns whether this recipe has a given ref as output"""
        outputs = self.get_recipe_outputs()
        for (output_role_name, output_role) in outputs.items():
            for item in output_role.get("items", []):
                if item.get("ref", None) == output_ref:
                    return True
        return False

    def replace_input(self, current_input_ref, new_input_ref):
        """Replaces an object reference as input of this recipe by another"""
        inputs = self.get_recipe_inputs()
        for (input_role_name, input_role) in inputs.items():
            for item in input_role.get("items", []):
                if item.get("ref", None) == current_input_ref:
                    item["ref"] = new_input_ref

    def replace_output(self, current_output_ref, new_output_ref):
        """Replaces an object reference as output of this recipe by another"""
        outputs = self.get_recipe_outputs()
        for (output_role_name, output_role) in outputs.items():
            for item in output_role.get("items", []):
                if item.get("ref", None) == current_output_ref:
                    item["ref"] = new_output_ref

    def add_input(self, role, ref, partition_deps=None):
        if partition_deps is None:
            partition_deps = []
        self._get_or_create_input_role(role)["items"].append({"ref": ref, "deps": partition_deps})

    def add_output(self, role, ref, append_mode=False):
        self._get_or_create_output_role(role)["items"].append({"ref": ref, "appendMode": append_mode})

    def _get_or_create_input_role(self, role):
        inputs = self.get_recipe_inputs()
        if not role in inputs:
            role_obj = {"items": []}
            inputs[role] = role_obj
        return inputs[role]

    def _get_or_create_output_role(self, role):
        outputs = self.get_recipe_outputs()
        if not role in outputs:
            role_obj = {"items": []}
            outputs[role] = role_obj
        return outputs[role]

    def _get_flat_inputs(self):
        ret = []
        for role_key, role_obj in self.get_recipe_inputs().items():
            for item in role_obj["items"]:
                ret.append((role_key, item))
        return ret

    def _get_flat_outputs(self):
        ret = []
        for role_key, role_obj in self.get_recipe_outputs().items():
            for item in role_obj["items"]:
                ret.append((role_key, item))
        return ret

    def get_flat_input_refs(self):
        """
        Returns a list of all input refs of this recipe, regardless of the input role
        :rtype list of strings
        """
        ret = []
        for role_key, role_obj in self.get_recipe_inputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret

    def get_flat_output_refs(self):
        """
        Returns a list of all output refs of this recipe, regardless of the output role
        :rtype list of strings
        """
        ret = []
        for role_key, role_obj in self.get_recipe_outputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret


# Old name, deprecated
class DSSRecipeDefinitionAndPayload(DSSRecipeSettings):
    """
    Deprecated. Settings of a recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass

class RequiredSchemaUpdates(object):
    """
    Representation of the updates required to the schema of the outputs of a recipe.
    Do not create this class directly, use :meth:`DSSRecipe.compute_schema_updates`
    """

    def __init__(self, recipe, data):
        self.recipe = recipe
        self.data = data
        self.drop_and_recreate = True
        self.synchronize_metastore = True

    def any_action_required(self):
        return self.data["totalIncompatibilities"] > 0

    def apply(self):
        results  = []
        for computable in self.data["computables"]:
            osu = {
                "computableType": computable["type"],
                # dirty
                "computableId": computable["type"] == "DATASET" and computable["datasetName"] or computable["id"],
                "newSchema": computable["newSchema"],
                "dropAndRecreate": self.drop_and_recreate,
                "synchronizeMetastore" : self.synchronize_metastore
            }

            results.append(self.recipe.client._perform_json("POST",
                    "/projects/%s/recipes/%s/actions/updateOutputSchema" % (self.recipe.project_key, self.recipe.recipe_name),
                    body=osu))
        return results

#####################################################
# Recipes creation infrastructure
#####################################################

class DSSRecipeCreator(object):
    """
    Helper to create new recipes

    :param str type: type of the recipe
    :param str name: name for the recipe
    :param :class:`dataikuapi.dss.project.DSSProject` project: project in which the recipe will be created
    """
    def __init__(self, type, name, project):
        self.project = project
        self.recipe_proto = {
            "inputs" : {},
            "outputs" : {},
            "type" : type,
            "name" : name
        }
        self.creation_settings = {
        }

    def set_name(self, name):
        self.recipe_proto["name"] = name

    def _build_ref(self, object_id, project_key=None):
        if project_key is not None and project_key != self.project.project_key:
            return project_key + '.' + object_id
        else:
            return object_id

    def _with_input(self, dataset_name, project_key=None, role="main"):
        role_obj = self.recipe_proto["inputs"].get(role, None)
        if role_obj is None:
            role_obj = { "items" : [] }
            self.recipe_proto["inputs"][role] = role_obj
        role_obj["items"].append({'ref':self._build_ref(dataset_name, project_key)})
        return self

    def _with_output(self, dataset_name, append=False, role="main"):
        role_obj = self.recipe_proto["outputs"].get(role, None)
        if role_obj is None:
            role_obj = { "items" : [] }
            self.recipe_proto["outputs"][role] = role_obj
        role_obj["items"].append({'ref':self._build_ref(dataset_name, None), 'appendMode': append})
        return self

    def _get_input_refs(self):
        ret = []
        for role_key, role_obj in self.recipe_proto["inputs"].items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret

    def with_input(self, dataset_name, project_key=None, role="main"):
        """
        Add an existing object as input to the recipe-to-be-created

        :param dataset_name: name of the dataset, or identifier of the managed folder
                             or identifier of the saved model
        :param project_key: project containing the object, if different from the one where the recipe is created
        :param str role: the role of the recipe in which the input should be added
        """
        return self._with_input(dataset_name, project_key, role)

    def with_output(self, dataset_name, append=False, role="main"):
        """
        The output dataset must already exist. If you are creating a visual recipe with a single
        output, use with_existing_output

        :param dataset_name: name of the dataset, or identifier of the managed folder
                             or identifier of the saved model
        :param append: whether the recipe should append or overwrite the output when running
                       (note: not available for all dataset types)
        :param str role: the role of the recipe in which the input should be added
        """
        return self._with_output(dataset_name, append, role)

    def build(self):
        """Deprecated. Use create()"""
        return self.create()

    def create(self):
        """
        Creates the new recipe in the project, and return a handle to interact with it.

        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
        """
        self._finish_creation_settings()
        return self.project.create_recipe(self.recipe_proto, self.creation_settings)

    def set_raw_mode(self):
        self.creation_settings["rawCreation"] = True

    def _finish_creation_settings(self):
        pass

class SingleOutputRecipeCreator(DSSRecipeCreator):
    """
    Create a recipe that has a single output
    """

    def __init__(self, type, name, project):
        DSSRecipeCreator.__init__(self, type, name, project)
        self.create_output_dataset = None
        self.output_dataset_settings = None
        self.create_output_folder = None
        self.output_folder_settings = None

    def with_existing_output(self, dataset_name, append=False):
        """
        Add an existing object as output to the recipe-to-be-created

        :param dataset_name: name of the dataset, or identifier of the managed folder
                             or identifier of the saved model
        :param append: whether the recipe should append or overwrite the output when running
                       (note: not available for all dataset types)
        """
        assert self.create_output_dataset is None
        self.create_output_dataset = False
        self._with_output(dataset_name, append)
        return self

    def with_new_output(self, name, connection_id, typeOptionId=None, format_option_id=None, override_sql_schema=None, partitioning_option_id=None, append=False, object_type='DATASET', overwrite=False):
        """
        Create a new dataset as output to the recipe-to-be-created. The dataset is not created immediately,
        but when the recipe is created (ie in the create() method)

        :param str name: name of the dataset or identifier of the managed folder
        :param str connection_id: name of the connection to create the dataset on
        :param str typeOptionId: sub-type of dataset, for connection where the type could be ambiguous. Typically,
                                 this is SCP or SFTP, for SSH connection
        :param str format_option_id: name of a format preset relevant for the dataset type. Possible values are: CSV_ESCAPING_NOGZIP_FORHIVE,
                                     CSV_UNIX_GZIP, CSV_EXCEL_GZIP, CSV_EXCEL_GZIP_BIGQUERY, CSV_NOQUOTING_NOGZIP_FORPIG, PARQUET_HIVE,
                                     AVRO, ORC
        :param override_sql_schema: schema to force dataset, for SQL dataset. If left empty, will be autodetected
        :param str partitioning_option_id: to copy the partitioning schema of an existing dataset 'foo', pass a
                                           value of 'copy:dataset:foo'
        :param append: whether the recipe should append or overwrite the output when running
                       (note: not available for all dataset types)
        :param str object_type: DATASET or MANAGED_FOLDER
        :param overwrite: If the dataset being created already exists, overwrite it (and delete data)
        """
        if object_type == 'DATASET':
            assert self.create_output_dataset is None

            dataset = self.project.get_dataset(name)
            if overwrite and dataset.exists():
                dataset.delete(drop_data=True)

            self.create_output_dataset = True
            self.output_dataset_settings = {'connectionId':connection_id,'typeOptionId':typeOptionId,'specificSettings':{'formatOptionId':format_option_id, 'overrideSQLSchema':override_sql_schema},'partitioningOptionId':partitioning_option_id}
            self._with_output(name, append)
        elif object_type == 'MANAGED_FOLDER':
            assert self.create_output_folder is None
            self.create_output_folder = True
            self.output_folder_settings = {'connectionId':connection_id,'typeOptionId':typeOptionId,'partitioningOptionId':partitioning_option_id}
            self._with_output(name, append)
        return self

    def with_output(self, dataset_name, append=False):
        """Alias of with_existing_output"""
        return self.with_existing_output(dataset_name, append)

    def _finish_creation_settings(self):
        self.creation_settings['createOutputDataset'] = self.create_output_dataset
        self.creation_settings['outputDatasetSettings'] = self.output_dataset_settings
        self.creation_settings['createOutputFolder'] = self.create_output_folder
        self.creation_settings['outputFolderSettings'] = self.output_folder_settings

class VirtualInputsSingleOutputRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a recipe that has a single output and several inputs
    """

    def __init__(self, type, name, project):
        SingleOutputRecipeCreator.__init__(self, type, name, project)
        self.virtual_inputs = []

    def with_input(self, dataset_name, project_key=None):
        self.virtual_inputs.append(self._build_ref(dataset_name, project_key))
        return self

    def _finish_creation_settings(self):
        super(VirtualInputsSingleOutputRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['virtualInputs'] = self.virtual_inputs


#####################################################
# Per-recipe-type classes: Visual recipes
#####################################################

class GroupingRecipeSettings(DSSRecipeSettings):
    """
    Settings of a grouping recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    def clear_grouping_keys(self):
        """Removes all grouping keys from this grouping recipe"""
        self.obj_payload["keys"] = []

    def add_grouping_key(self, column):
        """
        Adds grouping on a column
        :param str column: Column to group on
        """
        self.obj_payload["keys"].append({"column":column})

    def set_global_count_enabled(self, enabled):
        self.obj_payload["globalCount"] = enabled

    def get_or_create_column_settings(self, column):
        """
        Gets a dict representing the aggregations to perform on a column.
        Creates it and adds it to the potential aggregations if it does not already exists
        :param str column: The column name
        :rtype dict
        """
        found = None
        for gv in self.obj_payload["values"]:
            if gv["column"] == column:
                found = gv
                break
        if found is None:
            found = {"column" : column}
            self.obj_payload["values"].append(found)
        return found

    def set_column_aggregations(self, column, type, min=False, max=False, count=False, count_distinct=False,
                                sum=False,concat=False,stddev=False,avg=False):
        """
        Sets the basic aggregations on a column.
        Returns the dict representing the aggregations on the column

        :param str column: The column name
        :param str type: The type of the column (as a DSS schema type name)
        :rtype dict
        """
        cs = self.get_or_create_column_settings(column)
        cs["type"] = type
        cs["min"] = min
        cs["max"] = max
        cs["count"] = count
        cs["countDistinct"] = count_distinct
        cs["sum"] = sum
        cs["concat"] = concat
        cs["stddev"] = stddev
        return cs

class GroupingRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Group recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'grouping', name, project)
        self.group_key = None

    def with_group_key(self, group_key):
        """
        Set a column as the first grouping key. Only a single grouping key may be set
        at recipe creation time. For additional groupings, get the recipe settings

        :param str group_key: name of a column in the input dataset
        """
        self.group_key = group_key
        return self

    def _finish_creation_settings(self):
        super(GroupingRecipeCreator, self)._finish_creation_settings()
        if self.group_key is not None:
            self.creation_settings['groupKey'] = self.group_key


class WindowRecipeSettings(DSSRecipeSettings):
    """
    Settings of a window recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for window

class WindowRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Window recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'window', name, project)


class SyncRecipeSettings(DSSRecipeSettings):
    """
    Settings of a sync recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for sync

class SyncRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sync recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sync', name, project)


class SortRecipeSettings(DSSRecipeSettings):
    """
    Settings of a sort recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for sort

class SortRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sort recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sort', name, project)


class TopNRecipeSettings(DSSRecipeSettings):
    """
    Settings of a topn recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for topn

class TopNRecipeCreator(DSSRecipeCreator):
    """
    Create a TopN recipe
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'topn', name, project)


class DistinctRecipeSettings(DSSRecipeSettings):
    """
    Settings of a distinct recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for distinct

class DistinctRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Distinct recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'distinct', name, project)


class PrepareRecipeSettings(DSSRecipeSettings):
    """
    Settings of a prepare recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass

    @property
    def raw_steps(self):
        """
        Returns a raw list of the steps of this prepare recipe.
        You can modify the returned list.

        Each step is a dict of settings. The precise settings for each step are not documented
        """
        return self.obj_payload["steps"]

    def add_processor_step(self, type, params):
        step = {
            "metaType": "PROCESSOR",
            "type": type,
            "params": params
        }
        self.raw_steps.append(step)

    def add_filter_on_bad_meaning(self, meaning, columns):
        params = {
            "action" : "REMOVE_ROW",
            "type" : meaning
        }
        if isinstance(columns, basestring):
            params["appliesTo"] = "SINGLE_COLUMN"
            params["columns"] = [columns]
        elif isinstance(columns, list):
            params["appliesTo"] = "COLUMNS"
            params["columns"] = columns

class PrepareRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Prepare recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'shaker', name, project)


class JoinRecipeSettings(DSSRecipeSettings):
    """
    Settings of a join recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`

    In order to enable self-joins, join recipes are based on a concept of "virtual inputs".
    Every join, computed pre-join column, pre-join filter, ... is based on one virtual input, and
    each virtual input references an input of the recipe, by index

    For example, if a recipe has inputs A and B and declares two joins:
        - A->B
        - A->A(based on a computed column)

    There are 3 virtual inputs:
        * 0: points to recipe input 0 (i.e. dataset A)
        * 1: points to recipe input 1 (i.e. dataset B)
        * 2: points to recipe input 0 (i.e. dataset A) and includes the computed column

    * The first join is between virtual inputs 0 and 1
    * The second join is between virtual inputs 0 and 2
    """
    pass # TODO: Write helpers for join

    @property
    def raw_virtual_inputs(self):
        """
        Returns the raw list of virtual inputs
        :rtype list of dict
        """
        return self.obj_payload["virtualInputs"]

    @property
    def raw_joins(self):
        """
        Returns the raw list of joins
        :rtype list of dict
        """
        return self.obj_payload["joins"]

    def add_virtual_input(self, input_dataset_index):
        """
        Adds a virtual input pointing to the specified input dataset of the recipe
        (referenced by index in the inputs list)
        """
        self.raw_virtual_inputs.append({"index": input_dataset_index})

    def add_pre_join_computed_column(self, virtual_input_index, computed_column):
        """
        Adds a computed column to a virtual input

        Use :class:`dataikuapi.dss.utils.DSSComputedColumn` to build the computed_column object
        """
        self.raw_virtual_inputs[virtual_input_index]["computedColumns"].append(computed_column)

    def add_join(self, join_type="LEFT", input1=0, input2=1):
        """
        Adds a join between two virtual inputs. The join is initialized with no condition.

        Use :meth:`add_condition_to_join` on the return value to add a join condition (for example column equality)
        to the join

        :returns the newly added join as a dict
        :rtype dict
        """
        jp = self.obj_payload
        if not "joins" in jp:
            jp["joins"] = []
        join = {
            "conditionsMode": "AND",
            "on": [],
            "table1": input1,
            "table2": input2,
            "type": join_type
        }
        jp["joins"].append(join)
        return join

    def add_condition_to_join(self, join, type="EQ", column1=None, column2=None):
        """
        Adds a condition to a join
        :param str column1: Name of "left" column
        :param str column2: Name of "right" column
        """
        cond = {
            "type" : type,
            "column1": {"name": column1, "table": join["table1"]},
            "column2": {"name": column2, "table": join["table2"]},
        }
        join["on"].append(cond)
        return cond

    def add_post_join_computed_column(self, computed_column):
        """
        Adds a post-join computed column

        Use :class:`dataikuapi.dss.utils.DSSComputedColumn` to build the computed_column object
        """
        self.obj_payload["computedColumns"].append(computed_column)

    def set_post_filter(self, postfilter):
        self.obj_payload["postFilter"] = postfilter

class JoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Join recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'join', name, project)

class FuzzyJoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a FuzzyJoin recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'fuzzyjoin', name, project)

class GeoJoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a GeoJoin recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'geojoin', name, project)

class StackRecipeSettings(DSSRecipeSettings):
    """
    Settings of a stack recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for stack

class StackRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Stack recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'vstack', name, project)


class SamplingRecipeSettings(DSSRecipeSettings):
    """
    Settings of a sampling recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for sampling

class SamplingRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sample/Filter recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sampling', name, project)


class SplitRecipeSettings(DSSRecipeSettings):
    """
    Settings of a split recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for split

class SplitRecipeCreator(DSSRecipeCreator):
    """
    Create a Split recipe
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, "split", name, project)

    def _finish_creation_settings(self):
        pass


class DownloadRecipeSettings(DSSRecipeSettings):
    """
    Settings of a download recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass # TODO: Write helpers for download

class DownloadRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Download recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'download', name, project)


#####################################################
# Per-recipe-type classes: Code recipes
#####################################################

class CodeRecipeSettings(DSSRecipeSettings):
    """
    Settings of a code recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    def get_code(self):
        """
        Returns the code of the recipe as a string
        :rtype string
        """
        self._payload_to_str()
        return self._str_payload

    def set_code(self, code):
        """
        Updates the code of the recipe
        :param str code: The new code as a string
        """
        self.set_payload(code)

    def get_code_env_settings(self):
        """
        Returns the code env settings for this recipe
        :rtype dict
        """
        rp = self.get_recipe_params()
        if not "envSelection" in rp:
            raise ValueError("This recipe kind does not seem to take a code env selection")
        return rp["envSelection"]

    def set_code_env(self, code_env=None, inherit=False, use_builtin=False):
        """
        Sets the code env to use for this recipe.

        Exactly one of `code_env`, `inherit` or `use_builtin` must be passed

        :param str code_env: The name of a code env
        :param bool inherit: Use the project's default code env
        :param bool use_builtin: Use the builtin code env
        """
        rp = self.get_recipe_params()
        if not "envSelection" in rp:
            raise ValueError("This recipe kind does not seem to take a code env selection")

        if code_env is not None:
            rp["envSelection"] = {"envMode": "EXPLICIT_ENV", "envName": code_env}
        elif inherit:
            rp["envSelection"] = {"envMode": "INHERIT"}
        elif use_builtin:
            rp["envSelection"] = {"envMode": "USE_BUILTIN_MODE"}
        else:
            raise ValueError("No env setting selected")

class CodeRecipeCreator(DSSRecipeCreator):
    def __init__(self, name, type, project):
        """
        Create a recipe running a script

        :param str type: the type of the recipe (possible values : python, r, hive, impala, spark_scala, pyspark, sparkr)
        """
        DSSRecipeCreator.__init__(self, type, name, project)
        self.script = None

    def with_script(self, script):
        """
        Set the code of the recipe

        :param str script: the script of the recipe
        """
        self.script = script
        return self

    def with_new_output_dataset(self, name, connection,
                                type=None, format=None,
                                copy_partitioning_from="FIRST_INPUT",
                                append=False, overwrite=False):
        """
        Create a new managed dataset as output to the recipe-to-be-created. The dataset is created immediately

        :param str name: name of the dataset to create
        :param str connection_id: name of the connection to create the dataset on
        :param str type: type of dataset, for connection where the type could be ambiguous. Typically,
                                 this is SCP or SFTP, for SSH connection
        :param str format: name of a format preset relevant for the dataset type. Possible values are: CSV_ESCAPING_NOGZIP_FORHIVE,
                                     CSV_UNIX_GZIP, CSV_EXCEL_GZIP, CSV_EXCEL_GZIP_BIGQUERY, CSV_NOQUOTING_NOGZIP_FORPIG, PARQUET_HIVE,
                                     AVRO, ORC. If None, uses the default
        :param str copy_partitioning_from: Whether to copy the partitioning from another thing.
                    Use None for not partitioning the output, "FIRST_INPUT" to copy from the first input of the recipe,
                    "dataset:XXX" to copy from a dataset name, or "folder:XXX" to copy from a folder id
        :param append: whether the recipe should append or overwrite the output when running (note: not available for all dataset types)
        :param overwrite: If the dataset being created already exists, overwrite it (and delete data)
        """

        ch = self.project.new_managed_dataset_creation_helper(name)
        ch.with_store_into(connection, type_option_id=type, format_option_id=format)

        # FIXME: can't manage input folder
        if copy_partitioning_from == "FIRST_INPUT":
            inputs = self._get_input_refs()
            if len(inputs) == 0:
                logging.warn("No input declared yet, can't copy partitioning from first input")
            else:
                self.creation_settings["partitioningOptionId"] = "copy:dataset:%s" % (inputs[0])
        elif copy_partitioning_from is not None:
            self.creation_settings["partitioningOptionId"] = "copy:%s" % copy_partitioning_from

        ch.create(overwrite=overwrite)

        self.with_output(name, append=append)
        return self

    def _finish_creation_settings(self):
        super(CodeRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['script'] = self.script

class PythonRecipeCreator(CodeRecipeCreator):
    """
    Creates a Python recipe.
    A Python recipe can be defined either by its complete code, like a normal Python recipe, or
    by a function signature.

    When using a function, the function must take as arguments:
     * A list of dataframes corresponding to the dataframes of the input datasets
     * Optional named arguments corresponding to arguments passed to the creator
    """

    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, "python", name, project)

    DEFAULT_RECIPE_CODE_TMPL = """
# This code is autogenerated by PythonRecipeCreator function mode
import dataiku, dataiku.recipe, json
from {module_name} import {fname}
input_datasets = dataiku.recipe.get_inputs_as_datasets()
output_datasets = dataiku.recipe.get_outputs_as_datasets()
params = json.loads('{params_json}')

logging.info("Reading %d input datasets as dataframes" % len(input_datasets))
input_dataframes = [ds.get_dataframe() for ds in input_datasets]

logging.info("Calling user function {fname}")
function_input = input_dataframes if len(input_dataframes) > 1 else input_dataframes[0]
output_dataframes = {fname}(function_input, **params)

if not isinstance(output_dataframes, list):
    output_dataframes = [output_dataframes]

if not len(output_dataframes) == len(output_datasets):
    raise Exception("Code function {fname}() returned %d dataframes but recipe expects %d output datasets", \\
                                            (len(output_dataframes), len(output_datasets)))
output = list(zip(output_datasets, output_dataframes))
for ds, df in output:
    logging.info("Writing function result to dataset %s" % ds.name)
    ds.write_with_schema(df)
"""

    def with_function_name(self, module_name, function_name, custom_template=None, **function_args):
        """
        Defines this recipe as being a functional recipe calling a function name from a module name
        """
        script_tmpl = PythonRecipeCreator.DEFAULT_RECIPE_CODE_TMPL if custom_template is None else custom_template

        if function_args is None:
            function_args = {}

        code = script_tmpl.format(module_name=module_name, fname=function_name, params_json = json.dumps(function_args))
        self.with_script(code)

        return self

    def with_function(self, fn, custom_template=None, **function_args):
        import inspect
        #TODO: add in documentation that relative imports wont work
        module_name = inspect.getmodule(fn).__name__
        fname = fn.__name__
        return self.with_function_name(module_name, fname, custom_template, **function_args)

class SQLQueryRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a SQL query recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sql_query', name, project)


#####################################################
# Per-recipe-type classes: ML recipes
#####################################################

class PredictionScoringRecipeCreator(SingleOutputRecipeCreator):
    """
    Builder for the creation of a new "Prediction scoring" recipe, from an
    input dataset, with an input saved model identifier

    .. code-block:: python

        # Create a new prediction scoring recipe outputing to a new dataset

        project = client.get_project("MYPROJECT")
        builder = PredictionScoringRecipeCreator("my_scoring_recipe", project)
        builder.with_input_model("saved_model_id")
        builder.with_input("dataset_to_score")
        builder.with_new_output("my_output_dataset", "myconnection")

        # Or for a filesystem output connection
        # builder.with_new_output("my_output_dataset, "filesystem_managed", format_option_id="CSV_EXCEL_GZIP")

        new_recipe = builder.build()

        def with_new_output(self, name, connection_id, typeOptionId=None, format_option_id=None, override_sql_schema=None, partitioning_option_id=None, append=False, object_type='DATASET'):

    """

    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'prediction_scoring', name, project)

    def with_input_model(self, model_id):
        """Sets the input model"""
        return self._with_input(model_id, self.project.project_key, "model")


class EvaluationRecipeCreator(DSSRecipeCreator):
    """
    Builder for the creation of a new "Evaluate" recipe, from an
    input dataset, with an input saved model identifier

    .. code-block:: python

        # Create a new evaluation recipe outputing to a new dataset, to a metrics dataset and/or to a model evaluation store

        project = client.get_project("MYPROJECT")
        builder = project.new_recipe("evaluation")
        builder.with_input_model(saved_model_id)
        builder.with_input("dataset_to_evaluate")

        builder.with_output("output_scored")
        builder.with_output_metrics("output_metrics")
        builder.with_output_evaluation_store(evaluation_store_id)

        new_recipe = builder.build()

        # Access the settings

        er_settings = new_recipe.get_settings()
        payload = er_settings.obj_payload

        # Change the settings

        payload['dontComputePerformance'] = True
        payload['outputProbabilities'] = False
        payload['metrics'] = ["precision", "recall", "auc", "f1", "costMatrixGain"]

        # Manage evaluation labels

        payload['labels'] = [dict(key="label_1", value="value_1"), dict(key="label_2", value="value_2")]

        # Save the settings and run the recipe

        er_settings.save()

        new_recipe.run()

    Outputs must exist. They can be created using the following:

    .. code-block:: python

        builder = project.new_managed_dataset("output_scored")
        builder.with_store_into(connection)
        dataset = builder.create()

        builder = project.new_managed_dataset("output_scored")
        builder.with_store_into(connection)
        dataset = builder.create()

        evaluation_store_id = project.create_model_evaluation_store("output_model_evaluation").mes_id
    """

    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'evaluation', name, project)

    def with_input_model(self, model_id):
        """Sets the input model"""
        return self._with_input(model_id, self.project.project_key, "model")

    def with_output(self, name):
        """Sets the ouput dataset containing the scored input"""
        return self._with_output(name, role="main")

    def with_output_metrics(self, name):
        """Sets the output dataset containing the metrics"""
        return self._with_output(name, role="metrics")

    def with_output_evaluation_store(self, mes_id):
        """Sets the output model evaluation store"""
        return self._with_output(mes_id, role="evaluationStore")


class StandaloneEvaluationRecipeCreator(DSSRecipeCreator):
    """
    Builder for the creation of a new "Standalone Evaluate" recipe, from an
    input dataset

    .. code-block:: python

        # Create a new standalone evaluation of a scored dataset

        project = client.get_project("MYPROJECT")
        builder = project.new_recipe("standalone_evaluation")
        builder.with_input("scored_dataset_to_evaluate")
        builder.with_output_evaluation_store(evaluation_store_id)

        # Add a reference dataset (optional) to compute data drift

        builder.with_reference_dataset("reference_dataset")

        # Finish creation of the recipe

        new_recipe = builder.create()

        # Modify the model parameters in the SER settings

        ser_settings = new_recipe.get_settings()
        payload = ser_settings.obj_payload

        payload['predictionType'] = "BINARY_CLASSIFICATION"
        payload['targetVariable'] = "Survived"
        payload['predictionVariable'] = "prediction"
        payload['isProbaAware'] = True
        payload['dontComputePerformance'] = False

        # For a classification model with probabilities, the 'probas' section can be filled with the mapping of the class and the probability column
        # e.g. for a binary classification model with 2 columns: proba_0 and proba_1

        class_0 = dict(key=0, value="proba_0")
        class_1 = dict(key=1, value="proba_1")
        payload['probas'] = [class_0, class_1]

        # Change the 'features' settings for this standalone evaluation
        # e.g. reject the features that you do not want to use in the evaluation

        feature_passengerid = dict(name="Passenger_Id", role="REJECT", type="TEXT")
        feature_ticket = dict(name="Ticket", role="REJECT", type="TEXT")
        feature_cabin = dict(name="Cabin", role="REJECT", type="TEXT")

        payload['features'] = [feature_passengerid, feature_ticket, feature_cabin]

        # To set the cost matrix properly, access the 'metricParams' section of the payload and set the cost matrix weights:

        payload['metricParams'] = dict(costMatrixWeights=dict(tpGain=0.4, fpGain=-1.0, tnGain=0.2, fnGain=-0.5))

        # Save the recipe and run the recipe
        # Note that with this method, all the settings that were not explicitly set are instead set to their default value.

        ser_settings.save()

        new_recipe.run()

    Output model evaluation store must exist. It can be created using the following:

    .. code-block:: python

        evaluation_store_id = project.create_model_evaluation_store("output_model_evaluation").mes_id
    """

    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'standalone_evaluation', name, project)

    def with_output_evaluation_store(self, mes_id):
        """Sets the output model evaluation store"""
        return self._with_output(mes_id, role="main")

    def with_reference_dataset(self, dataset_name):
        """Sets the dataset to use as a reference in data drift computation (optional)."""
        return self._with_input(dataset_name, self.project.project_key, role="reference")


class ClusteringScoringRecipeCreator(SingleOutputRecipeCreator):
    """
    Builder for the creation of a new "Clustering scoring" recipe, from an
    input dataset, with an input saved model identifier

    .. code-block:: python

        # Create a new prediction scoring recipe outputing to a new dataset

        project = client.get_project("MYPROJECT")
        builder = ClusteringScoringRecipeCreator("my_scoring_recipe", project)
        builder.with_input_model("saved_model_id")
        builder.with_input("dataset_to_score")
        builder.with_new_output("my_output_dataset", "myconnection")

        # Or for a filesystem output connection
        # builder.with_new_output("my_output_dataset, "filesystem_managed", format_option_id="CSV_EXCEL_GZIP")

        new_recipe = builder.build()

        def with_new_output(self, name, connection_id, typeOptionId=None, format_option_id=None, override_sql_schema=None, partitioning_option_id=None, append=False, object_type='DATASET'):

    """

    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'clustering_scoring', name, project)

    def with_input_model(self, model_id):
        """Sets the input model"""
        return self._with_input(model_id, self.project.project_key, "model")
