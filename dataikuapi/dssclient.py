
import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from dss.project import DSSProject
from dss.user import DSSUser
from dss.group import DSSGroup

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

    def create_project(self, project_key, name, owner, description=None, settings=None):
        """
        Creates a project, and return a DSSProject object
        """
        resp = self._perform_text(
               "POST", "/projects/", body={
                   "projectKey" : project_key,    
                   "name" : name,    
                   "owner" : owner,    
                   "settings" : settings,    
                   "description" : description
               })
        return DSSProject(self, project_key)

    ########################################################
    # Users
    ########################################################

    def list_users(self):
        return self._perform_json(
            "GET", "/admin/users/")

    def get_user(self, login):
        """
        Get a handler to interact with a specific user
        """
        return DSSUser(self, login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=[]):
        """
        Creates a user, and return a DSSUser object
        """
        resp = self._perform_text(
               "POST", "/admin/users/", body={
                   "login" : login,
                   "password" : password,
                   "displayName" : display_name,
                   "sourceType" : source_type,
                   "groups" : groups
               })
        return DSSUser(self, login)

    ########################################################
    # Groups
    ########################################################

    def list_groups(self):
        return self._perform_json(
            "GET", "/admin/groups/")

    def get_group(self, name):
        """
        Get a handler to interact with a specific group
        """
        return DSSGroup(self, name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Creates a group, and return a DSSGroup object
        """
        resp = self._perform_text(
               "POST", "/admin/groups/", body={
                   "name" : name,
                   "description" : description,
                   "sourceType" : source_type
               })
        return DSSGroup(self, name)

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
