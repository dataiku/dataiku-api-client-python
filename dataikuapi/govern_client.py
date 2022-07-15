import json

from requests import Session, exceptions
from requests.auth import HTTPBasicAuth

from dataikuapi.govern.admin import GovernUser, GovernGroup, GovernOwnUser
from dataikuapi.govern.admin_roles_audit import GovernAdminRolesAudit
from dataikuapi.govern.artifact_search_handler import GovernArtifactSearchHandler
from dataikuapi.govern.artifact_sign_off_handler import GovernArtifactSignOffHandler
from dataikuapi.govern.blueprint_designer import GovernBlueprintDesigner
from dataikuapi.govern.custom_page_editor import GovernCustomPageEditor
from dataikuapi.govern.models import GovernArtifact
from dataikuapi.govern.models.admin.admin_custom_page import GovernAdminCustomPage
from dataikuapi.govern.models.blueprint import GovernBlueprint
from dataikuapi.govern.roles_permissions_editor import GovernRolesPermissionsEditor
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

    def get_blueprint_designer(self):
        """
        Return a handle to interact with the blueprint designer

        :rtype: A :class:`dataikuapi.govern.blueprint_designer.GovernBlueprintDesigner`
        """
        return GovernBlueprintDesigner(self)

    ########################################################
    # Roles and Permissions
    ########################################################

    def get_roles_and_permissions_editor(self):
        """
        Return a handle to edit roles and permissions on the Govern instance

        :rtype: A :class:`dataikuapi.govern.roles_permissions_editor.GovernRolesPermissionsEditor`
        """
        return GovernRolesPermissionsEditor(self)

    ########################################################
    # Blueprints
    ########################################################

    def list_blueprints(self):
        """
        List all blueprints of a Govern node

        :return: a Python list of :class:`govern.models.Blueprint`
        """
        blueprint_list = self._perform_json('GET', '/blueprints')
        return blueprint_list

    def get_blueprint(self, blueprint_id):
        """
        Retrieve a blueprint from a Govern node. If you want to edit a blueprint or its version, use:
        :class: `dataikuapi.govern.blueprint_designer.GovernBlueprintDesigner`

        :param str blueprint_id: id of the blueprint to retrieve
        :returns The handle of the blueprint
        :rtype: :class:`dataikuapi.govern.models.blueprint.Blueprint`
        """
        return GovernBlueprint(self, blueprint_id)

    ########################################################
    # Artifacts
    ########################################################

    def get_artifact(self, artifact_id):
        """
        Retrieve an artifact from a Govern node

        :param str artifact_id: id of the artifact to retrieve

        :return: the corresponding :class:`govern.models.Artifact`
        """
        result = self._perform_json('GET', '/artifact/%s' % artifact_id)
        return GovernArtifact(self, artifact_id, result)

    def create_artifact(self, artifact):
        """
        Create an artifact on a Govern node

        :param artifact: the :class:`govern.models.Artifact` to create

        :return: the created :class:`govern.models.Artifact`
        """
        result = self._perform_json('POST', '/artifacts', body=artifact)
        return GovernArtifact(self, result.id, result)

    def delete_artifact(self, artifact_id):
        """
        Delete an artifact from a Govern node

        :param str artifact_id: id of the artifact to delete
        """
        self._perform_empty('DELETE', '/artifact/%s' % artifact_id)

    ########################################################
    # Custom  Pages
    ########################################################

    def get_custom_page_editor(self):
        """
        Return a handle to edit custom pages on the Govern instance

        :rtype: A :class:`dataikuapi.govern.custom_page_editor.GovernCustomPageEditor
        """
        return GovernCustomPageEditor(self)

    def get_artifact_sign_off_handler(self, artifact_id):
        """
        Return a handle to interact with the sign-off of a specific artifact

        :param str artifact_id: id of the artifact for which the handler will interact
        :rtype: A :class:`dataikuapi.govern.sign_off_handler.GovernArtifactSignOffHandler`
        """

        return GovernArtifactSignOffHandler(self, artifact_id)

    def get_artifact_search_handler(self):
        """
        Return a handle to build and perform artifact search requests.

        :rtype: A :class:`dataikuapi.govern.artifact_search_handler.GovernArtifactSearchHandler`
        """

        return GovernArtifactSearchHandler(self)

    def get_admin_roles_audit(self):
        """
        Return a handle to get audit information on roles and permissions for Govern objects.

        :rtype: A :class:`dataikuapi.govern.admin_roles_audit.GovernAdminRolesAudit`
        """

        return GovernAdminRolesAudit(self)

    def get_custom_page(self, custom_page_id):
        """
        Retrieve a custom page from a Govern node

        :param str custom_page_id: id of the custom page to retrieve

        :return: the corresponding :class:`govern.models.CustomPage`
        """
        result = self._perform_json('GET', '/customPage/%s' % custom_page_id)

        return GovernAdminCustomPage(self, custom_page_id, result)

    ########################################################
    # Users
    ########################################################

    def list_users(self, as_objects=False):
        """
        List all user setup on the DSS instance

        Note: this call requires an API key with admin rights

        :return: A list of users, as a list of :class:`dataikuapi.govern.admin.admin.GovernUser` if as_objects is True,
         else as a list of dicts
        :rtype: list of :class:`dataikuapi.govern.admin.admin.GovernUser` or list of dicts
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

        :return: A :class:`dataikuapi.govern.admin.admin.GovernUser` user handle
        """
        return GovernUser(self, login)

    def get_own_user(self):

        """
        Get a handle to interact with the current user


        :return: A :class:`dataikuapi.govern.admin.admin.GovernOwnUser` user handle
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

        :return: A :class:`dataikuapi.govern.admin.admin.GovernUser` user handle
        """
        if groups is None:
            groups = []

        self._perform_json('POST', '/admin/users/', body={
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
        return GovernGroup(self, name)
