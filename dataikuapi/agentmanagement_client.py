import json
import warnings
from datetime import datetime, timedelta, timezone

from requests import Session
from requests.auth import HTTPBasicAuth
from .utils import dku_basestring_type, handle_http_exception
from .agentmanagement.metrics import BucketedMetricsFetchResults
from .agentmanagement._utils import dku_quote_fn, _to_timestamp_ms, _format_list
from .agentmanagement.agent import AgentFilter, Agent, AgentListItem
from .agentmanagement.risk import EstateRiskExposure, RiskTaxonomySettings
from .agentmanagement.operations import OperationSearchResult, Operation
from .agentmanagement.platform import Platform, PlatformListItem
from .agentmanagement.alerting import AlertConfiguration, AlertConfigurationListItem, MetricAlertConfigurationBuilder, TriggeredAlertSearchResult, Alert
from .agentmanagement.settings import Settings
from .agentmanagement.topic_family import TopicFamily, TopicFamilyListItem
from .agentmanagement.cobuild import CobuildConversation


def _consolidate_metric_chunks(chunks):
    series = []
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for index, chunk in enumerate(chunks):
        time_columns = [i for i, column in enumerate(chunk["columns"]) if column in ("timestamp", "start", "end")]
        for row in chunk.get("rows", []):
            for i in time_columns:
                if row[i] is not None:
                    row[i] = epoch + timedelta(milliseconds=row[i])
        chunks[index] = None
        if (series
                and series[-1].get("infrastructureName") == chunk.get("infrastructureName")
                and series[-1].get("agentId") == chunk.get("agentId")
                and series[-1].get("columns") == chunk.get("columns")):
            rows = chunk.get("rows", [])
            series[-1]["rows"].extend(rows)
            del rows[:]
            chunk.clear()
        else:
            series.append(chunk)
    del chunks[:]
    return series


