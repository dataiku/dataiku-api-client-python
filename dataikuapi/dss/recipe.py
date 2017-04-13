from ..utils import DataikuException
import json

class DSSRecipe(object):
    """
    A handle to an existing recipe on the DSS instance
    """
    def __init__(self, client, project_key, recipe_name):
        self.client = client
        self.project_key = project_key
        self.recipe_name = recipe_name

    ########################################################
    # Dataset deletion
    ########################################################

    def delete(self):
        """
        Delete the recipe
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))

    ########################################################
    # Recipe definition
    ########################################################

    def get_definition_and_payload(self):
        """
        Get the definition of the recipe

        Returns:
            the definition, as a DSSRecipeDefinitionAndPayload object, containing the recipe definition itself and its payload
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name))
        return DSSRecipeDefinitionAndPayload(data)

    def set_definition_and_payload(self, definition):
        """
        Set the definition of the recipe

        Args:
            definition: the definition, as a DSSRecipeDefinitionAndPayload object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s" % (self.project_key, self.recipe_name),
                body=definition.data)

    ########################################################
    # Recipe metadata
    ########################################################

    def get_metadata(self):
        """
        Get the metadata attached to this recipe. The metadata contains label, description
        checklists, tags and custom metadata of the recipe

        Returns:
            a dict object. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/latest
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


class DSSRecipeDefinitionAndPayload(object):
    """
    Definition for a recipe, that is, the recipe definition itself and its payload
    """
    def __init__(self, data):
        self.data = data

    def get_recipe_raw_definition(self):
        return self.data.get('recipe', None)

    def get_recipe_inputs(self):
        return self.data.get('recipe').get('inputs')

    def get_recipe_outputs(self):
        return self.data.get('recipe').get('outputs')

    def get_recipe_params(self):
        return self.data.get('recipe').get('params')

    def get_payload(self):
        return self.data.get('payload', None)

    def get_json_payload(self):
        return json.loads(self.data.get('payload', None))

    def set_payload(self, payload):
        self.data['payload'] = payload

    def set_json_payload(self, payload):
        self.data['payload'] = json.dumps(payload)

class DSSRecipeCreator(object):
    """
    Helper to create new recipes
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

    def with_input(self, dataset_name, project_key=None, role="main"):
        return self._with_input(dataset_name, project_key, role)

    def with_output(self, dataset_name, append=False, role="main"):
        """The output dataset must already exist. If you are creating a visual recipe with a single
        output, use with_existing_output"""
        return self._with_output(dataset_name, append, role)

    def build(self):
        """
        Create a new recipe in the project, and return a handle to interact with it. 

        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
        """
        self._finish_creation_settings()
        return self.project.create_recipe(self.recipe_proto, self.creation_settings)

    def _finish_creation_settings(self):
        pass

class SingleOutputRecipeCreator(DSSRecipeCreator):
    def __init__(self, type, name, project):
        DSSRecipeCreator.__init__(self, type, name, project)
        self.create_output_dataset = None
        self.output_dataset_settings = None

    def with_existing_output(self, dataset_name, append=False):
        assert self.create_output_dataset is None
        self.create_output_dataset = False
        self._with_output(dataset_name, append)
        return self

    def with_new_output(self, dataset_name, connection_id, format_option_id=None, partitioning_option_id=None, append=False):
        assert self.create_output_dataset is None
        self.create_output_dataset = True
        self.output_dataset_settings = {'connectionId':connection_id,'formatOptionId':format_option_id,'partitioningOptionId':partitioning_option_id}
        self._with_output(dataset_name, append)
        return self

    def with_output(self, dataset_name, append=False):
        return self.with_existing_output(dataset_name, append)

    def _finish_creation_settings(self):
        self.creation_settings['createOutputDataset'] = self.create_output_dataset
        self.creation_settings['outputDatasetSettings'] = self.output_dataset_settings

class VirtualInputsSingleOutputRecipeCreator(SingleOutputRecipeCreator):
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
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'window', name, project)

class SyncRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sync', name, project)

class GroupingRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'grouping', name, project)
        self.group_key = None

    def with_group_key(self, group_key):
        self.group_key = group_key
        return self

    def _finish_creation_settings(self):
        super(GroupingRecipeCreator, self)._finish_creation_settings()
        self.creation_settings['groupKey'] = self.group_key

class TopNRecipeCreator(DSSRecipeCreator):
    def __init__(self, name, project):
        DSSRecipeCreator.__init__(self, 'topn', name, project)

class JoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'join', name, project)

class StackRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'vstack', name, project)

class SamplingRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sampling', name, project)

class CodeRecipeCreator(DSSRecipeCreator):
    def __init__(self, name, type, project):
        DSSRecipeCreator.__init__(self, type, name, project)

    def _finish_creation_settings(self):
        pass

class SQLQueryRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sql_query', name, project)