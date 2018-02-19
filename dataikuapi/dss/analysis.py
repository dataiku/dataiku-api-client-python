from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import time
from .metrics import ComputedMetrics
from .ml import DSSMLTask

class DSSAnalysis(object):
    """A handle to interact with a DSS visual analysis"""
    def __init__(self, client, project_key, analysis_id):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id

    ########################################################
    # Analysis deletion
    ########################################################

    def delete(self, drop_data=False):
        """
        Delete the dataset

        :param bool drop_data: Should the data of the dataset be dropped
        """
        return self.client._perform_empty("DELETE", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id))


    ########################################################
    # Analysis definition
    ########################################################

    def get_definition(self):
        """
        Get the definition of the analysis

        Returns:
            the definition, as a JSON object
        """
        return self.client._perform_json("GET", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id))

    def set_definition(self, definition):
        """
        Set the definition of the analysis
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json("PUT", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id), body=definition)


    ########################################################
    # ML
    ########################################################

    def create_prediction_ml_task(self, target_variable,
                                   ml_backend_type = "PY_MEMORY",
                                   guess_policy = "DEFAULT"):


        """Creates a new prediction task in this visual analysis lab
        for a dataset.


        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: DEFAULT, SIMPLE_FORMULA, DECISION_TREE, EXPLANATORY and PERFORMANCE
        """

        obj = {
            "taskType" : "PREDICTION",
            "targetVariable" : target_variable,
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        ref = self.client._perform_json("POST", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id), body=obj)
        return DSSMLTask(self.client, self.project_key, self.analysis_id, ref["mlTaskId"])

    def create_clustering_ml_task(self,
                                   ml_backend_type = "PY_MEMORY",
                                   guess_policy = "KMEANS"):


        """Creates a new clustering task in a new visual analysis lab
        for a dataset.


        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and ANOMALY_DETECTION
        """

        obj = {
            "taskType" : "CLUSTERING",
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        ref = self.client._perform_json("POST", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id), body=obj)
        return DSSMLTask(self.client, self.project_key, self.analysis_id, ref["mlTaskId"])

    def list_ml_tasks(self):
        """
        List the ML tasks in this visual analysis
        
        Returns:
            the list of the ML tasks summaries, each one as a JSON object
        """
        return self.client._perform_json("GET", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id))

    def get_ml_task(self, mltask_id):
        """
        Get a handle to interact with a specific ML task
       
        Args:
            mltask_id: the identifier of the desired ML task 
        
        Returns:
            A :class:`dataikuapi.dss.ml.DSSMLTask` ML task handle
        """
        return DSSMLTask(self.client, self.project_key, self.analysis_id, mltask_id)

