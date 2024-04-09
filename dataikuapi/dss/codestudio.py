from ..utils import DataikuException, _timestamp_ms_to_zoned_datetime
import json
from datetime import datetime
from .future import DSSFuture

class DSSCodeStudioObjectListItem(object):
    """
    An item in a list of code studios.

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_code_studios`
    """
    def __init__(self, client, project_key, data):
        self.client = client
        self.project_key = project_key
        self._data = data

    def to_code_studio(self):
        """
        Get a handle to interact with this code studio

        :return: a handle on the code studio
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObject`
        """
        return DSSCodeStudioObject(self.client, self.project_key, self._data["id"])

    @property
    def name(self):
        """
        Get the name of the code studio

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: string
        """
        return self._data["name"]
    @property
    def id(self):
        """
        Get the identifier of the code studio

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self._data["id"]
    @property
    def owner(self):
        """
        Get the login of the owner of the code studio

        :rtype: string
        """
        return self._data["owner"]
    @property
    def template_id(self):
        """
        Get the identifier of the template that this code studio was created from

        :rtype: string
        """
        return self._data["templateId"]
    @property
    def template_label(self):
        """
        Get the label of the template that this code studio was created from

        :rtype: string
        """
        return self._data.get('desc', {}).get('label', self._data['id'])
    @property
    def template_description(self):
        """
        Get the description of the template that this code studio was created from

        :rtype: string
        """
        return self._data.get('desc', {}).get('shortDesc', '')


class DSSCodeStudioObject(object):
    """
    A handle to manage a code studio in a project

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_code_studio`
        or :meth:`dataikuapi.dss.project.DSSProject.create_code_studio` instead
    """
    def __init__(self, client, project_key, code_studio_id):
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
        Get the code studio's definition

        Usage example

        .. code-block:: python

            # list code studios of some user
            for code_studio in project.list_code_studios(as_type="objects"):
                settings = code_studio.get_settings()
                if settings.owner == 'the_user_login':
                    print("User owns code studio %s from template %s" % (settings.name, settings.template_id))

        :return: a handle to inspect the code studio definition
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObjectSettings`
        """
        settings = self.client._perform_json("GET", "/projects/%s/code-studios/%s" % (self.project_key, self.code_studio_id))
        return DSSCodeStudioObjectSettings(self.client, self.project_key, self.code_studio_id, settings)

    def get_status(self):
        """
        Get the code studio's state

        Usage example

        .. code-block:: python

            # print list of currently running code studios
            for code_studio in project.list_code_studios(as_type="objects"):
                status = code_studio.get_status()
                if status.state == 'RUNNING':
                    settings = code_studio.get_settings()
                    print("Code studio %s from template %s is running" % (settings.name, settings.template_id))


        :return: a handle to inspect the code studio state
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObjectStatus`
        """
        status = self.client._perform_json("GET", "/projects/%s/code-studios/%s/status" % (self.project_key, self.code_studio_id))
        return DSSCodeStudioObjectStatus(self.client, self.project_key, self.code_studio_id, status)

    def stop(self):
        """
        Stop a running code studio

        :return: a future to wait on the stop, or None if already stopped
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/code-studios/%s/stop" % (self.project_key, self.code_studio_id))
        return DSSFuture.from_resp(self.client, ret)

    def restart(self):
        """
        Start or restart a code studio

        :return: a future to wait on the start
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/projects/%s/code-studios/%s/restart" % (self.project_key, self.code_studio_id))
        return DSSFuture.from_resp(self.client, ret)

    def check_conflicts(self, zone):
        """
        Checks whether the files in a zone of the code studio have conflicting changes
        with what the DSS instance has.

        Usage example

        .. code-block:: python

            # stop a code studio if there's no conflict in any zone
            status = code_studio.get_status()
            conflict_count = 0
            for zone in status.get_zones(as_type="names"):
                conflicts = code_studio.check_conflicts(zone)
                conflict_count += len(conflicts.added)
                conflict_count += len(conflicts.modified)
                conflict_count += len(conflicts.deleted)
            if conflict_count == 0:
                code_studio.stop().wait_for_result()


        :param string zone: name of the zone to check (see :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObjectStatus.get_zones`)

        :return: a summary of the conflicts that were found.
        :rtype: :class:`DSSCodeStudioObjectConflicts`
        """
        conflicts = self.client._perform_json("GET", "/projects/%s/code-studios/%s/conflicts/%s" % (self.project_key, self.code_studio_id, zone))
        return DSSCodeStudioObjectConflicts(zone, conflicts)

    def pull_from_code_studio(self, zone):
        """
        Copies the files from a zone of the code studio to the DSS instance

        :param str zone: name of the zone to pull (see :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObjectStatus.get_zones`)
        """
        return self.client._perform_json("GET", "/projects/%s/code-studios/%s/pull/%s" % (self.project_key, self.code_studio_id, zone))

    def push_to_code_studio(self, zone):
        """
        Copies the files from the DSS instance to a zone of the code studio

        :param str zone: name of the zone to push (see :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObjectStatus.get_zones`)

        :return: a dictionary of {count: <number of files copied>, size: <total size copied>}
        :rtype: dict
        """
        return self.client._perform_json("GET", "/projects/%s/code-studios/%s/push/%s" % (self.project_key, self.code_studio_id, zone))

    def change_owner(self, new_owner):
        """
        Allows to change the owner of the Code Studio
        
        .. note::

            You need to be either admin or owner of the Code Studio in order to change the owner.

        :param str new_owner: the id of the new owner

        :return: a handle on the updated code studio
        :rtype: :class:`dataikuapi.dss.codestudio.DSSCodeStudioObject`
        """
        return self.client._perform_json("POST", "/projects/%s/code-studios/%s/change-owner?newOwner=%s"  % (self.project_key, self.code_studio_id, new_owner))

class DSSCodeStudioObjectConflicts(dict):
    """
    Summary of the conflicts on zones of a code studio.

    .. note::

        Only conflicting files are listed, that is, files added, modified or deleted in the code studio for which
        the corresponding file in the DSS instance has been also added, modified or deleted.
    """
    def __init__(self, zone, conflicts):
        super(DSSCodeStudioObjectConflicts, self).__init__(conflicts)
        self._zone = zone
        self._conflicts = conflicts

    def get_raw(self):
        """
        Get the raw conflicts summary.

        :return: a summary of the conflicts that were found, as a dict. The top-level field is the zone checked, or 'error' if it wasn't found. The dict should
                 contain summary information about the count of changes, and **commitFrom** and **commitTo** hashes to identify the state of the files
                 on the DSS instance at the time of the last sync to the code studio pod and now.

        :rtype: dict
        """
        return self._conflicts

    @property
    def is_error(self):
        """
        Whether fetching the conflicts failed.

        Typically this can happen if the name of the zone(s) for which the conflicts where requested
        is invalid.

        :rtype: boolean
        """
        return "error" in self._conflicts

    @property
    def authors(self):
        """
        Get the authors of changes to the files.

        :return: a list of logins of users who modified the conflicting files in the DSS instance.
        :rtype: list[string]
        """
        return self._conflicts.get(self._zone, {}).get("authors", [])

    @property
    def added(self):
        """
        Get the list of files added in the code studio.

        :return: a list of paths to files that were added in the code studio and conflict with changes on the DSS instance.
        :rtype: list[string]
        """
        return self._conflicts.get(self._zone, {}).get("added", [])

    @property
    def modified(self):
        """
        Get the list of files modified in the code studio.

        :return: a list of paths to files that were modified in the code studio and conflict with changes on the DSS instance.
        :rtype: list[string]
        """
        return self._conflicts.get(self._zone, {}).get("modified", [])

    @property
    def deleted(self):
        """
        Get the list of files deleted in the code studio.

        :return: a list of paths to files that were deleted in the code studio and conflict with changes on the DSS instance.
        :rtype: list[string]
        """
        return self._conflicts.get(self._zone, {}).get("deleted", [])


class DSSCodeStudioObjectSettings(object):
    """
    Settings for a code studio

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObject.get_settings` instead

    """
    def __init__(self, client, project_key, code_studio_id, settings):
        self.client = client
        self.project_key = project_key
        self.code_studio_id = code_studio_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary.

        :return: the settings, as a dict. The dict contains a **templateId** field indicating which code studio template
                 was used to create this code studio.

        :rtype: dict
        """
        return self.settings

    @property
    def id(self):
        """
        Get the identifier of the code studio.

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self.settings["id"]

    @property
    def name(self):
        """
        Get the name of the code studio.

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: string
        """
        return self.settings["name"]

    @property
    def template_id(self):
        """
        Get the identifier of the template that the code studio was created from.

        :rtype: string
        """
        return self.settings["templateId"]

    @property
    def lib_name(self):
        """
        Get the name of the folder resource files of the code studio are stored in.

        The path to the resources files is then "<dss_data_dir>/lib/code_studio/<project_key>/<lib_name>/"

        :rtype: string
        """
        return self.settings["libName"]

    @property
    def owner(self):
        """
        Get the login of the owner of the code studio.

        Only the owner of a code studio can use it. Administrators of the project can merely stop/start
        code studios, not use them.

        :rtype: string
        """
        return self.settings["owner"]


class DSSCodeStudioObjectStatus(object):
    """
    Handle to inspect the status of a code studio

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.codestudio.DSSCodeStudioObject.get_status()` instead
    """
    def __init__(self, client, project_key, code_studio_id, status):
        self.client = client
        self.project_key = project_key
        self.code_studio_id = code_studio_id
        self.status = status

    def get_raw(self):
        """
        Gets the status as a raw dict.

        .. note::

            Some fields are only defined when the code studio is running. For instance, **exposed** and **syncedZones**
            are empty when the code studio is not running.

        :return: the dict contains a **state** field indicating whether the code studio is STOPPED, STARTING, RUNNING or STOPPING.
                 If RUNNING, then the dict holds additional information about the zones that can be synchronized inside the pod, and
                 the ports of the pod that are exposed.

        :rtype: dict
        """
        return self.status

    @property
    def state(self):
        """
        Get the current state of the code studio.

        Possible values are STOPPED, STARTING, RUNNING, STOPPING

        :rtype: string
        """
        return self.status["state"]

    @property
    def last_state_change(self):
        """
        Get the timestamp of the last change of the state.

        :return: a datetime, or None if the code studio was never started
        :rtype: `datetime.datetime`
        """
        ts = self.status.get("lastStateChange", 0)
        return _timestamp_ms_to_zoned_datetime(ts)

    def get_zones(self, as_type="names"):
        """
        Get the list of the zones synchronized inside the code studio

        :param string as_type: if set to "names", then return a list of zone identifiers; if set to "objects", then return
                               a list of zone definitions

        :return: the list of zones, each one either a string (if `as_type` is "names), or a dict of with a **id** field.
        :rtype: list
        """
        zones = self.status.get("syncedZones", [])
        if as_type == 'name' or as_type == 'names':
            return [z.get('id') for z in zones]
        if as_type == 'object' or as_type == 'objects':
            return zones
        else:
            raise Exception("Only 'names' or 'objects' is supported for as_type")

