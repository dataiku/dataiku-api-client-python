import json
import sys

from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote


INSIGHTS_URI_FORMAT = "/projects/%s/insights/"
INSIGHT_URI_FORMAT = INSIGHTS_URI_FORMAT + "%s/"

class DSSInsight(object):
    """
    A handle to interact with an insight on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_insight`
    """
    def __init__(self, client, project_key, insight_id):
        """
        :param DSSClient client: an api client to connect to the DSS backend
        :param str project_key: identifier of the project to access
        :param str insight_id: identifier of the insight
        """
        self.client = client
        self.project_key = project_key
        self.insight_id = insight_id

    def delete(self):
        """
        Delete the insight
        """
        return self.client._perform_empty("DELETE", INSIGHT_URI_FORMAT % (self.project_key, self.insight_id))

    def get_settings(self):
        """
        Get the insight settings

        :returns: the insight settings
        :rtype: dict
        """
        return DSSInsightSettings(self.client, self.client._perform_json("GET", INSIGHT_URI_FORMAT % (self.project_key, self.insight_id)))

class DSSInsightSettings(DSSTaggableObjectSettings):
    """
    :param DSSClient client: an api client to connect to the DSS backend
    :param str project_key: identifier of the project to access
    :param str insight_data: data of the insight
    """
    def __init__(self, client, insight_data):
        super(DSSInsightSettings, self).__init__(insight_data)
        self.client = client
        self.project_key = insight_data['projectKey']
        self.id = insight_data['id']
        self.data = insight_data

    def get_raw(self):
        return self.data

    def save(self):
        """
        Save the settings to the insight
        """
        return self.client._perform_json("POST", INSIGHT_URI_FORMAT % (self.project_key, self.id), body = {'insight': self.data})