class AgentManagementClient(object):
    """
    Entry point for the Dataiku Agent Management API client.

    Instance administration methods delegate to :class:`dataikuapi.DSSClient` on the same
    Agent Management instance and return the existing DSS handles. Use :meth:`get_dssclient`
    for projects, datasets, recipes, plugins and code environments.

    Usage example:

    .. code-block:: python

        import dataikuapi

        client = dataikuapi.AgentManagementClient("https://agent-management.example", api_key="your-api-key")
        agent = client.get_agent("my-platform", "my-agent")
        status = agent.get_status()
    """

    def __init__(self, host, api_key=None, internal_ticket=None, extra_headers=None, no_check_certificate=False, client_certificate=None,
                 jwt_bearer_token=None, **kwargs):
        """Initialize a new Agent Management API client.

        Args:
            host (str): The host URL of the Agent Management instance (e.g., "http://localhost:11200")
            api_key (str, optional): API key for authentication
            no_check_certificate (bool, optional): If True, disables SSL certificate verification. Defaults to False.
            extra_headers (dict, optional): Additional HTTP headers to include in requests.
            client_certificate (str or tuple, optional): Path to client certificate file or tuple of (cert, key) paths.
            jwt_bearer_token (str, optional): JWT bearer token for authentication.
        """
        self.api_key = api_key
        self.internal_ticket = internal_ticket
        self.jwt_bearer_token = jwt_bearer_token
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
        elif jwt_bearer_token is not None:
            self._session.headers.update({"Authorization": "Bearer " + jwt_bearer_token})
        else:
            raise ValueError("Authentication is required. You must provide either api_key, internal_ticket or jwt_bearer_token.")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    ########################################################
    # Running tasks
    ########################################################

    def list_futures(self, as_objects=False, all_users=False):
        """
        List the currently-running generic long tasks (a.k.a futures).

        This does not list all Agent Management operations. Use list_operations() for platform and agent operations.

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.future.DSSFuture`
        :param boolean all_users: if True, returns futures for all users (requires admin privileges). Else, only returns futures for the user associated with the current authentication context (if any)

        :return: list of futures. if as_objects is True, each future in the list is a :class:`dataikuapi.dss.future.DSSFuture`. Else, each future in the list is a dict. Each dict contains at least a 'jobId' field
        :rtype: list of :class:`dataikuapi.dss.future.DSSFuture` or list of dict
        """
        return self.get_dssclient().list_futures(as_objects=as_objects, all_users=all_users)

    def get_future(self, job_id):
        """
        Get a handle to interact with a specific long task (a.k.a future). This notably allows aborting this future.

        :param str job_id: the identifier of the desired future (which can be returned by :py:meth:`list_futures`)
        :returns: A handle to interact the future
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return self.get_dssclient().get_future(job_id=job_id)

    ########################################################
    # User and group directories
    ########################################################

    def list_users_info(self):
        """
        Gets basic information about users on the Agent Management instance.

        You do not need to be admin to call this

        :return: A list of users, as a list of :class:`dataikuapi.dss.admin.DSSUserInfo`
        """
        return self.get_dssclient().list_users_info()

    def list_groups_info(self):
        """
        Gets basic information about groups on the Agent Management instance.

        You do not need to be admin to call this

        :return: A list of groups, as a list of :class:`dataikuapi.dss.admin.DSSGroupInfo`
        """
        return self.get_dssclient().list_groups_info()

    ########################################################
    # Users
    ########################################################

    def list_users(self, as_objects=False, include_settings=False):
        """
        List all users setup on the Agent Management instance

        Note: this call requires an API key with admin rights

        :param bool as_objects: Return a list of :class:`dataikuapi.dss.admin.DSSUser` instead of dictionaries. Defaults to False.
        :param bool include_settings: Include detailed user settings in the response. Only useful if as_objects is False. Defaults to False.

        :return: A list of users, as a list of :class:`dataikuapi.dss.admin.DSSUser` if as_objects is True, else as a list of dicts
        :rtype: list of :class:`dataikuapi.dss.admin.DSSUser` or list of dicts
        """
        return self.get_dssclient().list_users(as_objects=as_objects, include_settings=include_settings)

    def get_user(self, login):
        """
        Get a handle to interact with a specific user

        The handle's :meth:`~dataikuapi.dss.admin.DSSUser.get_client_as` method returns
        a :class:`dataikuapi.DSSClient` authenticated as this user on the same AM instance.

        :param str login: the login of the desired user

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        return self.get_dssclient().get_user(login=login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=None, profile='REGULAR_USER', email=None):
        """
        Create a user, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        Note: this call is not available to Dataiku Cloud users

        :param str login: the login of the new user. Must be nonblank.
        :param str password: the password used for 'LOCAL' authentication, subject to the instance's password policy. Ignored for other sources (pass None).
        :param str display_name: the displayed name for the new user. Must be nonblank, despite the default value of ''.
        :param str source_type: the user provisioning source type. Examples include 'LOCAL', 'LOCAL_NO_AUTH', 'LDAP', 'PAM', 'AZURE_AD' and 'CUSTOM'. Defaults to 'LOCAL'.
        :param list groups: the names of the groups the new user belongs to (defaults to `[]`)
        :param str profile: The Agent Management profile of the new user: REGULAR_USER (default) or POWER_USER.
        :param str email: The email for the new user.

        :return: A :class:`dataikuapi.dss.admin.DSSUser` user handle
        """
        return self.get_dssclient().create_user(
            login=login, password=password, display_name=display_name, source_type=source_type,
            groups=groups, profile=profile, email=email)

    def create_users(self, users):
        """
        Create multiple users, and return a list of creation status

        Note: this call requires an API key with admin rights

        Note: this call is not available to Dataiku Cloud users

        :param list users: a list of dictionaries where each dictionary contains the parameters for user creation. It accepts the following keys:

                           - 'login' (str): the login of the new user. Required and must be nonblank.
                           - 'password' (str): used only for 'LOCAL' authentication; subject to the instance's password policy when provided. Ignored for other sources.
                           - 'displayName' (str): the displayed name for the new user. Required and must be nonblank.
                           - 'sourceType' (str): the user provisioning source type. Examples include 'LOCAL', 'LOCAL_NO_AUTH', 'LDAP', 'PAM', 'AZURE_AD' and 'CUSTOM'. Defaults to 'LOCAL'.
                           - 'groups' (list): the names of the groups the new user belongs to. Defaults to []
                           - 'userProfile' (str): The Agent Management profile: REGULAR_USER (default) or POWER_USER.
                           - 'email' (str): The email for the new user. Defaults to None

        :rtype: list[dict]
        :return: A list of dictionaries, where each dictionary represents the creation status of a user. It should contain the following keys:

                 - 'login' (str): the login of the created user
                 - 'status' (str): the creation status of the user. Can be 'SUCCESS' or 'FAILURE'
                 - 'error' (str): the error that occurred during that user's creation. Empty if status is not 'FAILURE'.
        """
        for user in users:
            user.setdefault('userProfile', 'REGULAR_USER')
        return self.get_dssclient().create_users(users=users)

    def edit_users(self, user_changes):
        """
        Edits multiple users in a single bulk operation. This method is very permissive and is intended
        for mass operations. If you are modifying a small number of users, it is advised to get a handle
        from the get_user method and interact directly with a `DSSUser` object.

        A valid workflow is to get the full users dictionaries from `list_users(include_settings=True)`,
        modify them and use this method to apply the modifications.

        Note: This call requires an API key with admin rights.

        Note: this call is not available to Dataiku Cloud users

        :param list[dict] user_changes: A list of dictionaries, where each dictionary defines the
                                        changes for a single user. Each dictionary **must** contain the
                                        'login' key to identify the user. Other keys can be included
                                        to modify the user's properties, matching the structure of a
                                        user settings object (see the output of
                                        `list_users(include_settings=True))`. Available keys include:

                                        - 'login' (str): The login of the user to modify (mandatory). Cannot be modified.
                                        - 'displayName' (str): The user's display name.
                                        - 'email' (str): The user's email address.
                                        - 'groups' (list[str]): The list of groups for the user.
                                        - 'userProfile' (str): The user's Agent Management profile (REGULAR_USER or POWER_USER).
                                        - 'enabled' (bool): Whether the user is enabled.
                                        - 'sourceType': User provisioning source type. Examples include 'LOCAL', 'LOCAL_NO_AUTH', 'LDAP', 'PAM', 'AZURE_AD' and 'CUSTOM'.
                                        - 'adminProperties' (dict): Custom admin properties for the user.
                                        - 'userProperties' (dict): Custom user properties for the user.
                                        - 'secrets' (list): A list of user-specific secrets.
                                        - 'preferences' (dict): A dictionary of user preferences:

                                            - 'uiLanguage' (str): UI language code (e.g., 'en', 'ja', 'fr').
                                            - 'mentionEmails' (bool): Email notifications for mentions.
                                            - 'discussionEmails' (bool): Email notifications for discussions.
                                            - 'accessRequestEmails' (bool): Email notifications for access requests.
                                            - 'grantedAccessEmails' (bool): Email notifications when access is granted.
                                            - 'grantedPluginRequestEmails' (bool): Email notifications when a plugin request is granted.
                                            - 'pluginRequestEmails' (bool): Email notifications for plugin requests.
                                            - 'instanceAccessRequestsEmails' (bool): Email notifications for instance access requests.
                                            - 'profileUpgradeRequestsEmails' (bool): Email notifications for profile upgrade requests.
                                            - 'codeEnvCreationRequestEmails' (bool): Email notifications for code env creation requests.
                                            - 'grantedCodeEnvCreationRequestEmails' (bool): Email notifications when a code env request is granted.
                                            - 'dailyDigestsEmails' (bool): Daily digest emails.
                                            - 'offlineActivityEmails' (bool): Offline activity summary emails.
                                            - 'rememberPositionFlow' (bool): Remember position in the Flow.
                                            - 'loginLogoutNotifications' (bool): Notifications for login/logout.
                                            - 'watchedObjectsEditionsNotifications' (bool): Notifications for edits on watched objects.
                                            - 'objectOnCurrentProjectCreatedDeletedNotifications' (bool): Notifications for object creation/deletion in the current project.
                                            - 'anyObjectOnCurrentProjectEditedNotifications' (bool): Notifications for any object edit in the current project.
                                            - 'watchStarOnCurrentProjectNotifications' (bool): Notifications for watch/star actions in the current project.
                                            - 'otherUsersJobsTasksNotifications' (bool): Notifications for jobs/tasks from other users.
                                            - 'requestAccessNotifications' (bool): Notifications for access requests.
                                            - 'scenarioRunNotifications' (bool): Notifications for scenario runs.

        :rtype: list[dict]
        :return: A list of dictionaries, one for each attempted modification, indicating the status. Each dictionary contains the following keys:

                 - 'login' (str): The login of the user that was modified.
                 - 'status' (str): The result of the operation, either 'SUCCESS' or 'FAILURE'.
                 - 'error' (str): The error message if the status is 'FAILURE', otherwise empty.
        """
        return self.get_dssclient().edit_users(user_changes=user_changes)

    def delete_users(self, user_logins, allow_self_deletion=False):
        """
        Bulk deletes multiple users.

        Note: This call requires an API key with admin rights.

        Note: this call is not available to Dataiku Cloud users

        :param list[str] user_logins: A list of logins for the users to be deleted.
        :param bool allow_self_deletion: Allow the use of this function to delete your own user. Warning: this is very dangerous and used recklessly could lead to the deletion of all users/admins.

        :rtype: list[dict]
        :return: A list of dictionaries, one for each attempted deletion, indicating the status. Each dictionary contains the following keys:

                 - 'login' (str): The login of the user that was deleted.
                 - 'status' (str): The result of the deletion, either 'SUCCESS' or 'FAILURE'.
                 - 'error' (str): The error message if the status is 'FAILURE', otherwise empty.
        """
        return self.get_dssclient().delete_users(user_logins=user_logins, allow_self_deletion=allow_self_deletion)

    def get_own_user(self):
        """
        Get a handle to interact with the current user

        :return: A :class:`dataikuapi.dss.admin.DSSOwnUser` user handle
        """
        return self.get_dssclient().get_own_user()

    def list_users_activity(self, enabled_users_only=False):
        """
        List all users activity

        Note: this call requires an API key with admin rights

        :return: A list of user activity logs, as a list of :class:`dataikuapi.dss.admin.DSSUserActivity`
        :rtype: list of :class:`dataikuapi.dss.admin.DSSUserActivity`
        """
        return self.get_dssclient().list_users_activity(enabled_users_only=enabled_users_only)

    def start_resync_users_from_supplier(self, logins):
        """
        Starts a resync of multiple users from an external supplier (LDAP, Azure AD or custom auth)

        :param list logins: list of logins to resync
        :return: a :class:`dataikuapi.dss.future.DSSFuture` representing the sync process
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return self.get_dssclient().start_resync_users_from_supplier(logins=logins)

    def start_resync_all_users_from_supplier(self):
        """
        Starts a resync of all users from an external supplier (LDAP, Azure AD or custom auth)

        :return: a :class:`dataikuapi.dss.future.DSSFuture` representing the sync process
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return self.get_dssclient().start_resync_all_users_from_supplier()

    def start_fetch_external_groups(self, user_source_type):
        """
        Fetch groups from external source

        :param user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        :return: a DSSFuture containing a list of group names
        """
        return self.get_dssclient().start_fetch_external_groups(user_source_type=user_source_type)

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
        return self.get_dssclient().start_fetch_external_users(
            user_source_type=user_source_type, login=login, email=email, group_name=group_name)

    def start_provision_users(self, user_source_type, users):
        """
        Provision users of given source type

        :param string user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :param list users: list of user attributes coming form the external source
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return self.get_dssclient().start_provision_users(user_source_type=user_source_type, users=users)

    ########################################################
    # Groups
    ########################################################

    def list_groups(self):
        """
        List all groups setup on the Agent Management instance

        Note: this call requires an API key with admin rights

        :returns: A list of groups, as an list of dicts
        :rtype: list of dicts
        """
        return self.get_dssclient().list_groups()

    def get_group(self, name):
        """
        Get a handle to interact with a specific group

        :param str name: the name of the desired group
        :returns: A :class:`dataikuapi.dss.admin.DSSGroup` group handle
        """
        return self.get_dssclient().get_group(name=name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Create a group, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str name: the name of the new group
        :param str description: (optional) a description of the new group
        :param source_type: the type of the new group. Admissible values are 'LOCAL' and 'LDAP'

        :returns: A :class:`dataikuapi.dss.admin.DSSGroup` group handle
        """
        return self.get_dssclient().create_group(name=name, description=description, source_type=source_type)

    ########################################################
    # Connections
    ########################################################

    def list_connections(self, as_type="dictitems"):
        """
        List all connections setup on the Agent Management instance.

        .. note::

            This call requires an API key with admin rights

        :param string as_type: how to return the connection. Possible values are "dictitems", "listitems" and "objects"

        :return: if **as_type** is dictitems, a dict of connection name to :class:`dataikuapi.dss.admin.DSSConnectionListItem`.
                 if **as_type** is listitems, a list of :class:`dataikuapi.dss.admin.DSSConnectionListItem`.
                 if **as_type** is objects, a list of :class:`dataikuapi.dss.admin.DSSConnection`.

        :rtype: dict or list
        """
        return self.get_dssclient().list_connections(as_type=as_type)

    def list_connections_names(self, connection_type):
        """
        List all connections names on the Agent Management instance.

        :param str connection_type: Returns only connections with this type. Use 'all' if you don't want to filter.

        :return: the list of connections names
        :rtype: List[str]
        """
        return self.get_dssclient().list_connections_names(connection_type=connection_type)

    def get_connection(self, name):
        """
        Get a handle to interact with a specific connection

        :param str name: the name of the desired connection
        :returns: A :class:`dataikuapi.dss.admin.DSSConnection` connection handle
        """
        return self.get_dssclient().get_connection(name=name)

    def create_connection(self, name, type, params=None, usable_by='ALL', allowed_groups=None, description=None):
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
        :param str description: (optional) a description of the new connection

        :returns: A :class:`dataikuapi.dss.admin.DSSConnection` connection handle
        """
        return self.get_dssclient().create_connection(
            name=name, type=type, params=params, usable_by=usable_by,
            allowed_groups=allowed_groups, description=description)

    ########################################################
    # Global API keys
    ########################################################

    def list_global_api_keys(self, as_type='listitems'):
        """
        List all global API keys set up on the Agent Management instance

        .. note::

            This call requires an API key with admin rights

        .. note::

            If the secure API keys feature is enabled, the secret key of the listed
            API keys will not be present in the returned objects

        :param str as_type: How to return the global API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSGlobalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSGlobalApiKey`.
        """
        return self.get_dssclient().list_global_api_keys(as_type=as_type)

    def get_global_api_key_by_id(self, id_):
        """
        Get a handle to interact with a specific Global API key

        :param str id_: the id the API key
        :returns: A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        return self.get_dssclient().get_global_api_key_by_id(id_=id_)

    def create_global_api_key(self, label=None, description=None, admin=False):
        """
        Create a Global API key, and return a handle to interact with it.

        Use :meth:`AgentManagementClient.create_global_api_key_with_groups` to create global API keys that use groups
        to manage their permissions.

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
        return self.get_dssclient().create_global_api_key(label=label, description=description, admin=admin)

    def create_global_api_key_with_groups(self, label=None, description=None, groups=None):
        """
        Create a Global API key, and return a handle to interact with it.

        .. note::

            This call requires an API key with admin rights

        .. note::

            The secret key of the created API key will always be present in the returned object,
            even if the secure API keys feature is enabled

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param list groups: the groups the new API key belongs to

        :returns: A :class:`dataikuapi.dss.admin.DSSGlobalApiKey` API key handle
        """
        return self.get_dssclient().create_global_api_key_with_groups(label=label, description=description, groups=groups)

    ########################################################
    # Personal API keys
    ########################################################

    def list_personal_api_keys(self, as_type='listitems'):
        """
        List all your personal API keys.

        :param str as_type: How to return the personal API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSPersonalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        return self.get_dssclient().list_personal_api_keys(as_type=as_type)

    def get_personal_api_key(self, id):
        """
        Get a handle to interact with a specific Personal API key.

        :param str id: the id of the desired API key

        :returns: A :class:`dataikuapi.dss.admin.DSSPersonalApiKey` API key handle
        """
        return self.get_dssclient().get_personal_api_key(id=id)

    def create_personal_api_key(self, label="", description="", as_type='dict'):
        """
        Create a Personal API key associated with your user.

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param str as_type: How to return the personal API keys. Possible values are "dict" and "object"

        :return: if as_type=dict, the new personal API key is returned as a dict.
                 if as_type=object, the new personal API key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        return self.get_dssclient().create_personal_api_key(label=label, description=description, as_type=as_type)

    def list_all_personal_api_keys(self, as_type='listitems'):
        """
        List all personal API keys.
        Only admin can list all the keys.

        :param str as_type: How to return the personal API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.dss.admin.DSSPersonalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.dss.admin.DSSPersonalApiKey`.
        """
        return self.get_dssclient().list_all_personal_api_keys(as_type=as_type)

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
        return self.get_dssclient().create_personal_api_key_for_user(
            user=user, label=label, description=description, as_type=as_type)

    ########################################################
    # Logs and audit
    ########################################################

    def list_logs(self):
        """
        List all available log files on the Agent Management instance
        This call requires an API key with admin rights

        :returns: A list of log file names
        """
        return self.get_dssclient().list_logs()

    def get_log(self, name):
        """
        Get the contents of a specific log file
        This call requires an API key with admin rights

        :param str name: the name of the desired log file (obtained with :meth:`list_logs`)
        :returns: The contents of the log file, limited to the last 1,000 lines
        """
        return self.get_dssclient().get_log(name=name)

    def log_custom_audit(self, custom_type, custom_params=None):
        """
        Log a custom entry to the audit trail

        :param str custom_type: value for customMsgType in audit trail item
        :param dict custom_params: value for customMsgParams in audit trail item (defaults to `{}`)
        """
        return self.get_dssclient().log_custom_audit(custom_type=custom_type, custom_params=custom_params)

    ########################################################
    # Authentication
    ########################################################

    def get_auth_info(self):
        """
        Returns various information about the user currently authenticated using
        this instance of the API client.

        This method returns a dict that may contain the following keys (may also contain others):

        * authIdentifier: login for a user, id for an API key
        * groups: list of group names (if  context is an user)

        :returns: a dict
        :rtype: dict
        """
        return self.get_dssclient().get_auth_info()

    ########################################################
    # Instance information
    ########################################################

    def get_instance_info(self):
        """
        Get global information about the Agent Management instance

        :returns: a :class:`dataikuapi.dssclient.DSSInstanceInfo`
        """
        return self.get_dssclient().get_instance_info()

    ########################################################
    # Licensing
    ########################################################

    def get_licensing_status(self):
        """
        Returns a dictionary with information about licensing status of this Agent Management instance

        :rtype: dict
        """
        return self.get_dssclient().get_licensing_status()

    def set_license(self, license):
        """
        Sets a new licence for the Agent Management instance.

        :param license: license (content of license file)
        :return: None
        """
        return self.get_dssclient().set_license(license=license)

    ########################################################
    # Messaging channels
    ########################################################

    def get_messaging_channel(self, channel_id):
        """
        Get the messaging channel with the corresponding ID

        :param channel_id: ID of channel as specified Notifications & Integrations UI
        :return: A messaging channel object, such as :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannel`, or a :class:`dataikuapi.dss.messaging_channel.DSSMailMessagingChannel` for a mail channel
        """
        return self.get_dssclient().get_messaging_channel(channel_id=channel_id)

    def list_messaging_channels(self, as_type="listitems", channel_type=None, channel_family=None):
        """
        List all available messaging channels

        :param str as_type: How to return the list. Supported values are "listitems" and "objects" (defaults to **listitems**).
        :param str channel_type: a channel type to filter by, e.g. "smtp", "aws-ses-mail", "slack" (see :meth:`AgentManagementClient.create_messaging_channel` for the full list of supported types)
        :param str channel_family: a str to filter for family of channels with a similar interface - "mail" for all channels that send email-like messages
        :return: A list of messaging channels after the filtering specified, as listitems (:class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelListItem`) or objects (:class:`dataikuapi.dss.messaging_channel.DSSMessagingChannel` or :class:`dataikuapi.dss.messaging_channel.DSSMailMessagingChannel`)
        """
        return self.get_dssclient().list_messaging_channels(
            as_type=as_type, channel_type=channel_type, channel_family=channel_family)

    def new_messaging_channel(self, type):
        """
        Initializes the creation of a new messaging channel. Returns a :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelCreator`
        or one of its subclasses to complete the creation of the messaging channel. The creation requires admin privileges.

        :param str type: Type of the messaging channel. Can be one of the following: "smtp", "aws-ses-mail", "microsoft-graph-mail", "slack", "msft-teams" or "google-chat".
        :returns: A new DSS Messaging Channel Creator handle
        :rtype: :class:`dataikuapi.dss.messaging_channel.DSSMessagingChannelCreator`

        Usage example:

        .. code-block:: python

            smtp_messaging_channel_creator = client.new_messaging_channel("smtp")
            smtp_messaging_channel_creator.with_id("Some ID")
            smtp_messaging_channel_creator.with_sender("email@example.com")
            smtp_messaging_channel_creator.with_authorized_domains(["example.com", "example.org", "something.example.com"])
            smtp_messaging_channel_creator.with_login("username")
            smtp_messaging_channel_creator.with_password("password")
            smtp_messaging_channel_creator.with_host("host.example.com")
            smtp_messaging_channel_creator.with_port(443)
            smtp_messaging_channel_creator.with_session_properties([{ "key": "key1", "value": "value1" }, { "key": "key2", "value": "value2" }])
            smtp_messaging_channel = smtp_messaging_channel_creator.create()
        """
        if type in ("twilio", "shell"):
            raise ValueError("Unsupported messaging channel type for Agent Management: %s" % type)
        return self.get_dssclient().new_messaging_channel(type=type)

    def create_messaging_channel(self, channel_type, channel_id=None, channel_configuration=None, permissions=None):
        """
        Create a messaging channel. Requires admin privileges.

        We strongly recommend that you use the creator helpers instead of calling this directly. See :meth:`AgentManagementClient.new_messaging_channel`.

        :param str channel_type: type of the channel. Common types are "smtp", "aws-ses-mail", "microsoft-graph-mail", "slack", "msft-teams" and "google-chat". Twilio and shell channels are not supported by Agent Management.
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
                    - "clientSecret": Microsoft application client secret value.
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

        :param list[dict] permissions: optional list of permissions objects (all users can use the channel if not defined). Can be:

            - { "group": group_id, canUse: True } to authorize a group to use the channel
            - { "user": user_login, canUse: True } to authorize a single user to use the channel

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
        if channel_type in ("twilio", "shell"):
            raise ValueError("Unsupported messaging channel type for Agent Management: %s" % channel_type)
        return self.get_dssclient().create_messaging_channel(
            channel_type=channel_type, channel_id=channel_id,
            channel_configuration=channel_configuration, permissions=permissions)

    ########################################################
    # Identity and access management
    ########################################################

    def get_sso_settings(self):
        """
        Get the Single Sign-On (SSO) settings

        :return: SSO settings
        :rtype: :class:`dataikuapi.iam.settings.SSOSettings`
        """
        return self.get_dssclient().get_sso_settings()

    def get_ldap_settings(self):
        """
        Get the LDAP settings

        :return: LDAP settings
        :rtype: :class:`dataikuapi.iam.settings.LDAPSettings`
        """
        return self.get_dssclient().get_ldap_settings()

    def get_azure_ad_settings(self):
        """
        Get the Azure Active Directory (aka Microsoft Entra ID) settings

        :return: Azure AD settings
        :rtype: :class:`dataikuapi.iam.settings.AzureADSettings`
        """
        return self.get_dssclient().get_azure_ad_settings()

    ########################################################
    # Cobuild
    ########################################################

    def get_cobuild_status(self):
        """
        Returns whether Cobuild is available to the authenticated caller.

        The result contains enabled and, when access is denied, reason.

        :rtype: dict
        """
        return self.get_dssclient().get_cobuild_status()

    def new_cobuild_conversation(self):
        """
        Start a new empty Cobuild conversation in Agent Management.

        Example::

            conversation = client.new_cobuild_conversation()
            response = conversation.send_message("List the agents in my estate")
            print(response.message)

        Pass ``allow_edit=True`` to ``send_message`` or ``approve_plan`` to allow changes
        for that turn. Assistant responses can request a confirmation or an explicit
        answer; continue with ``answer_confirmation`` or ``answer_question`` respectively.

        :rtype: :class:`dataikuapi.agentmanagement.cobuild.CobuildConversation`
        """
        raw = self._perform_json("POST", "/agent-management/cobuild/conversations", body={})
        return CobuildConversation(self, raw["conversationId"])

    def get_settings(self):
        """
        Returns the global Agent Management settings.

        :rtype: :class:`dataikuapi.agentmanagement.settings.Settings`
        """
        settings = self._perform_json("GET", "/agent-management/settings")
        return Settings(self, settings)

    def list_alert_configurations(self, as_type="listitems"):
        """
        Lists alert configurations owned globally, not configurations from other levels.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        path = "/agent-management/alert-configurations"
        configurations = self._perform_json("GET", path)
        return _format_list([AlertConfigurationListItem(self, configuration, path) for configuration in configurations], as_type)

    def new_alert_configuration(self, type="metric", name=None):
        """
        Initializes a new alert configuration builder owned by this client.

        Configure the returned builder, then call its ``create()`` method to submit it.

        :param str type: ``metric``; agent review configurations can only be created on an agent
        :param str name: optional display name
        :rtype: MetricAlertConfigurationBuilder
        """
        if type == "metric":
            return MetricAlertConfigurationBuilder(self, "/agent-management/alert-configurations", name)
        raise ValueError("Unsupported alert configuration type: %r" % (type,))

    def get_alert_configuration(self, configuration_id):
        """
        Returns a handle to an alert configuration owned globally.

        :param str configuration_id: configuration ID
        :rtype: :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        """
        return AlertConfiguration(self, "/agent-management/alert-configurations", configuration_id)

    def list_platforms(self, as_type="listitems"):
        """
        Lists Agent Management platforms.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.platform.Platform`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        platforms = self._perform_json("GET", "/agent-management/platforms")
        return _format_list([PlatformListItem(self, platform) for platform in platforms], as_type)

    def create_platform(self, platform_id, platform_type, display_name, connection_name=None, default_project_key=None,
                     permissions=None, default_agent_permissions=None):
        """
        Creates an Agent Management platform with default settings and returns a handle to it.

        :param str platform_id: unique identifier of the platform
        :param str platform_type: type of platform
        :param str display_name: display name of the platform
        :param str connection_name: platform connection used by the platform (except OpenTelemetryReceiver)
        :param str default_project_key: default DSS project used by the platform
        :param list permissions: platform permissions; the creator is also made an administrator
        :param list default_agent_permissions: default permissions for agents in the platform
        :rtype: :class:`dataikuapi.agentmanagement.platform.Platform`
        """
        body = {
            "id": platform_id,
            "displayName": display_name,
            "defaultProjectKey": default_project_key,
            "type": platform_type,
            "connectionName": connection_name,
            "permissions": permissions or [],
            "defaultAgentPermissions": default_agent_permissions or []
        }
        created = self._perform_json("POST", "/agent-management/platforms", body=body)
        return Platform(self, created["id"])

    def get_platform(self, platform_id):
        """
        Returns a handle to an Agent Management platform.

        :param str platform_id: identifier of the platform
        :rtype: :class:`dataikuapi.agentmanagement.platform.Platform`
        """
        return Platform(self, platform_id)

    def get_agent(self, platform_id, agent_id):
        """
        Returns a handle to an agent.

        :param str platform_id: identifier of the platform
        :param str agent_id: identifier of the agent
        :rtype: :class:`dataikuapi.agentmanagement.agent.Agent`
        """
        return Agent(self, platform_id, agent_id)

    def list_agents(self, as_type="listitems", agent_filter=None):
        """
        Lists readable agents matching an optional filter.

        :param str as_type: "listitems"/"listitem" returns AgentListItem entries; "objects"/"object" returns Agent handles
        :param AgentFilter agent_filter: optional agent selection
        :rtype: list
        """
        agents = self.search_agents(agent_filter=agent_filter)["agents"]
        return _format_list([AgentListItem(self, agent) for agent in agents], as_type)

    def search_agents(self, agent_filter=None):
        """
        Lists the readable agents matching a filter.

        Values of a facet are combined with OR, while different facets are combined with AND.

        :param AgentFilter agent_filter: agent filter
        :returns: a dictionary containing ``agents`` and contextual ``facets`` counts
        :rtype: dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = agent_filter._as_dict() if agent_filter is not None else {}
        return self._perform_json("POST", "/agent-management/agents/search", body=body)

    def evaluate_alerts(self, agent_filter=None, mode="DUE"):
        """
        Queues alert evaluation through the scheduler for editable agents matching a filter,
        whether or not periodic evaluation is enabled. Evaluation errors are logged asynchronously.

        Agents that the caller cannot edit are ignored.

        :param AgentFilter agent_filter: optional agent selection
        :param str mode: ``DUE`` processes pending metric buckets within the catch-up limit.
                         ``FORCE_LATEST`` recomputes the latest completed eligible bucket and
                         corrects its alerts. ``FORCE_CATCH_UP`` does the same for the last N
                         buckets, where N is the configured catch-up depth. Both read additional
                         supporting history when consecutive breaches require it. Affected alerts
                         remain in history as invalidated. Replacements have new IDs, even when
                         recomputed values are unchanged, and do not inherit acknowledgements;
                         these remain on the original alerts. Missing target observations prevent
                         correction of the requested range. Missing older supporting observations
                         also prevent correction when too few consecutive breaches remain to establish the observed severity.
                         Agent-review alerts evaluate the latest eligible review run in every mode.
        :returns: number of agents included in the queued request
        :rtype: int
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        response = self._perform_json("POST", "/agent-management/agents/actions/evaluate-alerts", params={"mode": mode},
                                             body=agent_filter._as_dict() if agent_filter is not None else {})
        return response["queuedAgentCount"]

    def get_available_metric_ids(self, agent_filter=None):
        """
        Lists the metric identifiers supported by readable agents matching the filter.

        Returns the union across selected agents, sorted by identifier. Each dictionary contains
        ``id``, ``supportsBuckets`` and ``supportsTimeSeries``. The flags indicate compatibility with
        :meth:`get_metric_buckets` and :meth:`get_metric_time_series`; they do not guarantee stored data.
        Configured business KPIs use the ``business-kpi.`` prefix and support both query methods.
        An empty agent selection returns an empty list.

        :param AgentFilter agent_filter: optional agent filter; omitted selects all readable agents
        :returns: metric identifiers and their query compatibility
        :rtype: list of dict

        Example::

            available = dam.get_available_metric_ids()
            bucket_metric_ids = [metric["id"] for metric in available if metric["supportsBuckets"]]
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        return self._perform_json("POST", "/agent-management/agents/metrics/available",
                                  body=agent_filter._as_dict() if agent_filter is not None else {})

    def get_metric_time_series(self, metrics, agent_filter=None, from_time=None, to_time=None, latest_only=False):
        """
        Returns stored, non-aggregated metric values for the selected agents.

        This method can only return metrics for which individual values are stored. Metrics which
        exist only as aggregates cannot be reconstructed as time-series values and must be queried
        with :meth:`get_metric_buckets` instead.

        ``metrics`` is a list of qualified metric identifiers. Each identifier includes its family,
        for example ``reliability.uptime_test_status``. The accepted identifiers are ``reliability.uptime_test_status``,
        ``performance.uptime_test_response_time_ms`` and ``business-kpi.<id>``, where ``<id>`` is the identifier of a
        business KPI assigned to the agent. Uptime and business KPI metrics can be requested in the
        same call. Examples of metrics which only exist as buckets include ``reliability.uptime_successful_tests_count``,
        ``reliability.uptime_tests_count``, ``reliability.uptime_pct`` and all activity, consumption, behavior and bucketed performance metrics. This list is not
        exhaustive; any requested metric which is not stored as individual values is rejected.

        The response is a list of series. Each series has ``infrastructureName``, ``agentId``,
        ``columns`` and ``rows``. The first column is ``timestamp`` as a UTC-aware datetime; remaining
        columns are the qualified metrics. Rows are chronological lists aligned with
        ``columns``. Metrics sharing the same stored timeline are grouped; each business KPI has its
        own series. A selected agent with no value has an empty ``rows`` list.

        If ``latest_only`` is True, each series contains at most its latest available row. Metrics
        which share a timeline still share one row: this mode does not look for the latest non-null
        value of each metric separately. Both timestamps must be omitted in this mode. Otherwise
        ``from_time`` is required and ``to_time`` defaults to the current time.

        To get the latest available values, omit both timestamps and set ``latest_only=True``:

        .. code-block:: python

            latest_time_series = dam.get_metric_time_series(
                metrics=["reliability.uptime_test_status", "performance.uptime_test_response_time_ms"],
                latest_only=True
            )

        This example requests one metric from each family available as stored time-series values.
        The business KPI points are deliberately shifted by five minutes from the uptime points:

        .. code-block:: python

            from datetime import datetime, timezone

            time_series = dam.get_metric_time_series(
                metrics=["reliability.uptime_test_status", "business-kpi.customer-satisfaction"],
                from_time=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                to_time=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
                agent_filter=AgentFilter().with_agent_ids("support-agent")
            )

            # time_series == [
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "reliability.uptime_test_status"],
            #         "rows": [[datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc), "OK"], [datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc), "ERROR"]]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "business-kpi.customer-satisfaction"],
            #         "rows": [[datetime(2026, 1, 1, 1, 5, tzinfo=timezone.utc), 4.6], [datetime(2026, 1, 1, 2, 5, tzinfo=timezone.utc), 4.8]]
            #     }
            # ]

        :param list metrics: qualified metric identifiers, for example
            ``["reliability.uptime_test_status", "performance.uptime_test_response_time_ms", "business-kpi.revenue"]``
        :param AgentFilter agent_filter: optional agent selection
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime;
            required when ``latest_only`` is False and forbidden when it is True
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime;
            defaults to the current time when ``from_time`` is set and is forbidden when ``latest_only`` is True
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        if latest_only and (from_time is not None or to_time is not None):
            raise ValueError("from_time and to_time must be omitted when latest_only is True")
        if not latest_only and from_time is None:
            raise ValueError("from_time is required when latest_only is False")
        chunks = self._perform_json("POST", "/agent-management/agents/metrics/time-series", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": _to_timestamp_ms(from_time, "from_time"),
            "toTimestamp": _to_timestamp_ms(to_time, "to_time"),
            "metrics": list(metrics),
            "latestOnly": latest_only
        })
        return _consolidate_metric_chunks(chunks)

    def get_metric_buckets(self, metrics, bucket, agent_filter=None, from_time=None, to_time=None):
        """
        Returns bucketed metrics for the selected agents.

        ``metrics`` is a list of qualified metric identifiers. Each identifier has the form
        ``<family>.<metric>`` and a single request may mix families. The accepted identifiers are:

        - reliability: ``reliability.uptime_pct``, ``reliability.uptime_tests_count``,
          ``reliability.uptime_successful_tests_count``, ``reliability.uptime_failed_tests_count``,
          ``reliability.interaction_errors``, ``reliability.interaction_error_rate_pct``,
          ``reliability.platform_side.interaction_errors``,
          ``reliability.platform_side.interaction_error_rate_pct``, ``reliability.platform_side.throttles``;
        - activity: ``activity.distinct_users_count``, ``activity.interactions``, ``activity.conversations``,
          ``activity.platform_side.interactions`` and ``activity.interactions_per_conversation`` statistics;
        - performance: ``performance.interaction_latency_ms`` and ``performance.conversation_total_latency_ms`` statistics,
          plus ``performance.platform_side.interaction_latency_ms_avg`` and ``performance.platform_side.interaction_latency_ms_p95``;
        - consumption: ``consumption.tokens.input``, ``consumption.tokens.output``, ``consumption.tokens.total``,
          ``consumption.tokens.input_cache_read``, ``consumption.tokens.input_cache_write``,
          ``consumption.cost.total``, plus ``consumption.tokens.input_per_interaction``,
          ``consumption.tokens.output_per_interaction``, ``consumption.tokens.total_per_interaction``,
          ``consumption.cost.per_interaction`` and ``consumption.cost.per_conversation`` statistics;
        - behavior: ``behavior.tool_calls``, plus ``behavior.tool_calls_per_interaction``
          and ``behavior.tool_calls_per_conversation`` statistics;
        - business KPI: ``business-kpi.<id>``.

        Request statistics with an explicit ``.avg`` or ``.percentile.95`` suffix, for example
        ``performance.conversation_total_latency_ms.percentile.95``. Platform-side latency values
        are supplied by the platform and do not support custom aggregation suffixes.
        Percentages, including uptime and error rates, range from 0 to 100; rates without samples are missing.

        Supported buckets are ``HOUR``, ``DAY``, ``WEEK`` and ``MONTH`` for all metric families.
        Business KPI buckets use the latest dataset value within each bucket.
        Activity counts distinct users and conversations within each bucket, not sums of smaller buckets.
        Conversation statistics use only interactions within the bucket and exclude missing conversation IDs.
        Conversation total latency is the sum of interaction durations, excluding time spent waiting for the user.
        Tool-call metrics describe recorded calls and include interactions with zero recorded calls in their population;
        missing trace data cannot be distinguished from no calls. Cost is an estimate: partially priced samples
        contribute known charges, while entirely unpriced samples are excluded from cost distributions.

        Bucket boundaries always use the global metrics timezone configured in Agent Management.
        Weekly boundaries also use the globally configured first day of the week. ``start`` and
        ``end`` are nevertheless absolute instants returned as UTC-aware datetimes.

        Returns :class:`dataikuapi.agentmanagement.metrics.BucketedMetricsFetchResults`.
        Its ``agents()`` lists represented agents as platform/agent tuples. Use
        ``agent_series(platform_name, agent_id)`` for a unified ``{columns, rows}`` table:
        columns are ``start``, ``end`` and the requested metrics in request order, and rows are
        joined on exact bucket boundaries and sorted chronologically. Missing values are ``None``.
        ``raw_agent_data(platform_name, agent_id)`` preserves the original grouped series and metadata.
        ``agent_single_series(platform_name, agent_id, metric_id)`` returns ``(start, end, value)`` tuples.
        ``agent_values_at_time(platform_name, agent_id, time)`` returns metric values in the bucket
        containing the instant, accepting epoch milliseconds or an aware datetime.

        Example::

            results = dam.get_metric_buckets(
                ["activity.interactions", "performance.conversation_total_latency_ms.avg"],
                "DAY", from_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
            for platform_name, agent_id in results.agents():
                table = results.agent_series(platform_name, agent_id)

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param AgentFilter agent_filter: optional agent selection
        :param int or datetime from_time: inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime;
            defaults to the current time
        :rtype: dataikuapi.agentmanagement.metrics.BucketedMetricsFetchResults
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        if from_time is None:
            raise ValueError("from_time is required")
        metrics = list(metrics)
        chunks = self._perform_json("POST", "/agent-management/agents/metrics/buckets", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": _to_timestamp_ms(from_time, "from_time"),
            "toTimestamp": _to_timestamp_ms(to_time, "to_time"),
            "metrics": metrics,
            "bucket": bucket
        })
        return BucketedMetricsFetchResults(_consolidate_metric_chunks(chunks), metrics)

    def list_operations(self, agent_filter=None, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None, current_only=False, as_type="listitems"):
        """
        Lists readable Agent Management operations matching the supplied filters.

        The result contains ``operations`` and ``has_more``, which indicates whether additional operations matched.

        :param AgentFilter agent_filter: filter selecting operations attached to matching agents
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: maximum number of returned operations, defaults to 1000, up to 10000
        :param boolean current_only: whether to return only queued or running operations
        :param str as_type: "listitems"/"listitem" returns OperationListItem entries; "objects"/"object" returns Operation handles
        :rtype: :class:`dataikuapi.agentmanagement.operations.OperationSearchResult`
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = {"agentFilter": agent_filter._as_dict() if agent_filter is not None else {}}
        body.update({
            name: value for name, value in (
                ("type", operation_types),
                ("status", statuses),
                ("trigger", triggers),
                ("fromTimestamp", from_timestamp),
                ("toTimestamp", to_timestamp),
                ("limit", limit),
                ("currentOnly", current_only),
            ) if value is not None
        })
        response = self._perform_json("POST", "/agent-management/operations/search", body=body)
        return OperationSearchResult(self, response, as_type)

    def search_triggered_alerts(self, agent_filter=None, states=None, severities=None, configuration_ids=None,
                                origins=None, from_timestamp=None, to_timestamp=None, limit=None, as_objects=True):
        """
        Searches readable Agent Management triggered alerts matching the supplied filters.

        If ``states`` is omitted or empty, only active, unacknowledged alerts are returned. Explicitly requesting ``OPEN`` also
        includes acknowledged alerts that remain open pending recovery.

        :param AgentFilter agent_filter: filter selecting triggered alerts attached to matching agents
        :param list states: triggered alert states, either ``OPEN`` or ``CLOSED``
        :param list severities: triggered alert severities, either ``WARNING`` or ``CRITICAL``
        :param list configuration_ids: alert configuration IDs, without an origin prefix
        :param list origins: configuration origins: ``GLOBAL``, ``INFRA``, ``AGENT``, or ``SCOPE``;
            combined with ``configuration_ids`` when both filters are supplied
        :param int from_timestamp: optional inclusive lower opening timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper opening timestamp bound, in milliseconds since the Unix epoch
        :param int limit: optional maximum number of returned alerts; defaults to 100 and is capped at 1000
        :param boolean as_objects: if True, the result contains :class:`dataikuapi.agentmanagement.alerting.Alert` handles, otherwise dictionaries
        :rtype: :class:`dataikuapi.agentmanagement.alerting.TriggeredAlertSearchResult`
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = {"agentFilter": agent_filter._as_dict() if agent_filter is not None else {}}
        body.update({
            name: value for name, value in (
                ("state", states),
                ("severity", severities),
                ("configurationId", configuration_ids),
                ("origin", origins),
                ("fromTimestamp", from_timestamp),
                ("toTimestamp", to_timestamp),
                ("limit", limit),
            ) if value is not None
        })
        response = self._perform_json("POST", "/agent-management/alerts/search", body=body)
        return TriggeredAlertSearchResult(self, response, as_objects)

    def get_triggered_alert(self, alert_id):
        """
        Returns a handle to an Agent Management triggered alert.

        :param str alert_id: identifier of the alert
        :rtype: :class:`dataikuapi.agentmanagement.alerting.Alert`
        """
        return Alert(self, alert_id)

    # def list_topic_families(self, as_type="listitems"):
    #     """
    #     Lists the Agent Management topic families.
    #
    #     :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     :returns: a list - see ``as_type`` for more information
    #     :rtype: list
    #     """
    #     families = self._perform_json("GET", "/agent-management/settings/topic-families")
    #     return _format_list([TopicFamilyListItem(self, family) for family in families], as_type)
    #
    # def create_topic_family(self, definition):
    #     """
    #     Creates a topic family.
    #
    #     :param dict definition: topic family definition, including its ``id``
    #     :rtype: :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     """
    #     created = self._perform_json("POST", "/agent-management/settings/topic-families", body=definition)
    #     return TopicFamily(self, created["id"])
    #
    # def get_topic_family(self, family_id):
    #     """
    #     Returns a handle to a topic family.
    #
    #     :param str family_id: identifier of the topic family
    #     :rtype: :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     """
    #     return TopicFamily(self, family_id)

    def get_risk_exposure(self):
        """
        Returns the aggregated Agent Management risk exposure.

        :rtype: :class:`dataikuapi.agentmanagement.risk.EstateRiskExposure`
        """
        exposure = self._perform_json("GET", "/agent-management/risk-exposure")["exposure"]
        return EstateRiskExposure(exposure)

    def get_risk_taxonomy(self):
        """
        Returns the Agent Management risk taxonomy settings.

        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskTaxonomySettings`
        """
        taxonomy = self._perform_json("GET", "/agent-management/risk-taxonomy")
        return RiskTaxonomySettings(self, taxonomy)

    def get_default_risk_taxonomy(self):
        """
        Returns the default Agent Management risk taxonomy settings.

        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskTaxonomySettings`
        """
        taxonomy = self._perform_json("GET", "/agent-management/risk-taxonomy/default")
        return RiskTaxonomySettings(self, taxonomy)

    def list_tags(self):
        """
        Lists tags used by Agent Management agents.

        :rtype: :class:`dataikuapi.agentmanagement_client.AgentManagementTags`
        """
        return AgentManagementTags(self, self._perform_json("GET", "/agent-management/tags"))


    def get_dssclient(self):
        """
        Creates a DSSClient targeting the same Agent Management instance with the same authentication context.

        Use this client for projects, datasets, recipes, plugins and code environments.
        Instance administration methods on AgentManagementClient also use this client internally.

        :return: a DSSClient client
        :rtype: :class:`dataikuapi.DSSClient`
        """
        from .dssclient import DSSClient

        amc = DSSClient(self.host, api_key=self.api_key, internal_ticket=self.internal_ticket,
                                    extra_headers=self._session.headers, client_certificate=self._session.cert, jwt_bearer_token=self.jwt_bearer_token)

        # When the client was created from a ticket with encrypted RPC, verify is not just a boolean
        if self._session.verify is not None:
            amc._session.verify = self._session.verify

        return amc

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None, headers=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        http_res = self._session.request(
                method, "%s/dip/publicapi%s" % (self.host, path),
                params=params, data=body,
                files=files,
                stream=stream,
                headers=headers,
                verify=self._session.verify)
        handle_http_exception(http_res)
        return http_res

    def _perform_empty(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers)

    def _perform_text(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).text

    def _perform_json(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).json()

    def _perform_raw(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body, headers=headers)


