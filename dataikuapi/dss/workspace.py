from dataikuapi.dss.app import DSSApp
from dataikuapi.dss.dataset import DSSDataset
from dataikuapi.dss.wiki import DSSWikiArticle


class DSSWorkspace:
    """
    A handle to interact with a workspace on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_workspace`
    """

    def __init__(self, client, workspace_key):
        self.client = client
        self.workspace_key = workspace_key

    def get_settings(self):
        """
        Gets the settings of this workspace.

        :returns: a handle to read, modify and save the settings
        :rtype: :class:`DSSWorkspaceSettings`
        """
        return DSSWorkspaceSettings(self, self.client._perform_json("GET", "/workspaces/%s" % self.workspace_key))

    def list_objects(self):
        """
        List the objects in this workspace

        :returns: The list of the objects
        :rtype: list of :class:`.DSSWorkspaceObject`
        """
        objects = self.client._perform_json("GET", "/workspaces/%s/objects" % self.workspace_key)
        return [DSSWorkspaceObject(self, object) for object in objects]

    def add_object(self, object):
        """
        Add an object to this workspace.
        Object can be of different shapes (:class:`dataikuapi.dss.dataset.DSSDataset`, :class:`dataikuapi.dss.wiki.DSSWikiArticle`, :class:`dataikuapi.dss.app.DSSApp`, :class:`.DSSWorkspaceHtmlLinkObject` or a :class:`.dict` that contains the raw data)
        """
        if isinstance(object, DSSDataset):
            data = {"reference": {"projectKey": object.project_key, "type": "DATASET", "id": object.dataset_name}}
        elif isinstance(object, DSSWikiArticle):
            data = {"reference": {"projectKey": object.project_key, "type": "ARTICLE", "id": object.article_id}}
        elif isinstance(object, DSSApp):
            data = {"appId": object.app_id}
        elif isinstance(object, DSSWorkspaceHtmlLinkObject):
            data = {"htmlLink": {"name": object.name, "url": object.url, "description": object.description}}
        elif isinstance(object, dict):
            data = object
        else:
            raise ValueError("Unsupported object type")
        self.client._perform_json("POST", "/workspaces/%s/objects" % self.workspace_key, body=data)

    def delete(self):
        """
        Delete the workspace

        This call requires Administrator rights on the workspace.
        """
        return self.client._perform_empty("DELETE", "/workspaces/%s" % self.workspace_key)


class DSSWorkspaceHtmlLinkObject:
    def __init__(self, name, url, description):
        self.name = name
        self.url = url
        self.description = description


class DSSWorkspaceObject:
    """
    A handle on an object of a workspace

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSWorkspace.list_objects`
    """

    def __init__(self, workspace, data):
        self.workspace = workspace
        self.data = data

    def get_raw(self):
        return self.data

    def remove(self):
        """
        Remove this object from the workspace
        
        This call requires Contributor rights on the workspace.
        """
        self.workspace.client._perform_empty(
            "DELETE", "/workspaces/%s/objects/%s" % (self.workspace.workspace_key, self.data['id']))


class DSSWorkspaceSettings:
    """
    A handle on the settings of a workspace

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSWorkspace.get_settings`
    """

    def __init__(self, workspace, settings):
        self.workspace = workspace
        self.settings = settings

    def get_raw(self):
        return self.settings

    @property
    def display_name(self):
        """
        Get or set the name of the workspace

        :rtype: :class:`str`
        """
        return self.settings['displayName']

    @display_name.setter
    def display_name(self, value):
        self.settings['displayName'] = value

    @property
    def color(self):
        """
        Get or set the background color of the workspace (using #xxxxxx syntax)

        :rtype: :class:`str`
        """
        return self.settings['color']

    @color.setter
    def color(self, value):
        self.settings['color'] = value

    @property
    def description(self):
        """
        Get or set the description of the workspace

        :rtype: :class:`str`
        """
        return self.settings['description']

    @description.setter
    def description(self, value):
        self.settings['description'] = value

    @property
    def permissions(self):
        """
        Get or set the permissions controlling who is a member, contributor or admin of the workspace

        :rtype: list of :class:`.DSSWorkspacePermissionItem`
        """
        return [DSSWorkspacePermissionItem(permission) for permission in self.settings['permissions']]

    @permissions.setter
    def permissions(self, value):
        self.settings['permissions'] = value

    @property
    def current_user_permissions(self):
        """
        Permissions of the current user (read-only)

        :rtype: :class:`.DSSWorkspacePermissionItem`
        """
        return DSSWorkspacePermissionItem(self.settings['currentUserPermissions'])

    def save(self):
        """
        Save the changes made on the settings
        
        This call requires Administrator rights on the workspace.
        """
        self.workspace.client._perform_empty(
            "PUT", "/workspaces/%s" % self.workspace.workspace_key,
            body=self.settings)


class DSSWorkspacePermissionItem(dict):
    def __init__(self, data):
        super(DSSWorkspacePermissionItem, self).__init__(data)

    @classmethod
    def admin_group(cls, group):
        return cls({"group": group, "admin": True, "write": True, "read": True})

    @classmethod
    def contributor_group(cls, group):
        return cls({"group": group, "admin": False, "write": True, "read": True})

    @classmethod
    def member_group(cls, group):
        return cls({"group": group, "admin": False, "write": False, "read": True})

    @classmethod
    def admin_user(cls, user):
        return cls({"user": user, "admin": True, "write": True, "read": True})

    @classmethod
    def contributor_user(cls, user):
        return cls({"user": user, "admin": False, "write": True, "read": True})

    @classmethod
    def member_user(cls, user):
        return cls({"user": user, "admin": False, "write": False, "read": True})

    @property
    def user(self):
        """
        Get user login

        :rtype: :class:`str`
        """
        return self['user']

    @property
    def group(self):
        """
        Get group name

        :rtype: :class:`str`
        """
        return self['group']

    @property
    def admin(self):
        """
        Get admin permission

        :rtype: :class:`boolean`
        """
        return self['admin']

    @property
    def write(self):
        """
        Get write permission

        :rtype: :class:`boolean`
        """
        return self['write']

    @property
    def read(self):
        """
        Get read permission

        :rtype: :class:`boolean`
        """
        return self['read']
