from .labeling_task import DSSLabelingTask
from ..utils import _write_response_content_to_file
from .utils import AnyLoc
from .dataset import DSSDataset
from .managedfolder import DSSManagedFolder
from .savedmodel import DSSSavedModel
from .modelevaluationstore import DSSModelEvaluationStore
from .recipe import DSSRecipe, DSSRecipeDefinitionAndPayload
from .knowledgebank import DSSKnowledgeBank
from .future import DSSFuture
from .streaming_endpoint import DSSStreamingEndpoint
import logging, json
import warnings


class DSSProjectFlow(object):
    def __init__(self, client, project):
        self.client = client
        self.project = project

    def get_graph(self):
        """
        Get the flow graph.

        :return: A handle to use the flow graph
        :rtype: :class:`.DSSProjectFlowGraph`
        """
        data = self.client._perform_json("GET", "/projects/%s/flow/graph/" % (self.project.project_key))
        return DSSProjectFlowGraph(self, data)

    def create_zone(self, name, color="#2ab1ac"):
        """
        Creates a new flow zone.

        :param str name: new flow zone name
        :param str color: new flow zone color, in hexadecimal format #RRGGBB (defaults to **#2ab1ac**)

        :returns: the newly created zone
        :rtype: :class:`DSSFlowZone`
        """
        data = self.client._perform_json("POST", "/projects/%s/flow/zones" % (self.project.project_key), body={
            "name": name,
            "color": color
        })
        return DSSFlowZone(self, data)

    def get_zone(self, id):
        """
        Gets a single Flow zone by id.

        :param str id: flow zone id

        :returns: A flow zone
        :rtype: :class:`DSSFlowZone`
        """
        data = self.client._perform_json("GET", "/projects/%s/flow/zones/%s" % (self.project.project_key, id))
        return DSSFlowZone(self, data)

    def get_default_zone(self):
        """
        Returns the default zone of the Flow.

        :returns: A flow zone
        :rtype: :class:`DSSFlowZone`
        """
        return self.get_zone("default")

    def list_zones(self):
        """
        Lists all zones in the Flow.

        :returns: A list of flow zones
        :rtype: list of :class:`DSSFlowZone`
        """
        data = self.client._perform_json("GET", "/projects/%s/flow/zones" % (self.project.project_key))
        return [DSSFlowZone(self, z) for z in data]

    def get_zone_of_object(self, obj):
        """
        Finds the zone to which this object belongs.

        If the object is not found in any specific zone, it belongs to the default zone, and the default
        zone is returned.

        :param obj: An object to search
        :type obj: :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSRecipe`
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`

        :returns: The flow zone containing the object
        :rtype: :class:`DSSFlowZone`
        """
        sr = self._to_smart_ref(obj)

        for zone in self.list_zones():
            for item in zone._raw["items"]:
                if json.dumps(sr) == json.dumps(item):
                    return zone
        return self.get_default_zone()

    def replace_input_computable(self, current_ref, new_ref, type="DATASET"):
        """
        This method replaces all references to a "computable" (Dataset, Managed Folder or Saved Model)
        as input of recipes in the whole Flow by a reference to another computable.

        No specific checks are performed. It is your responsibility to ensure that the schema
        of the new dataset will be compatible with the previous one (in the case of datasets).

        If `new_ref` references an object in a foreign project, this method will automatically
        ensure that `new_ref` is exposed to the current project.

        :param str current_ref: Either a "simple" object id (dataset name or model/folder/model evaluation store/streaming endpoint id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id"
        :param str new_ref: Either a "simple" object id (dataset name or model/folder/model evaluation store/streaming endpoint id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id"
        :param str type: The type of object being replaced (DATASET, SAVED_MODEL, MANAGED_FOLDER, MODEL_EVALUATION_STORE, STREAMING_ENDPOINT) (defaults to **DATASET**)
        """

        new_loc = AnyLoc.from_ref(self.project.project_key, new_ref)

        if new_loc.project_key != self.project.project_key:
            logging.info("New ref is in project %s, exposing it to project %s" % (new_loc.project_key, self.project.project_key))
            new_ref_src_project = self.client.get_project(new_loc.project_key)
            settings = new_ref_src_project.get_settings()
            settings.add_exposed_object(type, new_loc.object_id, self.project.project_key)
            settings.save()

        for recipe in self.project.list_recipes():
            recipe_handle = self.project.get_recipe(recipe["name"])
            fake_rap = DSSRecipeDefinitionAndPayload(recipe_handle, {"recipe": recipe})
            if fake_rap.has_input(current_ref):
                logging.info("Recipe %s has %s as input, performing the replacement by %s" % \
                             (recipe["name"], current_ref, new_ref))
                recipe_obj = self.project.get_recipe(recipe["name"])
                dap = recipe_obj.get_definition_and_payload()
                dap.replace_input(current_ref, new_ref)
                recipe_obj.set_definition_and_payload(dap)

    def generate_documentation(self, folder_id=None, path=None):
        """
        Start the flow document generation from a template docx file in a managed folder,
        or from the default template if no folder id and path are specified.

        :param str folder_id: the id of the managed folder (defaults to **None**)
        :param str path: the path to the file from the root of the folder (defaults to **None**)

        :return: The flow document generation future
        :rtype: :class:`.DSSFuture`
        """
        if bool(folder_id) != bool(path):
            raise ValueError("Both folder id and path arguments are required to use a template from folder. " +
                             "Use without argument to generate the flow documentation using the default template")

        template_mode_url = "" if folder_id is None and path is None else "-with-template-in-folder"

        f = self.client._perform_json("POST", "/projects/%s/flow/documentation/generate%s" % (self.project.project_key, template_mode_url),
                                      params={"folderId": folder_id, "path": path})
        return DSSFuture(self.client, f["jobId"])

    def generate_documentation_from_custom_template(self, fp):
        """
        Start the flow document generation from a docx template (as a file object).

        :param object fp: A file-like object pointing to a template docx file

        :return: The flow document generation future
        :rtype: :class:`.DSSFuture`
        """
        files = {'file': fp}
        f = self.client._perform_json("POST", "/projects/%s/flow/documentation/generate-with-template" % self.project.project_key, files=files)
        return DSSFuture(self.client, f["jobId"])

    def download_documentation_stream(self, export_id):
        """
        Download a flow documentation, as a binary stream.

        .. warning ::
            You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param str export_id: the id of the generated flow documentation returned as the result of the future

        :returns: the generated flow documentation file as a stream
        :rtype: :class:`requests.Response`
        """
        return self.client._perform_raw("GET", "/projects/%s/flow/documentation/generated/%s" % (self.project.project_key, export_id))

    def download_documentation_to_file(self, export_id, path):
        """
        Download a flow documentation into the given output file.

        :param str export_id: the id of the generated flow documentation returned as the result of the future
        :param str path: the path where to download the flow documentation
        """
        stream = self.download_documentation_stream(export_id)
        _write_response_content_to_file(stream, path)

    ########################################################
    # Flow tools
    ########################################################

    def start_tool(self, type, data={}):
        """
        .. caution::

            Deprecated, this method will no longer be available for views (starting with DSS 13.4):
            TAGS, CUSTOM_FIELDS, CONNECTIONS, COUNT_OF_RECORDS, FILESIZE, FILEFORMATS, RECIPES_ENGINES, RECIPES_CODE_ENVS, IMPALA_WRITE_MODE, HIVE_MODE, SPARK_CONFIG, SPARK_PIPELINES, SQL_PIPELINES, PARTITIONING, PARTITIONS, SCENARIOS, CREATION, LAST_MODIFICATION, LAST_BUILD, RECENT_ACTIVITY, WATCH.
            It will be maintained for flow actions.

        Start a tool in the flow.

        :param str type: one of {COPY, CHECK_CONSISTENCY, PROPAGATE_SCHEMA}
        :param dict data: initial data for the tool (defaults to **{}**)

        :returns: A handle to interact with the newly-created tool or view
        :rtype: :class:`.DSSFlowTool`
        """
        if type in ['TAGS', 'CUSTOM_FIELDS', 'CONNECTIONS', 'COUNT_OF_RECORDS', 'FILESIZE', 'FILEFORMATS', 'RECIPES_ENGINES', 'RECIPES_CODE_ENVS', 'IMPALA_WRITE_MODE', 'HIVE_MODE', 'SPARK_CONFIG', 'SPARK_PIPELINES', 'SQL_PIPELINES', 'PARTITIONING', 'PARTITIONS', 'SCENARIOS', 'CREATION', 'LAST_MODIFICATION', 'LAST_BUILD', 'RECENT_ACTIVITY', 'WATCH']:
            warnings.warn("This method is deprecated for views and will be removed in a future version (starting with DSS 13.4).", DeprecationWarning)
        tool_id = self.client._perform_text("POST", "/projects/%s/flow/tools/" % self.project.project_key, params={'type': type}, body=data)
        return DSSFlowTool(self.client, self.project.project_key, tool_id)

    def new_schema_propagation(self, dataset_name):
        """
        Start an automatic schema propagation from a dataset.

        :param str dataset_name: name of a dataset to start propagating from

        :returns: A handle to set options and start the propagation
        :rtype: :class:`.DSSSchemaPropagationRunBuilder`
        """
        return DSSSchemaPropagationRunBuilder(self.project, self.client, dataset_name)

    def _to_smart_ref(self, obj):
        if isinstance(obj, DSSDataset):
            ot = "DATASET"
        elif isinstance(obj, DSSManagedFolder):
            ot = "MANAGED_FOLDER"
        elif isinstance(obj, DSSSavedModel):
            ot = "SAVED_MODEL"
        elif isinstance(obj, DSSModelEvaluationStore):
            ot = "MODEL_EVALUATION_STORE"
        elif isinstance(obj, DSSRecipe):
            ot = "RECIPE"
        elif isinstance(obj, DSSStreamingEndpoint):
            ot = "STREAMING_ENDPOINT"
        elif isinstance(obj, DSSLabelingTask):
            ot = "LABELING_TASK"
        elif isinstance(obj, DSSKnowledgeBank):
            ot = "RETRIEVABLE_KNOWLEDGE"
        else:
            raise ValueError("Cannot transform to DSS object ref: %s" % obj)

        if obj.project_key == self.project.project_key:
            return {
                "objectId": obj.id,
                "objectType": ot
            }
        else:
            return {
                "projectKey": obj.project_key,
                "objectId": obj.id,
                "objectType": ot
            }


