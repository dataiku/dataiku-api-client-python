from datetime import datetime

from .agent import DSSAgent
from .agent_tool import DSSAgentTool
from .savedmodel import DSSSavedModel
from .semantic_model import DSSSemanticModel
from ..utils import _timestamp_ms_to_zoned_datetime
from dataikuapi.dss.dataset import DSSDataset


class DSSDataCollectionListItem(object):
    """
    An item in a list of Catalog Collections.

    This class is also exposed as :class:`DSSCatalogCollectionListItem`.

    Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_collections`.
    """
    def __init__(self, client, data):
        self.client = client
        self._data = data

    def get_raw(self):
        """
        Get the raw representation of this :class:`DSSDataCollectionListItem`

        :rtype: :class:`dict`
        """
        return self._data

    @property
    def id(self):
        return self._data["id"]

    @property
    def display_name(self):
        return self._data["displayName"]

    @property
    def description(self):
        return self._data["description"]

    @property
    def color(self):
        return self._data["color"]

    @property
    def tags(self):
        return self._data["tags"]

    @property
    def item_count(self):
        return self._data["itemCount"]

    @property
    def last_modified_on(self):
        ts = self._data.get("lastModifiedOn", 0)
        return _timestamp_ms_to_zoned_datetime(ts)

    def to_data_collection(self):
        """
        Gets the :class:`DSSCatalogCollection` corresponding to this list item.

        :return: handle of the Catalog Collection
        :rtype: :class:`DSSCatalogCollection`
        """
        return DSSDataCollection(self.client, self._data["id"])

    def to_collection(self):
        """
        Gets the :class:`DSSCatalogCollection` corresponding to this list item.

        This is an alias for :meth:`to_data_collection`.

        :return: handle of the Catalog Collection
        :rtype: :class:`DSSCatalogCollection`
        """
        return self.to_data_collection()


class DSSDataCollection():
    """
    A handle to interact with a Catalog Collection on the DSS instance.

    This class is also exposed as :class:`DSSCatalogCollection`.

    Do not create this class directly instead use :meth:`dataikuapi.DSSClient.get_collection`, or :meth:`.DSSDataCollectionListItem.to_collection`.
    """

    def __init__(self, client, id):
        self.client = client
        self.id = id

    def get_settings(self):
        """
        Gets the settings of this Catalog Collection.

        :returns: a handle to read, modify and save the settings
        :rtype: :class:`DSSCatalogCollectionSettings`
        """
        return DSSDataCollectionSettings(self, self.client._perform_json("GET", "/data-collections/%s" % self.id))

    def list_objects(self, as_type='objects', filter_type=None):
        """
        List the objects in this Catalog Collection

        :param str as_type: How to return the list. Supported values are "objects" and "dict" (defaults to **objects**).
        :param str filter_type: Which elements to return in the list. Supported values are "DATASET", "SAVED_MODEL", "AGENT", "FINE_TUNED_MODEL", "AGENT_TOOL", "SEMANTIC_MODEL". If set to None or unset, no filtering is applied (defaults to None).

        :returns: The list of objects
        :rtype: list of :class:`.DSSCatalogCollectionItem` if as_type is "objects",
                list of :class:`dict` if as_type is "dict"
        """
        params={}
        if filter_type is not None:
            params["filterType"] = filter_type
        items = self.client._perform_json("GET", "/data-collections/%s/objects" % self.id, params=params or None)

        if as_type == "objects" or as_type == "object":
            return [DSSDataCollectionItem(self, item) for item in items]
        else:
            return items

    def add_object(self, obj):
        """
        Add an object to this Catalog Collection.

        :param obj: object to add to the Catalog Collection.
        :type obj: :class:`~dataikuapi.dss.dataset.DSSDataset`, :class:`.DSSDataCollectionItem` or :class:`dict`
        """
        if isinstance(obj, DSSDataset):
            data = ({
                "type": "DATASET",
                "projectKey": obj.project_key,
                "id": obj.id,
            })
        elif isinstance(obj, DSSSavedModel) or isinstance(obj, DSSAgent):
            data = ({
                "type": "SAVED_MODEL",
                "projectKey": obj.project_key,
                "id": obj.id,
            })
        elif isinstance(obj, DSSAgentTool):
            data = ({
                "type": "AGENT_TOOL",
                "projectKey": obj.project_key,
                "id": obj.id,
            })
        elif isinstance(obj, DSSSemanticModel):
            data = ({
                "type": "SEMANTIC_MODEL",
                "projectKey": obj.project_key,
                "id": obj.id,
            })
        elif isinstance(obj, DSSDataCollectionItem):
            data = obj.get_raw()
        elif isinstance(obj, dict):
            data = obj
        else:
            raise ValueError("Unsupported object type")
        self.client._perform_json("POST", "/data-collections/%s/objects" % self.id, body=data)

    def delete(self):
        """
        Delete this Catalog Collection

        This call requires Administrator rights on the Catalog Collection.
        """
        return self.client._perform_empty("DELETE", "/data-collections/%s" % self.id)

