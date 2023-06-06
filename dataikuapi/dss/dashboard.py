import json
import sys

from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote


DASHBOARDS_URI_FORMAT = "/projects/%s/dashboards/"
DASHBOARD_URI_FORMAT = DASHBOARDS_URI_FORMAT + "%s/"

class DSSDashboard(object):
    """
    A handle to interact with a dashboard on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.DSSProject.get_dashboard` instead
    """
    def __init__(self, client, project_key, dashboard_id):
        self.client = client
        self.project_key = project_key
        self.dashboard_id = dashboard_id

    def delete(self):
        """
        Delete the dashboard
        """
        return self.client._perform_empty("DELETE", DASHBOARD_URI_FORMAT % (self.project_key, self.dashboard_id))

    def get_settings(self):
        """
        Get the dashboard's definition

        :return: a handle to inspect the dashboard definition
        :rtype: :class:`dataikuapi.dss.dashboard.DSSDashboardSettings`
        """
        return DSSDashboardSettings(self.client, self.client._perform_json("GET", DASHBOARD_URI_FORMAT % (self.project_key, self.dashboard_id)))

class DSSDashboardListItem(DSSTaggableObjectListItem):
    """
    An item in a list of dashboards.

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_dashboards`
    """
    def __init__(self, client, data):
        super(DSSDashboardListItem, self).__init__(data)
        self.client = client

    def to_dashboard(self):
        """
        Get a handle to interact with this dashboard

        :return: a handle on the dashboard
        :rtype: :class:`dataikuapi.dss.dashboard.DSSDashboard`
        """
        return DSSDashboard(self.client, self._data["projectKey"], self._data["id"])

    @property
    def id(self):
        """
        Get the identifier of the dashboard

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        Get the name of the dashboard

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: str
        """
        return self._data['name']

    @property
    def listed(self):
        """
        Get the boolean indicating whether the dashboard is private or public (i.e. promoted)

        :rtype: bool
        """
        return self._data['listed']

    @property
    def owner(self):
        """
        Get the login of the owner of the dashboard

        :rtype: str
        """
        return self._data['owner']

    @property
    def num_pages(self):
        """
        Get the number of pages (i.e. slides) in the dashboard

        :rtype: int
        """
        return self._data['numPages']

    @property
    def num_tiles(self):
        """
        Get the number of tiles in the dashboard

        :rtype: int
        """
        return self._data['numTiles']


class DSSDashboardSettings(DSSTaggableObjectSettings):
    """
    Settings for a dashboard

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.dashboard.DSSDashboard.get_settings` instead

    """
    def __init__(self, client, settings):
        super(DSSDashboardSettings, self).__init__(settings)
        self.client = client
        self.project_key = settings['projectKey']
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary.

        :return: the settings, as a dict. Fields are:

                    * **projectKey** and **id** : identify the dashboard
                    * **name** : name (label) of the dashboard
                    * **owner** : login of the owner of the dashboard
                    * **listed** : boolean indicating whether the dashboard is private or public (i.e. promoted)
                    * **pages** : definition of the different slides
                    * **versionTag**, **creationTag**, **checklists**, **tags**, **customFields** : common fields on DSS objects

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Save the settings to the dashboard
        """
        return self.client._perform_json("PUT", DASHBOARD_URI_FORMAT % (self.project_key, self.id), body = self.settings)

    @property
    def id(self):
        """
        Get the identifier of the dashboard

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self.settings["id"]

    @property
    def name(self):
        """
        Get the name of the dashboard

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: str
        """
        return self.settings['name']

    @property
    def listed(self):
        """
        Get the boolean indicating whether the dashboard is private or public (i.e. promoted)

        :rtype: bool
        """
        return self.settings['listed']

    @property
    def owner(self):
        """
        Get the login of the owner of the dashboard

        :rtype: str
        """
        return self.settings['owner']
    