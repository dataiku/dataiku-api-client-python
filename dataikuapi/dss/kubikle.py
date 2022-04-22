from ..utils import DataikuException
import json
from datetime import datetime

class DSSKubikleObjectListItem(object):
    """An item in a list of kubikles. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_kubikle_objects`"""
    def __init__(self, client, project_key, data):
        self.client = client
        self.project_key = project_key
        self._data = data

    def to_kubikle_object(self):
        """Gets the :class:`DSSKubikleTemplate` corresponding to this kubikle object """
        return DSSKubikleObject(self.client, self.project_key, self._data["id"])

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


class DSSKubikleObject(object):
    """
    A handle to manage a kubikle object of a project
    """
    def __init__(self, client, project_key, kubikle_object_id):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_kubikle_object`"""
        self.client = client
        self.project_key = project_key
        self.kubikle_object_id = kubikle_object_id

    def delete(self):
        """
        Delete the kubikle
        """
        self.client._perform_empty("DELETE", "/projects/%s/kubikles/%s" % (self.project_key, self.kubikle_object_id))

    def get_settings(self):
        """
        Get the kubikle object's settings

        :returns: a handle to manage the kubikle settings
        :rtype: :class:`dataikuapi.dss.kubikle.DSSKubikleObjectSettings`
        """
        settings = self.client._perform_json("GET", "/projects/%s/kubikles/%s" % (self.project_key, self.kubikle_object_id))
        return DSSKubikleObjectSettings(self.client, self.project_key, self.kubikle_object_id, settings)

    def get_status(self):
        """
        Get the kubikle object's state

        :returns: a handle to inspect the kubikle state
        :rtype: :class:`dataikuapi.dss.kubikle.DSSKubikleObjectStatus`
        """
        status = self.client._perform_json("GET", "/projects/%s/kubikles/%s/status" % (self.project_key, self.kubikle_object_id))
        return DSSKubikleObjectStatus(self.client, self.project_key, self.kubikle_object_id, status)

    def stop(self):
        """
        Stop a running kubikle

        :returns: a future to wait on the stop, or None if already stopped
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/kubikles/%s/stop" % (self.project_key, self.kubikle_object_id))
        if 'jobId' in ret:
            return self.client.get_future(ret["jobId"])
        else:
            return None

    def restart(self):
        """
        Restart a kubikle

        :returns: a future to wait on the start
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/kubikles/%s/restart" % (self.project_key, self.kubikle_object_id))
        if 'jobId' in ret:
            return self.client.get_future(ret["jobId"])
        else:
            return None

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

class DSSKubikleObjectStatus(object):
    """
    Status of a kubikle object
    """
    def __init__(self, client, project_key, kubikle_object_id, status):
        """Do not call directly, use :meth:`dataikuapi.dss.kubikle.DSSKubikleObject.get_state`"""
        self.client = client
        self.project_key = project_key
        self.kubikle_object_id = kubikle_object_id
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
    def last_built(self):
        ts = self.status.get("lastStateChange", 0)
        if ts > 0:
            return datetime.fromtimestamp(ts / 1000)
        else:
            return None
