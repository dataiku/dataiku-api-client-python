from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
from .metrics import ComputedMetrics

class DSSSavedModel(object):
    """
    A saved model on the DSS instance
    """
    def __init__(self, client, project_key, sm_id):
        self.client = client
        self.project_key = project_key
        self.sm_id = sm_id
        
        
    ########################################################
    # Versions
    ########################################################

    def list_versions(self):
        """
        Get the versions of this saved model
        
        Returns:
            an list of the versions
        """
        return self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions" % (self.project_key, self.sm_id))


    ########################################################
    # Metrics
    ########################################################

    def get_metric_values(self, version_id):
        """
        Get the values of the metrics on the version of this saved model
        
        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/metrics/%s" % (self.project_key, self.sm_id, version_id)))



                
    ########################################################
    # Usages
    ########################################################

    def get_usages(self):
        """
        Get the recipes referencing this model

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/savedmodels/%s/usages" % (self.project_key, self.sm_id))