class AgentManagementTags(object):
    """
    A snapshot of tags used by Agent Management agents, iterable as tag objects.

    Do not create this directly, use :meth:`AgentManagementClient.list_tags`.
    """
    def __init__(self, client, tags):
        self._tags = [AgentManagementTag(client, tag) for tag in tags]

    def __iter__(self):
        return iter(self._tags)

    def __len__(self):
        return len(self._tags)

    def tag(self, name):
        """
        Returns a tag by its name.

        :param str name: tag name
        :rtype: :class:`AgentManagementTag`
        :raises KeyError: if the tag is not in this collection
        """
        for tag in self._tags:
            if tag.name == name:
                return tag
        raise KeyError(name)


class AgentManagementTag(object):
    """
    An Agent Management tag.

    Do not create this directly, use :meth:`AgentManagementTags.tag`.
    """
    def __init__(self, client, tag):
        self.client = client
        self._tag = dict(tag)

    def __repr__(self):
        return "<AgentManagementTag name=%r>" % self.name

    @property
    def name(self):
        """The tag name (read-only). Use :meth:`rename` to change it."""
        return self._tag["name"]

    @property
    def color(self):
        """The tag color. Changes are persisted by :meth:`save`."""
        return self._tag["color"]

    @color.setter
    def color(self, color):
        self._tag["color"] = color

    def save(self):
        """
        Saves the tag color.

        :returns: this tag with its saved definition
        :rtype: :class:`AgentManagementTag`
        """
        self._tag = self.client._perform_json("PUT", "/agent-management/tags/%s" % dku_quote_fn(self.name, safe=""),
                                              body={"color": self.color})
        return self

    def rename(self, new_name):
        """
        Renames the tag everywhere it is used and updates this object's definition.

        :param str new_name: new tag name
        :returns: this tag with its renamed definition
        :rtype: :class:`AgentManagementTag`
        """
        self._tag = self.client._perform_json("POST", "/agent-management/tags/%s/actions/rename" % dku_quote_fn(self.name, safe=""),
                                              body={"newName": new_name})
        return self

    def delete(self):
        """Deletes the tag everywhere it is used."""
        self.client._perform_empty("DELETE", "/agent-management/tags/%s" % dku_quote_fn(self.name, safe=""))