class DSSSchemaPropagationRunBuilder(object):
    """
    .. important ::
        Do not create this directly, use :meth:`DSSProjectFlow.new_schema_propagation`.
    """
    def __init__(self, project, client, dataset_name):
        self.project = project
        self.client = client
        self.dataset_name = dataset_name
        self.settings = {
            'recipeUpdateOptions': {
                "byType": {},
                "byName": {}
            },
            'defaultPartitionValuesByDimension': {},
            'partitionsByComputable': {},
            'excludedRecipes': [],
            'markAsOkRecipes': [],
            'autoRebuild': True
        }

    def set_auto_rebuild(self, auto_rebuild):
        """
        Sets whether to automatically rebuild datasets if needed while propagating.

        :param bool auto_rebuild: whether to automatically rebuild datasets if needed (defaults to **True**)
        """
        self.settings["autoRebuild"] = auto_rebuild

    def set_default_partitioning_value(self, dimension, value):
        """
        In the case of partitioned flows, sets the default partition value to use when rebuilding, for a specific dimension name.

        :param str dimension: a partitioning dimension name
        :param str value: a partitioning dimension value
        """
        self.settings["defaultPartitionValuesByDimension"][dimension] = value

    def set_partition_for_computable(self, full_id, partition):
        """
        In the case of partitioned flows, sets the partition id to use when building a particular computable.
        Overrides the default partitioning value per dimension.

        :param str full_id: Full name of the computable, in the form PROJECTKEY.id
        :param str partition: a full partition id (all dimensions)
        """
        self.settings["partitionsByComputable"][full_id] = partition

    def stop_at(self, recipe_name):
        """
        Sets the given recipe as a schema propagation stop mark.

        :param str recipe_name: the name of the recipe
        """
        self.settings["excludedRecipes"].append(recipe_name)

    def mark_recipe_as_ok(self, name):
        """
        Marks a recipe as always considered as OK during propagation.

        :param str name: recipe to mark as ok
        """
        self.settings["markAsOkRecipes"].append(name)

    def set_grouping_update_options(self, recipe=None, remove_missing_aggregates=True, remove_missing_keys=True,
                                    new_aggregates={}):
        """
        Sets update options for grouping recipes.

        :param str recipe: if None, applies to all grouping recipes. Else, applies only to this name (defaults to **None**)
        :param bool remove_missing_aggregates: whether to remove missing aggregates (defaults to **True**)
        :param bool remove_missing_keys: whether to remove missing keys (defaults to **True**)
        :param dict new_aggregates: new aggregates (defaults to **{}**)
        """
        data = {
            "removeMissingAggregates": remove_missing_aggregates,
            "removeMissingKeys": remove_missing_keys,
            "newAggregates": new_aggregates
        }
        if recipe is None:
            self.settings["recipeUpdateOptions"]["byType"]["grouping"] = data
        else:
            self.settings["recipeUpdateOptions"]["byName"][recipe] = data

    def set_window_update_options(self, recipe=None, remove_missing_aggregates=True, remove_missing_in_window=True,
                                  new_aggregates={}):
        """
        Sets update options for window recipes.

        :param str recipe: if None, applies to all window recipes. Else, applies only to this name (defaults to **None**)
        :param bool remove_missing_aggregates: whether to remove missing aggregates (defaults to **True**)
        :param bool remove_missing_in_window: whether to remove missing keys in windows (defaults to **True**)
        :param dict new_aggregates: new aggregates (defaults to **{}**)
        """
        data = {
            "removeMissingAggregates": remove_missing_aggregates,
            "removeMissingInWindow": remove_missing_in_window,
            "newAggregates": new_aggregates
        }
        if recipe is None:
            self.settings["recipeUpdateOptions"]["byType"]["window"] = data
        else:
            self.settings["recipeUpdateOptions"]["byName"][recipe] = data

    def set_join_update_options(self, recipe=None, remove_missing_join_conditions=True, remove_missing_join_values=True,
                                new_selected_columns={}):
        """
        Sets update options for join recipes.

        :param str recipe: if None, applies to all join recipes. Else, applies only to this name (defaults to **None**)
        :param bool remove_missing_join_conditions: whether to remove missing join conditions (defaults to **True**)
        :param bool remove_missing_join_values: whether to remove missing join values (defaults to **True**)
        :param dict new_selected_columns: new selected columns (defaults to **{}**)
        """
        data = {
            "removeMissingJoinConditions": remove_missing_join_conditions,
            "removeMissingJoinValues": remove_missing_join_values,
            "newSelectedColumns": new_selected_columns
        }
        if recipe is None:
            self.settings["recipeUpdateOptions"]["byType"]["join"] = data
        else:
            self.settings["recipeUpdateOptions"]["byName"][recipe] = data

    def start(self):
        """
        Starts the actual propagation. Returns a future to wait for completion.

        :returns: A future representing the schema propagation job
        :rtype: :class:`.DSSFuture`
        """
        loc = AnyLoc.from_ref(self.project.project_key, self.dataset_name)
        future_resp = self.client._perform_json("POST", "/projects/%s/flow/tools/propagate-schema/" % self.project.project_key,
                                                body={ "options": self.settings, "sources": [{"projectKey": loc.project_key, "id": loc.object_id}]})
        return DSSFuture.from_resp(self.client, future_resp)


