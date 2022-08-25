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
    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_scenario`
    """
    def __init__(self, client, project_key, dashboard_id):
        """
        :param DSSClient client: an api client to connect to the DSS backend
        :param str project_key: identifier of the project to access
        :param str dashboard_id: identifier of the dashboard
        """
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
        Get the dashboard settings

        :returns: the dashboard settings
        :rtype: dict
        """
        return DSSDashboardSettings(self.client, self.client._perform_json("GET", DASHBOARD_URI_FORMAT % (self.project_key, self.dashboard_id)))

class DSSDashboardListItem(DSSTaggableObjectListItem):
    """An item in a list of dashboards. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_dashboards"""
    def __init__(self, client, data):
        super(DSSDashboardListItem, self).__init__(data)
        self.client = client

    def to_dashboard(self):
        return DSSDashboard(self.client, self._data["projectKey"], self._data["id"])

    def num_pages(self):
        return self._data['numPages']

    def num_tiles(self):
        return self._data['numTiles']

    def owner(self):
        return self._data['owner']


class DSSDashboardSettings(DSSTaggableObjectSettings):
    """
    :param DSSClient client: an api client to connect to the DSS backend
    :param str project_key: identifier of the project to access
    :param str dashboard_data: data of the dashboard
    """
    def __init__(self, client, dashboard_data):
        super(DSSDashboardSettings, self).__init__(dashboard_data)
        self.client = client
        self.project_key = dashboard_data['projectKey']
        self.id = dashboard_data['id']
        self.data = dashboard_data

    def get_raw(self):
        return self.data

    def save(self):
        """
        Save the settings to the dashboard
        """
        return self.client._perform_json("PUT", DASHBOARD_URI_FORMAT % (self.project_key, self.id), body = self.data)