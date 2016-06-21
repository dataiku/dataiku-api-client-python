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
    
    def get_definition(self):
        """
        Get the definition of the recipe
        
        Returns:
            the definition, as a JSON object, containing the recipe definition itself and its payload
        """
        return self.client._perform_json(
                "GET", "/projects/%s/recipes/%s/" % (self.project_key, self.recipe_name))

    def set_definition(self, definition):
        """
        Set the definition of the recipe
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/recipes/%s/" % (self.project_key, self.recipe_name),
                body=definition)

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


             