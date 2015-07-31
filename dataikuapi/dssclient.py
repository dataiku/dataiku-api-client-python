
import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from dss.dataset import DSSDataset

class DataikuException(Exception):
    """Exception launched by DSS client when an error occurs"""

class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key):
        self.api_key = api_key
        self.host = host
        self._session = Session()

    def list_datasets(self, project_key):
        return self._perform_json(
            "GET", "/projects/%s/datasets/" % project_key)

    def dataset(self, project_key, dataset_name):
        """
        Get a handler to interact with a specific dataset
        """
        return DSSDataset(self, project_key, dataset_name)

    def _perform_json(self, method, path, params=None, body=None):
        if body:
            body = json.dumps(body)

        auth = HTTPBasicAuth(self.api_key, "")

        try:
            http_res = self._session.request(
                    method, "%s/%s" % (self.host, path),
                    params=params, data=body,
                    auth=auth)
            http_res.raise_for_status()
            return http_res.json()
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

