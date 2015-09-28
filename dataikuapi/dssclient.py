
import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from dss.project import DSSProject
from dss.user import DSSUser
from dss.group import DSSGroup
from dss.connection import DSSConnection
from dss.sqlquery import DSSSQLQuery

from .utils import DataikuException

class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key):
        """
        Instantiate a new DSS API client on the given host with the given API key. 
        
        API keys can be managed
        in DSS on the project page or in the global settings. The API key will define which operations are
        allowed for the client.
        """
        self.api_key = api_key
        self.host = host
        self._session = Session()

    ########################################################
    # Projects
    ########################################################

    def list_project_keys(self):
        """
        Lists the project keys (=project identifiers).

        Returns:
            list of identifiers (=strings)
        """
        return [x["projectKey"] for x in self._perform_json("GET", "/projects/")]

    def get_project(self, project_key):
        """
        Get a handle to interact with a specific project.

        Args:
            project_key: the project key of the desired project
            
        Returns:
            A :class:`dataikuapi.dss.project.DSSProject`
        """
        return DSSProject(self, project_key)

    def create_project(self, project_key, name, owner, description=None, settings=None):
        """
        Creates a project, and return a project handle to interact with it.

        Note: this call requires an API key with admin rights

        Args:
            project_key: the identifier to use for the project.
            name: the name for the project.
            owner: the owner of the project.
            description: a short description for the project.
        
        Returns:
            A :class:`dataikuapi.dss.project.DSSProject` project handle
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
    # SQL queries
    ########################################################

    def sql_query(self, query, connection=None, database=None, dataset_full_name=None, pre_queries=None, post_queries=None, type='sql'):
        """
        Initiate a SQL, Hive or Impala query and get a handle to retrieve the results of the query.
        Internally, the query is run by DSS. The  database to run the query on is specified either by 
        passing a connection name, or by passing a database name, or by passing a dataset full name
        (whose connection is then used to retrieve the database)
        
        Args:
            query: the query to run
            connection: the connection on which the query should be run (exclusive of database and dataset_full_name)
            database: the database on which the query should be run (exclusive of connection and dataset_full_name)
            dataset_full_name: the dataset on the connection of which the query should be run (exclusive of connection and database)
            pre_queries: (optional) array of queries to run before the query
            post_queries: (optional) array of queries to run after the query
            type: the type of query : either 'sql', 'hive' or 'impala'
        
        Returns:
            A :class:`dataikuapi.dss.sqlquery.DSSSQLQuery` query handle
        """
        return DSSSQLQuery(self, query, connection, database, dataset_full_name, pre_queries, post_queries, type)

    ########################################################
    # Users
    ########################################################

    def list_users(self):
        """
        List all users setup on the DSS instance

        Note: this call requires an API key with admin rights
        
        Returns:
            A list of users, as an array of JSON object
        """
        return self._perform_json(
            "GET", "/admin/users/")

    def get_user(self, login):
        """
        Get a handle to interact with a specific user
        
        Args:
            login: the login of the desired user
        
        Returns:
            A :class:`dataikuapi.dss.user.DSSUser` user handle
        """
        return DSSUser(self, login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=[]):
        """
        Creates a user, and return a handle to interact with it
        
        Note: this call requires an API key with admin rights

        Args:
            login: the login of the new user
            password: the password of the new user
            display_name: the displayed name for the new user
            source_type: the type of new user. Admissible values are 'LOCAL', 'LDAP', 'SAAS'
            groups: the names of the groups the new user belongs to

        Returns:
            A :class:`dataikuapi.dss.user.DSSUser` user handle
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
        """
        List all groups setup on the DSS instance

        Note: this call requires an API key with admin rights
        
        Returns:
            A list of groups, as an array of JSON objects
        """
        return self._perform_json(
            "GET", "/admin/groups/")

    def get_group(self, name):
        """
        Get a handle to interact with a specific group
        
        Args:
            name: the name of the desired group
        
        Returns:
            A :class:`dataikuapi.dss.group.DSSGroup` group  handle
        """
        return DSSGroup(self, name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Creates a group, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        Args:
            name: the name of the new group
            description: a description of the new group
            source_type: the type of the new group. Admissible values are 'LOCAL', 'LDAP', 'SAAS'
            
        Returns:
            A :class:`dataikuapi.dss.group.DSSGroup` group handle
        """
        resp = self._perform_text(
               "POST", "/admin/groups/", body={
                   "name" : name,
                   "description" : description,
                   "sourceType" : source_type
               })
        return DSSGroup(self, name)

    ########################################################
    # Connections
    ########################################################

    def list_connections(self):
        """
        List all connections setup on the DSS instance

        Note: this call requires an API key with admin rights
        
        Returns:
			All connections, as a map of connection name to connection definition
        """
        return self._perform_json(
            "GET", "/admin/connections/")

    def get_connection(self, name):
        """
        Get a handle to interact with a specific connection
        
        Args:
            name: the name of the desired connection
        
        Returns:
            A :class:`dataikuapi.dss.connection.DSSConnection` connection  handle
        """
        return DSSConnection(self, name)

    def create_connection(self, name, type=None, params=None, usable_by='ALL', allowed_groups=None):
        """
        Creates a connection, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        Args:
            name: the name of the new connection
            type: the type of the new connection
            params: the parameters of the new connection, as a JSON object
            usable_by: the type of access control for the connection. Either 'ALL' (=no access control) 
                       or 'ALLOWED' (=access restricted to users of a list of groups)
            allowed_groups: when using access control (that is, setting usable_by='ALLOWED'), the list
                            of names of the groups whose users are allowed to use the new connection
            
        Returns:
            A :class:`dataikuapi.dss.connection.DSSConnection` connection handle
        """
        resp = self._perform_text(
               "POST", "/admin/connections/", body={
                   "name" : name,
                   "type" : type,
                   "params" : params,
                   "usableBy" : usable_by,
                   "allowedGroups" : allowed_groups
               })
        return DSSConnection(self, name)

    ########################################################
    # Logs
    ########################################################

    def list_logs(self):
        """
        List all logs on the DSS instance
 
        Note: this call requires an API key with admin rights
        
        Returns:
            A list of log names
        """
        return self._perform_json(
            "GET", "/admin/logs/")

    def get_log(self, name):
        """
        Get a specific log

        Note: this call requires an API key with admin rights
        
        Args:
            name: the name of the desired log
        
        Returns:
            The full log, as a string
        """
        return self._perform_json(
            "GET", "/admin/logs/%s" % name)

    ########################################################
    # Variables
    ########################################################

    def get_variables(self):
        """
        Get the DSS instance's variables

        Note: this call requires an API key with admin rights
        
        Returns:
            A JSON object
        """
        return self._perform_json(
            "GET", "/admin/variables/")

    def set_variables(self, variables):
        """
        Set the DSS instance's variables

        Note: this call requires an API key with admin rights
        
        Args:
            variables: the new state of all variables of the instance, as a JSON object

        """
        return self._perform_empty(
            "PUT", "/admin/variables/", body=variables)

    ########################################################
    # Internal Request handling
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
