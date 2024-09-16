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

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_insight` instead
    """
    def __init__(self, client, project_key, insight_id):
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
        Get the insight's definition

        :return: a handle to inspect the insight definition
        :rtype: :class:`dataikuapi.dss.insight.DSSInsightSettings`
        """
        return DSSInsightSettings(self.client, self.client._perform_json("GET", INSIGHT_URI_FORMAT % (self.project_key, self.insight_id)))

class DSSInsightListItem(DSSTaggableObjectListItem):
    """
    An item in a list of insights.

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_insights`
    """
    def __init__(self, client, data):
        super(DSSInsightListItem, self).__init__(data)
        self.client = client

    @property
    def id(self):
        """
        Get the identifier of the insight

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        Get the name of the insight

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: str
        """
        return self._data['name']

    @property
    def type(self):
        """
        Get the type of the insight (ex: "chart")

        :rtype: str
        """
        return self._data['type']

    @property
    def listed(self):
        """
        Get the boolean indicating whether the insight is private or public (i.e. promoted)

        :rtype: bool
        """
        return self._data['listed']

    @property
    def owner(self):
        """
        Get the login of the owner of the insight

        :rtype: str
        """
        return self._data['owner']

    def to_insight(self):
        """
        Get a handle to interact with this insight

        :return: a handle on the insight
        :rtype: :class:`dataikuapi.dss.insight.DSSInsight`
        """
        return DSSInsight(self.client, self._data["projectKey"], self._data["id"])

class DSSInsightSettings(DSSTaggableObjectSettings):
    """
    Settings for an insight

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.insight.DSSInsight.get_settings` instead

    """
    def __init__(self, client, settings):
        super(DSSInsightSettings, self).__init__(settings)
        self.client = client
        self.project_key = settings['projectKey']
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary.

        :return: the settings, as a dict. Fields are:

                    * **projectKey** and **id** : identify the insight
                    * **name** : name (label) of the insight
                    * **owner** : login of the owner of the insight
                    * **versionTag**, **creationTag**, **checklists**, **tags**, **customFields** : common fields on DSS objects

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Save the settings to the insight
        """
        return self.client._perform_json("POST", INSIGHT_URI_FORMAT % (self.project_key, self.id), body = {'insight': self.settings})

    @property
    def id(self):
        """
        Get the identifier of the insight

        .. note::

            The id is generated by DSS upon creation and random.

        :rtype: string
        """
        return self.settings["id"]

    @property
    def name(self):
        """
        Get the name of the insight

        .. note::

            The name is user-provided and not necessarily unique.

        :rtype: str
        """
        return self.settings['name']

    @property
    def type(self):
        """
        Get the type of the insight (ex: "chart")

        :rtype: str
        """
        return self.settings['type']

    @property
    def listed(self):
        """
        Get the boolean indicating whether the insight is private or public (i.e. promoted)

        :rtype: bool
        """
        return self.settings['listed']

    @property
    def owner(self):
        """
        Get the login of the owner of the insight

        :rtype: str
        """
        return self.settings['owner']