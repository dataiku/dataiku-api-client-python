from .future import DSSFuture
from .utils import DSSTaggableObjectListItem


class DSSWebApp(object):
    """
    A handle for the webapp.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_webapps`.
    """

    def __init__(self, client, project_key, webapp_id):
        self.client = client
        self.project_key = project_key
        self.webapp_id = webapp_id

    def get_state(self):
        """
        :returns: A wrapper object holding the webapp backend state.
        :rtype: :class:`dataikuapi.dss.webapp.DSSWebAppBackendState`
        """
        state = self.client._perform_json("GET", "/projects/%s/webapps/%s/backend/state" % (self.project_key, self.webapp_id))
        return DSSWebAppBackendState(self.webapp_id, state)

    def stop_backend(self):
        """
        Stop the webapp backend.
        """
        self.client._perform_empty("PUT", "/projects/%s/webapps/%s/backend/actions/stop" % (self.project_key, self.webapp_id))

    def start_or_restart_backend(self):
        """
        Start or restart the webapp backend.

        :returns: A future tracking the restart progress.
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        resp = self.client._perform_json("PUT", "/projects/%s/webapps/%s/backend/actions/restart" % (self.project_key, self.webapp_id))
        return DSSFuture.from_resp(self.client, resp)

    def get_settings(self):
        """
        :returns: A handle for the webapp settings.
        :rtype: :class:`dataikuapi.dss.webapp.DSSWebAppSettings`
        """
        data = self.client._perform_json("GET", "/projects/%s/webapps/%s" % (self.project_key, self.webapp_id))
        return DSSWebAppSettings(self.client, self, data)


class DSSWebAppBackendState(object):
    """
    A wrapper object holding the webapp backend state.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.webapp.DSSWebApp.get_state`.
    """

    def __init__(self, webapp_id, state):
        self.webapp_id = webapp_id
        self._state = state

    @property
    def state(self):
        """
        :returns: The webapp backend state as a dict containing the keys:

            * **projectKey**: the related project key,
            * **webAppId**: the webapp id,
            * **futureInfo**: the status of the last webapp start or restart job if such job exists
              (prefer using :attr:`dataikuapi.dss.webapp.DSSWebAppBackendState.running`).

        :rtype: python dict
        """
        return self._state

    @property
    def running(self):
        """
        :returns: Is the backend of the webapp currently running.
        :rtype: bool
        """
        return "futureInfo" in self._state and \
               "alive" in self._state["futureInfo"] and \
               self._state["futureInfo"]["alive"]


class DSSWebAppSettings(object):
    """
    A handle for the webapp settings.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.webapp.DSSWebApp.get_settings`.
    """

    def __init__(self, client, webapp, data):
        self.client = client
        self.webapp = webapp
        self.data = data

    def get_raw(self):
        """
        :returns: The webapp settings as a dict containing among other keys:

            * **id**: the webapp id,
            * **name**: the webapp name,
            * **type**: the webapp type (e.g. "STANDARD"),
            * **projectKey**: the related project key,
            * **params**: a dict containing other information depending on the webapp type such as the source code.

        :rtype: python dict
        """
        return self.data

    def save(self):
        """
        Save the current webapp settings.
        """
        self.client._perform_json("PUT", "/projects/%s/webapps/%s" % (self.webapp.project_key, self.webapp.webapp_id), body=self.data)


class DSSWebAppListItem(DSSTaggableObjectListItem):
    """
    An item in a list of webapps.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_webapps`.
    """

    def __init__(self, client, data):
        super(DSSWebAppListItem, self).__init__(data)
        self.client = client

    def to_webapp(self):
        """
        Convert the current item.

        :returns: A handle for the webapp.
        :rtype: :class:`dataikuapi.dss.webapp.DSSWebApp`
        """
        return DSSWebApp(self.client, self._data["projectKey"], self._data["id"])

    @property
    def id(self):
        """
        :returns: The id of the webapp.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the webapp.
        :rtype: string
        """
        return self._data["name"]