class DSSDataCollectionItem:
    """
    A handle on an object inside a Catalog Collection

    This class is also exposed as :class:`DSSCatalogCollectionItem`.

    Do not create this class directly, instead use :meth:`.DSSDataCollection.list_objects`
    """

    def __init__(self, data_collection, data):
        self.data_collection = data_collection
        self.data = data

    def get_raw(self):
        """
        Get the raw description of the Catalog Collection item. This returns a reference to the raw data, not a copy.
        
        :return: the Catalog Collection item raw description
        :rtype: :class:`dict`
        """
        return self.data

    def get_as_dataset(self):
        """
        Gets a handle on the corresponding dataset.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing a dataset in a collection doesn't necessarily imply a lot of rights.

        :returns: a handle on a dataset
        :rtype: :class:`dataikuapi.dss.dataset.DSSDataset`
        """
        if self.data["type"] != "DATASET":
            raise ValueError("Object is not of type DATASET but %s" % self.data["type"])

        return DSSDataset(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def get_as_saved_model(self):
        """
        Gets a handle on the corresponding saved model or fine-tuned model.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing a saved model in a collection doesn't necessarily imply a lot of rights.

        :returns: a handle on a saved model
        :rtype: :class:`dataikuapi.dss.savedmodel.DSSSavedModel`
        """
        if self.data["type"] != "SAVED_MODEL":
            raise ValueError("Object is not of type SAVED_MODEL but %s" % self.data["type"])

        if self.data["savedModelType"] not in ["DSS_MANAGED", "MLFLOW_PYFUNC", "PROXY_MODEL", "LLM_GENERIC"]:
            raise ValueError("Object is not of type SAVED_MODEL but AGENT")

        return DSSSavedModel(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def get_as_agent(self):
        """
        Gets a handle on the corresponding agent.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing an agent in a collection doesn't necessarily imply a lot of rights.

        :returns: a handle on an agent
        :rtype: :class:`dataikuapi.dss.agent.DSSAgent`
        """
        if self.data["type"] != "SAVED_MODEL":
            raise ValueError("Object is not of type AGENT but %s" % self.data["type"])

        if self.data["savedModelType"] not in ["PYTHON_AGENT", "PLUGIN_AGENT", "TOOLS_USING_AGENT", "STRUCTURED_AGENT", "RETRIEVAL_AUGMENTED_LLM"]:
            raise ValueError("Object is not of type AGENT but SAVED_MODEL")

        return DSSAgent(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def get_as_agent_tool(self):
        """
        Gets a handle on the corresponding agent tool.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing an agent tool in a collection doesn't necessarily imply a lot of rights.

        :returns: a handle on an agent tool
        :rtype: :class:`dataikuapi.dss.agent_tool.DSSAgentTool`
        """
        if self.data["type"] != "AGENT_TOOL":
            raise ValueError("Object is not of type AGENT_TOOL but %s" % self.data["type"])

        return DSSAgentTool(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def get_as_semantic_model(self):
        """
        Gets a handle on the corresponding semantic model.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing a semantic model in a collection doesn't necessarily imply a lot of rights.

        :returns: a handle on an agent tool
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModel`
        """
        if self.data["type"] != "SEMANTIC_MODEL":
            raise ValueError("Object is not of type SEMANTIC_MODEL but %s" % self.data["type"])

        return DSSSemanticModel(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def remove(self):
        """
        Remove this object from the Catalog Collection

        This call requires Contributor rights on the Catalog Collection.
        """
        if self.data["type"] == "DATASET":
            self.data_collection.client._perform_empty(
                "DELETE", "/data-collections/%s/objects/dataset/%s/%s" % (self.data_collection.id, self.data['projectKey'], self.data['id']))
        elif self.data["type"] == "SAVED_MODEL":
            self.data_collection.client._perform_empty(
                "DELETE", "/data-collections/%s/objects/saved-model/%s/%s" % (self.data_collection.id, self.data['projectKey'], self.data['id']))
        elif self.data["type"] == "AGENT_TOOL":
            self.data_collection.client._perform_empty(
                "DELETE", "/data-collections/%s/objects/agent-tool/%s/%s" % (self.data_collection.id, self.data['projectKey'], self.data['id']))
        elif self.data["type"] == "SEMANTIC_MODEL":
            self.data_collection.client._perform_empty(
                "DELETE", "/data-collections/%s/objects/semantic-model/%s/%s" % (self.data_collection.id, self.data['projectKey'], self.data['id']))

class DSSDataCollectionSettings:
    """
    A handle on the settings of a Catalog Collection

    This class is also exposed as :class:`DSSCatalogCollectionSettings`.

    Do not create this class directly, instead use :meth:`.DSSDataCollection.get_settings`
    """

    def __init__(self, data_collection, settings):
        self.data_collection = data_collection
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of the Catalog Collection. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :return: the Catalog Collection raw settings
        :rtype: :class:`dict`
        """
        return self.settings

    @property
    def id(self):
        """
        The Catalog Collection id (read-only)

        :rtype: :class:`str`
        """
        return self.settings['id']

    @property
    def display_name(self):
        """
        Get or set the name of the Catalog Collection

        :rtype: :class:`str`
        """
        return self.settings['displayName']

    @display_name.setter
    def display_name(self, value):
        self.settings['displayName'] = value

    @property
    def color(self):
        """
        Get or set the background color of the Catalog Collection (using #RRGGBB syntax)

        :rtype: :class:`str`
        """
        return self.settings['color']

    @color.setter
    def color(self, value):
        self.settings['color'] = value

    @property
    def description(self):
        """
        Get or set the description of the Catalog Collection

        :rtype: :class:`str`
        """
        return self.settings['description']

    @description.setter
    def description(self, value):
        self.settings['description'] = value


    @property
    def tags(self):
        """
        Get or set the tags of the Catalog Collection

        :rtype: list of :class:`str`
        """
        return self.settings['tags']

    @tags.setter
    def tags(self, value):
        self.settings['tags'] = value

    @property
    def permissions(self):
        """
        Get or set the permissions controlling who is a reader, contributor or admin of the Catalog Collection.

        If the user is not an admin of the data collection, the permissions property will be redacted as None.

        :return: a list of the Catalog Collection permissions
        :rtype: list of :class:`dict` or :class:`None`
        """
        return self.settings['permissions'] if 'permissions' in self.settings else None

    @permissions.setter
    def permissions(self, value):
        self.settings['permissions'] = value

    def save(self):
        """
        Save the changes made on the settings

        This call requires Administrator rights on the Catalog Collection.


        """
        self.data_collection.client._perform_empty(
            "PUT", "/data-collections/%s" % self.data_collection.id,
            body=self.settings)

class DSSDataCollectionPermissionItem:
    """
    Helper constructors for Catalog Collection permission entries.

    This class is also exposed as :class:`DSSCatalogCollectionPermissionItem`.
    """

    @classmethod
    def admin_group(cls, group):
        """Creates a :class:`dict` representing an admin authorization for a group"""
        return {"group": group, "admin": True, "write": True, "read": True}

    @classmethod
    def contributor_group(cls, group):
        """Creates a :class:`dict` representing an contributor authorization for a group"""
        return {"group": group, "admin": False, "write": True, "read": True}

    @classmethod
    def reader_group(cls, group):
        """Creates a :class:`dict` representing an reader authorization for a group"""
        return {"group": group, "admin": False, "write": False, "read": True}

    @classmethod
    def admin_user(cls, user):
        """Creates a :class:`dict` representing an admin authorization for a user"""
        return {"user": user, "admin": True, "write": True, "read": True}

    @classmethod
    def contributor_user(cls, user):
        """Creates a :class:`dict` representing an contributor authorization for a user"""
        return {"user": user, "admin": False, "write": True, "read": True}

    @classmethod
    def reader_user(cls, user):
        """Creates a :class:`dict` representing an reader authorization for a user"""
        return {"user": user, "admin": False, "write": False, "read": True}

DSSCatalogCollection = DSSDataCollection
DSSCatalogCollectionListItem = DSSDataCollectionListItem
DSSCatalogCollectionItem = DSSDataCollectionItem
DSSCatalogCollectionSettings = DSSDataCollectionSettings
DSSCatalogCollectionPermissionItem = DSSDataCollectionPermissionItem
