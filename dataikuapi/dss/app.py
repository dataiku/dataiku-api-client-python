import sys
import os.path as osp
from .future import DSSFuture
from dataikuapi.utils import DataikuException


class DSSApp(object):
    """
    A handle to interact with a app on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_app``
    """
    def __init__(self, client, app_id):
       self.client = client
       self.app_id = app_id


    ########################################################
    # Instances
    ########################################################

    def list_instances(self):
        """
        List the instances in this project
        
        Returns:
            the list of the instances, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/apps/%s/instances/" % self.app_id)


