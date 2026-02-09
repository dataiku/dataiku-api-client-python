import sys

from .future import DSSFuture


class DSSBusinessAppListItem(object):
    """
    An item in a list of Business Applications.

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_business_apps` instead
    """
    def __init__(self, client, data):
        self.client = client
        self._data = data

    @property
    def id(self):
        """
        Get the identifier of the Business Application.

        :rtype: str
        """
        return self._data["id"]

    @property
    def version(self):
        """
        Get the version of the Business Application.

        :rtype: str
        """
        return self._data["version"]

    @property
    def name(self):
        """
        Get the name of the Business Application.

        :rtype: str
        """
        return self._data["name"]

    @property
    def description(self):
        """
        Get the description of the Business Application.

        :rtype: str
        """
        return self._data.get("description")

    def get_raw(self):
        """
        Get the raw data of this list item.

        :return: the raw data as a dict
        :rtype: dict
        """
        return self._data

    def to_business_app(self):
        """
        Get a handle corresponding to this Business Application.

        :return: a handle to interact with the Business Application
        :rtype: :class:`DSSBusinessApp`
        """
        return DSSBusinessApp(self.client, self._data["id"])


class DSSBusinessApp(object):
    """
    A handle to interact with a Business Application on the DSS instance.

    .. important::

        Do not instantiate this class directly, instead use :meth:`dataikuapi.DSSClient.get_business_app`
    """
    def __init__(self, client, business_app_id):
        self.client = client
        self.business_app_id = business_app_id

    @property
    def id(self):
        """
        Get the ID of the Business Application.

        :rtype: str
        """
        return self.business_app_id

    def get_details(self):
        """
        Get detailed information about this Business Application.

        :return: the details of the Business Application
        :rtype: :class:`DSSBusinessAppDetails`
        """
        data = self.client._perform_json("GET", "/business-apps/%s" % self.business_app_id)
        return DSSBusinessAppDetails(self.client, self.business_app_id, data)

    def get_settings(self):
        """
        Get the settings of this Business Application.

        :return: the settings of the Business Application
        :rtype: :class:`DSSBusinessAppSettings`
        """
        data = self.client._perform_json("GET", "/business-apps/%s/settings" % self.business_app_id)
        return DSSBusinessAppSettings(self.client, self.business_app_id, data)

    def list_instances(self):
        """
        List the existing instances of this Business Application.

        :return: a list of instances
        :rtype: list of :class:`DSSBusinessAppInstanceListItem`
        """
        items = self.client._perform_json("GET", "/business-apps/%s/instances" % self.business_app_id)
        return [DSSBusinessAppInstanceListItem(self.client, self.business_app_id, item) for item in items]

    def get_instance(self, project_key):
        """
        Get a handle on a particular instance of this Business Application.

        :param str project_key: the project key of the instance
        :return: a handle to interact with the instance
        :rtype: :class:`DSSBusinessAppInstance`
        """
        return DSSBusinessAppInstance(self.client, self.business_app_id, project_key)

    def create_instance(self, project_key, project_name, short_desc=None, wait=True):
        """
        Create a new instance of this Business Application.

        Each instance must have a globally unique project key, separate from any other project
        key across the whole DSS instance.

        :param str project_key: project key for the new created instance
        :param str project_name: name for the new created instance
        :param str short_desc: optional short description for the instance
        :param bool wait: if False, the method returns immediately with a :class:`dataikuapi.dss.future.DSSFuture`
                         on which to wait for the instance to be created

        :return: if wait is True, returns a handle to interact with the instance.
                 if wait is False, returns a :class:`dataikuapi.dss.future.DSSFuture`
        :rtype: :class:`DSSBusinessAppInstance` or :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self.client._perform_json(
            "POST", "/business-apps/%s/instances" % self.business_app_id, body={
                "projectKey": project_key,
                "projectName": project_name,
                "shortDesc": short_desc
            })
        future = DSSFuture(self.client, future_resp.get("jobId", None), future_resp)
        if wait:
            future.wait_for_result()
            return DSSBusinessAppInstance(self.client, self.business_app_id, project_key)
        else:
            return future


class DSSBusinessAppDetails(object):
    """
    Details of a Business Application.

    .. important::

        Do not instantiate this class directly, use :meth:`DSSBusinessApp.get_details`
    """
    def __init__(self, client, business_app_id, data):
        self.client = client
        self.business_app_id = business_app_id
        self._data = data

    def get_raw(self):
        """
        Get the raw data of the details.

        :return: the raw data as a dict
        :rtype: dict
        """
        return self._data

    @property
    def id(self):
        """
        Get the ID of the Business Application.

        :rtype: str
        """
        return self.business_app_id

    @property
    def name(self):
        """
        Get the name of the Business Application.

        :rtype: str
        """
        return self._data["name"]

    @property
    def version(self):
        """
        Get the version of the Business Application.

        :rtype: str
        """
        return self._data["version"]

    @property
    def description(self):
        """
        Get the description of the Business Application.

        :rtype: str
        """
        return self._data["description"]

    @property
    def web_app_id(self):
        """
        Get the ID of the webapp of the Business Application.

        :rtype: str
        """
        return self._data["webAppId"]

    @property
    def code_env_name(self):
        """
        Get the name of the code environment of the Business Application.

        :rtype: str
        """
        return self._data["codeEnvName"]

    @property
    def connections(self):
        """
        Get the connection names and types (before remapping) used by this Business Application.

        :rtype: dict
        """
        return self._data.get("connections", {})

    @property
    def settings(self):
        """
        Get the settings of this Business Application.

        :return: the settings of the Business Application
        :rtype: :class:`DSSBusinessAppSettings`
        :raises Exception: if the user does not have admin privileges
        """
        return DSSBusinessAppSettings(self.client, self.id, self._data["settings", {}])

class DSSBusinessAppSettings(object):
    """
    Settings of a Business Application.

    .. important::

        Do not instantiate this class directly, use :meth:`DSSBusinessApp.get_settings`
    """
    def __init__(self, client, business_app_id, data):
        self.client = client
        self.business_app_id = business_app_id
        self._data = data

    def get_raw(self):
        """
        Get the raw settings data.

        :return: the raw settings as a dict
        :rtype: dict
        """
        return self._data

    @property
    def remapping(self):
        """
        Get the connection remapping settings.

        :rtype: dict
        """
        return self._data.get("remapping", {})

    @remapping.setter
    def remapping(self, value):
        """
        Set the connection remapping settings.

        :param dict value: the remapping settings
        """
        self._data["remapping"] = value

    def save(self):
        """
        Save the settings back to DSS. Requires admin privileges.
        """
        self.client._perform_empty("PUT", "/business-apps/%s/settings" % self.business_app_id, body=self._data)


class DSSBusinessAppInstanceListItem(object):
    """
    An item in a list of Business Application instances.

    .. important::

        Do not instantiate this class, use :meth:`DSSBusinessApp.list_instances` instead
    """
    def __init__(self, client, business_app_id, data):
        self.client = client
        self.business_app_id = business_app_id
        self._data = data

    @property
    def project_key(self):
        """
        Get the project key of this instance.

        :rtype: str
        """
        return self._data["projectKey"]

    @property
    def name(self):
        """
        Get the name of this instance.

        :rtype: str
        """
        return self._data["name"]

    @property
    def business_app_version(self):
        """
        Get the Business Application version of this instance.

        :rtype: str
        """
        return self._data.get("businessAppVersion")

    def get_raw(self):
        """
        Get the raw data of this list item.

        :return: the raw data as a dict
        :rtype: dict
        """
        return self._data

    def to_instance(self):
        """
        Get a handle corresponding to this instance.

        :return: a handle to interact with the instance
        :rtype: :class:`DSSBusinessAppInstance`
        """
        return DSSBusinessAppInstance(self.client, self.business_app_id, self._data["projectKey"])


class DSSBusinessAppInstance(object):
    """
    A handle to interact with an instance of a Business Application.

    .. important::

        Do not instantiate this class directly, use :meth:`DSSBusinessApp.get_instance`
    """
    def __init__(self, client, business_app_id, project_key):
        self.client = client
        self.business_app_id = business_app_id
        self.project_key = project_key

    def get_as_project(self):
        """
        Get a handle on the project corresponding to this instance.

        :return: a handle on a DSS project
        :rtype: :class:`dataikuapi.dss.project.DSSProject`
        """
        return self.client.get_project(self.project_key)

    def upgrade(self, wait=True):
        """
        Upgrade this instance to the latest version of the Business Application.

        :param bool wait: if False, the method returns immediately with a :class:`dataikuapi.dss.future.DSSFuture`
                         on which to wait for the upgrade to complete

        :return: if wait is True, returns a dict with the upgrade result.
                 if wait is False, returns a :class:`dataikuapi.dss.future.DSSFuture`
        :rtype: dict or :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self.client._perform_json(
            "POST", "/business-apps/%s/instances/%s/upgrade" % (self.business_app_id, self.project_key))
        future = DSSFuture(self.client, future_resp.get("jobId", None), future_resp)
        if wait:
            return future.wait_for_result()
        else:
            return future

    def delete(self, clear_managed_datasets=True, clear_output_managed_folders=True, clear_job_and_scenario_logs=True):
        """
        Delete this instance.

        :param bool clear_managed_datasets: if True, delete the data of managed datasets
        :param bool clear_output_managed_folders: if True, delete the data of managed folders
        :param bool clear_job_and_scenario_logs: if True, delete job and scenario logs
        """
        self.get_as_project().delete(
            clear_managed_datasets=clear_managed_datasets,
            clear_output_managed_folders=clear_output_managed_folders,
            clear_job_and_scenario_logs=clear_job_and_scenario_logs
        )

    def get_user_permissions(self, user):
        """
        Get the effective permissions of a user on this Business Application instance.

        :param str user: user login
        :return: a dict with the user's effective permissions. The structure is::

                     {
                         "login": "<login>",
                         "admin": bool,
                         "readProjectContent": bool,
                         "writeProjectContent": bool
                     }

        Usage example:

        .. code-block:: python

            perms = instance.get_user_permissions("alice")
            if perms["admin"]:
                print("User is admin")
        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/business-apps/%s/instances/%s/permissions/%s" % (self.business_app_id, self.project_key, user))
