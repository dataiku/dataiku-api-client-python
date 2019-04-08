from .project import DSSProject

class DSSProjectFolder(object):
    """
    A handle to interact with a project folder on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_project_folder` or :meth:`dataikuapi.DSSClient.get_root_project_folder`
    """
    def __init__(self, client, project_folder_id):
        self.client = client
        self.project_folder_id = project_folder_id

    ########################################################
    # Project folder basics
    ########################################################
    def get_name(self):
        """
        Get this project folder's name or None if it is the root project folder

        :returns str: the name of this project folders or None for the root project folder
        """
        return self.client._perform_json("GET", "/project-folders/%s" % self.project_folder_id).get("name", None)

    def get_parent(self):
        """
        Get this project folder's parent or None if it is the root project folder

        :returns: A :class:`dataikuapi.dss.projectfolders.DSSProjectFolder` to interact with its parent or None for the root project folder
        """
        parent = self.client._perform_json("GET", "/project-folders/%s" % self.project_folder_id).get("parent", None)
        if parent is None:
            return None
        else:
            return DSSProjectFolderSettings(self.client, parent)

    def get_children(self):
        """
        Get this project folder's children

        :returns list: A list of :class:`dataikuapi.dss.projectfolders.DSSProjectFolder` to interact with its children
        """
        children = self.client._perform_json("GET", "/project-folders/%s" % self.project_folder_id).get("children", [])
        ret = []
        for child in children:
            ret.append(DSSProjectFolder(self.client, child))
        return ret

    def get_projects(self):
        """
        Get this project folder's projects

        :returns list:  A list of :class:`dataikuapi.dss.project.DSSProject` to interact with its projects
        """
        project_keys = self.client._perform_json("GET", "/project-folders/%s" % self.project_folder_id).get("projectKeys", [])
        ret = []
        for pkey in project_keys:
            ret.append(DSSProject(self.client, pkey))
        return ret

    ########################################################
    # Project folder deletion
    ########################################################
    def delete(self):
        """
        Delete the project folder

        This call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/project-folders/%s" % self.project_folder_id)

    ########################################################
    # Project folder settings
    ########################################################
    def get_settings(self):
        """
        :returns: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolderSettings` to interact with this project folder settings
        """
        settings = self.client._perform_json("GET", "/project-folders/%s/settings" % self.project_folder_id)
        return DSSProjectFolderSettings(self.client, self.project_folder_id, settings)

    ########################################################
    # Project folder sub-folder creation
    ########################################################
    def create_sub_folder(self, name):
        """
        Create a sub-folder into the current project folder

        :param str name: the name of the project folder to create
        :returns: A :class:`dataikuapi.dss.projectfolder.DSSProjectFolder` to interact with the newly created project folder
        """
        body = {
            "name": name
        }
        pf = self.client._perform_json("POST", "/project-folders/%s/children" % self.project_folder_id, body = body)
        return DSSProjectFolder(self.client, pf["id"])

    ########################################################
    # Project creation
    ########################################################
    def create_project(self, project_key, name, owner, description=None, settings=None):
        """
        Creates a new project within this project folder, and return a project handle to interact with it.

        Note: this call requires an API key with admin rights or the rights to create a project

        :param str project_key: the identifier to use for the project. Must be globally unique
        :param str name: the display name for the project.
        :param str owner: the login of the owner of the project.
        :param str description: a description for the project.
        :param dict settings: Initial settings for the project (can be modified later). The exact possible settings are not documented.
        
        :returns: A class:`dataikuapi.dss.project.DSSProject` project handle to interact with this project
        """
        resp = self._perform_text(
               "POST", "/project-folders/%s/projects" % self.project_folder_id, body={
                   "projectKey" : project_key,
                   "name" : name,
                   "owner" : owner,
                   "settings" : settings,
                   "description" : description
               })
        return DSSProject(self, project_key)

    ########################################################
    # Project folder move
    ########################################################
    def move(self, destination):
        """
        Move this project folder into another project folder (aka. destination)

        :param destination: the project folder to put this project folder into
        :type destination: A :class:`dataikuapi.dss.projectfolders.DSSProjectFolder`
        """
        body = {
            "destination": destination.project_folder_id
        }
        self.client._perform_json("POST", "/project-folders/%s/move" % self.project_folder_id, body = body)

    ########################################################
    # Project move
    ########################################################
    def project_move(self, project_key, destination):
        """
        Move a project within this project folder into another project folder (aka. destination)

        :param str project_key: the project key associated with the project to move
        :param destination: the project folder to put this project into
        :type destination: A :class:`dataikuapi.dss.projectfolders.DSSProjectFolder`
        """
        body = {
            "destination": destination.project_folder_id
        }
        self.client._perform_json("POST", "/project-folders/%s/children/%s/move" % (self.project_folder_id, project_key), body = body)

class DSSProjectFolderSettings(object):
    """
    A handle to interact with project folder settings

    Do not create this class directly, instead use :meth:`dataikuapi.dss.projectfolder.DSSProjectFolder.get_settings`
    """
    def __init__(self, client, project_folder_id, settings):
        self.client = client
        self.project_folder_id = project_folder_id
        self.settings = settings

    def get_raw(self):
        """Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """Saves back the settings to the project folder"""
        self.client._perform_empty("PUT", "/project-folders/%s/settings" % (self.project_folder_id), body = self.settings)
