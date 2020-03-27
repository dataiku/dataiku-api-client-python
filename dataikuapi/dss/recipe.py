from ..utils import DataikuException
from .discussion import DSSObjectDiscussions
import json
import logging

class DSSRecipe(object):
    """
    A handle to an existing recipe on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_recipe`
    """
    def __init__(self, client, project_key, recipe_name):
        self.client = client
        self.project_key = project_key
        self.recipe_name = recipe_name

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

        settings = self.get_settings()
        output_refs = settings.get_flat_output_refs()

        if len(output_refs) == 0:
            raise Exception("recipe has no outputs, can't run it")

        jd = self.client.get_project(self.project_key).new_job(job_type)
        jd.with_output(output_refs[0], partition=partitions)

        if wait:
            return jd.start_and_wait()
        else:
            return jd.start()

    def delete(self):
        """
        Delete the recipe
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))

    ########################################################
    # Recipe definition
    ########################################################

    def get_settings(self):
        """
        Gets the settings of the recipe, as a :class:`DSSRecipeSettings` or one of its subclasses.

        Some recipes have a dedicated class for the settings, with additional helpers to read and modify the settings

        Once you are done modifying the returned settings object, you can call :meth:`~DSSRecipeSettings.save` on it
        in order to save the modifications to the DSS recipe
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        print(data)
        type = data["recipe"]["type"]

        if type == "grouping":
            return GroupingRecipeSettings(self, data)
        else:
            return DSSRecipeSettings(self, data)

    def get_definition_and_payload(self):
        """
        Gets the definition of the recipe

        :returns: the definition, as a :py:class:`DSSRecipeDefinitionAndPayload` object, containing the recipe definition itself and its payload
        :rtype: :py:class:`DSSRecipeDefinitionAndPayload`
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        return DSSRecipeDefinitionAndPayload(self, data)

    def set_definition_and_payload(self, definition):
        """
        Sets and saves the definition of the recipe

        :param definition object: the definition, as a :py:class:`DSSRecipeDefinitionAndPayload` object. You should only set a definition object 
            that has been retrieved using the :py:meth:get_definition_and_payload call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name),
                body=definition.data)

    ########################################################
    # Recipe status
    ########################################################

    def get_status(self):
        """
        Gets the status of this recipe (status messages, engines status, ...)

        :return: an object to interact 
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipeStatus`
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/status" % (self.project_key, self.recipe_name))
        return DSSRecipeStatus(self.client, data)

    ########################################################
    # Recipe metadata
    ########################################################

    def get_metadata(self):
        """
        Get the metadata attached to this recipe. The metadata contains label, description
        checklists, tags and custom metadata of the recipe

        Returns:
            a dict object. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/5.0/rest/
        """
        return self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this recipe.

        Args:
            metadata: the new state of the metadata for the recipe. You should only set a metadata object 
            that has been retrieved using the get_metadata call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name),
                body=metadata)

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the recipe

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "RECIPE", self.recipe_name)

class DSSRecipeStatus(object):
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

class DSSRecipeSettings(object):
    """
    Settings of a recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    def __init__(self, recipe, data):
        self.recipe = recipe
        self.data = data
        self.recipe_settings = self.data["recipe"]
        self.str_payload = self.data.get("payload", None)
        self.obj_payload = None

    def save(self):
        """
        Saves back the recipe in DSS.
        """
        self._payload_to_str()
        return self.recipe.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.recipe.project_key, self.recipe.recipe_name),
                body=self.data)

    def _payload_to_str(self):
        if self.obj_payload is not None:
            self.str_payload = json.dumps(self.obj_payload)
            self.obj_payload = None
        if self.str_payload is not None:
            self.data["payload"] = self.str_payload

    def _payload_to_obj(self):
        if self.str_payload is not None:
            self.obj_payload = json.loads(self.str_payload)
            self.str_payload = None

    def get_recipe_raw_definition(self):
        """
        Get the recipe definition as a raw dict
        """
        return self.recipe_settings

    def get_recipe_inputs(self):
        """
        Get the list of inputs of this recipe
        """
        return self.recipe_settings.get('inputs')

    def get_recipe_outputs(self):
        """
        Get the list of outputs of this recipe
        """
        return self.recipe_settings.get('outputs')

    def get_recipe_params(self):
        """
        Get the parameters of this recipe, as a raw JSON object
        """
        return self.recipe_settings.get('params')

    def get_payload(self):
        """
        Get the payload or script of this recipe, as a raw string
        """
        self._payload_to_str()
        return self.str_payload

    def get_json_payload(self):
        """
        Get the payload or script of this recipe, as a JSON object
        """
        self._payload_to_obj()
        return self.obj_payload

    def set_payload(self, payload):
        """
        Set the raw payload of this recipe

        :param str payload: the payload, as a string
        """
        self.str_payload = payload
        self.obj_payload = None

    def set_json_payload(self, payload):
        """
        Set the raw payload of this recipe

        :param dict payload: the payload, as a dict. The payload will be converted to a JSON string internally
        """
        self.str_payload = None
        self.obj_payload = payload

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

    def get_flat_input_refs(self):
        ret = []
        for role_key, role_obj in self.get_recipe_inputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret

    def get_flat_output_refs(self):
        ret = []
        for role_key, role_obj in self.get_recipe_outputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret



