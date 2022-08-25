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

        :returns a handle to read, modify and save the settings
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

        This call requires an API key with admin rights
        """
        return self.client._perform_empty("DELETE", "/workspaces/%s" % self.workspace_key)

class DSSWorkspaceHtmlLinkObject:
    def __init__(self, name, url, description):
        self.name = name
        self.url = url
        self.description = description

class DSSWorkspaceObject:
    """
    A handle on the settings of a workspace

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSWorkspace.list_objects`
    """
    def __init__(self, workspace, data):
        self.workspace = workspace
        self.data = data

    def get_raw(self):
        return self.data

    def remove(self):
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

    def save(self):
        self.workspace.client._perform_empty(
            "PUT", "/workspaces/%s" % self.workspace.workspace_key,
            body=self.settings)