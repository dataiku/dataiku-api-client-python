import json, warnings
import sys

if sys.version_info >= (3,0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote

from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
from .iam.settings import DSSSSOSettings, DSSLDAPSettings, DSSAzureADSettings

from .dss.data_collection import DSSDataCollection, DSSDataCollectionListItem
from .dss.feature_store import DSSFeatureStore
from .dss.notebook import DSSNotebook
from .dss.future import DSSFuture
from .dss.projectfolder import DSSProjectFolder
from .dss.project import DSSProject
from .dss.app import DSSApp, DSSAppListItem
from .dss.plugin import DSSPlugin
from .dss.admin import DSSGlobalApiKeyListItem, DSSPersonalApiKeyListItem, DSSUser, DSSUserActivity, DSSOwnUser, DSSGroup, DSSConnection, DSSConnectionListItem, DSSGeneralSettings, DSSCodeEnv, DSSGlobalApiKey, DSSCluster, DSSCodeStudioTemplate, DSSCodeStudioTemplateListItem, DSSGlobalUsageSummary, DSSInstanceVariables, DSSPersonalApiKey, DSSAuthorizationMatrix, DSSLLMCostLimitingCounters
from .dss.messaging_channel import DSSMailMessagingChannel, DSSMessagingChannelListItem, DSSMessagingChannel, SMTPMessagingChannelCreator, AWSSESMailMessagingChannelCreator, MicrosoftGraphMailMessagingChannelCreator, SlackMessagingChannelCreator, MSTeamsMessagingChannelCreator, GoogleChatMessagingChannelCreator, TwilioMessagingChannelCreator, ShellMessagingChannelCreator
from .dss.meaning import DSSMeaning
from .dss.sqlquery import DSSSQLQuery
from .dss.discussion import DSSObjectDiscussions
from .dss.apideployer import DSSAPIDeployer
from .dss.projectdeployer import DSSProjectDeployer
from .dss.unifiedmonitoring import DSSUnifiedMonitoring
from .dss.utils import DSSInfoMessages, Enum
from .dss.workspace import DSSWorkspace
import os.path as osp
from .utils import dku_basestring_type, handle_http_exception
from .govern_client import GovernClient


class DSSClient(object):
    """Entry point for the DSS API client"""

    def __init__(self, host, api_key=None, internal_ticket=None, extra_headers=None, no_check_certificate=False, client_certificate=None, **kwargs):
        """Initialize a new DSS API client.

        Args:
            host (str): The host URL of the DSS instance (e.g., "http://localhost:11200")
            api_key (str, optional): API key for authentication. Can be managed in DSS project page or global settings.
            internal_ticket (str, optional): Internal ticket for authentication.
            extra_headers (dict, optional): Additional HTTP headers to include in requests.
            no_check_certificate (bool, optional): If True, disables SSL certificate verification. 
                Defaults to False.
            client_certificate (str or tuple, optional): Path to client certificate file or tuple of (cert, key) paths.
            **kwargs: Additional keyword arguments. Note: 'insecure_tls' is deprecated in favor of no_check_certificate.

        Note:
            The API key determines which operations are allowed for the client.
            If no_check_certificate is True, SSL certificate verification will be disabled.
            If client_certificate is provided, it will be used for client certificate authentication.
        """
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate

        self.api_key = api_key
        self.internal_ticket = internal_ticket
        self.host = host
        self._session = Session()
        if no_check_certificate:
            self._session.verify = False
        if client_certificate:
            self._session.cert = client_certificate
            
        if self.api_key is not None:
            self._session.auth = HTTPBasicAuth(self.api_key, "")
        elif self.internal_ticket is not None:
            self._session.headers.update({"X-DKU-APITicket" : self.internal_ticket})
        else:
            raise ValueError("API Key is required")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    ########################################################
    # Futures
    ########################################################

    def list_futures(self, as_objects=False, all_users=False):
        """
        List the currently-running long tasks (a.k.a futures)

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.future.DSSFuture`
        :param boolean all_users: if True, returns futures for all users (requires admin privileges). Else, only returns futures for the user associated with the current authentication context (if any)

        :return: list of futures. if as_objects is True, each future in the list is a :class:`dataikuapi.dss.future.DSSFuture`. Else, each future in the list is a dict. Each dict contains at least a 'jobId' field
        :rtype: list of :class:`dataikuapi.dss.future.DSSFuture` or list of dict
        """
        list = self._perform_json("GET", "/futures/", params={"withScenarios":False, "withNotScenarios":True, 'allUsers' : all_users})
        if as_objects:
            return [DSSFuture(self, state['jobId'], state) for state in list]
        else:
            return list

    def list_running_scenarios(self, all_users=False):
        """
        List the running scenarios

        :param boolean all_users: if True, returns scenarios for all users (requires admin privileges). Else, only returns scenarios for the user associated with the current authentication context (if any)

        :return: list of running scenarios, each one as a dict containing at least a "jobId" field for the
            future hosting the scenario run, and a "payload" field with scenario identifiers
        :rtype: list of dicts
        """
        return self._perform_json("GET", "/futures/", params={"withScenarios":True, "withNotScenarios":False, 'allUsers' : all_users})

    def get_future(self, job_id):
        """
        Get a handle to interact with a specific long task (a.k.a future). This notably allows aborting this future.

        :param str job_id: the identifier of the desired future (which can be returned by :py:meth:`list_futures` or :py:meth:`list_running_scenarios`)
        :returns: A handle to interact the future
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return DSSFuture(self, job_id)


    ########################################################
    # Notebooks
    ########################################################

    def list_running_notebooks(self, as_objects=True):
        """
        List the currently-running Jupyter notebooks

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.notebook.DSSNotebook`

        :return: list of notebooks. if as_objects is True, each entry in the list is a :class:`dataikuapi.dss.notebook.DSSNotebook`. Else, each item in the list is a dict which contains at least a "name" field.
        :rtype: list of :class:`dataikuapi.dss.notebook.DSSNotebook` or list of dict
        """
        notebook_list = self._perform_json("GET", "/admin/notebooks/")
        if as_objects:
            return [DSSNotebook(self, notebook['projectKey'], notebook['name'], notebook) for notebook in notebook_list]
        else:
            return notebook_list

    ########################################################
    # Project folders
    ########################################################
    def get_root_project_folder(self):
        """
        Get a handle to interact with the root project folder.

        :returns: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder` to interact with this project folder
        """
        return self.get_project_folder("ROOT")

    def get_project_folder(self, project_folder_id):
        """
        Get a handle to interact with a project folder.

        :param str project_folder_id: the project folder ID of the desired project folder
        :returns: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder` to interact with this project folder
        """
        data = self._perform_json("GET", "/project-folders/%s" % project_folder_id)
        return DSSProjectFolder(self, data)

    ########################################################
    # Projects
    ########################################################

    def list_project_keys(self):
        """
        List the project keys (=project identifiers).

        :returns: list of project keys identifiers, as strings
        :rtype: list of strings
        """
        return [x["projectKey"] for x in self._perform_json("GET", "/projects/")]

    def list_projects(self):
        """
        List the projects

        :returns: a list of projects, each as a dict. Each dictcontains at least a 'projectKey' field
        :rtype: list of dicts
        """
        return self._perform_json("GET", "/projects/")

    def get_project(self, project_key):
        """
        Get a handle to interact with a specific project.

        :param str project_key: the project key of the desired project
        :returns: A :class:`dataikuapi.dss.project.DSSProject` to interact with this project
        """
        return DSSProject(self, project_key)

    def get_default_project(self):
        """
        Get a handle to the current default project, if available (i.e. if dataiku.default_project_key() is valid)
        """
        import dataiku
        return DSSProject(self, dataiku.default_project_key())

    def create_project(self, project_key, name, owner, description=None, settings=None, project_folder_id=None):
        """
        Creates a new project, and return a project handle to interact with it.

        Note: this call requires an API key with admin rights or the rights to create a project

        :param str project_key: the identifier to use for the project. Must be globally unique
        :param str name: the display name for the project.
        :param str owner: the login of the owner of the project.
        :param str description: a description for the project.
        :param dict settings: Initial settings for the project (can be modified later). The exact possible settings are not documented.
        :param str project_folder_id: the project folder ID in which the project will be created (root project folder if not specified)

        :returns: A :class:`dataikuapi.dss.project.DSSProject` project handle to interact with this project
        """
        params = {}
        if project_folder_id is not None:
            params["projectFolderId"] = project_folder_id
        resp = self._perform_text(
               "POST", "/projects/", body={
                   "projectKey" : project_key,
                   "name" : name,
                   "owner" : owner,
                   "settings" : settings,
                   "description" : description
               }, params=params)
        return DSSProject(self, project_key)

    ########################################################
    # Apps
    ########################################################

    def list_apps(self, as_type="listitems"):
        """
        List the apps.

        :param str as_type: How to return the list. Supported values are "listitems" and "objects" (defaults to **listitems**).

        :returns: The list of the apps. If "as_type" is "listitems", each one as a :class:`dataikuapi.dss.app.DSSAppListItem`.
                  If "as_type" is "objects", each one as a :class:`dataikuapi.dss.app.DSSApp`
        :rtype: list
        """
        items = self._perform_json("GET", "/apps/")
        if as_type == "listitems" or as_type == "listitem":
            return [DSSAppListItem(self, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSApp(self, item["appId"]) for item in items]
        else:
            raise ValueError("Unknown as_type")

    def get_app(self, app_id):
        """
        Get a handle to interact with a specific app.

        .. note::

            If a project XXXX is an app template, the identifier of the associated app is PROJECT_XXXX

        :param str app_id: the id of the desired app
        :returns: A :class:`dataikuapi.dss.app.DSSApp` to interact with this project
        """
        return DSSApp(self, app_id)

    ########################################################
    # Plugins
    ########################################################

    def list_plugins(self):
        """
        List the installed plugins

        :returns: list of dict. Each dict contains at least a 'id' field
        """
        return self._perform_json("GET", "/plugins/")

    def download_plugin_stream(self, plugin_id):
        """
        Download a development plugin, as a binary stream
        :param str plugin_id: identifier of the plugin to download

        :param plugin_id:
        :return: the binary stream
        """
        return self._perform_raw("GET", "/plugins/%s/download" % plugin_id)

    def download_plugin_to_file(self, plugin_id, path):
        """
        Download a development plugin to a file

        :param str plugin_id: identifier of the plugin to download
        :param str path: the path where to download the plugin
        :return: None
        """
        stream = self.download_plugin_stream(plugin_id)
        with open(path, 'wb') as f:
            for chunk in stream.iter_content(chunk_size=10000):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def install_plugin_from_archive(self, fp):
        """
        Install a plugin from a plugin archive (as a file object)

        :param object fp: A file-like object pointing to a plugin archive zip
        """
        files = {'file': fp }
        self._perform_json("POST", "/plugins/actions/installFromZip", files=files)

    def start_install_plugin_from_archive(self, fp):
        """
        Install a plugin from a plugin archive (as a file object)
        Returns immediately with a future representing the process done asycnhronously

        :param object fp: A file-like object pointing to a plugin archive zip
        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the install process
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        files = {'file': fp }
        f = self._perform_json("POST", "/plugins/actions/future/installFromZip", files=files)
        return DSSFuture.from_resp(self, f)

    def install_plugin_from_store(self, plugin_id):
        """
        Install a plugin from the Dataiku plugin store

        :param str plugin_id: identifier of the plugin to install
        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the install process
        """
        f = self._perform_json("POST", "/plugins/actions/installFromStore", body={
            "pluginId": plugin_id
        })
        return DSSFuture.from_resp(self, f)

    def install_plugin_from_git(self, repository_url, checkout = "master", subpath=None):
        """
        Install a plugin from a Git repository. DSS must be setup to allow access to the repository.

        :param str repository_url: URL of a Git remote
        :param str checkout: branch/tag/SHA1 to commit. For example "master"
        :param str subpath: Optional, path within the repository to use as plugin. Should contain a 'plugin.json' file
        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the install process
        """
        f = self._perform_json("POST", "/plugins/actions/installFromGit", body={
            "gitRepositoryUrl": repository_url,
            "gitCheckout" : checkout,
            "gitSubpath": subpath
        })
        return DSSFuture.from_resp(self, f)

    def get_plugin(self, plugin_id):
        """
        Get a handle to interact with a specific plugin

        :param str plugin_id: the identifier of the desired plugin
        :returns: A :class:`dataikuapi.dss.project.DSSPlugin`
        """
        return DSSPlugin(self, plugin_id)

    ########################################################
    # SQL queries
    ########################################################

    def sql_query(self, query, connection=None, database=None, dataset_full_name=None, pre_queries=None, post_queries=None, type='sql', extra_conf=None, script_steps=None, script_input_schema=None, script_output_schema=None, script_report_location=None, read_timestamp_without_timezone_as_string=True, read_date_as_string=False, project_key=None, datetimenotz_read_mode="AS_IS", dateonly_read_mode="AS_IS"):
        """
        Initiate a SQL, Hive or Impala query and get a handle to retrieve the results of the query.

        Internally, the query is run by DSS. The  database to run the query on is specified either by
        passing a connection name, or by passing a database name, or by passing a dataset full name
        (whose connection is then used to retrieve the database)

        :param str query: the query to run
        :param str connection: the connection on which the query should be run (exclusive of database and dataset_full_name)
        :param str database: the database on which the query should be run (exclusive of connection and dataset_full_name)
        :param str dataset_full_name: the dataset on the connection of which the query should be run (exclusive of connection and database)
        :param list pre_queries: (optional) array of queries to run before the query
        :param list post_queries: (optional) array of queries to run after the query
        :param str type: the type of query : either 'sql', 'hive' or 'impala' (default: sql)
        :param str project_key: The project_key on which the query should be run (especially useful for user isolation/impersonation scenario)
        :param str datetimenotz_read_mode: if set to 'AS_IS', read SQL data types that map to the 'datetime no tz' DSS type as such. If set
                                          to 'AS_STRING', read them as strings, straight from the database (ie: conversion to string is
                                          done by the database, according to its own settings). If set to 'AS_DATE', read them as the DSS 'datetime with tz'
                                          type, in the UTC timezone. Default 'AS_IS'
        :param str dateonly_read_mode: if set to 'AS_IS', read SQL data types that map to the 'date only' DSS type as such. If set
                                          to 'AS_STRING', read them as strings, straight from the database. If set to 'AS_DATE', read them as the
                                          DSS 'datetime with tz' type, in the UTC timezone. Default 'AS_IS'

        :return: a handle on the SQL query
        :rtype: :class:`dataikuapi.dss.sqlquery.DSSSQLQuery`
        """
        if extra_conf is None:
            extra_conf = {}
        return DSSSQLQuery(self, query, connection, database, dataset_full_name, pre_queries, post_queries, type, extra_conf, script_steps, script_input_schema, script_output_schema, script_report_location, read_timestamp_without_timezone_as_string, read_date_as_string, datetimenotz_read_mode, dateonly_read_mode, project_key)

    ########################################################
    # Users
    ########################################################

    def list_users(self, as_objects=False):
        """
        List all users setup on the DSS instance

        Note: this call requires an API key with admin rights

        :return: A list of users, as a list of :class:`dataikuapi.dss.admin.DSSUser` if as_objects is True, else as a list of dicts
        :rtype: list of :class:`dataikuapi.dss.admin.DSSUser` or list of dicts
        """
        users = self._perform_json("GET", "/admin/users/")

        if as_objects:
            return [DSSUser(self, user["login"]) for user in users]
        else:
            return users

    def get_user(self, login):
        """
        Get a handle to interact with a specific user

        :param str login: the login of the desired user

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        return DSSUser(self, login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=None, profile='DATA_SCIENTIST', email=None):
        """
        Create a user, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str login: the login of the new user
        :param str password: the password of the new user
        :param str display_name: the displayed name for the new user
        :param str source_type: the type of new user. Admissible values are 'LOCAL' or 'LDAP'
        :param list groups: the names of the groups the new user belongs to (defaults to `[]`)
        :param str profile: The profile for the new user. Typical values (depend on your license): FULL_DESIGNER, DATA_DESIGNER, AI_CONSUMER, ...
        :param str email: The email for the new user.

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        if groups is None:
            groups = []
        resp = self._perform_text(
               "POST", "/admin/users/", body={
                   "login" : login,
                   "password" : password,
                   "displayName" : display_name,
                   "sourceType" : source_type,
                   "groups" : groups,
                   "userProfile" : profile,
                   "email": email
               })
        return DSSUser(self, login)

    def get_own_user(self):
        return DSSOwnUser(self)

    def list_users_activity(self, enabled_users_only=False):
        """
        List all users activity

        Note: this call requires an API key with admin rights

        :return: A list of user activity logs, as a list of :class:`dataikuapi.dss.admin.DSSUserActivity` if as_objects is True, else as a list of dict
        :rtype: list of :class:`dataikuapi.dss.admin.DSSUserActivity` or a list of dict
        """
        params = {
            "enabledUsersOnly": enabled_users_only
        }
        all_activity = self._perform_json("GET", "/admin/users-activity", params=params)

        return [DSSUserActivity(self, user_activity["login"], user_activity) for user_activity in all_activity]

    def list_expired_trial_users(self):
        """
        List users whose trials have expired
        :return: A list of users
        """
        users = self._perform_json("GET", "/admin/list-trial-expired-users")
        return users

    def get_authorization_matrix(self):
        """
        Get the authorization matrix for all enabled users and groups

        Note: this call requires an API key with admin rights

        :return: The authorization matrix
        :rtype: A :class:`dataikuapi.dss.admin.DSSAuthorizationMatrix` authorization matrix handle
        """
        resp = self._perform_json("GET", "/admin/authorization-matrix")
        return DSSAuthorizationMatrix(resp)

    def start_resync_users_from_supplier(self, logins):
        """
        Starts a resync of multiple users from an external supplier (LDAP, Azure AD or custom auth)

        :param list logins: list of logins to resync
        :return: a :class:`dataikuapi.dss.future.DSSFuture` representing the sync process
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/resync-multi", body=logins)
        return DSSFuture.from_resp(self, future_resp)

    def start_resync_all_users_from_supplier(self):
        """
        Starts a resync of all users from an external supplier (LDAP, Azure AD or custom auth)

        :return: a :class:`dataikuapi.dss.future.DSSFuture` representing the sync process
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/resync-multi")
        return DSSFuture.from_resp(self, future_resp)

    def start_fetch_external_groups(self, user_source_type):
        """
        Fetch groups from external source

        :param user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        :return: a DSSFuture containing a list of group names
        """
        future_resp = self._perform_json("GET", "/admin/external-groups", params={'userSourceType': user_source_type})
        return DSSFuture.from_resp(self, future_resp)

    def start_fetch_external_users(self, user_source_type, login=None, email=None, group_name=None):
        """
        Fetch users from external source filtered by login or group name:
         - if login or email is provided, will search for a user with an exact match in the external source (e.g. before login remapping)
         - else,
            - if group_name is provided, will search for members of the group in the external source
            - else will search for all users

        :param user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :param login: optional - the login of the user in the external source
        :param email: optional - the email of the user in the external source
        :param group_name: optional - the group name of the group in the external source
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        :return: a DSSFuture containing a list of ExternalUser
        """
        future_resp = self._perform_json("GET", "/admin/external-users", params={'userSourceType': user_source_type, 'login': login, 'email': email, 'groupName': group_name})
        return DSSFuture.from_resp(self, future_resp)

    def start_provision_users(self, user_source_type, users):
        """
        Provision users of given source type

        :param string user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :param list users: list of user attributes coming form the external source
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/provision", body={'userSourceType': user_source_type, 'users': users})
        return DSSFuture.from_resp(self, future_resp)

    ########################################################
    # Groups
    ########################################################

    def list_groups(self):
        """
        List all groups setup on the DSS instance

        Note: this call requires an API key with admin rights

        :returns: A list of groups, as an list of dicts
        :rtype: list of dicts
        """
        return self._perform_json(
            "GET", "/admin/groups/")

    def get_group(self, name):
        """
        Get a handle to interact with a specific group

        :param str name: the name of the desired group
        :returns: A :class:`dataikuapi.dss.admin.DSSGroup` group handle
        """
        return DSSGroup(self, name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Create a group, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str name: the name of the new group
        :param str description: (optional) a description of the new group
        :param source_type: the type of the new group. Admissible values are 'LOCAL' and 'LDAP'

        :returns: A :class:`dataikuapi.dss.admin.DSSGroup` group handle
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

    def list_connections(self, as_type="dictitems"):
        """
        List all connections setup on the DSS instance.

        .. note::

            This call requires an API key with admin rights

        :param string as_type: how to return the connection. Possible values are "dictitems", "listitems" and "objects"

        :return: if **as_type** is dictitems, a dict of connection name to :class:`dataikuapi.dss.admin.DSSConnectionListItem`.
                 if **as_type** is listitems, a list of :class:`dataikuapi.dss.admin.DSSConnectionListItem`.
                 if **as_type** is objects, a list of :class:`dataikuapi.dss.admin.DSSConnection`.

        :rtype: dict or list
        """
        items_dict = self._perform_json(
            "GET", "/admin/connections/")

        if as_type == "dictitems" or as_type == "dictitem":
            return {name:DSSConnectionListItem(self, items_dict[name]) for name in items_dict.keys()}
        if as_type == "listitems" or as_type == "listitem":
            return [DSSConnectionListItem(self, items_dict[name]) for name in items_dict.keys()]
        elif as_type == "objects" or as_type == "object":
            return [DSSConnection(self, name) for name in items_dict.keys()]
        else:
            raise ValueError("Unknown as_type")

    def list_connections_names(self, connection_type):
        """
        List all connections names on the DSS instance.

        :param str connection_type: Returns only connections with this type. Use 'all' if you don't want to filter.

        :return: the list of connections names
        :rtype: List[str]
        """
        return self._perform_json("GET", "/connections/get-names", params={"type": connection_type})

    def get_connection(self, name):
        """
        Get a handle to interact with a specific connection

        :param str name: the name of the desired connection
        :returns: A :class:`dataikuapi.dss.admin.DSSConnection` connection handle
        """
        return DSSConnection(self, name)

    def create_connection(self, name, type, params=None, usable_by='ALL', allowed_groups=None):
        """
        Create a connection, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param name: the name of the new connection
        :param type: the type of the new connection
        :param dict params: the parameters of the new connection, as a JSON object (defaults to `{}`)
        :param usable_by: the type of access control for the connection. Either 'ALL' (=no access control)
            or 'ALLOWED' (=access restricted to users of a list of groups)
        :param list allowed_groups: when using access control (that is, setting usable_by='ALLOWED'), the list
            of names of the groups whose users are allowed to use the new connection (defaults to `[]`)

        :returns: A :class:`dataikuapi.dss.admin.DSSConnection` connection handle
        """
        if params is None:
            params = {}
        if allowed_groups is None:
            allowed_groups = []
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

    def list_code_envs(self, as_objects=False):
        """
        List all code envs setup on the DSS instance

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.future.DSSCodeEnv`
        :returns: a list of code envs. Each code env is a dict containing at least "name", "type" and "language"
        """
        list = self._perform_json(
            "GET", "/admin/code-envs/")
        if as_objects:
            return [DSSCodeEnv(self, e.get("envLang"), e.get("envName")) for e in list]
        else:
            return list

    def get_code_env(self, env_lang, env_name):
        """
        Get a handle to interact with a specific code env

        :param env_lang: the language (PYTHON or R) of the new code env
        :param env_name: the name of the new code env
        :returns: A :class:`dataikuapi.dss.admin.DSSCodeEnv` code env  handle
        """
        return DSSCodeEnv(self, env_lang, env_name)

    def create_internal_code_env(self, internal_env_type, python_interpreter=None, code_env_version=None):
        """
        Create a Python internal code environment, and return a handle to interact with it.

        Note: this call requires an API key with `Create code envs` or `Manage all code envs` permission

        Example:

        .. code-block:: python

            env_handle = client.create_internal_code_env(internal_env_type="RAG_CODE_ENV", python_interpreter="PYTHON310")

        :param str internal_env_type: the internal env type, can be `DEEP_HUB_IMAGE_CLASSIFICATION_CODE_ENV`, `DEEP_HUB_IMAGE_OBJECT_DETECTION_CODE_ENV`, `PROXY_MODELS_CODE_ENV`, `DATABRICKS_UTILS_CODE_ENV`, `PII_DETECTION_CODE_ENV`, `HUGGINGFACE_LOCAL_CODE_ENV` or `RAG_CODE_ENV`.
        :param str python_interpreter: Python interpreter version, can be `PYTHON39`, `PYTHON310`, `PYTHON311` or `PYTHON312`. If None, DSS will try to select a supported & available interpreter.
        :param str code_env_version: Version of the code env. Reserved for future use.
        :returns: A :class:`dataikuapi.dss.admin.DSSCodeEnv` code env handle
        """
        request_params = {
            'dssInternalCodeEnvType': internal_env_type,
            'pythonInterpreter': python_interpreter,
            'codeEnvVersion': code_env_version,
        }

        response = self._perform_json("POST", "/admin/code-envs/internal-env/create", params=request_params)

        if response is None:
            raise Exception('Env creation returned no data')
        if response.get('messages', {}).get('error', False):
            raise Exception('Env creation failed : %s' % (json.dumps(response.get('messages', {}).get('messages', {}))))

        return DSSCodeEnv(self, "python", response["envName"])

    def create_code_env(self, env_lang, env_name, deployment_mode, params=None):
        """
        Create a code env, and return a handle to interact with it

        Note: this call requires an API key with `Create code envs` or `Manage all code envs` permission

        :param env_lang: the language (PYTHON or R) of the new code env
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

    def list_code_env_usages(self):
        """
        List all usages of a code env in the instance

        :return: a list of objects where the code env is used
        """
        return self._perform_json("GET", "/admin/code-envs/usages")

    def create_code_env_from_python_preset(self, preset_name, allow_update=True, interpreter=None, prefix=None):
        request_params = {
            'allowUpdate': allow_update,
            'interpreter': interpreter,
            'prefix': prefix
        }
        return self._perform_json("POST", "/admin/code-envs/from-python-preset/%s" % (preset_name), params=request_params)

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

    def create_cluster(self, cluster_name, cluster_type='manual', params=None, cluster_architecture='HADOOP'):
        """
        Create a cluster, and return a handle to interact with it

        :param cluster_name: the name of the new cluster
        :param cluster_type: the type of the new cluster
        :param params: the parameters of the new cluster, as a JSON object
        :param cluster_architecture: the architecture of the new cluster. 'HADOOP' or 'KUBERNETES'

        :returns: A :class:`dataikuapi.dss.admin.DSSCluster` cluster handle

        """
        definition = {}
        definition['name'] = cluster_name
        definition['type'] = cluster_type
        definition['architecture'] = cluster_architecture
        definition['params'] = params if params is not None else {}
        resp = self._perform_json(
               "POST", "/admin/clusters/", body=definition)
        if resp is None:
            raise Exception('Cluster creation returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster creation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return DSSCluster(self, resp['id'])


    ########################################################
    # Code studio templates
    ########################################################

    def list_code_studio_templates(self, as_type='listitems'):
        """
        List all code studio templates on the DSS instance

        :returns: List of templates (name, type)
        """
        items = self._perform_json("GET", "/admin/code-studios/")
        if as_type == "listitems" or as_type == "listitem":
            return [DSSCodeStudioTemplateListItem(self, item) for item in items]
        elif as_type == "objects" or as_type == "object":
            return [DSSCodeStudioTemplate(self, item["id"]) for item in items]
        else:
            raise ValueError("Unknown as_type")

    def get_code_studio_template(self, template_id):
        """
        Get a handle to interact with a specific code studio template

        :param str template_id: the template id of the desired code studio template

        :returns: A :class:`dataikuapi.dss.admin.DSSCodeStudioTemplate` code studio template handle
        """
        return DSSCodeStudioTemplate(self, template_id)


    ########################################################
    # Global API Keys
    ########################################################

    def list_global_api_keys(self, as_type='listitems'):
        """
        List all global API keys set up on the DSS instance

        .. note::

            This call requires an API key with admin rights

        .. note::

            If the secure API keys feature is enabled, the secret key of the listed
            API keys will not be present in the returned objects

        :param str as_type: How to return the global API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSGlobalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSGlobalApiKey`.
        """
        resp = self._perform_json(
            "GET", "/admin/global-api-keys/")

        if as_type == "listitems":
            return [DSSGlobalApiKeyListItem(self, item) for item in resp]
        elif as_type == 'objects':
            return [DSSGlobalApiKey(self, item["key"], item["id"]) for item in resp]
        else:
            raise ValueError("Unknown as_type")

    def get_global_api_key(self, key):
        """
        Get a handle to interact with a specific Global API key

        .. deprecated:: 13.0.0
            Use :meth:`DSSClient.get_global_api_key_by_id`. Calling this method with an invalid secret key
            will now result in an immediate error.

        :param str key: the secret key of the API key
        :returns: A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "GET", "/admin/globalAPIKeys/%s" % key)
        return DSSGlobalApiKey(self, key, resp['id'])

    def get_global_api_key_by_id(self, id_):
        """
        Get a handle to interact with a specific Global API key

        :param str id_: the id the API key
        :returns: A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "GET", "/admin/global-api-keys/%s" % id_)
        return DSSGlobalApiKey(self, resp["key"], id_)

    def create_global_api_key(self, label=None, description=None, admin=False):
        """
        Create a Global API key, and return a handle to interact with it

        .. note::

            This call requires an API key with admin rights

        .. note::

            The secret key of the created API key will always be present in the returned object,
            even if the secure API keys feature is enabled

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param boolean admin: has the new API key admin rights (True or False)

        :returns: A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "POST", "/admin/global-api-keys/", body={
                "label": label,
                "description": description,
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
        return DSSGlobalApiKey(self, resp.get('key', ''), resp['id'])

    ########################################################
    # Personal API Keys
    ########################################################

    def list_personal_api_keys(self, as_type='listitems'):
        """
        List all your personal API keys.

        :param str as_type: How to return the personal API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSPersonalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        resp = self._perform_json(
            "GET", "/personal-api-keys/")

        if as_type == "listitems":
            return [DSSPersonalApiKeyListItem(self, item) for item in resp]
        elif as_type == 'objects':
            return [DSSPersonalApiKey(self, item.get('key', ''), item['id']) for item in resp]
        else:
            raise ValueError("Unknown as_type")

    def get_personal_api_key(self, id):
        """
        Get a handle to interact with a specific Personal API key.

        :param str id: the id of the desired API key

        :returns: A :class:`dataikuapi.dss.admin.DSSPersonalApiKey` API key handle
        """
        return DSSPersonalApiKey(self, "", id)

    def create_personal_api_key(self, label="", description="", as_type='dict'):
        """
        Create a Personal API key associated with your user.

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param str as_type: How to return the personal API keys. Possible values are "dict" and "object"

        :return: if as_type=dict, the new personal API key is returned as a dict.
                 if as_type=object, the new personal API key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        resp = self._perform_json(
            "POST", "/personal-api-keys/", body={"label": label, "description": description})
        if resp is None:
            raise Exception('API key creation returned no data')
        if not resp.get('id', False):
            raise Exception('API key creation returned no key')

        if as_type == 'object':
            return DSSPersonalApiKey(self, resp.get('key', ''), resp["id"])
        else:
            return resp

    def list_all_personal_api_keys(self, as_type='listitems'):
        """
        List all personal API keys.
        Only admin can list all the keys.

        :param str as_type: How to return the personal API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSPersonalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        resp = self._perform_json(
            "GET", "/admin/personal-api-keys/")
        if as_type == "listitems":
            return [DSSPersonalApiKeyListItem(self, item) for item in resp]
        elif as_type == 'objects':
            return [DSSPersonalApiKey(self, item.get('key', ''), item['id']) for item in resp]
        else:
            raise ValueError("Unknown as_type")

    def create_personal_api_key_for_user(self, user, label="", description="", as_type='object'):
        """
        Create a Personal API key associated on behalf of a user.
        Only admin can create a key for another user.

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param str user: the id of the user to impersonate
        :param str as_type: How to return the personal API keys. Possible values are "dict" and "object"

        :return: if as_type=dict, the new personal API key is returned as a dict.
                 if as_type=object, the new personal API key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        resp = self._perform_json(
            "POST", "/admin/personal-api-keys/", body={"user": user, "label": label, "description": description})
        if resp is None:
            raise Exception('API key creation returned no data')
        if not resp.get('id', False):
            raise Exception('API key creation returned no key')

        if as_type == 'object':
            return DSSPersonalApiKey(self, resp.get('key', ''), resp["id"])
        else:
            return resp

    ########################################################
    # Meanings
    ########################################################

    def list_meanings(self):
        """
        List all user-defined meanings on the DSS instance

        Note: this call requires an API key with admin rights

        :returns: A list of meanings. Each meaning is a dict
        :rtype: list of dicts
        """
        return self._perform_json(
            "GET", "/meanings/")

    def get_meaning(self, id):
        """
        Get a handle to interact with a specific user-defined meaning

        Note: this call requires an API key with admin rights

        :param str id: the ID of the desired meaning
        :returns: A :class:`dataikuapi.dss.meaning.DSSMeaning` meaning  handle
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
        :param values (optional): when type is 'VALUES_LIST', the list of values, or a list of {'value':'the value', 'color':'an optional color'}
        :param mappings (optional): when type is 'VALUES_MAPPING', the mapping, as a list of objects with this
            structure: {'from': 'value_1', 'to': 'value_a'}
        :param pattern (optional): when type is 'PATTERN', the pattern
        :param normalizationMode (optional): when type is 'VALUES_LIST', 'VALUES_MAPPING' or 'PATTERN', the normalization
            mode to use for value matching. One of 'EXACT', 'LOWERCASE', or 'NORMALIZED' (not available
            for 'PATTERN' type). Defaults to 'EXACT'.
        :param detectable (optional): whether DSS should consider assigning the meaning to columns set to 'Auto-detect'. Defaults to False.

        :returns: A :class:`dataikuapi.dss.meaning.DSSMeaning` meaning handle
        """
        def make_entry(v):
            if isinstance(v, dku_basestring_type):
                return {'value':v}
            else:
                return v
        def make_mapping(v):
            return {'from':v.get('from', None), 'to':make_entry(v.get('to', None))}
        entries = None
        if values is not None:
            entries = [make_entry(v) for v in values]
        if mappings is not None:
            mappings = [make_mapping(v) for v in mappings]
        resp = self._perform_text(
               "POST", "/meanings/", body={
                    "id" : id,
                    "label": label,
                    "type": type,
                    "description": description,
                    "entries": entries,
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

        :returns: A list of log file names
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

    def log_custom_audit(self, custom_type, custom_params=None):
        """
        Log a custom entry to the audit trail

        :param str custom_type: value for customMsgType in audit trail item
        :param dict custom_params: value for customMsgParams in audit trail item (defaults to `{}`)
        """
        if custom_params is None:
            custom_params = {}
        return self._perform_empty("POST",
            "/admin/audit/custom/%s" % custom_type,
            body = custom_params)

    ########################################################
    # Monitoring
    ########################################################

    def get_global_usage_summary(self, with_per_project=False):
        """
        Gets a summary of the global usage of this DSS instance (number of projects, datasets, ...)
        :returns: a summary object
        """
        data = self._perform_json(
            "GET", "/admin/monitoring/global-usage-summary", params={'withPerProject':with_per_project})
        return DSSGlobalUsageSummary(data)

   ########################################################
    # Variables
    ########################################################

    def get_variables(self):
        """
        Deprecated. Use :meth:`get_global_variables`
        """
        warnings.warn("get_variables is deprecated, please use get_global_variables", DeprecationWarning)
        return self.get_global_variables()

    def get_global_variables(self):
        """
        Get the DSS instance's variables, as a Python dictionary

        This call requires an API key with admin rights

        :returns: A :class:`dataikuapi.dss.admin.DSSInstanceVariables` handle
        """
        variables = self._perform_json("GET", "/admin/variables/")
        return DSSInstanceVariables(self, variables)

    def set_variables(self, variables):
        """
        Deprecated. Use :meth:`get_global_variables` and :meth:`dataikuapi.dss.admin.DSSInstanceVariables.save`

        Updates the DSS instance's variables

        This call requires an API key with admin rights

        It is not possible to update a single variable, you must set all of them at once. Thus, you
        should only use a ``variables`` parameter that has been obtained using :meth:`get_variables`.

        :param dict variables: the new dictionary of all variables of the instance

        """
        warnings.warn("set_variables is deprecated, please use get_global_variables().save()", DeprecationWarning)
        return DSSInstanceVariables(self, variables).save()

    def get_resolved_variables(self, project_key=None, typed=False):
        """
        Get a dictionary of resolved variables of the project.

        :param str project_key: the project key, defaults to the current project if any
        :param bool typed: if True, the variable values will be typed in the returned dict, defaults to False
        :returns: a dictionary with instance and project variables merged
        """
        import dataiku
        return self._perform_json(
            "GET",
            "/projects/%s/variables-resolved" % (dataiku.default_project_key() if project_key is None else project_key),
            params={
                "typed": "true" if typed else "false"
            })


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

    class PermissionsPropagationPolicy(Enum):
        NONE = "NONE"
        READ_ONLY = "READ_ONLY"
        ALL = "ALL"

    def create_project_from_bundle_local_archive(self, archive_path, project_folder=None, permissions_propagation_policy=PermissionsPropagationPolicy.NONE):
        """
        Create a project from a bundle archive.
        Warning: this method can only be used on an automation node.

        :param string archive_path: Path on the local machine where the archive is
        :param project_folder: the project folder in which the project will be created or None for root project folder
        :type project_folder: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        :param permissions_propagation_policy: propagate the permissions that were set in the design node to the new project on the automation node (default: False)
        :type permissions_propagation_policy: A :class:`PermissionsPropagationPolicy`
        """
        if isinstance(permissions_propagation_policy, DSSClient.PermissionsPropagationPolicy):
            permissions_propagation_policy = permissions_propagation_policy.value
        params = {
            "archivePath": osp.abspath(archive_path),
            "permissionsPropagationPolicy": permissions_propagation_policy,
        }
        if project_folder is not None:
            params["projectFolderId"] = project_folder.project_folder_id
        return self._perform_json("POST", "/projectsFromBundle/fromArchive", params=params)

    def create_project_from_bundle_archive(self, fp, project_folder=None):
        """
        Create a project from a bundle archive (as a file object)
        Warning: this method can only be used on an automation node.

        :param string fp: A file-like object pointing to a bundle archive zip
        :param project_folder: the project folder in which the project will be created or None for root project folder
        :type project_folder: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        params = {}
        if project_folder is not None:
            params['projectFolderId'] = project_folder.project_folder_id
        files = {'file': fp }
        return self._perform_json("POST",
                "/projectsFromBundle/", files=files, params=params)

    def prepare_project_import(self, f):
        """
        Prepares import of a project archive.
        Warning: this method can only be used on a design node.

        :param file-like fp: the input stream, as a file-like object
        :returns: a :class:`TemporaryImportHandle` to interact with the prepared import
        """
        val = self._perform_json_upload(
                "POST", "/projects/import/upload",
                "tmp-import.zip", f)
        return TemporaryImportHandle(self, val.json()["id"])

    ########################################################
    # API Deployer
    ########################################################

    def get_apideployer(self):
        """Gets a handle to work with the API Deployer

        :rtype: :class:`~dataikuapi.dss.apideployer.DSSAPIDeployer`
        """
        return DSSAPIDeployer(self)

    ########################################################
    # Project Deployer
    ########################################################

    def get_projectdeployer(self):
        """Gets a handle to work with the Project Deployer

        :rtype: :class:`~dataikuapi.dss.projectdeployer.DSSProjectDeployer`
        """
        return DSSProjectDeployer(self)

    ########################################################
    # Unified Monitoring
    ########################################################

    def get_unified_monitoring(self):
        """Gets a handle to work with Unified Monitoring

        :rtype: :class:`~dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring`
        """
        return DSSUnifiedMonitoring(self)

    ########################################################
    # Data Catalog
    ########################################################

    def catalog_index_connections(self, connection_names=None, all_connections=False, indexing_mode="FULL"):
        """
        Triggers an indexing of multiple connections in the data catalog

        :param list connection_names: list of connections to index, ignored if `all_connections=True` (defaults to `[]`)
        :param bool all_connections: index all connections (defaults to `False`)
        """
        if connection_names is None:
            connection_names = []
        return self._perform_json("POST", "/catalog/index", body={
            "connectionNames": connection_names,
            "indexAllConnections": all_connections,
            "indexingMode": indexing_mode
        })

    ########################################################
    # Model export
    ########################################################
    def get_scoring_libs_stream(self):
        """
        Get the scoring libraries jar required for scoring with model jars that don't include libraries.
        You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :returns: a jar file, as a stream
        :rtype: file-like
        """
        return self._perform_raw("GET", "/resources/scoring-lib-jar")

    ########################################################
    # Auth
    ########################################################

    def get_auth_info(self, with_secrets=False):
        """
        Returns various information about the user currently authenticated using
        this instance of the API client.

        This method returns a dict that may contain the following keys (may also contain others):

        * authIdentifier: login for a user, id for an API key
        * groups: list of group names (if  context is an user)
        * secrets: list of dicts containing user secrets (if context is an user)

        :param: with_secrets boolean: Return user secrets
        :returns: a dict
        :rtype: dict
        """
        return self._perform_json("GET", "/auth/info", params={"withSecrets": with_secrets})

    def get_auth_info_from_browser_headers(self, headers_dict, with_secrets=False):
        """
        Returns various information about the DSS user authenticated by the dictionary of
        HTTP headers provided in headers_dict.

        This is generally only used in webapp backends

        This method returns a dict that may contain the following keys (may also contain others):

        * authIdentifier: login for a user, id for an API key
        * groups: list of group names (if  context is an user)
        * secrets: list of dicts containing user secrets (if context is an user)

        :param: headers_dict dict: Dictionary of HTTP headers
        :param: with_secrets boolean: Return user secrets
        :returns: a dict
        :rtype: dict
        """
        return self._perform_json("POST", "/auth/info-from-browser-headers",
                params={"withSecrets": with_secrets}, body=headers_dict)

    def get_ticket_from_browser_headers(self, headers_dict):
         """
         Returns a ticket for the DSS user authenticated by the dictionary of
         HTTP headers provided in headers_dict.

         This is only used in webapp backends

         This method returns a ticket to use as a X-DKU-APITicket header

         :param: headers_dict dict: Dictionary of HTTP headers
         :returns: a string
         :rtype: string
         """
         return self._perform_json("POST", "/auth/ticket-from-browser-headers", body=headers_dict)


    ########################################################
    # Container execution
    ########################################################

    def push_base_images(self):
        """
        Push base images for Kubernetes container-execution and Spark-on-Kubernetes
        """
        resp = self._perform_json("POST", "/admin/container-exec/actions/push-base-images")
        return DSSFuture.from_resp(self, resp)

    def apply_kubernetes_namespaces_policies(self):
        """
        Apply Kubernetes namespaces policies defined in the general settings
        """
        resp = self._perform_json("POST", "/admin/container-exec/actions/apply-kubernetes-policies")
        return DSSFuture.from_resp(self, resp)

    def build_cde_plugins_image(self):
        """
        Build and Push the image for containerized dss engine (CDE) with plugins
        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the build process
        """
        resp = self._perform_json("POST", "/admin/container-exec/actions/build-cde-plugins-image")
        return DSSFuture.from_resp(self, resp)


    ########################################################
    # Global Instance Info
    ########################################################

    def get_instance_info(self):
        """
        Get global information about the DSS instance

        :returns: a :class:`DSSInstanceInfo`
        """
        resp = self._perform_json("GET", "/instance-info")
        return DSSInstanceInfo(resp)

    ########################################################
    # Instance Sanity Check
    ########################################################

    def perform_instance_sanity_check(self, exclusion_list=[], wait=True):
        """
        Run an Instance Sanity Check.

        This call requires an API key with admin rights.

        :param exclusion_list: a string list of codes to exclude in the sanity check, as returned by :meth:`get_sanity_check_codes`
        :return: a :class:`dataikuapi.dss.utils.DSSInfoMessages` if `wait` is `True`, or a :class:`dataikuapi.dss.future.DSSFuture` handle otherwise
        :rtype: :class:`dataikuapi.dss.utils.DSSInfoMessages` or :class:`dataikuapi.dss.future.DSSFuture`
        """
        resp = self._perform_json("POST", "/admin/sanity-check/run", body=exclusion_list)
        future = DSSFuture.from_resp(self, resp, result_wrapper=DSSInfoMessages)
        if wait:
            return future.wait_for_result()
        else:
            return future

    def get_sanity_check_codes(self):
        """
        Return the list of codes that can be generated by the sanity check.

        This call requires an API key with admin rights.

        :rtype: list[str]
        """
        return self._perform_json("GET", "/admin/sanity-check/codes")

    ########################################################
    # Licensing
    ########################################################

    def get_licensing_status(self):
        """
        Returns a dictionary with information about licensing status of this DSS instance

        :rtype: dict
        """
        return self._perform_json("GET", "/admin/licensing/status")

    def set_license(self, license):
        """
        Sets a new licence for DSS

        :param license: license (content of license file)
        :return: None
        """
        self._perform_empty(
            "POST", "/admin/licensing/license", body=json.loads(license))

    ########################################################
    # Govern
    ########################################################

    def get_govern_client(self):
        """
        Return the Govern Client handle corresponding to the Dataiku Govern integration settigns, or None if not enabled or misconfigured.

        This call requires an API key with admin rights.

        :return: a Dataiku Govern client handle or None if not enabled or misconfigured
        :rtype: :class:`dataikuapi.GovernClient` or None
        """
        resp = self._perform_json("GET", "/admin/get-govern-node-ref")
        if resp.get('enabled', False) is False or resp.get('nodeUrl', None) is None or resp.get('apiKey', None) is None:
            return None
        else:
            return GovernClient(resp['nodeUrl'], resp['apiKey'], no_check_certificate=resp.get('trustAllSSLCertificates', False))


    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None, headers=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        #logging.info("Request with headers=%s" % headers)

        http_res = self._session.request(
                method, "%s/dip/publicapi%s" % (self.host, path),
                params=params, data=body,
                files=files,
                stream=stream,
                headers=headers)
        handle_http_exception(http_res)
        return http_res

    def _perform_empty(self, method, path, params=None, body=None, files = None, raw_body=None, headers=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers)

    def _perform_text(self, method, path, params=None, body=None,files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).text

    def _perform_json(self, method, path, params=None, body=None,files=None, raw_body=None, headers=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).json()

    def _perform_raw(self, method, path, params=None, body=None,files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body, headers=headers)

    def _perform_json_upload(self, method, path, name, f):
        http_res = self._session.request(
            method, "%s/dip/publicapi%s" % (self.host, path),
            files = {'file': (name, f, {'Expires': '0'})} )

        handle_http_exception(http_res)
        return http_res

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self, project_key, object_type, object_id):
        """
        Get a handle to manage discussions on any object

        :param str project_key: identifier of the project to access
        :param str object_type: DSS object type
        :param str object_id: DSS object ID
        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self, project_key, object_type, object_id)

    ########################################################
    # Feature Store
    ########################################################
    def get_feature_store(self):
        """
        Get a handle to interact with the Feature Store.

        :return: a handle on the feature store
        :rtype: :class:`dataikuapi.feature_store.DSSFeatureStore`
        """
        return DSSFeatureStore(self)

    ########################################################
    # Workspaces
    ########################################################

    def list_workspaces(self, as_objects=False):
        """
        List the workspaces

        :returns: The list of workspaces.
        """
        items = self._perform_json("GET", "/workspaces/")
        if as_objects:
            return [DSSWorkspace(self, item["workspaceKey"]) for item in items]
        else:
            return items

    def get_workspace(self, workspace_key):
        """
        Get a handle to interact with a specific workspace

        :param str workspace_key: the workspace key of the desired workspace
        :returns: A :class:`dataikuapi.dss.workspace.DSSWorkspace` to interact with this workspace
        """
        return DSSWorkspace(self, workspace_key)

    def create_workspace(self, workspace_key, name, permissions=None, description=None, color=None):
        """
        Create a new workspace and return a workspace handle to interact with it

        :param str workspace_key: the identifier to use for the workspace. Must be globally unique
        :param str name: the display name for the workspace.
        :param [`dataikuapi.dss.workspace.DSSWorkspacePermissionItem`] permissions: Initial permissions for the workspace (can be modified later).
        :param str description: a description for the workspace.
        :param str color: The color to use (#RRGGBB format). A random color will be assigned if not specified

        :returns: A :class:`dataikuapi.dss.workspace.DSSWorkspace` workspace handle to interact with this workspace
        """
        resp = self._perform_text("POST", "/workspaces/", body={
            "workspaceKey": workspace_key,
            "displayName": name,
            "color": color,
            "description": description,
            "permissions": permissions
        })
        return DSSWorkspace(self, workspace_key)

    ########################################################
    # Data Collections
    ########################################################

    def list_data_collections(self, as_type="listitems"):
        """
        List the accessible data collections

        :param str as_type: How to return the list. Supported values are "listitems", "objects" and "dict" (defaults to **listitems**).
        :returns: The list of data collections.
        :rtype: a list of :class:`dataikuapi.dss.data_collection.DSSDataCollectionListItem` if as_type is "listitems",
            a list of :class:`dataikuapi.dss.data_collection.DSSDataCollection` if as_type is "objects",
            a list of dict if as_type is "dict"
        """
        items = self._perform_json("GET", "/data-collections/")
        if as_type == "listitems" or as_type == "listitem":
            return [DSSDataCollectionListItem(self, item) for item in items]
        if as_type == "objects" or as_type == "object":
            return [DSSDataCollection(self, item["id"]) for item in items]
        else:
            return items

    def get_data_collection(self, id):
        """
        Get a handle to interact with a specific data collection

        :param str id: the id of the data collection to fetch
        :rtype: :class:`dataikuapi.dss.data_collection.DSSDataCollection`
        """
        return DSSDataCollection(self, id)

    def create_data_collection(self, displayName, id=None, tags=None, description=None, color=None, permissions=None):
        """
        Create a new data collection and return a handle to interact with it

        :param str displayName: the display name for the data collection.
        :param str id: the identifier to use for the data_collection. Must be 8 alphanumerical characters if set, otherwise a random id will be generated.
        :param tags: The list of tags to use (defaults to *[]*)
        :type tags: list of str
        :param str description: a description for the data collection
        :param str color: The color to use (#RRGGBB format). A random color will be assigned if not specified
        :param permissions: Initial permissions for the data collection (can be modified later - current user will always be added as admin).
        :type permissions: a list of :class:`dict`

        :returns: Handle of the newly created Data Collection
        :rtype: :class:`dataikuapi.dss.data_collection.DSSDataCollection`
        """
        res = self._perform_json("POST", "/data-collections/", body={
            "id": id,
            "tags": tags if tags is not None else [],
            "displayName": displayName,
            "color": color,
            "description": description,
            "permissions": permissions
        })
        return DSSDataCollection(self, res['id'])

    ########################################################
    # Integration Channels
    ########################################################

    def _map_channel_to_object_type(self, channel):
        if 'mail' == channel.get("family", None):
            return DSSMailMessagingChannel(self, channel)
        else:
            return DSSMessagingChannel(self, channel)

    def get_messaging_channel(self, channel_id):
        """
        Get the messaging channel with the corresponding ID

        :param channel_id: ID of channel as specified Notifications & Integrations UI
        :return: A messaging channel object, such as :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannel`, or a :class:`dataikuapi.dss.messaging_channel.DSSMailMessagingChannel` for a mail channel
        """
        channel = self._perform_json('GET', '/messaging-channels/%s' % channel_id)
        return self._map_channel_to_object_type(channel)

    def list_messaging_channels(self, as_type="listitems", channel_type=None, channel_family=None):
        """
        List all available messaging channels

        :param str as_type: How to return the list. Supported values are "listitems" and "objects" (defaults to **listitems**).
        :param str channel_type: a channel type to filter by, e.g. "smtp", "aws-ses-mail", "slack" (see :meth:`DSSClient.create_messaging_channel` for the full list of supported types)
        :param str channel_family: a str to filter for family of channels with a similar interface - "mail" for all channels that send email-like messages
        :return: A list of messaging channels after the filtering specified, as listitems (:class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelListItem`) or objects (:class:`dataikuapi.dss.messaging_channel.DSSMessagingChannel` or :class:`dataikuapi.dss.messaging_channel.DSSMailMessagingChannel`)
        """
        query_string = ""
        if channel_type is not None:
            query_string = "?channelType=" + dku_quote_fn(channel_type)
        if channel_family is not None:
            query_string += "?" if query_string == "" else "&"
            query_string += "channelFamily=" + dku_quote_fn(channel_family)

        channels = self._perform_json('GET', '/messaging-channels/%s' % query_string)
        if as_type == "listitems" or as_type == "listitem":
            return [DSSMessagingChannelListItem(self, channel) for channel in channels]
        if as_type == "objects" or as_type == "object":
            return [self._map_channel_to_object_type(channel) for channel in channels]
        else:
            raise ValueError("Unknown as_type")


    def new_messaging_channel(self, type):
        """
        Initializes the creation of a new messaging channel. Returns a :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelCreator`
        or one of its subclasses to complete the creation of the messaging channel. The creation requires admin privileges.

        :param str type: Type of the messaging channel. Can be of one the following: "smtp", "aws-ses-mail", "microsoft-graph-mail", "slack", "msft-teams", "google-chat", "twilio" or "shell".
        :returns: A new DSS Messaging Channel Creator handle
        :rtype: :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelCreator`

        Usage example:

        .. code-block:: python

            smtp_messaging_channel_creator = client.new_messaging_channel("smtp")
            smtp_messaging_channel_creator.with_channel_id("Some ID")
            smtp_messaging_channel_creator.with_sender("email@example.com")
            smtp_messaging_channel_creator.with_authorized_domains(["example.com", "example.org", "something.example.com"])
            smtp_messaging_channel_creator.with_login("username")
            smtp_messaging_channel_creator.with_password("password")
            smtp_messaging_channel_creator.with_host("host.example.com")
            smtp_messaging_channel_creator.with_port(443)
            smtp_messaging_channel_creator.with_session_properties([{ "key": "key1", "value": "value1" }, { "key": "key2", "value": "value2" }])
            smtp_messaging_channel = smtp_messaging_channel_creator.create()
        """
        if type == "smtp":
            return SMTPMessagingChannelCreator(self)
        elif type == "aws-ses-mail":
            return AWSSESMailMessagingChannelCreator(self)
        elif type == "microsoft-graph-mail":
            return MicrosoftGraphMailMessagingChannelCreator(self)
        elif type == "slack":
            return SlackMessagingChannelCreator(self)
        elif type == "msft-teams":
            return MSTeamsMessagingChannelCreator(self)
        elif type == "google-chat":
            return GoogleChatMessagingChannelCreator(self)
        elif type == "twilio":
            return TwilioMessagingChannelCreator(self)
        elif type == "shell":
            return ShellMessagingChannelCreator(self)
        else:
            raise ValueError("Unknown type")

    def create_messaging_channel(self, channel_type, channel_id=None, channel_configuration=None):
        """
        Create a messaging channel. Requires admin privileges.

        We strongly recommend that you use the creator helpers instead of calling this directly. See :meth:`DSSClient.new_messaging_channel`.

        :param str channel_type: type of the channel type. Can be of one the following: "smtp", "aws-ses-mail", "microsoft-graph-mail", "slack", "msft-teams", "google-chat", "twilio" or "shell".
        :param str channel_id: optional ID of the channel, must be unique. If None or empty a random ID will be generated.
        :param dict channel_configuration: optional specific configuration for the channel depending on the channel type. Every configuration entry is optional but not provided some may lead to a non-functional messaging channel.

            - "smtp", "aws-ses-mail", "microsoft-graph-mail":
                - "useCurrentUserAsSender": True to use the email of the user triggering the action as sender, False otherwise. Has precedence over 'sender' property;
                - "sender": sender email, use an adhoc provided email if not provided;
                - "authorizedDomain": comma-separated list of authorized domains for "To" addresses;
                - "useSSL": True to use SSL, False otherwise;
                - "useTLS": True to use TLS, False otherwise;
                - "login": user login;
                - "password": user password;
                - "host": host to connect to;
                - "port": port to connect to;
                - "sessionProperties": Array of dictionaries with "key" and "value" keys set for session extra properties;
                - Additional for "aws-ses-mail":
                    - "accessKey": AWS access key;
                    - "secretKey": AWS secret key;
                    - "regionOrEndpoint": AWS region or custom endpoint.
                - Additional for "microsoft-graph-mail":
                    - "clientId": Microsoft application ID;
                    - "tenantId": Microsoft directory ID;
                    - "clientSecret": Account used to sent mails with this channel. Must be a User Principal Name with a valid Microsoft 365 license.
            - "slack":
                - "useProxy": True to use DSS's proxy settings to connect, False otherwise;
                - "mode": connection mode. Can be "WEBHOOK" or "API";
                - "webhookUrl": webhook URL for "WEBHOOK" mode;
                - "authorizationToken": authorization token for "API" mode;
                - "channel": Slack channel ID.
            - "msft-teams":
                - "useProxy": True to use DSS's proxy settings to connect, False otherwise;
                - "webhookUrl": webhook URL;
                - "webhookType": type of webhook to use. Can be "WORKFLOWS" or "OFFICE365" (legacy).
            - "google-chat":
                - "useProxy": True to use DSS's proxy settings to connect, False otherwise;
                - "webhookUrl": webhook URL;
                - "webhookKey": key parameter for the webhook URL (mandatory if not included in the URL);
                - "webhookToken": token parameter for the webhook URL (mandatory if not included in the URL).
            - "twilio":
                - "useProxy": True to use DSS's proxy settings to connect, False otherwise;
                - "accountSid": Twilio account SID;
                - "authToken": authorization token;
                - "fromNumber": Twilio from number.
            - "shell":
                - "type": Type of shell execution. Can be "COMMAND" or "FILE";
                - "command": command to execute. In "FILE" mode this string will pass to the `-c` switch;
                - "script": script content to execute for mode "FILE".

        Usage example:

        .. code-block:: python

            channel_type = "smtp"
            channel_id = "Some ID"
            sender = "email@example.com"
            authorized_domains = ["example.com", "example.org", "something.example.com"]
            login = "username"
            password = "password"
            host = "host.example.com"
            port = 587
            session_properties = [{ "key": "key1", "value": "value1" }, { "key": "key2", "value": "value2" }]
            channel_params = {
                "useCurrentUserAsSender": False,
                "sender": sender,
                "authorizedDomain": ",".join(authorized_domains),
                "useSSL": True,
                "useTLS": True,
                "login": login,
                "password": password,
                "host": host,
                "port": port,
                "sessionProperties": session_properties
            }
            client.create_messaging_channel(channel_type, channel_id, channel_params)

        :return: The created messaging channel object, such as :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannel`, or a :class:`dataikuapi.dss.messaging_channel.DSSMailMessagingChannel` for a mail channel
        """
        return self._map_channel_to_object_type(self._perform_json(
            "POST",
            "/messaging-channels/",
            body = {
                "id": channel_id if channel_id else "",
                "type": channel_type,
                "configuration": channel_configuration if channel_configuration else {}
            }
        ))

    ########################################################
    # Data Quality
    ########################################################
    
    def get_data_quality_status(self):
        """
        Get the status of data-quality monitored projects, including the count of monitored datasets in Ok/Warning/Error/Empty statuses.

        :returns: The dict of data quality monitored project statuses.
        :rtype: dict with PROJECT_KEY as key
        """
        return self._perform_json("GET", "/data-quality/status")
    
    ########################################################
    # IAM
    ########################################################

    def get_sso_settings(self):
        """
        Get the Single Sign-On (SSO) settings

        :return: SSO settings
        :rtype: :class:`dataikuapi.iam.settings.SSOSettings`
        """
        sso = self._perform_json("GET", "/admin/iam/sso-settings")
        return DSSSSOSettings(self, sso)

    def get_ldap_settings(self):
        """
        Get the LDAP settings

        :return: LDAP settings
        :rtype: :class:`dataikuapi.iam.settings.LDAPSettings`
        """
        ldap = self._perform_json("GET", "/admin/iam/ldap-settings")
        return DSSLDAPSettings(self, ldap)

    def get_azure_ad_settings(self):
        """
        Get the Azure Active Directory (aka Microsoft Entra ID) settings

        :return: Azure AD settings
        :rtype: :class:`dataikuapi.iam.settings.AzureADSettings`
        """
        ldap = self._perform_json("GET", "/admin/iam/azure-ad-settings")
        return DSSAzureADSettings(self, ldap)

    ########################################################
    # LLM Cost limiting
    ########################################################

    def get_llm_cost_limiting_counters(self):
        """
        Gets the LLM cost limiting counters of the instance

        :return: the cost limiting counters
        :rtype: DSSLLMCostLimitingCounters
        """
        return DSSLLMCostLimitingCounters(self._perform_json("GET", "/admin/llm-cost-limiting/counters"))

class TemporaryImportHandle(object):
    def __init__(self, client, import_id):
        self.client = client
        self.import_id = import_id

    def execute(self, settings=None):
        """
        Executes the import with provided settings.

        :param dict settings: Dict of import settings (defaults to `{}`). The following settings are available:

            * targetProjectKey (string): Key to import under. Defaults to the original project key
            * remapping (dict): Dictionary of connection and code env remapping settings.

                See example of remapping dict:

                .. code-block:: python

                    "remapping" : {
                      "connections": [
                        { "source": "src_conn1", "target": "target_conn1" },
                        { "source": "src_conn2", "target": "target_conn2" }
                      ],
                      "codeEnvs" : [
                        { "source": "src_codeenv1", "target": "target_codeenv1" },
                        { "source": "src_codeenv2", "target": "target_codeenv2" }
                      ]
                    }

        @warning: You must check the 'success' flag
        """
        # Empty JSON dicts can't be parsed properly
        if settings is None:
            settings = {}
        if settings == {}:
            settings["_"] = "_"
        return self.client._perform_json("POST", "/projects/import/%s/process" % (self.import_id),
            body = settings)

class DSSInstanceInfo(object):
    """Global information about the DSS instance"""

    def __init__(self, data):
        """Do not call this directly, use :meth:`DSSClient.get_instance_info`"""
        self._data = data

    @property
    def raw(self):
        """Returns all data as a Python dictionary"""
        return self._data

    @property
    def node_id(self):
        """Returns the node id (as defined in Cloud Stacks or in install.ini)"""
        return self._data["nodeId"]

    @property
    def node_name(self):
        """Returns the node name as it appears in the navigation bar"""
        return self._data["nodeName"]

    @property
    def node_type(self):
        """
        Returns the node type
        :return: One of DESIGN, AUTOMATION or DEPLOYER
        """
        return self._data["nodeType"]
