
import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from dss.project import DSSProject

from .utils import DataikuException

class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key):
        self.api_key = api_key
        self.host = host
        self._session = Session()

    ########################################################
    # Projects
    ########################################################

    def list_projects(self):
        return self._perform_json(
            "GET", "/projects/")

    def get_project(self, project_key):
        """
        Get a handler to interact with a specific project
        """
        return DSSProject(self, project_key)

    def create_project(self, projectKey, name, owner, description=None, settings=None):
        """
        Creates a project, and return a DSSProject object
        """
        resp = self._perform_text(
               "POST", "/projects/", body={
                   "projectKey" : projectKey,    
                   "name" : name,    
                   "owner" : owner,    
                   "settings" : settings,    
                   "description" : description
               })
        return DSSProject(self, projectKey)

    ########################################################
    # Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False):
        if body:
            body = json.dumps(body)

        auth = HTTPBasicAuth(self.api_key, "")

        try:
            http_res = self._session.request(
                    method, "%s/dip/publicapi%s" % (self.host, path),
                    params=params, data=body,
                    auth=auth, stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None):
        self._perform_http(method, path, params, body, False)
            
    def _perform_text(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).text

    def _perform_json(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).json()

    def _perform_raw(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, True)
