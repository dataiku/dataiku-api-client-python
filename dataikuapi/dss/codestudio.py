from ..utils import DataikuException
import json
from datetime import datetime

class DSSCodeStudioObjectListItem(object):
    """An item in a list of code studios. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_code_studios`"""
    def __init__(self, client, project_key, data):
        self.client = client
        self.project_key = project_key
        self._data = data

    def to_code_studio(self):
        """Gets the :class:`DSSCodeStudioObject` corresponding to this code studio object """
        return DSSCodeStudioObject(self.client, self.project_key, self._data["id"])

    @property
    def name(self):
        return self._data["name"]
    @property
    def id(self):
        return self._data["id"]
    @property
    def owner(self):
        return self._data["owner"]
    @property
    def template_id(self):
        return self._data["templateId"]
    @property
    def template_label(self):
        return self._data.get('desc', {}).get('label', self._data['id'])
    @property
    def template_description(self):
        return self._data.get('desc', {}).get('shortDesc', '')


class DSSCodeStudioObject(object):
    """
    A handle to manage a code studio object of a project
    """
    def __init__(self, client, project_key, code_studio_id):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_code_studio`"""
        self.client = client
        self.project_key = project_key
        self.code_studio_id = code_studio_id

    def delete(self):
        """
        Delete the code studio
        """
        self.client._perform_empty("DELETE", "/projects/%s/code-studios/%s" % (self.project_key, self.code_studio_id))

    def get_settings(self):
        """
        Get the code studio object's definition

        :returns: a handle to manage the code studio definition
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObjectSettings`
        """
        settings = self.client._perform_json("GET", "/projects/%s/code-studios/%s" % (self.project_key, self.code_studio_id))
        return DSSCodeStudioObjectSettings(self.client, self.project_key, self.code_studio_id, settings)

    def get_status(self):
        """
        Get the code studio object's state

        :returns: a handle to inspect the code studio state
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObjectStatus`
        """
        status = self.client._perform_json("GET", "/projects/%s/code-studios/%s/status" % (self.project_key, self.code_studio_id))
        return DSSCodeStudioObjectStatus(self.client, self.project_key, self.code_studio_id, status)

    def stop(self):
        """
        Stop a running code studio

        :returns: a future to wait on the stop, or None if already stopped
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/code-studios/%s/stop" % (self.project_key, self.code_studio_id))
        return DSSFuture.from_resp(self.client, ret)

    def restart(self):
        """
        Restart a code studio

        :returns: a future to wait on the start
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/code-studios/%s/restart" % (self.project_key, self.code_studio_id))
        return DSSFuture.from_resp(self.client, ret)

class DSSCodeStudioObjectSettings(object):
    """
    Settings for the code studio object
    """
    def __init__(self, client, project_key, code_studio_id, settings):
        """Do not call directly, use :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObject.get_settings`"""
        self.client = client
        self.project_key = project_key
        self.code_studio_id = code_studio_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        """
        return self.settings

    @property
    def template_id(self):
        return self.settings["templateId"]
    @property
    def lib_name(self):
        return self.settings["libName"]


class DSSCodeStudioObjectStatus(object):
    """
    Status of a code studio object
    """
    def __init__(self, client, project_key, code_studio_id, status):
        """Do not call directly, use :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObject.get_state`"""
        self.client = client
        self.project_key = project_key
        self.code_studio_id = code_studio_id
        self.status = status

    def get_raw(self):
        """
        Gets the status as a raw dictionary. This returns a reference to the raw status, not a copy,
        """
        return self.status

    @property
    def state(self):
        return self.status["state"]
    @property
    def last_state_change(self):
        ts = self.status.get("lastStateChange", 0)
        if ts > 0:
            return datetime.fromtimestamp(ts / 1000)
        else:
            return None
