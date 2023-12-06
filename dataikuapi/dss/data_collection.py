from datetime import datetime
from ..utils import _timestamp_ms_to_zoned_datetime
from dataikuapi.dss.dataset import DSSDataset


class DSSDataCollectionListItem(object):
    """
    An item in a list of Data Collections.

    Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_data_collections`
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
        Gets the :class:`DSSDataCollection` corresponding to this list item

        :return: handle of the Data Collection
        :rtype: :class:`DSSDataCollection`
        """
        return DSSDataCollection(self.client, self._data["id"])

class DSSDataCollection():
    """
    A handle to interact with a Data Collection on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_data_collection` or :meth:`.DSSDataCollectionListItem.to_data_collection`
    """

    def __init__(self, client, id):
        self.client = client
        self.id = id

    def get_settings(self):
        """
        Gets the settings of this Data Collection.

        :returns: a handle to read, modify and save the settings
        :rtype: :class:`DSSDataCollectionSettings`
        """
        return DSSDataCollectionSettings(self, self.client._perform_json("GET", "/data-collections/%s" % self.id))

    def list_objects(self, as_type='objects'):
        """
        List the objects in this Data Collection

        :param str as_type: How to return the list. Supported values are "objects" and "dict" (defaults to **objects**).

        :returns: The list of objects
        :rtype: list of :class:`.DSSDataCollectionItem` if as_type is "objects",
                list of :class:`dict` if as_type is "dict"
        """
        items = self.client._perform_json("GET", "/data-collections/%s/objects" % self.id)

        if as_type == "objects" or as_type == "object":
            return [DSSDataCollectionItem(self, item) for item in items]
        else:
            return items

    def add_object(self, obj):
        """
        Add an object to this Data Collection.

        :param obj: object to add to the Data Collection.
        :type obj: :class:`~dataikuapi.dss.dataset.DSSDataset`, :class:`.DSSDataCollectionItem` or :class:`dict`
        """
        if isinstance(obj, DSSDataset):
            data = ({
                "type": "DATASET",
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
        Delete this Data Collection

        This call requires Administrator rights on the Data Collection.
        """
        return self.client._perform_empty("DELETE", "/data-collections/%s" % self.id)

class DSSDataCollectionItem:
    """
    A handle on an object inside a Data Collection

    Do not create this class directly, instead use :meth:`.DSSDataCollection.list_objects`
    """

    def __init__(self, data_collection, data):
        self.data_collection = data_collection
        self.data = data

    def get_raw(self):
        """
        Get the raw description of the Data Collection item. This returns a reference to the raw data, not a copy.
        
        :return: the Data Collection item raw description
        :rtype: :class:`dict`
        """
        return self.data

    def get_as_dataset(self):
        """
        Gets a handle on the corresponding dataset.

        .. attention::
            The usability of this handle might be limited by the current user's authorizations, as seeing a dataset in a data-collection doesn't necessarily imply a lot of rights.

        :returns: a handle on a dataset
        :rtype: :class:`dataikuapi.dss.dataset.DSSDataset`
        """
        return DSSDataset(self.data_collection.client, self.data["projectKey"], self.data["id"])

    def remove(self):
        """
        Remove this object from the Data Collection

        This call requires Contributor rights on the Data Collection.
        """
        if self.data["type"] == "DATASET":
            self.data_collection.client._perform_empty(
                "DELETE", "/data-collections/%s/objects/dataset/%s/%s" % (self.data_collection.id, self.data['projectKey'], self.data['id']))

class DSSDataCollectionSettings:
    """
    A handle on the settings of a Data Collection

    Do not create this class directly, instead use :meth:`.DSSDataCollection.get_settings`
    """

    def __init__(self, data_collection, settings):
        self.data_collection = data_collection
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of the Data Collection. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :return: the Data Collection raw settings
        :rtype: :class:`dict`
        """
        return self.settings

    @property
    def id(self):
        """
        The Data Collection id (read-only)

        :rtype: :class:`str`
        """
        return self.settings['id']

    @property
    def display_name(self):
        """
        Get or set the name of the Data Collection

        :rtype: :class:`str`
        """
        return self.settings['displayName']

    @display_name.setter
    def display_name(self, value):
        self.settings['displayName'] = value

    @property
    def color(self):
        """
        Get or set the background color of the Data Collection (using #RRGGBB syntax)

        :rtype: :class:`str`
        """
        return self.settings['color']

    @color.setter
    def color(self, value):
        self.settings['color'] = value

    @property
    def description(self):
        """
        Get or set the description of the Data Collection

        :rtype: :class:`str`
        """
        return self.settings['description']

    @description.setter
    def description(self, value):
        self.settings['description'] = value


    @property
    def tags(self):
        """
        Get or set the tags of the Data Collection

        :rtype: list of :class:`str`
        """
        return self.settings['tags']

    @tags.setter
    def tags(self, value):
        self.settings['tags'] = value

    @property
    def permissions(self):
        """
        Get or set the permissions controlling who is a reader, contributor or admin of the Data Collection.

        If the user is not an admin of the data-collection, the permissions property will be redacted as None.

        :return: a list of the Data Collection permissions
        :rtype: list of :class:`dict` or :class:`None`
        """
        return self.settings['permissions'] if 'permissions' in self.settings else None

    @permissions.setter
    def permissions(self, value):
        self.settings['permissions'] = value

    def save(self):
        """
        Save the changes made on the settings

        This call requires Administrator rights on the Data Collection.
        """
        self.data_collection.client._perform_empty(
            "PUT", "/data-collections/%s" % self.data_collection.id,
            body=self.settings)

class DSSDataCollectionPermissionItem:
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
