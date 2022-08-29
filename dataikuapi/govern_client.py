import json

from requests import Session, exceptions
from requests.auth import HTTPBasicAuth

from dataikuapi.govern.admin import GovernUser, GovernGroup, GovernOwnUser, GovernGlobalApiKey, GovernGeneralSettings
from dataikuapi.govern.admin_blueprint_designer import GovernAdminBlueprintDesigner
from dataikuapi.govern.admin_custom_page_editor import GovernAdminCustomPageEditor
from dataikuapi.govern.admin_roles_and_permissions_audit import GovernAdminRolesAndPermissionsAudit
from dataikuapi.govern.admin_roles_permissions_editor import GovernAdminRolesPermissionsEditor
from dataikuapi.govern.artifact import GovernArtifact
from dataikuapi.govern.artifact_search_handler import GovernArtifactSearchHandler
from dataikuapi.govern.blueprint import GovernBlueprint
from dataikuapi.govern.custom_page import GovernCustomPage
from dataikuapi.utils import DataikuException


class GovernClient(object):
    """Entry point for the Govern API client"""

    def __init__(self, host, api_key=None, internal_ticket=None, extra_headers=None):
        """
        Instantiate a new Govern API client on the given host with the given API key.
        API keys can be managed in Govern in the global settings.
        The API key will define which operations are allowed for the client.
        """
        self.api_key = api_key
        self.internal_ticket = internal_ticket
        self.host = host
        self._session = Session()

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

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        try:
            http_res = self._session.request(
                method, "%s/dip/publicapi%s" % (self.host, path),
                params=params,
                data=body,
                files=files,
                stream=stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException("%s: %s" % (
                ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None, files=None, raw_body=None):
        self._perform_http(method, path, params=params, body=body,
                           files=files, stream=False, raw_body=raw_body)

    def _perform_text(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False,
                                  raw_body=raw_body).text

    def _perform_json(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False,
                                  raw_body=raw_body).json()

    def _perform_raw(self, method, path, params=None, body=None, files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body)

    def _perform_json_upload(self, method, path, name, f):
        try:
            http_res = self._session.request(
                method, "%s/publicapi%s" % (self.host, path),
                files={'file': (name, f, {'Expires': '0'})})
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (
                ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    ########################################################
    # Blueprint Designer
    ########################################################

    def get_admin_blueprint_designer(self):
        """
        Return a handle to interact with the blueprint designer
        Note: this call requires an API key with admin rights

        :rtype: A :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner`
        """
        return GovernAdminBlueprintDesigner(self)

    ########################################################
    # Roles and Permissions
    ########################################################

    def get_admin_roles_permissions_editor(self):
        """
        Return a handle to edit the roles and permissions of the Govern instance
        Note: this call requires an API key with admin rights

        :rtype: A :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor`
        """
        return GovernAdminRolesPermissionsEditor(self)

    def get_admin_roles_and_permissions_audit(self):
        """
        Return a handle to get audit information on roles and permissions for Govern objects.
        Note: this call requires an API key with admin rights

        :rtype: A :class:`~dataikuapi.govern.admin_roles_and_permissions_audit.GovernAdminRolesAndPermissionsAudit`
        """
        return GovernAdminRolesAndPermissionsAudit(self)

    ########################################################
    # Custom Pages editor
    ########################################################

    def get_admin_custom_page_editor(self):
        """
        Return a handle to edit custom pages
        Note: this call requires an API key with admin rights

        :rtype: A :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageEditor`
        """
        return GovernAdminCustomPageEditor(self)

    ########################################################
    # Blueprints
    ########################################################

    def list_blueprints(self, as_objects=False):
        """
        List all the blueprints

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.blueprint.GovernBlueprint`,
        else returns a list of dict. Each dict contains at least a field "blueprint.id" indicating the identifier the blueprint
        :return: a list of blueprints, each as a dict or an object. Each dict contains at least an "blueprint.id" field
        :rtype: list of :class:`~dataikuapi.govern.blueprint.GovernBlueprint` or list of dict, see param as_objects
        """
        blueprint_list = self._perform_json("GET", "/blueprints")
        if as_objects:
            return [GovernBlueprint(self, blueprint["blueprint"]["id"]) for blueprint in blueprint_list]
        else:
            return blueprint_list

    def get_blueprint(self, blueprint_id):
        """
        Get a handle to interact with a blueprint. If you want to edit it or one of its versions, use instead:
        :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner`

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
        return GovernArtifact(self, result["artifact"]["id"])

    def get_artifact_search_handler(self):
        """
        Return a handle to build and perform artifact search requests.

        :rtype: A :class:`~dataikuapi.govern.artifact_search_handler.GovernArtifactSearchHandler`
        """

        return GovernArtifactSearchHandler(self)

    ########################################################
    # Custom  Pages
    ########################################################

    def get_custom_page(self, custom_page_id):
        """
        Retrieve a custom page. To edit a custom page use instead the custom page editor :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageEditor`

        :param str custom_page_id: id of the custom page to retrieve
        :return: the corresponding custom page object
        :rtype: a :class:`~dataikuapi.govern.custom_page.GovernCustomPage`
        """

        return GovernCustomPage(self, custom_page_id)

    def list_custom_pages(self, as_objects=False):
        """
        Lists custom pages.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.custom_page.GovernCustomPage`,
         else returns a list of dict. Each dict contains at least a field "id"
        :returns: a list of custom pages
        :rtype: list of :class:`~dataikuapi.govern.custom_page.GovernCustomPage` or list of dict, see param as_objects
        """
        pages = self._perform_json("GET", "/custom-pages")

        if as_objects:
            return [GovernCustomPage(self, page["id"]) for page in pages]
        else:
            return pages

    ########################################################
    # Users
    ########################################################

    def list_users(self, as_objects=False):
        """
        List all user setup on the Govern instance
        Note: this call requires an API key with admin rights

        :return: A list of users, as a list of :class:`~dataikuapi.govern.admin.GovernUser` if as_objects is True,
         else as a list of dicts
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

    def get_own_user(self):

        """
        Get a handle to interact with the current user

        :return: A :class:`~dataikuapi.govern.admin.GovernOwnUser` user handle
        """
        return GovernOwnUser(self)

    def create_user(self, login, password, display_name='', source_type='LOCAL', groups=None, profile='DATA_SCIENTIST'):
        """
        Create a user, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str login: the login of the new user
        :param str password: the password of the new user
        :param str display_name: the displayed name for the new user
        :param str source_type: the type of new user. Admissible values are 'LOCAL' or 'LDAP'
        :param list groups: the names of the groups the new user belongs to (defaults to `[]`)
        :param str profile: The profile for the new user, can be one of READER, DATA_ANALYST or DATA_SCIENTIST

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
        return self._perform_json(
            "GET", "/admin/groups/")

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

    def list_global_api_keys(self):
        """
        List all global API keys set up on the Govern instance

        Note: this call requires an API key with admin rights

        :returns: All global API keys, as a list of dicts
        """
        return self._perform_json(
            "GET", "/admin/globalAPIKeys/")

    def get_global_api_key(self, key):
        """
        Get a handle to interact with a specific Global API key

        :param str key: the secret key of the desired API key

        :returns: A :class:`~dataikuapi.govern.admin.GovernGlobalApiKey` API key handle
        """
        return GovernGlobalApiKey(self, key)

    def create_global_api_key(self, label=None, description=None, admin=False):
        """
        Create a Global API key, and return a handle to interact with it

        Note: this call requires an API key with admin rights

        :param str label: the label of the new API key
        :param str description: the description of the new API key
        :param boolean admin: has the new API key admin rights (True or False)

        :returns: A :class:`~dataikuapi.govern.admin.GovernGlobalApiKey` API key handle
        """
        resp = self._perform_json(
            "POST", "/admin/globalAPIKeys/", body={
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
        key = resp.get('key', '')
        return GovernGlobalApiKey(self, key)

    ########################################################
    # Logs
    ########################################################

    def list_logs(self):
        """
        List all available log files on the Govern instance
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
                                   body=custom_params)

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

    def get_auth_info_from_browser_headers(self, headers_dict):
        """
        Returns various information about the DSS user authenticated by the dictionary of
        HTTP headers provided in headers_dict.

        This is generally only used in webapp backends

        This method returns a dict that may contain the following keys (may also contain others):

        * authIdentifier: login for a user, id for an API key
        * groups: list of group names (if context is an user)

        :param: headers_dict dict: Dictionary of HTTP headers
        :returns: a dict
        :rtype: dict
        """
        return self._perform_json("POST", "/auth/info-from-browser-headers", body=headers_dict)

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
        self._perform_empty(
            "POST", "/admin/licensing/license", body=json.loads(license))
