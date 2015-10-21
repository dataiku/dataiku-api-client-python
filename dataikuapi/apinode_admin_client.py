from apinode_admin.service import APINodeService
from .utils import DataikuException
from .base_client import DSSBaseClient

class APINodeAdminClient(DSSBaseClient):
    """Entry point for the DSS APINode admin client"""

    def __init__(self, uri, api_key):
        """
        Instantiate a new DSS API client on the given base uri with the given API key.
        """
        DSSBaseClient.__init__(self, "%s/%s" % (uri, "admin/api"), api_key)

    ########################################################
    # Services generations
    ########################################################

    def create_service(self, service_id):
        self._perform_empty("POST", "services/", body = {
            "serviceId" : service_id
        })

    def service(self, service_id):
        """
        Gets a handle to interact with a service
        """
        return APINodeService(self, service_id)
