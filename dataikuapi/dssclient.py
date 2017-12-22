import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

from .dss.future import DSSFuture
from .dss.project import DSSProject
from .dss.plugin import DSSPlugin
from .dss.admin import DSSUser, DSSGroup, DSSConnection, DSSGeneralSettings, DSSCodeEnv, DSSGlobalApiKey, DSSCluster
from .dss.meaning import DSSMeaning
from .dss.sqlquery import DSSSQLQuery
from .dss.notebook import DSSNotebook
import os.path as osp
from .utils import DataikuException

class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key=None, internal_ticket = None):
        """
        Instantiate a new DSS API client on the given host with the given API key.

        API keys can be managed in DSS on the project page or in the global settings.

        The API key will define which operations are allowed for the client.
        """
        self.api_key = api_key
        self.internal_ticket = internal_ticket
        self.host = host
        self._session = Session()

        if self.api_key is not None:
            self._session.auth = HTTPBasicAuth(self.api_key, "")
        elif self.internal_ticket is not None:
            self._session.headers.update({"X-DKU-APITicket" : self.internal_ticket})
        else:
            raise ValueError("API Key is required")
            
            
    ########################################################
    # Futures
    ########################################################
            
    def list_futures(self, as_objects=False, all_users=False):
        """
        List the currently-running long tasks (a.k.a futures)

        Returns:
            list of futures. Each object contains at least a 'jobId' field
        """
        list = self._perform_json("GET", "/futures/", params={"withScenarios":False, "withNotScenarios":True, 'allUsers' : all_users})
        if as_objects:
            return [DSSFuture(self, state['jobId'], state) for state in list]
        else:
            return list

    def list_running_scenarios(self, all_users=False):
        """
        List the running scenarios

        Returns:
            the list of scenarios, each one as a JSON object containing a jobId field for the
            future hosting the scenario run, and a payload field with scenario identifiers
        """
        return self._perform_json("GET", "/futures/", params={"withScenarios":True, "withNotScenarios":False, 'allUsers' : all_users})

    def get_future(self, job_id):
        """
        Get a handle to interact with a specific long task (a.k.a future).

        Args:
            job_id: the job_id key of the desired future

        Returns:
            A :class:`dataikuapi.dss.future.DSSFuture`
        """
        return DSSFuture(self, job_id)


    ########################################################
    # Notebooks
    ########################################################
            
    def list_running_notebooks(self, as_objects=True):
        """
        List the currently-running notebooks

        Returns:
            list of notebooks. Each object contains at least a 'name' field
        """
        list = self._perform_json("GET", "/admin/notebooks/")
        if as_objects:
            return [DSSNotebook(self, notebook['projectKey'], notebook['name'], notebook) for notebook in list]
        else:
            return list


    ########################################################
    # Projects
    ########################################################

    def list_project_keys(self):
        """
        List the project keys (=project identifiers).

        Returns:
            list of identifiers (=strings)
        """
        return [x["projectKey"] for x in self._perform_json("GET", "/projects/")]

    def list_projects(self):
        """
        List the projects

        Returns:
            list of objects. Each object contains at least a 'projectKey' field
        """
        return self._perform_json("GET", "/projects/")

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
        Create a project, and return a project handle to interact with it.

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
    # Plugins
    ########################################################

    def list_plugins(self):
        """
        List the installed plugins

        Returns:
            list of objects. Each object contains at least a 'projectKey' field
        """
        return self._perform_json("GET", "/plugins/")

    def get_plugin(self, plugin_id):
        """
        Get a handle to interact with a specific dev plugin.

        Args:
            plugin_id: the identifier of the desired plugin
            
        Returns:
            A :class:`dataikuapi.dss.project.DSSPlugin`
        """
        return DSSPlugin(self, plugin_id)

    ########################################################
    # SQL queries
    ########################################################

    def sql_query(self, query, connection=None, database=None, dataset_full_name=None, pre_queries=None, post_queries=None, type='sql', extra_conf={}):
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
        return DSSSQLQuery(self, query, connection, database, dataset_full_name, pre_queries, post_queries, type, extra_conf)

    ########################################################
    # Users
    ########################################################

    def list_users(self):
        """
        List all users setup on the DSS instance

        Note: this call requires an API key with admin rights

        :return: A list of users, as an array of dicts.
        """
        return self._perform_json(
            "GET", "/admin/users/")

    def get_user(self, login):
        """
        Get a handle to interact with a specific user

        :param str login: the login of the desired user

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        return DSSUser(self, login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=[], profile='DATA_SCIENTIST'):
        """
        Create a user, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str login: the login of the new user
        :param str password: the password of the new user
        :param str display_name: the displayed name for the new user
        :param str source_type: the type of new user. Admissible values are 'LOCAL' or 'LDAP'
        :param list groups: the names of the groups the new user belongs to
        :param str profile: The profile for the new user, can be one of READER, DATA_ANALYST or DATA_SCIENTIST

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        resp = self._perform_text(
               "POST", "/admin/users/", body={
                   "login" : login,
                   "password" : password,
                   "displayName" : display_name,
                   "sourceType" : source_type,
                   "groups" : groups,
                   "userProfile" : profile
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
            A :class:`dataikuapi.dss.admin.DSSGroup` group  handle
        """
        return DSSGroup(self, name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Create a group, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        Args:
            name: the name of the new group
            description: a description of the new group
            source_type: the type of the new group. Admissible values are 'LOCAL', 'LDAP', 'SAAS'
            
        Returns:
            A :class:`dataikuapi.dss.admin.DSSGroup` group handle
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
            A :class:`dataikuapi.dss.admin.DSSConnection` connection  handle
        """
        return DSSConnection(self, name)

    def create_connection(self, name, type=None, params=None, usable_by='ALL', allowed_groups=None):
        """
        Create a connection, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param name: the name of the new connection
        :param type: the type of the new connection
        :param params: the parameters of the new connection, as a JSON object
        :param usable_by: the type of access control for the connection. Either 'ALL' (=no access control)
            or 'ALLOWED' (=access restricted to users of a list of groups)
        :param allowed_groups: when using access control (that is, setting usable_by='ALLOWED'), the list 
            of names of the groups whose users are allowed to use the new connection
        
        :returns: A :class:`dataikuapi.dss.admin.DSSConnection` connection handle
        
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
    # Code envs
    ########################################################

    def list_code_envs(self):
        """
        List all code envs setup on the DSS instance

        Note: this call requires an API key with admin rights
        
        Returns:
            List code envs (name, type, language)
        """
        return self._perform_json(
            "GET", "/admin/code-envs/")

    def get_code_env(self, env_lang, env_name):
        """
        Get a handle to interact with a specific code env
        
        Args:
            name: the name of the desired code env
        
        Returns:
            A :class:`dataikuapi.dss.admin.DSSCodeEnv` code env  handle
        """
        return DSSCodeEnv(self, env_lang, env_name)

    def create_code_env(self, env_lang, env_name, deployment_mode, params=None):
        """
        Create a code env, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param env_lang: the language (Python, R) of the new code env
        :param env_name: the name of the new code env
        :param deployment_mode: the type of the new code env
        :param params: the parameters of the new code env, as a JSON object
        
        :returns: A :class:`dataikuapi.dss.admin.DSSCodeEnv` code env handle
        
        """
        params = params if params is not None else {}
        params['deploymentMode'] = deployment_mode
        resp = self._perform_json(
               "POST", "/admin/code-envs/%s/%s" % (env_lang, env_name), body=params)
        if resp is None:
            raise Exception('Env creation returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env creation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return DSSCodeEnv(self, env_lang, env_name)

    ########################################################
    # Clusters
    ########################################################

    def list_clusters(self):
        """
        List all clusters setup on the DSS instance

        Returns:
            List clusters (name, type, state)
        """
        return self._perform_json(
            "GET", "/admin/clusters/")

    def get_cluster(self, cluster_id):
        """
        Get a handle to interact with a specific cluster
        
        Args:
            name: the name of the desired cluster
        
        Returns:
            A :class:`dataikuapi.dss.admin.DSSCluster` cluster handle
        """
        return DSSCluster(self, cluster_id)

    def create_cluster(self, cluster_name, cluster_type='manual', params=None):
        """
        Create a cluster, and return a handle to interact with it

        :param cluster_name: the name of the new cluster
        :param cluster_type: the type of the new cluster
        :param params: the parameters of the new cluster, as a JSON object
        
        :returns: A :class:`dataikuapi.dss.admin.DSSCluster` cluster handle
        
        """
        definition = {}
        definition['name'] = cluster_name
        definition['type'] = cluster_type
        definition['params'] = params if params is not None else {}
        resp = self._perform_json(
               "POST", "/admin/clusters/", body=definition)
        if resp is None:
            raise Exception('Cluster creation returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster creation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return DSSCluster(self, resp['id'])

    ########################################################
    # Global API Keys
    ########################################################

    def list_global_api_keys(self):
        """
        List all global API keys set up on the DSS instance

        Note: this call requires an API key with admin rights

        Returns:
            All global API keys, as a list
        """
        return self._perform_json(
            "GET", "/admin/globalAPIKeys/")

    def get_global_api_key(self, key):
        """
        Get a handle to interact with a specific Global API key

        Args:
            key: the secret key of the desired API key

        Returns:
            A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        return DSSGlobalApiKey(self, key)

    def create_global_api_key(self, label=None, description=None, admin=False):
        """
        Create a Global API key, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        Args:
            label: the label of the new API key
            description: the description of the new API key
            admin: has the new API key admin rights (True or False)

        Returns:
            A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "POST", "/admin/globalAPIKeys/", body={
                "label" : label,
                "description" : description,
                "globalPermissions": {
                    "admin": admin
                }
            })
        if resp is None:
            raise Exception('API key creation returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('API key creation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        if not resp.get('id', False):
            raise Exception('API key creation returned no key')
        key = resp.get('key', '')
        return DSSGlobalApiKey(self, key)

    ########################################################
    # Meanings
    ########################################################

    def list_meanings(self):
        """
        List all user-defined meanings on the DSS instance

        Note: this call requires an API key with admin rights

        Returns:
            A list of meanings, as an array of JSON objects
        """
        return self._perform_json(
            "GET", "/meanings/")

    def get_meaning(self, id):
        """
        Get a handle to interact with a specific user-defined meaning

        Note: this call requires an API key with admin rights

        Args:
            id: the ID of the desired meaning

        Returns:
            A :class:`dataikuapi.dss.meaning.DSSMeaning` meaning  handle
        """
        return DSSMeaning(self, id)

    def create_meaning(self, id, label, type, description=None,
                        values=None, mappings=None, pattern=None,
                        normalizationMode=None, detectable=False):
        """
        Create a meaning, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param id: the ID of the new meaning
        :param type: the type of the new meaning. Admissible values are 'DECLARATIVE', 'VALUES_LIST', 'VALUES_MAPPING' and 'PATTERN'
        :param description (optional): the description of the new meaning
        :param values (optional): when type is 'VALUES_LIST', the list of values
        :param mappings (optional): when type is 'VALUES_MAPPING', the mapping, as a list of objects with this
            structure: {'from': 'value_1', 'to': 'value_a'}
        :param pattern (optional): when type is 'PATTERN', the pattern
        :param normalizationMode (optional): when type is 'VALUES_LIST', 'VALUES_MAPPING' or 'PATTERN', the normalization
            mode to use for value matching. One of 'EXACT', 'LOWERCASE', or 'NORMALIZED' (not available
            for 'PATTERN' type). Defaults to 'EXACT'.
        :param detectable (optional): whether DSS should consider assigning the meaning to columns set to 'Auto-detect'. Defaults to False.

        :returns: A :class:`dataikuapi.dss.meaning.DSSMeaning` meaning handle
        """
        resp = self._perform_text(
               "POST", "/meanings/", body={
                    "id" : id,
                    "label": label,
                    "type": type,
                    "description": description,
                    "values": values,
                    "mappings": mappings,
                    "pattern": pattern,
                    "normalizationMode": normalizationMode,
                    "detectable": detectable
               })
        return DSSMeaning(self, id)

    ########################################################
    # Logs
    ########################################################

    def list_logs(self):
        """
        List all available log files on the DSS instance
        This call requires an API key with admin rights

        :returns: A list of log names
        """
        return self._perform_json(
            "GET", "/admin/logs/")

    def get_log(self, name):
        """
        Get the contents of a specific log file
        This call requires an API key with admin rights
        
        :param str name: the name of the desired log file (obtained with :meth:`list_logs`)
        :returns: The full content of the log file, as a string
        """
        return self._perform_json(
            "GET", "/admin/logs/%s" % name)

    ########################################################
    # Variables
    ########################################################

    def get_variables(self):
        """
        Get the DSS instance's variables, as a Python dictionary

        This call requires an API key with admin rights
        
        :returns: a Python dictionary of the instance-level variables
        """
        return self._perform_json(
            "GET", "/admin/variables/")

    def set_variables(self, variables):
        """
        Updates the DSS instance's variables

        This call requires an API key with admin rights

        It is not possible to update a single variable, you must set all of them at once. Thus, you 
        should only use a ``variables`` parameter that has been obtained using :meth:`get_variables`.

        :param dict variables: the new dictionary of all variables of the instance

        """
        return self._perform_empty(
            "PUT", "/admin/variables/", body=variables)


    ########################################################
    # General settings
    ########################################################

    def get_general_settings(self):
        """
        Gets a handle to interact with the general settings.

        This call requires an API key with admin rights

        :returns: a :class:`dataikuapi.dss.admin.DSSGeneralSettings` handle
        """
        return DSSGeneralSettings(self)


    ########################################################
    # Bundles / Import (Automation node)
    ########################################################

    def create_project_from_bundle_local_archive(self, archive_path):
        return self._perform_json("POST",
                "/projectsFromBundle/fromArchive",
                 params = { "archivePath" : osp.abspath(archive_path) })

    def create_project_from_bundle_archive(self, fp):
        files = {'file': fp }
        return self._perform_json("POST",
                "/projectsFromBundle/", files=files)


    def prepare_project_import(self, f):
        """
        Prepares import of a project archive

        :param file-like fp: the input stream, as a file-like object
        :returns: a :class:`TemporaryImportHandle` to interact with the prepared import
        """
        val = self._perform_json_upload(
                "POST", "/projects/import/upload",
                "tmp-import.zip", f)
        return TemporaryImportHandle(self, val.json()["id"])

    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        try:
            http_res = self._session.request(
                    method, "%s/dip/publicapi%s" % (self.host, path),
                    params=params, data=body,
                    files = files,
                    stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body)

    def _perform_text(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body).text

    def _perform_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body).json()

    def _perform_raw(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body)

    def _perform_json_upload(self, method, path, name, f):
        try:
            http_res = self._session.request(
                    method, "%s/dip/publicapi%s" % (self.host, path),
                    files = {'file': (name, f, {'Expires': '0'})} )
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))


class TemporaryImportHandle(object):
    def __init__(self, client, import_id):
        self.client = client
        self.import_id = import_id

    def execute(self, settings = {}):
        """
        Executes the import with provided settings.
        @warning: You must check the 'success' flag
        """
        # Empty JSON dicts can't be parsed properly
        if settings == {}:
            settings["_"] = "_"
        return self.client._perform_json("POST", "/projects/import/%s/process" % (self.import_id),
            body = settings)
