from ..utils import DataikuException
import json

class DSSRecipe(object):
    """
    A recipe on the DSS instance
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
                "GET", "/projects/%s/recipes/%s/" % (self.project_key, self.recipe_name))
        return DSSRecipeDefinitionAndPayload(data)

    def set_definition_and_payload(self, definition):
        """
        Set the definition of the recipe
        
        Args:
            definition: the definition, as a DSSRecipeDefinitionAndPayload object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s/" % (self.project_key, self.recipe_name),
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
        self.type = type
        self.name = name
        self.project = project
        self.recipe_inputs = []
        self.recipe_outputs = []
        self.recipe_params = {}
        
    def _build_ref(self, object_id, project_key=None):
        if project_key is not None and project_key != self.project.project_key:
            return project_key + '.' + object_id
        else:
            return object_id
    
    def with_input(self, dataset_name, project_key=None):
        self.recipe_inputs.append({'ref':self._build_ref(dataset_name, project_key)})
        return self
        
    def with_output(self, dataset_name, append=False):
        self.recipe_outputs.append({'ref':self._build_ref(dataset_name), 'appendMode':append})
        return self

    def _get_recipe_inputs(self):
        return self.recipe_inputs
        
    def _get_recipe_outputs(self):
        return self.recipe_outputs
        
    def _get_recipe_params(self):
        return self.recipe_params
        
    def build(self):
        """
        Create a new recipe in the project, and return a handle to interact with it. 
        
        Returns:
            A :class:`dataikuapi.dss.recipe.DSSRecipe` recipe handle
        """
        effective_inputs = self._get_recipe_inputs()
        effective_outputs = self._get_recipe_outputs()
        effective_params = self._get_recipe_params()
        return self.project.create_recipe(self.name, self.type, effective_inputs, effective_outputs, effective_params)


class SingleOutputRecipeCreator(DSSRecipeCreator):
    def __init__(self, type, name, project):
        DSSRecipeCreator.__init__(self, type, name, project)
        self.create_output_dataset = None
        self.output_dataset_settings = None

    def with_existing_output(self, dataset_name, append=False):
        assert self.create_output_dataset is None
        self.create_output_dataset = False
        self.recipe_outputs.append({'ref':self._build_ref(dataset_name), 'appendMode':append})
        return self
        
    def with_new_output(self, dataset_name, connection_id, format_option_id=None, partitioning_option_id=None, append=False):
        assert self.create_output_dataset is None
        self.create_output_dataset = True
        self.output_dataset_settings = {'connectionId':connection_id,'formatOptionId':format_option_id,'partitioningOptionId':partitioning_option_id}
        self.recipe_outputs.append({'ref':self._build_ref(dataset_name), 'appendMode':append})
        return self

    def with_output(self, dataset_name, append=False):
        return self.with_existing_output(dataset_name, append)
        
    def _get_recipe_params(self):
        return {'createOutputDataset':self.create_output_dataset, 'outputDatasetSettings':self.output_dataset_settings}

class VirtualInputsSingleOutputRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, type, name, project):
        SingleOutputRecipeCreator.__init__(self, type, name, project)
        self.virtual_inputs = []

    def with_input(self, dataset_name, project_key=None):
        self.virtual_inputs.append(self._build_ref(dataset_name, project_key))
        return self
        
    def _get_recipe_params(self):
        params = super(VirtualInputsSingleOutputRecipeCreator, self)._get_recipe_params()
        params['virtualInputs'] = self.virtual_inputs
        return params

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
        
    def _get_recipe_params(self):
        params = super(GroupingRecipeCreator, self)._get_recipe_params()
        params['groupKey'] = self.group_key
        return params

class JoinRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'join', name, project)

class StackRecipeCreator(VirtualInputsSingleOutputRecipeCreator):
    def __init__(self, name, project):
        VirtualInputsSingleOutputRecipeCreator.__init__(self, 'vstack', name, project)

class SamplingRecipeCreator(SingleOutputRecipeCreator):
    def __init__(self, name, project):
        SingleOutputRecipeCreator.__init__(self, 'sampling', name, project)
 
# shaker needs the unsafe code permission which is not on api keys       
#class ShakerRecipeCreator(SingleOutputRecipeCreator):
#    def __init__(self, name, project):
#        SingleOutputRecipeCreator.__init__(self, 'shaker', name, project)
        
        