# Old name
class DSSRecipeDefinitionAndPayload(DSSRecipeSettings):
    """
    Deprecated. Settings of a recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    pass

class GroupingRecipeSettings(DSSRecipeSettings):
    """
    Settings of a grouping recipe. Do not create this directly, use :meth:`DSSRecipe.get_settings`
    """
    def clear_grouping_keys(self):
        """Removes all grouping keys from this grouping recipe"""
        self._payload_to_obj()
        self.obj_payload["keys"] = []

    def add_grouping_key(self, column):
        """
        Adds grouping on a column
        :param str column: Column to group on
        """
        self._payload_to_obj()
        self.obj_payload["keys"].append({"column":column})

    def set_global_count_enabled(self, enabled):
        self._payload_to_obj()
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

    def with_new_output(self, name, connection_id, typeOptionId=None, format_option_id=None, override_sql_schema=None, partitioning_option_id=None, append=False, object_type='DATASET'):
        """
        Create a new dataset as output to the recipe-to-be-created. The dataset is not created immediately,
        but when the recipe is created (ie in the build() method)

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
        """
        if object_type == 'DATASET':
            assert self.create_output_dataset is None
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

########################
#
# actual recipe creators
#
########################
class WindowRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Window recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'window', name, project)

class SyncRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sync recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sync', name, project)

class SortRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sort recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sort', name, project)

class TopNRecipeCreator(DSSRecipeCreator):
    """
    Create a TopN recipe
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'topn', name, project)

class DistinctRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Distinct recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'distinct', name, project)

class PrepareRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Prepare recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'shaker', name, project)

class GroupingRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Group recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'grouping', name, project)
        self.group_key = None

    def with_group_key(self, group_key):
        """
        Set a column as grouping key

        :param str group_key: name of a column in the input
        """
        self.group_key = group_key
        return self

    def _finish_creation_settings(self):
        super(GroupingRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['groupKey'] = self.group_key

class JoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Join recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'join', name, project)

class StackRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Stack recipe
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'vstack', name, project)

class SamplingRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sample/Filter recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sampling', name, project)

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
                                append=False):
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

        ch.create()

        self.with_output(name, append=append)
        return self

    

    def _finish_creation_settings(self):
        super(CodeRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['script'] = self.script


class SQLQueryRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a SQL query recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sql_query', name, project)

class SplitRecipeCreator(DSSRecipeCreator):
    """
    Create a Split recipe
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, "split", name, project)

    def _finish_creation_settings(self):
        pass

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


class DownloadRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Download recipe
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'download', name, project)


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