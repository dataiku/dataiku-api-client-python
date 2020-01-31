from .utils import AnyLoc
from .recipe import DSSRecipeDefinitionAndPayload
from .future import DSSFuture
import logging

class DSSProjectFlow(object):
    def __init__(self, client, project):
        self.client = client
        self.project = project


    def replace_input_computable(self, current_ref, new_ref, type="DATASET"):
        """
        This method replaces all references to a "computable" (Dataset, Managed Folder or Saved Model)
        as input of recipes in the whole Flow by a reference to another computable.

        No specific checks are performed. It is your responsibility to ensure that the schema
        of the new dataset will be compatible with the previous one (in the case of datasets).

        If `new_ref` references an object in a foreign project, this method will automatically
        ensure that `new_ref` is exposed to the current project

        :param current_ref str: Either a "simple" object name (dataset name, model id, managed folder id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id")
        :param new_ref str: Either a "simple" object name (dataset name, model id, managed folder id)
                    or a foreign object reference in the form "FOREIGN_PROJECT_KEY.local_id")
        :param type str: The type of object being replaced (DATASET, SAVED_MODEL or MANAGED_FOLDER)
        """

        new_loc = AnyLoc.from_ref(self.project.project_key, new_ref)

        if new_loc.project_key != self.project.project_key:
            logging.info("New ref is in project %s, exposing it to project %s" % (new_loc.project_key, self.project.project_key))
            new_ref_src_project = self.client.get_project(new_loc.project_key)
            settings = new_ref_src_project.get_settings()
            settings.add_exposed_object(type, new_loc.object_id, self.project.project_key)
            settings.save()

        for recipe in self.project.list_recipes():
            fake_rap = DSSRecipeDefinitionAndPayload({"recipe" : recipe})
            if fake_rap.has_input(current_ref):
                logging.info("Recipe %s has %s as input, performing the replacement by %s"% \
                    (recipe["name"], current_ref, new_ref))
                recipe_obj = self.project.get_recipe(recipe["name"])
                dap = recipe_obj.get_definition_and_payload()
                dap.replace_input(current_ref, new_ref)
                recipe_obj.set_definition_and_payload(dap)

    ########################################################
    # Flow tools
    ########################################################

    def start_tool(self, type, data={}):
        """
        Start a tool or open a view in the flow

        :param type str: one of {COPY, CHECK_CONSISTENCY, PROPAGATE_SCHEMA} (tools) or {TAGS, CUSTOM_FIELDS, CONNECTIONS, COUNT_OF_RECORDS, FILESIZE, FILEFORMATS, RECIPES_ENGINES, RECIPES_CODE_ENVS, IMPALA_WRITE_MODE, HIVE_MODE, SPARK_ENGINE, SPARK_CONFIG, SPARK_PIPELINES, SQL_PIPELINES, PARTITIONING, PARTITIONS, SCENARIOS, CREATION, LAST_MODIFICATION, LAST_BUILD, RECENT_ACTIVITY, WATCH}  (views)
        :param data dict: initial data for the tool (optional)
    
        :returns: a :class:`.flow.DSSFlowTool` handle to interact with the newly-created tool or view
        """
        tool_id = self.client._perform_text("POST", "/projects/%s/flow/tools/" % self.project.project_key, params={'type':type}, body=data)
        return DSSFlowTool(self.client, self.project.project_key, tool_id)

    def propagate_schema(self, dataset_name, rebuild=False, recipe_update_options={}, excluded_recipes=[], mark_as_ok_recipes=[], partition_by_dim={}, partition_by_computable={}):
        """
        Start an automatic schema propagate from a dataset

        :param dataset_name str: name of a dataset to start propagating from
        :param rebuild bool: whether to automatically rebuild datasets if needed
        :param recipe_update_options str: pre-recipe or per-recipe-type update options to apply on recipes
        :param excluded_recipes list: list of recipes where propagation is to stop
        :param mark_as_ok_recipes list: list of recipes to consider as ok
        :param partition_by_dim dict: partition value to use for each dimension
        :param partition_by_computable dict: partition spec to use for a given dataset or recipe (overrides partition_by_dim)
    
        :returns: dict of the messages collected during the update
        """
        data = {'recipeUpdateOptions':recipe_update_options, 'partitionByDim':partition_by_dim, 'partitionByComputable':partition_by_computable, 'excludedRecipes':excluded_recipes, 'markAsOkRecipes':mark_as_ok_recipes}
        update_future = self.client._perform_json("POST", "/projects/%s/flow/tools/propagate-schema/%s/" % (self.project.project_key, dataset_name), params={'rebuild':rebuild}, body=data)
        return DSSFuture(self.client,update_future.get('jobId', None), update_future)


class DSSFlowTool(object):
    """
    Handle to interact with a flow tool
    """
    def __init__(self, client, project_key, tool_id):
        self.client = client
        self.project_key = project_key
        self.tool_id = tool_id

    def stop(self):
        """
        Stops the tool and releases the resources held by it
        """
        return self.client._perform_json("POST", "/projects/%s/flow/tools/%s/stop" % (self.project_key, self.tool_id))

    def get_state(self, options={}):
        """
        Get the current state of the tool or view

        :returns: the state, as a dict
        """
        return self.client._perform_json("GET", "/projects/%s/flow/tools/%s/state" % (self.project_key, self.tool_id), body=options)
 
    def do(self, action):
        """
        Perform a manual user action on the tool

        :returns: the current state, as a dict
        """
        return self.client._perform_json("PUT", "/projects/%s/flow/tools/%s/action" % (self.project_key, self.tool_id), body=action)
 
    def update(self, options={}):
        """
        (for tools only) Start updating the tool state

        :params options dict: options for the update (optional)

        :returns: a :class:`.future.DSSFuture` handle to interact with task of performing the update
        """
        update_future = self.client._perform_json("POST", "/projects/%s/flow/tools/%s/update" % (self.project_key, self.tool_id), body=options)
        return DSSFuture(self.client,update_future.get('jobId', None), update_future)

