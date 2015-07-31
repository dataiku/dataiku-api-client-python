
import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from dss.dataset import DSSDataset

from .utils import DataikuException

class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key):
        self.api_key = api_key
        self.host = host
        self._session = Session()


    ########################################################
    # Datasets
    ########################################################

    def list_datasets(self, project_key):
        return self._perform_json(
            "GET", "/projects/%s/datasets/" % project_key)

    def dataset(self, project_key, dataset_name):
        """
        Get a handler to interact with a specific dataset
        """
        return DSSDataset(self, project_key, dataset_name)

    def create_dataset(self, project_key, dataset_name, type,
                    params={}, formatType=None, formatParams={}):

        obj = {
            "name" : dataset_name,
            "projectKey" : project_key,
            "type" : type,
            "params" : params,
            "formatType" : formatType,
            "formatParams" : formatParams
        }
        self._perform_json("POST", "/projects/%s/datasets/" % project_key,
                            body = obj)

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

    def _perform_raw(self, method, path, params=None, body=None):
        if body:
            body = json.dumps(body)

        auth = HTTPBasicAuth(self.api_key, "")

        try:
            http_res = self._session.request(
                    method, "%s/%s" % (self.host, path),
                    params=params, data=body,
                    auth=auth, stream  = True)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

