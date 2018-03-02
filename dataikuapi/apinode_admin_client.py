from .apinode_admin.service import APINodeService
from .apinode_admin.auth import APINodeAuth
from .utils import DataikuException
from .base_client import DSSBaseClient

class APINodeAdminClient(DSSBaseClient):
    """Entry point for the DSS APINode admin client"""

    def __init__(self, uri, api_key, **kwargs):
        """
        Instantiate a new DSS API client on the given base uri with the given API key.

        :param str uri: Base URI of the DSS API node server (http://host:port/ or https://host:port/)
        :param str api_key: Optional, API key for the service. Only required if the service has authentication
        :param str tls_verify: Optional, can be False to disable CA checks, True to force enable, or be a file name containing the CA certs to be trusted
        :param str tls_client_cert: Optional, set a TLS/SSL client certificate. Use a string tuple (cert,key) or a string for a combined certificate
        """
        DSSBaseClient.__init__(self, "%s/%s" % (uri, "admin/api"), api_key, **kwargs)

    ########################################################
    # Services generations
    ########################################################

    def create_service(self, service_id):
        self._perform_empty("POST", "services/", body = {
            "serviceId" : service_id
        })

    def list_services(self):
        return self._perform_json("GET", "services")

    def service(self, service_id):
        """
        Gets a handle to interact with a service
        """
        return APINodeService(self, service_id)

    def auth(self):
        """Returns a handle to interact with authentication"""
        return APINodeAuth(self)

    def get_metrics(self):
        return self._perform_json("GET", "metrics")
