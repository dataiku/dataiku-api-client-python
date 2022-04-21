from ..utils import DataikuException
import json

class DSSKubikleObject(object):
    """
    A handle to manage a kubikle object of a project
    """
    def __init__(self, client, project_key, kubikle_object_id):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_kubikle_object`"""
        self.client = client
        self.project_key = project_key
        self.kubikle_object_id = kubikle_object_id

    def get_settings(self):
        """
        Get the kubikle object's settings

        :returns: a handle to manage the wiki settings (taxonomy, home article)
        :rtype: :class:`dataikuapi.dss.kubikle.DSSKubikleObjectSettings`
        """
        settings = self.client._perform_json("GET", "/projects/%s/kubikles/%s" % (self.project_key, self.kubikle_object_id))
        return DSSKubikleObjectSettings(self.client, self.project_key, self.kubikle_object_id, settings)


class DSSKubikleObjectSettings(object):
    """
    Settings for the kubikle object
    """
    def __init__(self, client, project_key, kubikle_object_id, settings):
        """Do not call directly, use :meth:`dataikuapi.dss.kubikle.DSSKubikleObject.get_settings`"""
        self.client = client
        self.project_key = project_key
        self.kubikle_object_id = kubikle_object_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        """
        return self.settings

