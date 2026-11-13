from ._utils import dku_quote_fn


class TopicFamily(object):
    """
    An Agent Management topic family.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_topic_family`.
    """
    def __init__(self, client, family_id):
        self.client = client
        self.family_id = family_id

    @property
    def id(self):
        return self.family_id

    def __repr__(self):
        return "<TopicFamily id=%r>" % self.family_id

    def get_definition(self):
        """
        Returns the definition of this topic family.

        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def set_definition(self, definition):
        """
        Replaces the topic family definition.

        :param dict definition: new definition
        :returns: the saved definition
        :rtype: dict
        """
        return self.client._perform_json("PUT", self._path(), body=definition)

    def delete(self):
        """Deletes the topic family."""
        self.client._perform_empty("DELETE", self._path())

    def _path(self):
        return "/agent-management/settings/topic-families/%s" % dku_quote_fn(self.family_id, safe="")


class TopicFamilyListItem(dict):
    """A TopicFamily listing entry with local accessors and conversion to a resource handle."""

    def __init__(self, client, data):
        super(TopicFamilyListItem, self).__init__(data)
        self.client = client

    @property
    def id(self):
        """The listing entry's id."""
        return self["id"]

    @property
    def name(self):
        """The listing entry's name."""
        return self.get("name")

    def to_topic_family(self):
        """Return a :class:`TopicFamily` handle without making an API call."""
        return TopicFamily(self.client, self.id)

    def _to_object(self):
        return self.to_topic_family()
