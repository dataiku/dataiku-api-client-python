import time
import sys
from ..utils import DataikuException

class DSSContinuousActivity(object):
    """
    A handle to interact with the execution of a continuous recipe on the DSS instance.

    .. important::

        Do not create this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.get_continuous_activity`
    """
    def __init__(self, client, project_key, recipe_id):
        self.client = client
        self.recipe_id = recipe_id
        self.project_key = project_key

    def start(self, loop_params={}):
        """
        Start the continuous activity

        :param dict loop_params: controls how the recipe is restarted after a failure, and the delay before 
                                 the restarting. Default is to restart indefinitely without delay. Fields are:

                                    * **abortAfterCrashes** : when reaching this number of failures, the recipe isn't restarted anymore. Use -1 as 'no limit on number of failures'
                                    * **initialRestartDelayMS** : initial delay to wait before restarting after a failure
                                    * **restartDelayIncMS** : increase to the delay before restarting upon subsequent failures
                                    * **maxRestartDelayMS** : max delay before restarting after failure
        """
        return self.client._perform_json(
            "POST", "/projects/%s/continuous-activities/%s/start" % (self.project_key, self.recipe_id), body=loop_params)

    def stop(self):
        """
        Stop the continuous activity.
        """
        self.client._perform_empty(
            "POST", "/projects/%s/continuous-activities/%s/stop" % (self.project_key, self.recipe_id))

    def get_status(self):
        """
        Get the current status of the continuous activity.

        Usage example:

        .. code-block:: python

            # stop a continuous activity via its future
            from dataikuapi.dss.future import DSSFuture
            activity = project.get_continuous_activity("my_continuous_recipe")
            status = activity.get_status()
            future = DSSFuture(a.client, status["mainLoopState"]['futureId'], status["mainLoopState"]['futureInfo'])  
            future.abort()          

            # this is equivalent to simply stop()
            activity.stop()
        
        :return: the state of the continuous activity. The state as requested by the use is stored in a **desiredState** 
                  field (values: 'STARTED' or 'STOPPED'), and the current effective state in a **mainLoopState** sub-dict.

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/projects/%s/continuous-activities/%s/" % (self.project_key, self.recipe_id))

    def get_recipe(self):
    	"""
    	Get a handle on the associated recipe.

        :rtype: :class:`dataikuapi.dss.recipe.DSSRecipe`
    	"""
    	from .recipe import DSSRecipe
    	return DSSRecipe(self.client, self.project_key, self.recipe_id)
