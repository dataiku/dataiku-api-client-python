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
    """
    An item in a list of recipes. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_recipes()`
    """
    def __init__(self, client, data):
        super(DSSRecipeListItem, self).__init__(data)
        self.client = client

    def to_recipe(self):
        """
        Gets a handle corresponding to this recipe.

        :rtype: :class:`DSSRecipe`
        """
        return DSSRecipe(self.client, self._data["projectKey"], self._data["name"])

    @property
    def name(self):
        """
        Get the name of the recipe.

        :rtype: string
        """
        return self._data["name"]

    @property
    def id(self):
        """
        Get the identifier of the recipe.

        For recipes, the name is the identifier.

        :rtype: string
        """
        return self._data["name"]

    @property
    def type(self):
        """
        Get the type of the recipe.

        :return: a recipe type, for example 'sync' or 'join'
        :rtype: string
        """
        return self._data["type"]

class DSSRecipe(object):
    """
    A handle to an existing recipe on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_recipe()`
    """
    def __init__(self, client, project_key, recipe_name):
        self.client = client
        self.project_key = project_key
        self.recipe_name = recipe_name

    @property
    def id(self):
        """
        Get the identifier of the recipe.

        For recipes, the name is the identifier.

        :rtype: string
        """
        return self.recipe_name

    @property
    def name(self):
        """
        Get the name of the recipe.

        :rtype: string
        """
        return self.recipe_name

    def compute_schema_updates(self):
        """
        Computes which updates are required to the outputs of this recipe.

        This method only computes which changes would be needed to make the schema of the outputs 
        of the reicpe match the actual schema that the recipe will produce. To effectively apply 
        these changes to the outputs, you can use the :meth:`~RequiredSchemaUpdates.apply()` on 
        the returned object.

        .. note::

            Not all recipe types can compute automatically the schema of their outputs. Code 
            recipes like Python recipes, notably can't. This method raises an exception in 
            these cases.

        Usage example:

        .. code-block:: python

            required_updates = recipe.compute_schema_updates()
            if required_updates.any_action_required():
                print("Some schemas will be updated")

            # Note that you can call apply even if no changes are required. This will be noop
            required_updates.apply()

        :return: an object containing the required updates
        :rtype: :class:`RequiredSchemaUpdates`
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

        :param string job_type: job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param string partitions: if the outputs are partitioned, a partition spec. A spec is a comma-separated list of partition 
                                  identifiers, and a partition identifier is a pipe-separated list of values for the partitioning
                                  dimensions 
        :param boolean no_fail: if True, does not raise if the job failed
        :param boolean wait: if True, the method waits for the job complettion. If False, the method returns immediately
        
        :return: a job handle corresponding to the recipe run
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
        Delete the recipe.
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))

    def get_settings(self):
        """
        Get the settings of the recipe, as a :class:`DSSRecipeSettings` or one of its subclasses.

        Some recipes have a dedicated class for the settings, with additional helpers to read and modify the settings

        Once you are done modifying the returned settings object, you can call :meth:`~DSSRecipeSettings.save` on it
        in order to save the modifications to the DSS recipe.

        :rtype: :class:`DSSRecipeSettings` or a subclass
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
        elif type == "pivot":
            return PivotRecipeSettings(self, data)
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
        Get the definition of the recipe.

        .. attention::

            Deprecated. Use :meth:`get_settings`

        :return: an object holding both the raw definition of the recipe (the type, which inputs and outputs, engine settings...) 
                 and the payload (SQL script, Python code, join definition,... depending on type)
        :rtype: :class:`DSSRecipeDefinitionAndPayload`
        """
        warnings.warn("Recipe.get_definition_and_payload is deprecated, please use get_settings", DeprecationWarning)

        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        return DSSRecipeDefinitionAndPayload(self, data)

    def set_definition_and_payload(self, definition):
        """
        Set the definition of the recipe.

        .. attention::

            Deprecated. Use :meth:`get_settings` then :meth:`DSSRecipeSettings.save()`

        .. important::

            The **definition** parameter should come from a call to :meth:`get_definition()`

        :param object definition: a recipe definition, as returned by :meth:`get_definition()`
        """
        warnings.warn("Recipe.set_definition_and_payload is deprecated, please use get_settings", DeprecationWarning)
        definition._payload_to_str()
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name),
                body=definition.data)

    def get_status(self):
        """
        Gets the status of this recipe.

        The status of a recipe is made of messages from checks performed by DSS on the recipe, of messages related
        to engines availability for the recipe, of messages about testing the recipe on the engine, ...

        :return: an object to interact with the status
        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipeStatus`
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/status" % (self.project_key, self.recipe_name))
        return DSSRecipeStatus(self.client, data)


    def get_metadata(self):
        """
        Get the metadata attached to this recipe. 

        The metadata contains label, description checklists, tags and custom metadata of the recipe

        :return: the metadata as a dict, with fields:

                    * **label** : label of the object (not defined for recipes)
                    * **description** : description of the object (not defined for recipes)
                    * **checklists** : checklists of the object, as a dict with a **checklists** field, which is a list of checklists, each a dict of fields:

                        * **id** : identifier of the checklist
                        * **title** : label of the checklist
                        * **createdBy** : user who created the checklist
                        * **createdOn** : timestamp of creation, in milliseconds
                        * **items** : list of the items in the checklist, each a dict of

                            * **done** : True if the item has been done
                            * **text** : label of the item
                            * **createdBy** : who created the item
                            * **createdOn** : when the item was created, as a timestamp in milliseconds
                            * **stateChangedBy** : who ticked the item as done (or not done)
                            * **stateChangedOn** : when the item was last changed to done (or not done), as a timestamp in milliseconds 

                    * **tags** : list of tags, each a string
                    * **custom** : custom metadata, as a dict with a **kv** field, which is a dict with any contents the user wishes
                    * **customFields** : dict of custom field info (not defined for recipes)

        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this recipe.

        .. important::

            You should only set a **metadata** object that has been retrieved using :meth:`get_metadata()`.

        :params dict metadata: the new state of the metadata for the recipe. 
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s/metadata" % (self.project_key, self.recipe_name),
                body=metadata)

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the recipe.

        :return: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "RECIPE", self.recipe_name)

    def get_continuous_activity(self):
        """
        Get a handle on the associated continuous activity.

        .. note::

            Should only be used on continuous recipes.

        :rtype: :class:`dataikuapi.dss.continuousactivity.DSSContinuousActivity`
        """
        from .continuousactivity import DSSContinuousActivity
        return DSSContinuousActivity(self.client, self.project_key, self.recipe_name)

    def move_to_zone(self, zone):
        """
        Move this object to a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object
        """
        if isinstance(zone, basestring):
           zone = self.client.get_project(self.project_key).get_flow().get_zone(zone)
        zone.add_item(self)

class DSSRecipeStatus(object):
    """
    Status of a recipe.

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_status`
    """
    def __init__(self, client, data):
        self.client = client
        self.data = data

    def get_selected_engine_details(self):
        """
        Get the selected engine for this recipe.

        This method will raise if there is no selected engine, whether it's because the present recipe type
        has no notion of engine, or because DSS couldn't find any viable engine for running the recipe.

        :return: a dict of the details of the selected recipe, with fields:

                    * **type** : engine type
                    * **typeLabel** : user-friendly label for the type
                    * **variant** : engine sub-type. For example, **type** can be SPARK, and **variant** one of SPARK_SQL, SPARK_SCALA or SPARK_NATIVE
                    * **variantLabel** : user-friendly label for the variant
                    * **label** : user-friendly label for the engine (type and variant)
                    * **description** : longer version of **label**
                    * **isSelectable** : whether the engine can be selected (would be always True for the engine returned by this method)
                    * **recommended** : whether this is the engine DSS recommends, given the inputs and outputs of the recipe, and the DSS instance setup
                    * **statusWarnLevel** : status of the check on the engine. Possible values: OK, WARN, ERROR
                    * **statusMessage** : optional message about the status
                    * **statusAdditionalMessage** : optional details about **statusMessage** (only for Prepare recipes)
                    * **canEngineAppend** : whether the engine handles appending to outputs, instead of just overwriting outputs

                 Many engines have additional fields with more detailed information on their known abilities:

                    * **queryBased** : whether the engine will translate the recipe to SQL form
                    * **canAnalyticalFunctions** : whether OLAP functions are accessible (for group, window, join, ... )
                    * **canStddevAsAnalyticalFunctions** : whether there is an OLAP function to compute the standard deviation
                    * **canDistinctSelect** : whether SELECT DISTINCT... is possible (for visual recipes)
                    * **canNonEquiJoin** : whether join conditions can be other than mere equalities (for join recipes)
                    * **canFullOuterJoin** : whether full outer join is possible (for join recipes)
                    * **canDeduplicateJoinMatches** : whether it's possible to have unique join matches (for join recipes)
                    * **doNotSupportLeadLagWithWindow** : whether lead and lag exist as OLAP functions
                    * **aggregabilities** : capabilities for the aggregates in this SQL dialect, as a dict of aggregate name to a dict of capabilities
                    * **identifierQuotingCharacter** : quoting character for identifier in SQL code
                    * **stringQuotingCharacter** : quoting character for literals in SQL code
                    * **lowercasesColumnNames** : whether the engine will automatically lowercase column names

        :rtype: dict
        """
        if not "selectedEngine" in self.data:
            raise ValueError("This recipe doesn't have a selected engine")
        return self.data["selectedEngine"]

    def get_engines_details(self):
        """
        Get details about all possible engines for this recipe.

        This method will raise if there is no engine, whether it's because the present recipe type
        has no notion of engine, or because DSS couldn't find any viable engine for running the recipe.

        :return: a list of dict of the details of each possible engine. See :meth:`get_selected_engine_details()` for the fields of each dict.
        :rtype: list[dict]
        """
        if not "engines" in self.data:
            raise ValueError("This recipe doesn't have engines")
        return self.data["engines"]

    def get_status_severity(self):
        """
        Get the overall status of the recipe.

        This is the final result of checking the different parts of the recipe, and depends on the recipe type. Examples
        of checks done include:

        - checking the validity of the formulas in computed columns or filters
        - checking if some of the input columns retrieved by joins overlap
        - checking against the SQL database if the generated SQL is valid

        :return: SUCCESS, WARNING, ERROR or INFO. None if the status has no message at all.
        :rtype: string
        """
        return self.data["allMessagesForFrontend"].get("maxSeverity")

    def get_status_messages(self, as_objects=False):
        """
        Returns status messages for this recipe.

        :param boolean as_objects: if True, return a list of :class:`dataikuapi.dss.utils.DSSInfoMessage`. If False, as a list
                                   of raw dicts.

        :return: if **as_objects** is True, a list of  :class:`dataikuapi.dss.utils.DSSInfoMessage`, otherwise a list of 
                 message information, each one a dict of:

                     * **severity** : severity of the error in the message. Possible values are SUCCESS, INFO, WARNING, ERROR
                     * **isFatal** : for ERROR **severity**, whether the error is considered fatal to the operation
                     * **code** : a string with a well-known code documented in `DSS doc <https://doc.dataiku.com/dss/latest/troubleshooting/errors/index.html>`_
                     * **title** : short message
                     * **message** : the error message
                     * **details** : a more detailed error description

        :rtype: list
        """
        if as_objects:
            return [DSSInfoMessage(message) for message in self.data["allMessagesForFrontend"].get("messages", [])]
        else:
            return self.data["allMessagesForFrontend"]["messages"]


class DSSRecipeSettings(DSSTaggableObjectSettings):
    """
    Settings of a recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings`
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
        Save back the recipe in DSS.
        """
        self._payload_to_str()
        return self.recipe.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.recipe.project_key, self.recipe.recipe_name),
                body=self.data)

    @property
    def type(self):
        """
        Get the type of the recipe.

        :return: a type, like 'sync', 'python' or 'join'
        :rtype: string
        """
        return self.recipe_settings["type"]

    @property
    def str_payload(self):
        """
        The raw "payload" of the recipe.

        This is exactly the data persisted on disk.

        :return: for code recipes, the payload will be the script of the recipe. For visual recipes,
                 the payload is a JSON of settings that are specific to the recipe type, like the 
                 definitions of the aggregations for a grouping recipe. 
        :rtype: string
        """
        self._payload_to_str()
        return self._str_payload

    @str_payload.setter
    def str_payload(self, payload):
        self._str_payload = payload
        self._obj_payload = None

    @property
    def obj_payload(self):
        """
        The "payload" of the recipe, parsed from JSON.

        .. note:: 

            Do not use on code recipes, their payload isn't JSON-encoded.

        :return: settings that are specific to the recipe type, like the definitions of the 
                 aggregations for a grouping recipe. 
        :rtype: dict
        """
        self._payload_to_obj()
        return self._obj_payload

    @property
    def raw_params(self):
        """
        The non-payload settings of the recipe.

        :return: recipe type-specific settings that aren't stored in the payload. Typically
                 this comprises engine settings.
        :rtype: dict 
        """
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
        Get the recipe definition.

        :return: the part of the recipe's settings that aren't stored in the payload, as a dict. Notable fields are:

                    * **name** and **projectKey** : identifiers of the recipe
                    * **type** : type of the recipe
                    * **shortDesc** : short description of the recipe
                    * **description** : longer description (markdown-enabled)
                    * **tags** : list of tags, each one a string
                    * **checklists** : list of checklists on the recipe
                    * **doc** : free text attached to the recipe (not shown in UI)
                    * **params** : type-specific parameters of the recipe (on top of what is in the payload)
                    * **customMeta** : dict with a **kv** field, itself a dict
                    * **redispatchPartitioning** : for 'sync' and 'shaker' recipe, whether the recipe re-dispatches partitions of the input to the (partitioned) output
                    * **maxRunningActivities** : maximum number of partitions this recipe can run in parallel in a given job 
                    * **variables** : dict of recipe-specific variables
                    * **dkuProperties** : list of properties, each a dict with **name** and **value** string fields
                    * **labels** : (for model training recipes) list of labels to propagate to the model evaluation stores. Each label is a dict with fields **key** and **value**
                    * **inputs** : input roles to the recipe, as a dict of role name to role, where a role is a dict with an **items** field consisting of a list of one dict per input object. Each individual input has fields:

                        * **ref** : a dataset name or a managed folder id or a saved model id. Should be prefixed by the project key for exposed items, like in "PROJECT_KEY.dataset_name"
                        * **deps** : for partitioned inputs, a list of partition dependencies mapping output dimensions to dimensions in this input. Each partition dependency is a dict of:

                            * **out** : reference to the output used to compute the values for this partition dimension
                            * **idim** : name of the partition dimension in the input
                            * **odim** : name of the partition dimension in the output **out**
                            * **func** : function to use to deduce input partition values from a given output partition value. Possible values are: equals, all_available, time_range, latest_available, values, custom_python
                            * **params** : additional parameters for the dependency, for example the Python code when **func** is 'custom_python'
                            * **values** : list of values when **func** is 'values'. Each value is a string
                            * **expandVariables** : when **func** is 'values', whether the strings in **values** should go through variable expansion, variables being added as '${variable_name}'.

                    * **outputs** : output roles to the recipe, as a dict of role name to role, where a role is a dict with a **items** field consisting of a list of one dict per output object. Each individual output has fields:

                        * **ref** : a dataset name or a managed folder id or a saved model id. Should be prefixed by the project key for exposed items, like in "PROJECT_KEY.dataset_name"
                        * **appendMode** : if True, the recipe should append into the output; if False, the recipe should overwrite the output when running

        :rtype: dict
        """
        return self.recipe_settings

    def get_recipe_inputs(self):
        """
        Get the inputs to this recipe.

        :rtype: dict
        """
        return self.recipe_settings.get('inputs')

    def get_recipe_outputs(self):
        """
        Get the outputs of this recipe.

        :rtype: dict
        """
        return self.recipe_settings.get('outputs')

    def get_recipe_params(self):
        """
        The non-payload settings of the recipe.

        :return: recipe type-specific settings that aren't stored in the payload. Typically
                 this comprises engine settings.
        :rtype: dict 
        """
        return self.recipe_settings.get('params')

    def get_payload(self):
        """
        The raw "payload" of the recipe.

        This is exactly the data persisted on disk.

        :return: for code recipes, the payload will be the script of the recipe. For visual recipes,
                 the payload is a JSON of settings that are specific to the recipe type, like the 
                 definitions of the aggregations for a grouping recipe. 
        :rtype: string
        """
        self._payload_to_str()
        return self._str_payload

    def get_json_payload(self):
        """
        The "payload" of the recipe, parsed from JSON.

        .. note:: 

            Do not use on code recipes, their payload isn't JSON-encoded.

        :return: settings that are specific to the recipe type, like the definitions of the 
                 aggregations for a grouping recipe. 
        :rtype: dict
        """
        self._payload_to_obj()
        return self._obj_payload

    def set_payload(self, payload):
        """
        Set the payload of this recipe.

        :param string payload: the payload, as a string
        """
        self._str_payload = payload
        self._obj_payload = None

    def set_json_payload(self, payload):
        """
        Set the payload of this recipe.

        :param dict payload: the payload, as a dict. Will be converted to JSON internally.
        """
        self._str_payload = None
        self._obj_payload = payload

    def has_input(self, input_ref):
        """
        Whether a ref is part of the recipe's inputs.

        :param string input_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id. 
                                 Should be prefixed by the project key for exposed items, like in "PROJECT_KEY.dataset_name"
        :rtype: boolean
        """
        inputs = self.get_recipe_inputs()
        for (input_role_name, input_role) in inputs.items():
            for item in input_role.get("items", []):
                if item.get("ref", None) == input_ref:
                    return True
        return False

    def has_output(self, output_ref):
        """
        Whether a ref is part of the recipe's outputs.

        :param string output_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id. 
                                  Should be prefixed by the project key for exposed items, like in "PROJECT_KEY.dataset_name"
        :rtype: boolean
        """
        outputs = self.get_recipe_outputs()
        for (output_role_name, output_role) in outputs.items():
            for item in output_role.get("items", []):
                if item.get("ref", None) == output_ref:
                    return True
        return False

    def replace_input(self, current_input_ref, new_input_ref):
        """
        Replaces an input of this recipe by another.

        If the **current_input_ref** isn't part of the recipe's inputs, this method has no effect.

        :param string current_input_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id, 
                                         that is currently input to the recipe
        :param string new_input_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id, that
                                     **current_input_ref** should be replaced with.
        """
        inputs = self.get_recipe_inputs()
        for (input_role_name, input_role) in inputs.items():
            for item in input_role.get("items", []):
                if item.get("ref", None) == current_input_ref:
                    item["ref"] = new_input_ref

    def replace_output(self, current_output_ref, new_output_ref):
        """
        Replaces an output of this recipe by another.

        If the **current_output_ref** isn't part of the recipe's outputs, this method has no effect.

        :param string current_output_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id, 
                                          that is currently output to the recipe
        :param string new_output_ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id, that
                                      **current_output_ref** should be replaced with.
        """
        outputs = self.get_recipe_outputs()
        for (output_role_name, output_role) in outputs.items():
            for item in output_role.get("items", []):
                if item.get("ref", None) == current_output_ref:
                    item["ref"] = new_output_ref

    def add_input(self, role, ref, partition_deps=None):
        """
        Add an input to the recipe.

        For most recipes, there is only one role, named "main". Some few recipes have additional roles,
        like scoring recipes which have a "model" role. Check the roles known to the recipe with 
        :meth:`get_recipe_inputs()`.

        :param string role: name of the role of the recipe in which to add **ref** as input
        :param string ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id
        :param list partition_deps: if **ref** points to a partitioned object, a list of partition dependencies, one
                                    per dimension in the partitioning scheme
        """
        if partition_deps is None:
            partition_deps = []
        self._get_or_create_input_role(role)["items"].append({"ref": ref, "deps": partition_deps})

    def add_output(self, role, ref, append_mode=False):
        """
        Add an output to the recipe.

        For most recipes, there is only one role, named "main". Some few recipes have additional roles,
        like evaluation recipes which have a "metrics" role. Check the roles known to the recipe with
        :meth:`get_recipe_outputs()`.

        :param string role: name of the role of the recipe in which to add **ref** as input
        :param string ref: a ref to an object in DSS, i.e. a dataset name or a managed folder id or a saved model id
        :param list partition_deps: if **ref** points to a partitioned object, a list of partition dependencies, one
                                    per dimension in the partitioning scheme
        """
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
        List all input refs of this recipe, regardless of the input role.

        :return: a list of refs, i.e. of dataset names or managed folder ids or saved model ids
        :rtype: list[string]
        """
        ret = []
        for role_key, role_obj in self.get_recipe_inputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret

    def get_flat_output_refs(self):
        """
        List all output refs of this recipe, regardless of the input role.

        :return: a list of refs, i.e. of dataset names or managed folder ids or saved model ids
        :rtype: list[string]
        """
        ret = []
        for role_key, role_obj in self.get_recipe_outputs().items():
            for item in role_obj["items"]:
                ret.append(item["ref"])
        return ret


class DSSRecipeDefinitionAndPayload(DSSRecipeSettings):
    """
    Settings of a recipe.

    .. note::

        Deprecated. Alias to :class:`DSSRecipeSettings`, use :meth:`DSSRecipe.get_settings()` instead.
    """
    pass

class RequiredSchemaUpdates(object):
    """
    Handle on a set of required updates to the schema of the outputs of a recipe.

    .. important::
    
        Do not instantiate directly, use :meth:`DSSRecipe.compute_schema_updates()`

    For example, changes can be new columns in the output of a Group recipe when new aggregates
    are activated in the recipe's settings.
    """

    def __init__(self, recipe, data):
        self.recipe = recipe
        self.data = data
        self.drop_and_recreate = True
        self.synchronize_metastore = True

    def any_action_required(self):
        """
        Whether there are changes at all.

        :rtype: boolean
        """
        return self.data["totalIncompatibilities"] > 0

    def apply(self):
        """
        Apply the changes.

        All the updates found to be required are applied, for each of the recipe's outputs.
        """
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
    Helper to create new recipes.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
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
        """
        Set the name of the recipe-to-be-created.

        :param string name: a recipe name. Should only use alphanum letters and underscores. Cannot contain dots.
        """
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

    def with_input(self, input_id, project_key=None, role="main"):
        """
        Add an existing object as input to the recipe-to-be-created.

        :param string input_id: name of the dataset, or identifier of the managed folder
                                or identifier of the saved model
        :param string project_key: project containing the object, if different from the one where the recipe is created
        :param string role: the role of the recipe in which the input should be added. Most recipes only have one
                            role named "main".
        """
        return self._with_input(input_id, project_key, role)

    def with_output(self, output_id, append=False, role="main"):
        """
        Add an existing object as output to the recipe-to-be-created.

        The output dataset must already exist. 

        :param string output_id: name of the dataset, or identifier of the managed folder
                                 or identifier of the saved model
        :param boolean append: whether the recipe should append or overwrite the output when running
                               (note: not available for all dataset types)
        :param string role: the role of the recipe in which the input should be added. Most recipes only have one
                            role named "main".
        """
        return self._with_output(output_id, append, role)

    def build(self):
        """
        Create the recipe.

        .. note::

            Deprecated. Alias to :meth:`create()`
        """
        return self.create()

    def create(self):
        """
        Creates the new recipe in the project, and return a handle to interact with it.

        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipe`
        """
        self._finish_creation_settings()
        return self.project.create_recipe(self.recipe_proto, self.creation_settings)

    def set_raw_mode(self):
        """
        Activate raw creation mode. 

        .. caution::

            For advanced uses only.

        In this mode, the field "recipe_proto" of this recipe creator is used as-is to create the recipe,
        and if it exists, the value of creation_settings["rawPayload"] is used as the payload of the 
        created recipe. No checks of existence or validity of the inputs or outputs are done, and no
        output is auto-created.
        """
        self.creation_settings["rawCreation"] = True

    def _finish_creation_settings(self):
        pass

class SingleOutputRecipeCreator(DSSRecipeCreator):
    """
    Create a recipe that has a single output.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """

    def __init__(self, type, name, project):
        DSSRecipeCreator.__init__(self, type, name, project)
        self.create_output_dataset = None
        self.output_dataset_settings = None
        self.create_output_folder = None
        self.output_folder_settings = None

    def with_existing_output(self, output_id, append=False):
        """
        Add an existing object as output to the recipe-to-be-created.

        The output dataset must already exist.

        :param string output_id: name of the dataset, or identifier of the managed folder
                                 or identifier of the saved model
        :param boolean append: whether the recipe should append or overwrite the output when running
                               (note: not available for all dataset types)
        """
        assert self.create_output_dataset is None
        self.create_output_dataset = False
        self._with_output(output_id, append)
        return self

    def with_new_output(self, name, connection, type=None, format=None, 
                        override_sql_schema=None, partitioning_option_id=None, 
                        append=False, object_type='DATASET', overwrite=False, **kwargs):
        """
        Create a new dataset or managed folder as output to the recipe-to-be-created. 

        The dataset or managed folder is not created immediately, but when the recipe 
        is created (ie in the create() method). Whether a dataset is created or a managed
        folder is created, depends on the recipe type.

        :param string name: name of the dataset or identifier of the managed folder
        :param string connection: name of the connection to create the dataset or managed folder on
        :param string type: sub-type of dataset or managed folder, for connections where the type 
                            could be ambiguous. Typically applies to SSH connections, where sub-types
                            can be SCP or SFTP
        :param string format: name of a format preset relevant for the dataset type. Possible values are: CSV_ESCAPING_NOGZIP_FORHIVE,
                              CSV_UNIX_GZIP, CSV_EXCEL_GZIP, CSV_EXCEL_GZIP_BIGQUERY, CSV_NOQUOTING_NOGZIP_FORPIG, PARQUET_HIVE,
                              AVRO, ORC
        :param boolean override_sql_schema: schema to force dataset, for SQL dataset. If left empty, will be autodetected
        :param string partitioning_option_id: to copy the partitioning schema of an existing dataset 'foo', pass a
                                              value of 'copy:dataset:foo'. If unset, then the output will be non-partitioned
        :param boolean append: whether the recipe should append or overwrite the output when running
                               (note: not available for all dataset types)
        :param string object_type: DATASET or MANAGED_FOLDER
        :param boolean overwrite: If the dataset being created already exists, overwrite it (and delete data)
        """
        for k in kwargs: #for retrop comp
            if k == "connection_id":
                connection = kwargs.get("connection_id")
            elif k == "format_option_id":
                format = kwargs.get("format_option_id")
            elif k == "typeOptionId":
                type = kwargs.get("typeOptionId")
            elif k == "type_option_id":
                type = kwargs.get("type_option_id")
            else:
                raise Exception("Unknown argument '{}'".format(k))
        
        if object_type == 'DATASET':
            assert self.create_output_dataset is None

            dataset = self.project.get_dataset(name)
            if overwrite and dataset.exists():
                dataset.delete(drop_data=True)

            self.create_output_dataset = True
            self.output_dataset_settings = {'connectionId':connection,'typeOptionId':type,'specificSettings':{'formatOptionId':format, 'overrideSQLSchema':override_sql_schema},'partitioningOptionId':partitioning_option_id}
            self._with_output(name, append)
        elif object_type == 'MANAGED_FOLDER':
            assert self.create_output_folder is None
            self.create_output_folder = True
            self.output_folder_settings = {'connectionId':connection,'typeOptionId':type,'partitioningOptionId':partitioning_option_id}
            self._with_output(name, append)
        return self

    def with_output(self, output_id, append=False):
        """
        Add an existing object as output to the recipe-to-be-created.

        .. note::

            Alias of :meth:`with_existing_output()`
        """
        return self.with_existing_output(output_id, append)

    def _finish_creation_settings(self):
        self.creation_settings['createOutputDataset'] = self.create_output_dataset
        self.creation_settings['outputDatasetSettings'] = self.output_dataset_settings
        self.creation_settings['createOutputFolder'] = self.create_output_folder
        self.creation_settings['outputFolderSettings'] = self.output_folder_settings

class VirtualInputsSingleOutputRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a recipe that has a single output and several inputs.
    """

    def __init__(self, type, name, project):
        SingleOutputRecipeCreator.__init__(self, type, name, project)
        self.virtual_inputs = []

    def with_input(self, input_id, project_key=None):
        """
        Add an existing object as input to the recipe-to-be-created.

        :param string input_id: name of the dataset
        :param string project_key: project containing the object, if different from the one where the recipe is created
        """
        self.virtual_inputs.append(self._build_ref(input_id, project_key))
        return self

    def _finish_creation_settings(self):
        super(VirtualInputsSingleOutputRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['virtualInputs'] = self.virtual_inputs


#####################################################
# Per-recipe-type classes: Visual recipes
#####################################################

class GroupingRecipeSettings(DSSRecipeSettings):
    """
    Settings of a grouping recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    def clear_grouping_keys(self):
        """
        Clear all grouping keys.
        """
        self.obj_payload["keys"] = []

    def add_grouping_key(self, column):
        """
        Adds grouping on a column.

        :param string column: column to group on
        """
        self.obj_payload["keys"].append({"column":column})

    def set_global_count_enabled(self, enabled):
        """
        Activate computing the count of records per group.
        
        :param boolean enabled: True if the global count should be activated
        """
        self.obj_payload["globalCount"] = enabled

    def get_or_create_column_settings(self, column):
        """
        Get a dict representing the aggregations to perform on a column.

        If the column has no aggregation on it yet, the dict is created and added to the settings.

        :param string column: name of the column to aggregate on

        :return: the settings of the aggregations on a particular column, as a dict with fields:

                    * **column** : name of the column to aggregate
                    * **min**, **max**, **count**, **countDistinct**, **sum**, **concat**, **stddev**, **avg**, **first**, **last** and **sum2** : one boolean per aggregate, indicating whether it's computed. **sum2** is the sum of squares.
                    * **concatSeparator** : for the **concat** aggregate, a string to separate values 
                    * **concatDistinct** : for the **concat** aggregate, whether values concatenated are deduplicated
                    * **firstLastNotNull** : for **last** and **first**, whether empty values are ignored
                    * **orderColumn** : for **last** and **first**, name of a column on which rows in the group are sorted prior to taking the first or last row

        :rtype: dict
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

    def set_column_aggregations(self, column, type=None, min=False, max=False, count=False, count_distinct=False,
                                sum=False,concat=False,stddev=False,avg=False):
        """
        Set the basic aggregations on a column.

        .. note::

            Not all aggregations may be possible. For example string-typed columns don't have a mean
            or standard deviation, and some SQL databases can't compute the exact standard deviation.

        The method returns a reference to the settings of the column, not a copy. Modifying the dict
        returned by the method, then calling :meth:`DSSRecipeSettings.save()` will commit the changes.

        Usage example:

        .. code-block::

            # activate the concat aggregate on a column, and set optional parameters
            # pertaining to concatenation
            settings = recipe.get_settings()
            column_settings = settings.set_column_aggregations("my_column_name", concat=True)
            column_settings["concatDistinct"] = True
            column_settings["concatSeparator"] = ', '
            settings.save()


        :param string column: The column name
        :param string type: The type of the column (as a DSS schema type name)
        :param boolean min: whether the min aggregate is computed
        :param boolean max: whether the max aggregate is computed
        :param boolean count: whether the count aggregate is computed
        :param boolean count_distinct: whether the count distinct aggregate is computed
        :param boolean sum: whether the sum aggregate is computed
        :param boolean concat: whether the concat aggregate is computed
        :param boolean avg: whether the mean aggregate is computed
        :param boolean stddev: whether the standard deviation aggregate is computed

        :return: the settings of the aggregations on a the column, as a dict with fields:

                    * **column** : name of the column to aggregate
                    * **min**, **max**, **count**, **countDistinct**, **sum**, **concat**, **stddev**, **avg**, **first**, **last** : one boolean per aggregate, indicating whether it's computed
                    * **concatSeparator** : for the **concat** aggregate, a string to separate values 
                    * **concatDistinct** : for the **concat** aggregate, whether values concatenated are deduplicated
                    * **firstLastNotNull** : for **last** and **first**, whether empty values are ignored
                    * **orderColumn** : for **last** and **first**, name of a column on which rows in the group are sorted prior to taking the first or last row
        
        :rtype dict
        """
        cs = self.get_or_create_column_settings(column)
        if type is not None:
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
    Create a Group recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'grouping', name, project)
        self.group_key = None

    def with_group_key(self, group_key):
        """
        Set a column as the first grouping key. 

        Only a single grouping key may be set at recipe creation time. To add more grouping keys,
        get the recipe settings and use :meth:`GroupingRecipeSettings.add_grouping_key()`. To have
        no grouping keys at all, get the recipe settings and use 
        :meth:`GroupingRecipeSettings.clear_grouping_keys()`.

        :param string group_key: name of a column in the input dataset

        :return: self
        :rtype: :class:`GroupingRecipeCreator`
        """
        self.group_key = group_key
        return self

    def _finish_creation_settings(self):
        super(GroupingRecipeCreator, self)._finish_creation_settings()
        if self.group_key is not None:
            self.creation_settings['groupKey'] = self.group_key


class WindowRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Window recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for window

class WindowRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Window recipe
 
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
   """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'window', name, project)


class SyncRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Sync recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for sync

class SyncRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sync recipe
 
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
   """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sync', name, project)

class ContinuousSyncRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a continuous Sync recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'csync', name, project)


class SortRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Sort recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for sort

class SortRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sort recipe
 
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
   """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sort', name, project)

class PivotRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Pivot recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for sort

class PivotRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Pivot recipe
 
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
   """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'pivot', name, project)


class TopNRecipeSettings(DSSRecipeSettings):
    """
    Settings of a TopN recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for topn

class TopNRecipeCreator(DSSRecipeCreator):
    """
    Create a TopN recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'topn', name, project)


class DistinctRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Distinct recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for distinct

class DistinctRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Distinct recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'distinct', name, project)


class PrepareRecipeSettings(DSSRecipeSettings):
    """
    Settings of a Prepare recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass

    @property
    def raw_steps(self):
        """
        Get the list of the steps of this prepare recipe.

        This method returns a reference to the list of steps, not a copy. Modifying the list
        then calling :meth:`DSSRecipeSettings.save()` commits the changes.

        :return: list of steps, each step as a dict. The precise settings for each step are not documented, but
                 each dict has at least fields:

                    * **metaType** : one of PROCESSOR or GROUP. If GROUP, there there is a field **steps** with a sub-list of steps.
                    * **type** : type of the step, for example FillEmptyWithValue or ColumnRenamer (there are many types of steps)
                    * **params** : dict of the step's own parameters. Each step type has its own parameters.
                    * **disabled** : whether the step is disabled
                    * **name** : label of the step
                    * **comment** : comment on the step
                    * **alwaysShowComment**, **mainColor** and **secondaryColor** : UI settings

        :rtype: list[dict]
        """
        return self.obj_payload["steps"]

    def add_processor_step(self, type, params):
        """
        Add a step in the script.

        :param string type: type of the step, for example FillEmptyWithValue or ColumnRenamer (there are many types of steps)
        :param dict params: dict of the step's own parameters. Each step type has its own parameters.
        """
        step = {
            "metaType": "PROCESSOR",
            "type": type,
            "params": params
        }
        self.raw_steps.append(step)


class PrepareRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Prepare recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'shaker', name, project)


class JoinRecipeSettings(DSSRecipeSettings):
    """
    Settings of a join recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`

    In order to enable self-joins, join recipes are based on a concept of "virtual inputs".
    Every join, computed pre-join column, pre-join filter, ... is based on one virtual input, and
    each virtual input references an input of the recipe, by index

    For example, if a recipe has inputs A and B and declares two joins:

        - A->B
        - A->A (based on a computed column)

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
        Get the list of virtual inputs.

        This method returns a reference to the list of inputs, not a copy. Modifying the list
        then calling :meth:`DSSRecipeSettings.save()` commits the changes.

        :return: a list of virtual inputs, each one a dict of 

                    * **index** : index of the dataset of this virtual input in the recipe's list of inputs
                    * **preFilter** : filter applied to the input, as a dict of:

                        * **distinct** : whether the records in the input should be deduplicated
                        * **enabled** : whether filtering is enabled
                        * **uiData** : settings of the filter, if **enabled** is True, as a dict of:

                            * **mode** : type of filter. Possible values: CUSTOM, SQL, '&&' (boolean AND of conditions) and '||' (boolean OR of conditions)
                            * **conditions** : if mode is '&&' or '||', then a list of the actual filter conditions, each one a dict

                        * **expression** : if **uiData.mode** is CUSTOM, a formula in DSS `formula language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . If **uiData.mode** is SQL, a SQL expression.

                    * **computedColumns** : list of computed columns added to the input, each one a dict of:

                        * **mode** : type of expression used to define the computations. One of GREL or SQL.
                        * **name** : name of the column generated
                        * **type** : name of a DSS type for the computed column
                        * **expr** : if **mode** is CUSTOM, a formula in DSS `formula language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . If **mode** is SQL, a SQL expression.

                    * **alias** : optional alias to use instead of the name of the dataset pointed by this virtual input
                    * **autoSelectColumns** : whether to select all columns of the input 
                    * **prefix** : optional prefix to add to all columns of this input in the output schema

        :rtype: list[dict]
        """
        return self.obj_payload["virtualInputs"]

    @property
    def raw_joins(self):
        """
        Get raw list of joins.

        This method returns a reference to the list of joins, not a copy. Modifying the list
        then calling :meth:`DSSRecipeSettings.save()` commits the changes.

        :return: list of the join definitions, each as a dict of:

                    * **table1** : index of the virtual input used as left-side in this join
                    * **table2** : index of the virtual input used as right-side in this join
                    * **type** : type of join. Possible values: INNER, LEFT, RIGHT, FULL (full outer), CROSS, ADVANCED
                    * **outerJoinOnTheLeft** : used in ADVANCED mode only, whether to keep unmatched rows in left dataset or not
                    * **rightLimit** : optional limiting of the number of lines that can match each line of the left-side (after taking into account all conditions), as a dict
                    * **conditionsMode** : how the join conditions are assembled. Possible values: AND (match all conditions), OR (match at least one condition), NATURAL (for natural joins), CUSTOM
                    * **customSQLCondition** : when **conditionsMode** is CUSTOM, the SQL expression of the join conditions
                    * **on** : for **conditionsMode** valued AND or OR, a list of join conditions, each one a dict of:

                        * **column1** : name of the column on the left-side
                        * **column2** : name of the column on the right-side
                        * **type** : type of the condition. Possible values are EQ,  LTE, LT, GTE, GT, NE, WITHIN_RANGE, K_NEAREST, K_NEAREST_INFERIOR, CONTAINS, STARTS_WITH
                        * **caseInsensitive** : for conditions on strings, whether the equality is case-sensitive
                        * **normalizeText** : for conditions on strings, whether to lowercase and strip accents on both sides
                        * **maxDistance** : for K_NEAREST, K_NEAREST_INFERIOR condition, the maximum allowed distance for the nearest element
                        * **maxMatches** : for K_NEAREST, K_NEAREST_INFERIOR, the maximum number of matches (use 0 for unlimited)
                        * **strict** : whether the limit of **maxMatches** is strict. If not, matches at the same distance are taken, even if this means going over **maxMatches**
                        * **dateDiffUnit** : for comparison on date columns, rounding applied before comparing. Possible values are YEAR, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND.

        :rtype: list[dict]
        """
        return self.obj_payload["joins"]

    def add_virtual_input(self, input_dataset_index):
        """
        Add a virtual input pointing to the specified input dataset of the recipe.

        :param int input_dataset_index: index of the dataset in the list of input_dataset_index 
        """
        self.raw_virtual_inputs.append({"index": input_dataset_index})

    def add_pre_join_computed_column(self, virtual_input_index, computed_column):
        """
        Add a computed column to a virtual input.

        You can use :meth:`dataikuapi.dss.utils.DSSComputedColumn.formula()` to build the computed_column object.

        :param int input_dataset_index: index of the dataset in the list of input_dataset_index 
        :param dict computed_column: a computed column definition, as a dict of:

                        * **mode** : type of expression used to define the computations. One of GREL or SQL.
                        * **name** : name of the column generated
                        * **type** : name of a DSS type for the computed column
                        * **expr** : if **mode** is CUSTOM, a formula in DSS `formula language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . If **mode** is SQL, a SQL expression.
        """
        self.raw_virtual_inputs[virtual_input_index]["computedColumns"].append(computed_column)

    def add_join(self, join_type="LEFT", input1=0, input2=1):
        """
        Add a join between two virtual inputs. 

        The join is initialized with no condition.

        Use :meth:`add_condition_to_join()` on the return value to add a join condition (for example column equality)
        to the join.

        :return: the newly added join as a dict (see :meth:`raw_joins()`)
        :rtype: dict
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

    @staticmethod
    def add_condition_to_join(self, join, type="EQ", column1=None, column2=None):
        """
        Add a condition to a join.

        :param dict join: definition of a join
        :param string type: type of join condition. Possible values are EQ,  LTE, LT, GTE, GT, NE, WITHIN_RANGE, K_NEAREST, 
                            K_NEAREST_INFERIOR, CONTAINS, STARTS_WITH
        :param string column1: name of left-side column
        :param string column2: name of right-side column
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
        Add a post-join computed column.

        Use :class:`dataikuapi.dss.utils.DSSComputedColumn` to build the computed_column object.

        .. note:: 

            The columns accessible to the expression of the computed column are those selected in the different
            joins, in their "output" form. For example if a virtual inputs 0 and 1 are joined, and column "bar"
            of the first input is selected with a prefix of "foo", then the computed column can use "foobar"
            but not "bar".

        :param dict computed_column: a computed column definition, as a dict of:

                        * **mode** : type of expression used to define the computations. One of GREL or SQL.
                        * **name** : name of the column generated
                        * **type** : name of a DSS type for the computed column
                        * **expr** : if **mode** is CUSTOM, a formula in DSS `formula language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . If **mode** is SQL, a SQL expression.
        """
        self.obj_payload["computedColumns"].append(computed_column)

    def set_post_filter(self, postfilter):
        """
        Add a post filter on the join.

        Use the methods on :class:`dataikuapi.dss.utils.DSSFilter` to build filter definition.

        :param dict postfilter: definition of a filter, as a dict of:

                    * **distinct** : whether the records in the output should be deduplicated
                    * **enabled** : whether filtering is enabled
                    * **uiData** : settings of the filter, if **enabled** is True, as a dict of:

                        * **mode** : type of filter. Possible values: CUSTOM, SQL, '&&' (boolean AND of conditions) and '||' (boolean OR of conditions)
                        * **conditions** : if mode is '&&' or '||', then a list of the actual filter conditions, each one a dict

                    * **expression** : if **uiData.mode** is CUSTOM, a formula in DSS `formula language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . If **uiData.mode** is SQL, a SQL expression.
        """
        self.obj_payload["postFilter"] = postfilter

    def set_unmatched_output(self, ref, side='right', append_mode=False):
        """
        Adds an unmatched join output

        :param str ref: name of the dataset
        :param str side: side of the unmatched output, 'right' or 'left'.
        :param bool append_mode: whether the recipe should append or overwrite the output when running
        """
        if side not in ['right', 'left']:
            raise ValueError("Unknown side : " + side)
        if len(self.obj_payload["joins"]) != 1:
            raise DataikuException("Unmatched output can only be set on recipe that have a single join")
        join_type = self.obj_payload["joins"][0]["type"]
        if join_type not in ["RIGHT", "LEFT", "INNER"] or (side == 'left' and join_type == "LEFT") or (side == 'right' and join_type == "RIGHT"):
            raise DataikuException("No unmatched rows for " + side + " side with join type " + join_type)
        self._get_or_create_output_role("unmatchedRight" if side == 'right' else "unmatchedLeft")["items"] = [{"ref": ref, "appendMode": append_mode}]

class JoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Join recipe.

    The recipe is created with default joins guessed by matching column names in the
    inputs.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'join', name, project)

class FuzzyJoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a FuzzyJoin recipe

    The recipe is created with default joins guessed by matching column names in the
    inputs.
 
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
   """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'fuzzyjoin', name, project)

class GeoJoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a GeoJoin recipe

    The recipe is created with default joins guessed by matching column names in the
    inputs.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'geojoin', name, project)

class StackRecipeSettings(DSSRecipeSettings):
    """
    Settings of a stack recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for stack

class StackRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    """
    Create a Stack recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'vstack', name, project)


class SamplingRecipeSettings(DSSRecipeSettings):
    """
    Settings of a sampling recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for sampling

class SamplingRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Sample/Filter recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sampling', name, project)


class SplitRecipeSettings(DSSRecipeSettings):
    """
    Settings of a split recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for split

class SplitRecipeCreator(DSSRecipeCreator):
    """
    Create a Split recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, "split", name, project)

    def _finish_creation_settings(self):
        pass


class DownloadRecipeSettings(DSSRecipeSettings):
    """
    Settings of a download recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    pass # TODO: Write helpers for download

class DownloadRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a Download recipe

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'download', name, project)


#####################################################
# Per-recipe-type classes: Code recipes
#####################################################

class CodeRecipeSettings(DSSRecipeSettings):
    """
    Settings of a code recipe. 

    .. important::

        Do not instantiate directly, use :meth:`DSSRecipe.get_settings()`
    """
    def get_code(self):
        """
        Get the code of the recipe.

        :rtype: string
        """
        self._payload_to_str()
        return self._str_payload

    def set_code(self, code):
        """
        Update the code of the recipe.

        :param string code: the new code
        """
        self.set_payload(code)

    def get_code_env_settings(self):
        """
        Get the code env settings for this recipe.

        :return: settings to select the code env used by the recipe, as a dict of:

                    * **envMode** : one of USE_BUILTIN_MODE, INHERIT (inherit from project settings and/or instance settings), EXPLICIT_ENV
                    * **envName** : if **envMode** is EXPLICIT_ENV, the name of the code env to use

        :rtype: dict
        """
        rp = self.get_recipe_params()
        if not "envSelection" in rp:
            raise ValueError("This recipe kind does not seem to take a code env selection")
        return rp["envSelection"]

    def set_code_env(self, code_env=None, inherit=False, use_builtin=False):
        """
        Set which code env this recipe uses.

        Exactly one of `code_env`, `inherit` or `use_builtin` must be passed.

        :param string code_env: name of a code env
        :param boolean inherit: if True, use the project's default code env
        :param boolean use_builtin: if true, use the builtin code env
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
    """
    Create a recipe running a script.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()`
     """
    def __init__(self, name, type, project):
        DSSRecipeCreator.__init__(self, type, name, project)
        self.script = None

    def with_script(self, script):
        """
        Set the code of the recipe-to-be-created.

        :param string script: code of the recipe
        """
        self.script = script
        return self

    def with_new_output_dataset(self, name, connection,
                                type=None, format=None,
                                copy_partitioning_from="FIRST_INPUT",
                                append=False, overwrite=False,
                                **kwargs):
        """
        Create a new managed dataset as output to the recipe-to-be-created. 

        The dataset is created immediately.

        :param string name: name of the dataset
        :param string connection: name of the connection to create the dataset on
        :param string type: sub-type of dataset or managed folder, for connections where the type 
                            could be ambiguous. Typically applies to SSH connections, where sub-types
                            can be SCP or SFTP
        :param string format: name of a format preset relevant for the dataset type. Possible values are: CSV_ESCAPING_NOGZIP_FORHIVE,
                              CSV_UNIX_GZIP, CSV_EXCEL_GZIP, CSV_EXCEL_GZIP_BIGQUERY, CSV_NOQUOTING_NOGZIP_FORPIG, PARQUET_HIVE,
                              AVRO, ORC
        :param string partitioning_option_id: to copy the partitioning schema of an existing dataset 'foo', pass a
                                              value of 'copy:dataset:foo'. If unset, then the output will be non-partitioned
        :param boolean append: whether the recipe should append or overwrite the output when running
                               (note: not available for all dataset types)
        :param boolean overwrite: If the dataset being created already exists, overwrite it (and delete data)
        """
        for k in kwargs:  # for backward compat
            if k == "format_option_id":
                format = kwargs.get("format_option_id")
            elif k == "typeOptionId":
                type = kwargs.get("typeOptionId")
            elif k == "type_option_id":
                type = kwargs.get("type_option_id")
            else:
                raise Exception("Unknown argument '{}'".format(k))

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

    def with_new_output_streaming_endpoint(self, name, connection, format=None, overwrite=False, **kwargs):
        """
        Create a new managed streaming endpoint as output to the recipe-to-be-created. 

        The streaming endpoint is created immediately.

        :param str name: name of the streaming endpoint to create
        :param str connection: name of the connection to create the streaming endpoint on
        :param str format: name of a format preset relevant for the streaming endpoint type. Possible values are: 
                           json, avro, single (kafka endpoints) or json, string (SQS endpoints). If None, uses the 
                           default
        :param overwrite: If the streaming endpoint being created already exists, overwrite it
        """
        for k in kwargs:  # for backward compat
            if k == "format_option_id":
                format = kwargs.get("format_option_id")
            else:
                raise Exception("Unknown argument '{}'".format(k))     

        ch = self.project.new_managed_streaming_endpoint(name)
        ch.with_store_into(connection, format_option_id=format)
        ch.create(overwrite=overwrite)

        self.with_output(name, append=False)
        return self

    def _finish_creation_settings(self):
        super(CodeRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['script'] = self.script

class PythonRecipeCreator(CodeRecipeCreator):
    """
    Create a Python recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.

    A Python recipe can be defined either by its complete code, like a normal Python recipe, or
    by a function signature.
    """

    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, "python", name, project)

    _DEFAULT_RECIPE_CODE_TMPL = """
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
        Define this recipe as being a functional recipe calling a function.

        With the default template, the function must take as arguments:

             * A list of dataframes corresponding to the dataframes of the input datasets. If there is
               only one input, then a single dataframe
             * Optional named arguments corresponding to arguments passed to the creator as kwargs

        The function should then return a list of dataframes, one per recipe output. If there is a single
        output, it is possible to return a single dataframe rather than a list.

        :param string module_name: name of the module where the function is defined
        :param string function_name: name of the function
        :param kwargs function_args: additional parameters to the function.
        :param string custom_template: template to use to create the code of the recipe. The template
                                       is formatted with '{fname}' (function name), '{module_name}' (module
                                       name) and '{params_json}' (JSON representation of **function_args**)
        """
        script_tmpl = PythonRecipeCreator._DEFAULT_RECIPE_CODE_TMPL if custom_template is None else custom_template

        if function_args is None:
            function_args = {}

        code = script_tmpl.format(module_name=module_name, fname=function_name, params_json = json.dumps(function_args))
        self.with_script(code)

        return self

    def with_function(self, fn, custom_template=None, **function_args):
        """
        Define this recipe as being a functional recipe calling a function.

        With the default template, the function must take as arguments:

             * A list of dataframes corresponding to the dataframes of the input datasets. If there is
               only one input, then a single dataframe
             * Optional named arguments corresponding to arguments passed to the creator as kwargs

        The function should then return a list of dataframes, one per recipe output. If there is a single
        output, it is possible to return a single dataframe rather than a list.

        :param string fn: function to call
        :param kwargs function_args: additional parameters to the function.
        :param string custom_template: template to use to create the code of the recipe. The template
                                       is formatted with '{fname}' (function name), '{module_name}' (module
                                       name) and '{params_json}' (JSON representation of **function_args**)
        """
        import inspect
        #TODO: add in documentation that relative imports wont work
        module_name = inspect.getmodule(fn).__name__
        fname = fn.__name__
        return self.with_function_name(module_name, fname, custom_template, **function_args)

class SQLQueryRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a SQL query recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.
    """
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sql_query', name, project)


#####################################################
# Per-recipe-type classes: ML recipes
#####################################################

class PredictionScoringRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a new Prediction scoring recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.

    Usage example:
    
    .. code-block:: python

        # Create a new prediction scoring recipe outputing to a new dataset

        project = client.get_project("MYPROJECT")
        builder = project.new_recipe("prediction_scoring", "my_scoring_recipe")
        builder.with_input_model("saved_model_id")
        builder.with_input("dataset_to_score")
        builder.with_new_output("my_output_dataset", "myconnection")

        # Or for a filesystem output connection
        # builder.with_new_output("my_output_dataset, "filesystem_managed", format="CSV_EXCEL_GZIP")

        new_recipe = builder.build()
    """

    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'prediction_scoring', name, project)

    def with_input_model(self, model_id):
        """
        Set the input model.

        :param string model_id: identifier of a saved model
        """
        return self._with_input(model_id, self.project.project_key, "model")


class EvaluationRecipeCreator(DSSRecipeCreator):
    """
    Create a new Evaluate recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.

    Usage example:

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
        """
        Set the input model.

        :param string model_id: identifier of a saved model
        """
        return self._with_input(model_id, self.project.project_key, "model")

    def with_output(self, output_id):
        """
        Set the output dataset containing the scored input.

        :param string output_id: name of the dataset, or identifier of the managed folder
                                 or identifier of the saved model
        """
        return self._with_output(output_id, role="main")

    def with_output_metrics(self, name):
        """
        Set the output dataset containing the metrics.

        :param string name: name of an existing dataset
        """
        return self._with_output(name, role="metrics")

    def with_output_evaluation_store(self, mes_id):
        """
        Set the output model evaluation store.

        :param string mes_id: identifier of a model evaluation store
        """
        return self._with_output(mes_id, role="evaluationStore")


class StandaloneEvaluationRecipeCreator(DSSRecipeCreator):
    """
    Create a new Standalone Evaluate recipe.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.

    Usage example:

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
        """
        Set the output model evaluation store.

        :param string mes_id: identifier of a model evaluation store
        """
        return self._with_output(mes_id, role="main")

    def with_reference_dataset(self, dataset_name):
        """
        Set the dataset to use as a reference in data drift computation.

        :param string dataset_name: name of a dataset
        """
        return self._with_input(dataset_name, self.project.project_key, role="reference")


class ClusteringScoringRecipeCreator(SingleOutputRecipeCreator):
    """
    Create a new Clustering scoring recipe,.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_recipe()` instead.

    Usage example:

    .. code-block:: python

        # Create a new prediction scoring recipe outputing to a new dataset

        project = client.get_project("MYPROJECT")
        builder = project.new_recipe("clustering_scoring", "my_scoring_recipe")
        builder.with_input_model("saved_model_id")
        builder.with_input("dataset_to_score")
        builder.with_new_output("my_output_dataset", "myconnection")

        # Or for a filesystem output connection
        # builder.with_new_output("my_output_dataset, "filesystem_managed", format="CSV_EXCEL_GZIP")

        new_recipe = builder.build()

    """

    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'clustering_scoring', name, project)

    def with_input_model(self, model_id):
        """
        Set the input model.

        :param string model_id: identifier of a saved model
        """
        return self._with_input(model_id, self.project.project_key, "model")
