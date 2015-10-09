from .utils import DataikuException
from .base_client import DSSBaseClient

class APINodeClient(DSSBaseClient):
    """Entry point for the DSS APINode client"""

    def __init__(self, uri, service_id, api_key=None):
        """
        Instantiate a new DSS API client on the given base uri with the given API key.
        """
        DSSBaseClient.__init__(self, "%s/%s" % (uri, "public/api/v1/%s" % service_id), api_key)

    def predict_record(self, endpoint_id, features):
        return self._perform_json("POST",
            "%s/predict" % endpoint_id, body = {
                "features" :features
            })
