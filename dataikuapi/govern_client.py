import json
import warnings

from requests import Session, exceptions
from requests.auth import HTTPBasicAuth
from .iam.settings import DSSSSOSettings, DSSLDAPSettings, DSSAzureADSettings

from dataikuapi.govern.future import GovernFuture
from dataikuapi.govern.admin import GovernUser, GovernGroup, GovernOwnUser, GovernGlobalApiKey, GovernGeneralSettings, GovernUserActivity, \
    GovernAuthorizationMatrix, GovernGlobalApiKeyListItem
from dataikuapi.govern.admin_blueprint_designer import GovernAdminBlueprintDesigner
from dataikuapi.govern.admin_custom_pages_handler import GovernAdminCustomPagesHandler
from dataikuapi.govern.admin_roles_permissions_handler import GovernAdminRolesPermissionsHandler
from dataikuapi.govern.artifact import GovernArtifact
from dataikuapi.govern.artifact_search import GovernArtifactSearchRequest
from dataikuapi.govern.blueprint import GovernBlueprintListItem, GovernBlueprint
from dataikuapi.govern.custom_page import GovernCustomPageListItem, GovernCustomPage
from dataikuapi.govern.time_series import GovernTimeSeries
from dataikuapi.govern.uploaded_file import GovernUploadedFile
from dataikuapi.utils import handle_http_exception


