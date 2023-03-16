from .project import DSSProject
import warnings


class DSSProjectFolder(object):
    """
    A handle for a project folder on the DSS instance.

    .. important::
        Do not instantiate this class directly,
        instead use :meth:`dataikuapi.DSSClient.get_project_folder`
        or :meth:`dataikuapi.DSSClient.get_root_project_folder`.
    """

    def __init__(self, client, data):
        self.client = client
        self._data = data

    ########################################################
    # Project folder basics
    ########################################################

    @property
    def id(self):
        """
        :returns: The project folder id.
        :rtype: string
        """
        return self._data["id"]

    @property
    def project_folder_id(self):
        """
        .. caution::
            Deprecated. Please use :attr:`dataikuapi.dss.projectfolder.DSSProjectFolder.id`.
        """
        warnings.warn("DSSProjectFolder.project_folder_id is deprecated, please use id", DeprecationWarning)
        return self.id

    @property
    def name(self):
        """
        :returns: The project folder name or :const:`None` for the root project folder.
        :rtype: string
        """
        return self._data.get("name", None)

    def get_name(self):
        """
        See :attr:`dataikuapi.dss.projectfolder.DSSProjectFolder.name`.

        :returns: The project folder name or :const:`None` for the root project folder.
        :rtype: string
        """
        return self.name

    def get_path(self):
        """
        :returns: The project folder path from the root project folder (e.g. :const:`'/'` or :const:`'/foo/bar'`).
        :rtype: string
        """
        parent = self.get_parent()
        if parent is not None:
            path = parent.get_path()
            return ("" if path == "/" else path) + "/" + self.name
        else:
            return "/"

    def get_parent(self):
        """
        :returns: A handle for the parent folder or :const:`None` for the root project folder.
        :rtype: :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        parent_id = self._data.get("parentId", None)
        if parent_id is None:
            return None
        else:
            return self.client.get_project_folder(parent_id)

    def list_child_folders(self):
        """
        :returns: Handles for every child project folder.
        :rtype: list of :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        return [self.client.get_project_folder(child_id) for child_id in self._data["childrenIds"]]

    def list_project_keys(self):
        """
        :returns: The project keys of all projects stored in this project folder.
        :rtype: list of string
        """
        return self._data["projectKeys"]

    def list_projects(self):
        """
        :returns: Handles for every project stored in this project folder.
        :rtype: list of :class:`dataikuapi.dss.project.DSSProject`
        """
        return [self.client.get_project(pkey) for pkey in self.list_project_keys()]

    ########################################################
    # Project folder deletion
    ########################################################
    def delete(self):
        """
        Delete this project folder.

        .. important::
            This project folder must be empty, i.e. contain no project or subfolder.
            You must move or remove all this project folder content prior to deleting it.
        .. attention::
            This call requires an API key with admin rights.
        """
        return self.client._perform_empty("DELETE", "/project-folders/%s" % self.id)

    ########################################################
    # Project folder settings
    ########################################################
    def get_settings(self):
        """
        :returns: A handle for this project folder settings.
        :rtype: :class:`dataikuapi.dss.projectfolder.DSSProjectFolderSettings`
        """
        settings = self.client._perform_json("GET", "/project-folders/%s/settings" % self.id)
        return DSSProjectFolderSettings(self.client, self.id, settings)

    ########################################################
    # Project folder subfolder creation
    ########################################################
    def create_sub_folder(self, name):
        """
        Create a project subfolder inside this project folder.

        :param str name: The name of the project subfolder to create.
        :returns: A handle for the created project subfolder.
        :rtype: :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        params = {
            "name": name
        }
        pf = self.client._perform_json("POST", "/project-folders/%s/children" % self.id, params=params)
        return DSSProjectFolder(self.client, pf)

    ########################################################
    # Project creation
    ########################################################
    def create_project(self, project_key, name, owner, description=None, settings=None):
        """
        Create a new project within this project folder.
        Return a handle for the created project.

        .. important::
            The provided identifier for the new project must be globally unique.
        .. attention::
            This call requires an API key with admin rights or the right to create a project.

        :param str project_key: The identifier for the new project. Must be globally unique.
        :param str name: The displayed name for the new project.
        :param str owner: The login of the new project owner.
        :param str description: The description for the new project.
        :param dict settings: The initial settings for the new project. The settings can be modified later. The exact possible settings are not documented.

        :returns: A handle for the created project.
        :rtype: :class:`dataikuapi.dss.project.DSSProject`
        """
        return self.client.create_project(project_key, name, owner, description=description, settings=settings, project_folder_id=self.id)

    ########################################################
    # Project folder move
    ########################################################
    def move_to(self, destination):
        """
        Move this project folder into another project folder.

        :param destination: The new parent project folder of this project folder.
        :type destination: :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        params = {
            "destination": destination.id
        }
        self.client._perform_empty("POST", "/project-folders/%s/move" % self.id, params=params)

    ########################################################
    # Project move
    ########################################################
    def move_project_to(self, project_key, destination):
        """
        Move a project from this project folder into another project folder.

        :param str project_key: The identifier of the project to move.
        :param destination: The new parent project folder of the project.
        :type destination: :class:`dataikuapi.dss.projectfolder.DSSProjectFolder`
        """
        # Be nice with what people pass
        if isinstance(project_key, DSSProject):
            project_key = project_key.project_key
        params = {
            "destination": destination.id
        }
        self.client._perform_empty("POST", "/project-folders/%s/projects/%s/move" % (self.id, project_key), params=params)


class DSSProjectFolderSettings(object):
    """
    A handle for a project folder settings.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.projectfolder.DSSProjectFolder.get_settings`.
    """

    def __init__(self, client, project_folder_id, settings):
        self.client = client
        self.id = project_folder_id
        self.settings = settings

    def get_raw(self):
        """
        Get the settings of the project folder as a python dict.

        .. important::
            Returns a reference to the raw settings in opposition to a copy.
            Changes through the reference will be effective upon saving.

        :returns: The settings of the project folder as a python dict containing the keys:

            * **name**: the name of the project folder,
            * **owner**: the login of the project folder owner,
            * **permissions**: the list of the project folder permissions.

        :rtype: python dict
        """
        return self.settings

    def get_name(self):
        """
        :returns: The name of the project folder.
        :rtype: string
        """
        return self.settings.get("name", None)

    def set_name(self, name):
        """
        Set the name of the project folder.

        :param str name: The new name of the project folder.
        """
        self.settings["name"] = name

    def get_owner(self):
        """
        :returns: The login of the project folder owner.
        :rtype: string
        """
        return self.settings.get("owner", None)

    def set_owner(self, owner):
        """
        Set the owner of the project folder.

        :param str owner: The login of the new project folder owner.
        """
        self.settings["owner"] = owner

    def get_permissions(self):
        """
        Get the permissions of the project folder.

        .. important::
            Returns a reference to the permissions in opposition to a copy.
            Changes through the reference will be effective upon saving.

        :returns: The permissions of the project folder.
        :rtype: list of string
        """
        return self.settings["permissions"]

    def save(self):
        """
        Save back the settings to the project folder.
        """
        self.client._perform_empty("PUT", "/project-folders/%s/settings" % (self.id), body = self.settings)
