import time
import sys
from ..utils import DataikuException

class DSSContinuousActivity(object):
    """
    A continuous activity on the DSS instance
    """
    def __init__(self, client, project_key, recipe_id):
        self.client = client
        self.recipe_id = recipe_id
        self.project_key = project_key

    def start(self, loop_params={}):
        """
        Start the activity
        """
        return self.client._perform_json(
            "POST", "/projects/%s/continuous-activities/%s/start" % (self.project_key, self.recipe_id), body=loop_params)

    def stop(self):
        """
        Stop the activity
        """
        self.client._perform_empty(
            "POST", "/projects/%s/continuous-activities/%s/stop" % (self.project_key, self.recipe_id))

    def get_status(self):
        """
        Get the current status of the continuous activity
        
        Returns:
            the state of the continuous activity, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/continuous-activities/%s/" % (self.project_key, self.recipe_id))

    def get_recipe(self):
    	"""
    	Return a handle on the associated recipe
    	"""
    	from .recipe import DSSRecipe
    	return DSSRecipe(self.client, self.project_key, self.recipe_id)