class GovernClient(object):
    """Entry point for the Govern API client"""

    def __init__(self, host, api_key=None, internal_ticket=None, extra_headers=None, no_check_certificate=False, client_certificate=None, **kwargs):
        """Initialize a new Govern API client.

        This client provides access to Dataiku's Govern instance.

        Args:
            host (str): The URL of the DSS instance (e.g., "http://localhost:11200")
            api_key (str, optional): API key for authentication. Can be managed in Govern global settings.
                The API key determines which operations are allowed.
            internal_ticket (str, optional): Internal ticket for authentication
            extra_headers (dict, optional): Additional HTTP headers to include in all requests
            no_check_certificate (bool, optional): If True, disables SSL certificate verification.
                Defaults to False.
            client_certificate (str or tuple, optional): Path to client certificate file or tuple of 
                (cert, key) paths for client certificate authentication
            **kwargs: Additional keyword arguments

        Note:
            - API key is required for most operations and can be managed in Govern global settings
            - When using HTTPS, certificate verification is enabled by default for security
            - Use no_check_certificate=True only in development or when using self-signed certificates
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
            self._session.headers.update(
                {"X-DKU-APITicket": self.internal_ticket})
        else:
            raise ValueError("API Key is required")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    ########################################################
    # Internal Request handling
    ########################################################

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
                headers=headers)
        handle_http_exception(http_res)
        return http_res

    def _perform_empty(self, method, path, params=None, body=None, files=None, raw_body=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body)

    def _perform_text(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body).text

    def _perform_json(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body).json()

    def _perform_raw(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body)

    def _perform_json_upload(self, method, path, name, f):
        http_res = self._session.request(
                method, "%s/dip/publicapi%s" % (self.host, path),
                files={'file': (name, f, {'Expires': '0'})})
        handle_http_exception(http_res)
        return http_res

    ########################################################
    # Blueprint Designer
    ########################################################

    def get_blueprint_designer(self):
        """
        Return a handle to interact with the blueprint designer
        Note: this call requires an API key with Govern manager rights

        :rtype: A :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner`
        """
        return GovernAdminBlueprintDesigner(self)

    ########################################################
    # Roles and Permissions
    ########################################################

    def get_roles_permissions_handler(self):
        """
        Return a handler to manage the roles and permissions of the Govern instance
        Note: this call requires an API key with Govern manager rights

        :rtype: A :class:`~dataikuapi.govern.admin_roles_permissions_handler.GovernAdminRolesPermissionsHandler`
        """
        return GovernAdminRolesPermissionsHandler(self)

    ########################################################
    # Custom Pages handler
    ########################################################

    def get_custom_pages_handler(self):
        """
        Return a handler to manage custom pages
        Note: this call requires an API key with Govern manager rights

        :rtype: A :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPagesHandler`
        """
        return GovernAdminCustomPagesHandler(self)

    ########################################################
    # Blueprints
    ########################################################

    def list_blueprints(self):
        """
        List all the blueprints

        :return: a list of blueprints
        :rtype: list of :class:`~dataikuapi.govern.blueprint.GovernBlueprintListItem`
        """
        blueprint_list = self._perform_json("GET", "/blueprints")
        return [GovernBlueprintListItem(self, blueprint) for blueprint in blueprint_list]

    def get_blueprint(self, blueprint_id):
        """
        Get a handle to interact with a blueprint. If you want to edit it or one of its versions, use instead:
        :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner.get_blueprint`

        :param str blueprint_id: id of the blueprint to retrieve
        :returns: The handle of the blueprint
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprint`
        """
        return GovernBlueprint(self, blueprint_id)

    ########################################################
    # Artifacts
    ########################################################

    def get_artifact(self, artifact_id):
        """
        Return a handle to interact with an artifact.

        :param str artifact_id: id of the artifact to retrieve
        :return: the corresponding :class:`~dataikuapi.govern.artifact.GovernArtifact`
        """
        return GovernArtifact(self, artifact_id)

    def create_artifact(self, artifact):
        """
        Create an artifact

        :param dict artifact: the definition of the artifact as a dict
        :return: the created :class:`~dataikuapi.govern.artifact.GovernArtifact`
        """
        result = self._perform_json("POST", "/artifacts", body=artifact)
        return GovernArtifact(self, result["artifactId"])

    def new_artifact_search_request(self, artifact_search_query):
        """
        Create a new artifact search request and return the object that will be used to launch the requests.

        :param artifact_search_query: The query that will be addressed during the search.
        :type artifact_search_query: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchQuery`
        :return: The created artifact search request object
        :rtype: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchRequest`
        """
        return GovernArtifactSearchRequest(self, artifact_search_query)

    ########################################################
    # Custom  Pages
    ########################################################

    def get_custom_page(self, custom_page_id):
        """
        Retrieve a custom page. To edit a custom page use instead the custom page editor :meth:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPagesHandler.get_custom_page`

        :param str custom_page_id: id of the custom page to retrieve
        :return: the corresponding custom page object
        :rtype: a :class:`~dataikuapi.govern.custom_page.GovernCustomPage`
        """
        return GovernCustomPage(self, custom_page_id)

    def list_custom_pages(self):
        """
        List custom pages.

        :return: a list of custom pages
        :rtype: list of :class:`~dataikuapi.govern.custom_page.GovernCustomPageListItem`
        """
        pages = self._perform_json("GET", "/custom-pages")
        return [GovernCustomPageListItem(self, page) for page in pages]

    ########################################################
    # Time Series
    ########################################################

    def create_time_series(self, datapoints=None):
        """
        Create a new time series and push a list of values inside it.

        :param list datapoints: (Optional) a list of Python dict - The list of datapoints as Python dict containing the following keys "timeSeriesId", "timestamp" (an epoch in milliseconds), and "value" (an object)
        :return: the created time-series object
        :rtype: a :class:`~dataikuapi.govern.time_series.GovernTimeSeries`
        """
        if datapoints is None:
            datapoints = []
        result = self._perform_json("POST", "/time-series", body=datapoints)
        return GovernTimeSeries(self, result["id"])

    def get_time_series(self, time_series_id):
        """
        Return a handle to interact with the time series

        :param str time_series_id: ID of the time series
        :return: the corresponding time series object
        :rtype: a :class:`~dataikuapi.govern.time_series.GovernTimeSeries`
        """
        return GovernTimeSeries(self, time_series_id)

    ########################################################
    # Uploaded files
    ########################################################

    def get_uploaded_file(self, uploaded_file_id):
        """
        Return a handle to interact with an uploaded file

        :param str uploaded_file_id: ID of the uploaded file
        :return: the corresponding uploaded file object
        :rtype: a :class:`~dataikuapi.govern.uploaded_file.GovernUploadedFile`
        """
        return GovernUploadedFile(self, uploaded_file_id)

    def upload_file(self, file_name, file):
        """
        Upload a file on Govern. Return a handle to interact with this new uploaded file.

        :param str file_name: Name of the file
        :param stream file: file contents, as a stream - file-like object
        :return: the newly uploaded file object
        :rtype: a :class:`~dataikuapi.govern.uploaded_file.GovernUploadedFile`
        """
        description = self._perform_json_upload("POST", "/uploaded-files", file_name, file).json()
        return GovernUploadedFile(self, description["id"])

    ########################################################
    # Users
    ########################################################

    def list_users(self, as_objects=False):
        """
        List all user setup on the Govern instance
        Note: this call requires an API key with admin rights

        :return: A list of users, as a list of :class:`~dataikuapi.govern.admin.GovernUser` if as_objects is True, else as a list of dicts
        :rtype: list of :class:`~dataikuapi.govern.admin.GovernUser` or list of dicts
        """
        users = self._perform_json("GET", "/admin/users/")

        if as_objects:
            return [GovernUser(self, user["login"]) for user in users]
        else:
            return users

    def get_user(self, login):
        """
        Get a handle to interact with a specific user

        :param str login: the login of the desired user
        :return: A :class:`~dataikuapi.govern.admin.GovernUser` user handle
        """
        return GovernUser(self, login)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=None, profile='DATA_SCIENTIST'):
        """
        Create a user, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str login: the login of the new user
        :param str password: the password of the new user
        :param str display_name: the displayed name for the new user
        :param str source_type: the type of new user. Admissible values are 'LOCAL' or 'LDAP'
        :param list groups: the names of the groups the new user belongs to (defaults to `[]`)
        :param str profile: The profile for the new user. Typical values (depend on your license): FULL_DESIGNER, DATA_DESIGNER, AI_CONSUMER, ...

        :return: A :class:`~dataikuapi.govern.admin.GovernUser` user handle
        """
        if groups is None:
            groups = []

        self._perform_json("POST", '/admin/users/', body={
            "login": login,
            "password": password,
            "displayName": display_name,
            "sourceType": source_type,
            "groups": groups,
            "userProfile": profile
        })
        return GovernUser(self, login)

    def get_own_user(self):
        """
        Get a handle to interact with the current user

        :return: A :class:`~dataikuapi.govern.admin.GovernOwnUser` user handle
        """
        return GovernOwnUser(self)

    def list_users_activity(self, enabled_users_only=False):
        """
        List all users activity

        Note: this call requires an API key with admin rights

        :return: A list of user activity logs, as a list of :class:`dataikuapi.govern.admin.GovernUserActivity`
        :rtype: list of :class:`dataikuapi.govern.admin.GovernUserActivity`
        """
        params = {
            "enabledUsersOnly": enabled_users_only
        }
        all_activity = self._perform_json("GET", "/admin/users-activity", params=params)

        return [GovernUserActivity(self, user_activity["login"], user_activity) for user_activity in all_activity]

    def get_authorization_matrix(self):
        """
        Get the authorization matrix for all enabled users and groups

        Note: this call requires an API key with admin rights

        :return: The authorization matrix
        :rtype: A :class:`dataikuapi.govern.admin.GovernAuthorizationMatrix` authorization matrix handle
        """
        resp = self._perform_json("GET", "/admin/authorization-matrix")
        return GovernAuthorizationMatrix(resp)

    def start_resync_users_from_supplier(self, logins):
        """
        Starts a resync of multiple users from an external supplier (LDAP, Azure AD or custom auth)
        
        :param list logins: list of logins to resync
        :return: a :class:`dataikuapi.govern.future.GovernFuture` representing the sync process
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/resync-multi", body=logins)
        return GovernFuture.from_resp(self, future_resp)

    def start_resync_all_users_from_supplier(self):
        """
        Starts a resync of all users from an external supplier (LDAP, Azure AD or custom auth)

        :return: a :class:`dataikuapi.govern.future.GovernFuture` representing the sync process
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/resync-multi")
        return GovernFuture.from_resp(self, future_resp)

    def start_fetch_external_groups(self, user_source_type):
        """
        Fetch groups from external source

        :param user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        :return: a GovernFuture containing a list of group names
        """
        future_resp = self._perform_json("GET", "/admin/external-groups", params={'userSourceType': user_source_type})
        return GovernFuture.from_resp(self, future_resp)

    def start_fetch_external_users(self, user_source_type, login=None, email=None, group_name=None):
        """
        Fetch users from external source filtered by login or group name:
         - if login is provided, will search for a user with an exact match in the external source (e.g. before login remapping)
         - else,
            - if group_name is provided, will search for members of the group in the external source
            - else will search for all users

        :param user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :param login: optional - the login of the user in the external source
        :param email: optional - the email of the user in the external source
        :param group_name: optional - the group name of the group in the external source
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        :return: a GovernFuture containing a list of ExternalUser
        """
        future_resp = self._perform_json("GET", "/admin/external-users", params={'userSourceType': user_source_type, 'login': login, 'email': email, 'groupName': group_name})
        return GovernFuture.from_resp(self, future_resp)

    def start_provision_users(self, user_source_type, users):
        """
        Provision users of given source type

        :param string user_source_type: 'LDAP', 'AZURE_AD' or 'CUSTOM'
        :param list users: list of user attributes coming form the external source
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        """
        future_resp = self._perform_json("POST", "/admin/users/actions/provision", body={'userSourceType': user_source_type, 'users': users})
        return GovernFuture.from_resp(self, future_resp)

    ########################################################
    # Groups
    ########################################################

    def list_groups(self):
        """
        List all groups setup on the Govern instance

        Note: this call requires an API key with admin rights

        :returns: A list of groups, as a list of dicts
        :rtype: list of dicts
        """
        return self._perform_json("GET", "/admin/groups/")

    def get_group(self, name):
        """
        Get a handle to interact with a specific group

        :param str name: the name of the desired group
        :returns: A :class:`~dataikuapi.govern.admin.GovernGroup` group handle
        """
        return GovernGroup(self, name)

    def create_group(self, name, description=None, source_type='LOCAL'):
        """
        Create a group, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str name: the name of the new group
        :param str description: (optional) a description of the new group
        :param str source_type: the type of the new group. Admissible values are 'LOCAL' and 'LDAP'

        :returns: A :class:`~dataikuapi.govern.admin.GovernGroup` group handle
        """
        self._perform_text(
            "POST", "/admin/groups/", body={
                "name": name,
                "description": description,
                "sourceType": source_type
            })
        return GovernGroup(self, name)

    ########################################################
    # Global API Keys
    ########################################################

    def list_global_api_keys(self, as_type='listitems'):
        """
        List all global API keys set up on the Govern instance

        .. note::

            This call requires an API key with admin rights

        .. note::

            If the secure API keys feature is enabled, the secret key of the listed
            API keys will not be present in the returned objects

        :param str as_type: How to return the global API keys. Possible values are "listitems" and "objects"

        :return: if as_type=listitems, each key as a :class:`dataikuapi.govern.admin.GovernGlobalApiKeyListItem`.
                 if as_type=objects, each key is returned as a :class:`dataikuapi.govern.admin.GovernGlobalApiKey`.
        """
        resp = self._perform_json(
            "GET", "/admin/global-api-keys/")

        if as_type == "listitems":
            return [GovernGlobalApiKeyListItem(self, item) for item in resp]
        elif as_type == 'objects':
            return [GovernGlobalApiKey(self, item["key"], item["id"]) for item in resp]
        else:
            raise ValueError("Unknown as_type")

    def get_global_api_key(self, key):
        """
        Get a handle to interact with a specific Global API key

        .. deprecated:: 13.0.0
            Use :meth:`GovernClient.get_global_api_key_by_id`. Calling this method with an invalid secret key
            will now result in an immediate error.

        :param str key: the secret key of the API key
        :returns: A :class:`dataikuapi.govern.admin.GovernGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "GET", "/admin/globalAPIKeys/%s" % key)
        return GovernGlobalApiKey(self, key, resp['id'])

    def get_global_api_key_by_id(self, id_):
        """
        Get a handle to interact with a specific Global API key

        :param str id_: the id the API key
        :returns: A :class:`dataikuapi.govern.admin.GovernGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "GET", "/admin/global-api-keys/%s" % id_)
        return GovernGlobalApiKey(self, resp["key"], id_)

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

        :returns: A :class:`dataikuapi.govern.admin.GovernGlobalApiKey` API key handle
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
        return GovernGlobalApiKey(self, resp.get('key', ''), resp['id'])

    ########################################################
    # Logs
    ########################################################

    def list_logs(self):
        """
        List all available log files on the Govern instance
        This call requires an API key with admin rights

        :returns: A list of log file names
        """
        return self._perform_json("GET", "/admin/logs/")

    def get_log(self, name):
        """
        Get the contents of a specific log file
        This call requires an API key with admin rights

        :param str name: the name of the desired log file (obtained with :meth:`list_logs`)
        :returns: The full content of the log file, as a string
        """
        return self._perform_json("GET", "/admin/logs/%s" % name)

    def log_custom_audit(self, custom_type, custom_params=None):
        """
        Log a custom entry to the audit trail

        :param str custom_type: value for customMsgType in audit trail item
        :param dict custom_params: value for customMsgParams in audit trail item (defaults to `{}`)
        """
        if custom_params is None:
            custom_params = {}
        return self._perform_empty("POST", "/admin/audit/custom/%s" % custom_type, body=custom_params)

    ########################################################
    # General settings
    ########################################################

    def get_general_settings(self):
        """
        Gets a handle to interact with the general settings.

        This call requires an API key with admin rights

        :returns: a :class:`~dataikuapi.govern.admin.GovernGeneralSettings` handle
        """
        return GovernGeneralSettings(self)

    ########################################################
    # Auth
    ########################################################

    def get_auth_info(self):
        """
        Returns various information about the user currently authenticated using this instance of the API client.

        This method returns a dict that may contain the following keys (may also contain others):

        * authIdentifier: login for a user, id for an API key
        * groups: list of group names (if  context is a user)

        :returns: a dict
        :rtype: dict
        """
        return self._perform_json("GET", "/auth/info")

    ########################################################
    # Licensing
    ########################################################

    def get_licensing_status(self):
        """
        Returns a dictionary with information about licensing status of this Govern instance

        :rtype: dict
        """
        return self._perform_json("GET", "/admin/licensing/status")

    def set_license(self, license):
        """
        Sets a new licence for Govern

        :param str license: license (content of license file)
        :return: None
        """
        self._perform_empty("POST", "/admin/licensing/license", body=json.loads(license))

    ########################################################
    # Global Instance Info
    ########################################################

    def get_instance_info(self):
        """
        Get global information about the Govern instance

        :returns: a :class:`GovernInstanceInfo`
        """
        resp = self._perform_json("GET", "/instance-info")
        return GovernInstanceInfo(resp)

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


class GovernInstanceInfo(object):
    """Global information about the Govern instance"""

    def __init__(self, data):
        """Do not call this directly, use :meth:`GovernClient.get_instance_info`"""
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
        :return: GOVERN
        """
        return self._data["nodeType"]