class DSSFlowZone(object):
    """
    A zone in the Flow.

    .. important ::
        Do not create this object manually, use :meth:`DSSProjectFlow.get_zone` or :meth:`DSSProjectFlow.list_zones`
    """

    def __init__(self, flow, data):
        self.flow = flow
        self.client = flow.client
        self._raw = data

    @property
    def id(self):
        return self._raw["id"]

    @property
    def name(self):
        return self._raw["name"]

    @property
    def color(self):
        return self._raw["color"]

    def __repr__(self):
        return "<dataikuapi.dss.flow.DSSFlowZone (id=%s, name=%s)>" % (self.id, self.name)

    def get_settings(self):
        """Gets the settings of this zone in order to modify them.

        :returns: The settings of the flow zone
        :rtype: :class:`DSSFlowZoneSettings`
        """
        return DSSFlowZoneSettings(self)

    def _to_native_obj(self, zone_item):
        if not "projectKey" in zone_item or zone_item["projectKey"] == self.flow.project.project_key:
            p = self.flow.project
        else:
            p = self.client.get_project(zone_item["projectKey"])

        if zone_item["objectType"] == "DATASET":
            return p.get_dataset(zone_item["objectId"])
        elif zone_item["objectType"] == "MANAGED_FOLDER":
            return p.get_managed_folder(zone_item["objectId"])
        elif zone_item["objectType"] == "SAVED_MODEL":
            return p.get_saved_model(zone_item["objectId"])
        elif zone_item["objectType"] == "RECIPE":
            return p.get_recipe(zone_item["objectId"])
        elif zone_item["objectType"] == "STREAMING_ENDPOINT":
            return p.get_streaming_endpoint(zone_item["objectId"])
        elif zone_item["objectType"] == "LABELING_TASK":
            return p.get_labeling_task(zone_item["objectId"])
        elif zone_item["objectType"] == "MODEL_EVALUATION_STORE":
            return p.get_model_evaluation_store(zone_item["objectId"])
        elif zone_item["objectType"] == "RETRIEVABLE_KNOWLEDGE":
            return p.get_knowledge_bank(zone_item["objectId"])
        else:
            raise ValueError("Cannot transform to DSS object: %s" % zone_item)

    def add_item(self, obj):
        """
        Adds an item to this zone.

        The item will automatically be moved from its existing zone. Additional items may be moved to this zone
        as a result of the operation (notably the recipe generating `obj`).

        :param obj: object to add to the zone
        :type obj: :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSRecipe`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        self._raw = self.client._perform_json("POST", "/projects/%s/flow/zones/%s/items" % (self.flow.project.project_key, self.id),
                                              body=self.flow._to_smart_ref(obj))

    def add_items(self, items):
        """
        Adds items to this zone.

        The items will automatically be moved from their existing zones. Additional items may be moved to this zone
        as a result of the operations (notably the recipe generating the `items`).

        :param items: A list of objects to add to the zone
        :type items: list of :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSRecipe`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        smart_refs = []
        for item in items:
            smart_refs.append(self.flow._to_smart_ref(item))
        self._raw = self.client._perform_json("POST", "/projects/%s/flow/zones/%s/add-items" % (self.flow.project.project_key, self.id),
                                              body=smart_refs)

    @property
    def items(self):
        """
        The list of items explicitly belonging to this zone.

        This list is read-only.
        To add an object, use :meth:`add_item`. It will remove it from its current zone, if any.
        To remove an object from a zone without placing in another specific zone, add it to the default zone: ``flow.get_zone('default').add_item(item)``

        .. note ::
            The "default" zone content is defined as all items that are not explicitly in another zone.
            It cannot directly be listed with the ``items`` property.
            To get the list of items including those in the default zone, use the :meth:`get_graph` method.


        :returns: the items in the zone
        :rtype: list of :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSRecipe`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        return [self._to_native_obj(i) for i in self._raw["items"]]

    def add_shared(self, obj):
        """
        Share an item to this zone.

        The item will not be automatically unshared from its existing zone.

        :param obj: object to share to the zone
        :type obj: :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSRecipe`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        self._raw = self.client._perform_json("POST", "/projects/%s/flow/zones/%s/shared" % (self.flow.project.project_key, self.id),
                                              body=self.flow._to_smart_ref(obj))

    def remove_shared(self, obj):
        """
        Remove a shared item from this zone.

        :param obj: object to remove from the zone
        :type obj: :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        smartRef = self.flow._to_smart_ref(obj)
        self._raw = self.client._perform_json("DELETE", "/projects/%s/flow/zones/%s/shared/%s/%s" % (
        self.flow.project.project_key, self.id, smartRef['objectType'], smartRef['objectId']))

    @property
    def shared(self):
        """
        The list of items that have been explicitly pre-shared to this zone.

        This list is read-only, to modify it, use :meth:`add_shared` and :meth:`remove_shared`

        :returns: the items shared to this zone
        :rtype: list of :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        return [self._to_native_obj(i) for i in self._raw["shared"]]

    def get_graph(self):
        """
        Get the flow graph.

        :return: A handle to use the flow graph
        :rtype: :class:`DSSProjectFlowGraph`
        """
        data = self.client._perform_json("GET", "/projects/%s/flow/zones/%s/graph" % (self.flow.project.project_key, self.id))
        return DSSProjectFlowGraph(self.flow, data)

    def delete(self):
        """
        Delete the zone, all items will be moved to the default zone.
        """
        return self.client._perform_empty("DELETE", "/projects/%s/flow/zones/%s" % (self.flow.project.project_key, self.id))


class DSSFlowZoneSettings(object):
    """
    The settings of a flow zone.

    .. important ::
        Do not create this directly, use :meth:`DSSFlowZone.get_settings`.
    """
    def __init__(self, zone):
        self._zone = zone
        self._raw = zone._raw

    def get_raw(self):
        """
        Gets the raw settings of the zone.

        .. note ::
            You cannot modify the `items` and `shared` elements through this class.
            Instead, use :meth:`DSSFlowZone.add_item` and others
        """
        return self._raw

    @property
    def name(self):
        return self._raw["name"]

    @name.setter
    def name(self, new_name):
        self._raw["name"] = new_name

    @property
    def color(self):
        return self._raw["color"]

    @color.setter
    def color(self, new_color):
        self._raw["color"] = new_color

    def save(self):
        """Saves the settings of the zone"""
        self._zone.client._perform_empty("PUT", "/projects/%s/flow/zones/%s" % (self._zone.flow.project.project_key, self._zone.id),
                                         body=self._raw)


class DSSProjectFlowGraph(object):

    def __init__(self, flow, data):
        self.flow = flow
        self.data = data
        self.nodes = data["nodes"]

    def get_source_computables(self, as_type="dict"):
        """
        :param str as_type: How to return the source computables. Possible values are "dict" and "object" (defaults to **dict**)

        :returns: The list of source computables
        :rtype: If as_type=dict, each computable is returned as a dict containing at least "ref" and "type".
                If as_type=object, each computable is returned as a :class:`.DSSDataset`,
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """

        ret = []
        for node in self.nodes.values():
            if len(node["predecessors"]) == 0 and node["type"].startswith("COMPUTABLE"):
                ret.append(node)
        return self._convert_nodes_list(ret, as_type)


    def get_source_recipes(self, as_type="dict"):
        """
        :param str as_type: How to return the source recipes. Possible values are "dict" and "object" (defaults to **dict**)

        :returns: The list of source recipes
        :rtype: If as_type=dict, each recipe is returned as a dict containing at least "ref" and "type".
                If as_type=object, each recipe is returned as a  :class:`.DSSRecipe`.
        """
        ret = []
        for node in self.nodes.values():
            if len(node["predecessors"]) == 0 and node["type"] == "RUNNABLE_RECIPE":
                ret.append(node)
        return self._convert_nodes_list(ret, as_type)

    def get_source_datasets(self):
        """
        :returns: The list of source datasets for this project
        :rtype: List of :class:`.DSSDataset`
        """
        return [self._get_object_from_graph_node(x) for x in self.get_source_computables() if x["type"] == "COMPUTABLE_DATASET"]

    def get_successor_recipes(self, node, as_type="dict"):
        """
        :param node: Either a name or a dataset object
        :type node: str or :class:`.DSSDataset`
        :param str as_type: How to return the successor recipes. Possible values are "dict" and "object" (defaults to **dict**)

        :returns: A list of recipes that are a successor of the given graph node
        :rtype: If as_type=dict, each recipe is returned as a dict containing at least "ref" and "type".
                If as_type=object, each recipe is returned as a  :class:`.DSSRecipe`.
        """
        if isinstance(node, DSSDataset):
            node = node.dataset_name

        computable = self.nodes.get(node, None)
        if computable is None:
            raise ValueError("Computable %s not found in Flow graph" % node)

        runnables = [self.nodes[x] for x in computable["successors"]]
        return self._convert_nodes_list(runnables, as_type)

    def get_successor_computables(self, node, as_type="dict"):
        """
        :param node: Either a name or a recipe object
        :type node: str or :class:`.DSSRecipe`
        :param str as_type: How to return the successor computables. Possible values are "dict" and "object" (defaults to **dict**).

        :returns: A list of computables that are a successor of a given graph node
        :rtype: If as_type=dict, each computable is returned as a dict containing at least "ref" and "type".
                If as_type=object, each computable is returned as a :class:`.DSSDataset`.
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSModelEvaluationStore` or
                :class:`.DSSStreamingEndpoint`
        """
        if isinstance(node, DSSRecipe):
            node = node.recipe_name
        runnable = self.nodes.get(node, None)
        if runnable is None:
            raise ValueError("Runnable %s not found in Flow graph" % node)

        computables = [self.nodes[x] for x in runnable["successors"]]
        return self._convert_nodes_list(computables, as_type)

    def _convert_nodes_list(self, nodes, as_type):
        actual_nodes = [node for node in nodes if node['type'] != 'RUNNABLE_IMPLICIT_RECIPE']
        if as_type == "object" or as_type == "objects":
            return [self._get_object_from_graph_node(node) for node in actual_nodes]
        else:
            return nodes

    def _get_object_from_graph_node(self, node):
        if node["type"] == "COMPUTABLE_DATASET":
            return DSSDataset(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "RUNNABLE_RECIPE":
            return DSSRecipe(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "COMPUTABLE_FOLDER":
            return DSSManagedFolder(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "COMPUTABLE_SAVED_MODEL":
            return DSSSavedModel(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "COMPUTABLE_STREAMING_ENDPOINT":
            return DSSStreamingEndpoint(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "RUNNABLE_LABELING_TASK":
            return DSSLabelingTask(self.flow.client, self.flow.project.project_key, node["ref"])
        elif node["type"] == "COMPUTABLE_RETRIEVABLE_KNOWLEDGE":
            return DSSKnowledgeBank(self.flow.client, self.flow.project.project_key, node["ref"])
        else:
            # TODO add streaming elements
            raise Exception("unsupported node type: %s" % node["type"])

    def get_items_in_traversal_order(self, as_type="dict"):
        """
        Get the list of nodes in left to right order.

        :param str as_type: How to return the nodes. Possible values are "dict" and "object" (defaults to **dict**).

        :returns: A list of nodes
        :rtype: If as_type=dict, each item is returned as a dict containing at least "ref" and "type".
                If as_type=object, each item is returned as a :class:`.DSSDataset`.
                :class:`.DSSManagedFolder`,
                :class:`.DSSSavedModel`,
                :class:`.DSSModelEvaluationStore`,
                :class:`.DSSStreamingEndpoint` or
                :class:`.DSSRecipe`
        """
        ret = []

        def add_to_set(node):
            ret.append(node)

        def in_set(obj):
            for candidate in ret:
                if candidate["type"] == obj["type"] and candidate["ref"] == obj["ref"]:
                    return True
            return False

        def add_from(graph_node):
            # To keep traversal order, we recurse to predecessors first
            for predecessor_ref in graph_node["predecessors"]:
                predecessor_node = self.nodes[predecessor_ref]
                if not in_set(predecessor_node):
                    add_from(predecessor_node)

            # Then add ourselves
            if not in_set(graph_node):
                add_to_set(graph_node)

            # Then recurse to successors
            for successor_ref in graph_node["successors"]:
                successor_node = self.nodes[successor_ref]
                if not in_set(successor_node):
                    add_from(successor_node)

        for source_computable in self.get_source_computables():
            add_from(source_computable)

        for source_recipe in self.get_source_recipes():
            add_from(source_recipe)

        return self._convert_nodes_list(ret, as_type)


class DSSFlowTool(object):
    """
    Handle to interact with a flow tool.
    """

    def __init__(self, client, project_key, tool_id):
        self.client = client
        self.project_key = project_key
        self.tool_id = tool_id

    def stop(self):
        """
        Stops the tool and releases the resources held by it.
        """
        return self.client._perform_json("POST", "/projects/%s/flow/tools/%s/stop" % (self.project_key, self.tool_id))

    def get_state(self, options={}):
        """
        Get the current state of the tool or view.

        :param dict options: options (defaults to **{}**)

        :returns: the state
        :rtype: dict
        """
        return self.client._perform_json("GET", "/projects/%s/flow/tools/%s/state" % (self.project_key, self.tool_id), body=options)

    def do(self, action):
        """
        Perform a manual user action on the tool.

        :param dict action: the action to do. It must contain:
            * a string `name` (the object id)
            * a string `type` (`"MARK_DATASET_AS_REBUILT"` or `"MARK_RECIPE_AS_OK"`)

            If `type` is `"MARK_RECIPE_AS_OK"`, a boolean `updated` can be added to the dict, if `True`, marks the recipe as OK after the update.

        :returns: the current state
        :rtype: dict
        """
        return self.client._perform_json("PUT", "/projects/%s/flow/tools/%s/action" % (self.project_key, self.tool_id), body=action)

    def update(self, options={}):
        """
        (for tools only) Start updating the tool state.

        :params options dict: options for the update (defaults to **{}**)

        :returns: A handle to interact with task of performing the update
        :rtype: :class:`.DSSFuture`
        """
        update_future = self.client._perform_json("POST", "/projects/%s/flow/tools/%s/update" % (self.project_key, self.tool_id), body=options)
        return DSSFuture(self.client, update_future.get('jobId', None), update_future)
