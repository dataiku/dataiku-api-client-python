class GovernCustomPageListItem(object):
    """
    An item in a list of custom pages.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.list_custom_pages`
    """

    def __init__(self, client, data):
        self.client = client
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the custom page list item

        :return: the raw content of the custom page list item as a dict
        :rtype: dict
        """
        return self._data

    def to_custom_page(self):
        """
        Gets the :class:`~dataikuapi.govern.custom_page.GovernCustomPage` corresponding to this custom page object

        :return: the custom page object
        :rtype: a :class:`~dataikuapi.govern.custom_page.GovernCustomPage`
        """
        return GovernCustomPage(self.client, self._data["id"])


class GovernCustomPage(object):
    """
    A handle to interact with a custom page.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_custom_page`
    """

    def __init__(self, client, custom_page_id):
        self.client = client
        self.custom_page_id = custom_page_id

    def get_definition(self):
        """
        Get the definition of the custom page.

        :return: the corresponding custom page definition object
        :rtype: a :class:`~dataikuapi.govern.custom_page.GovernCustomPageDefinition`
        """
        result = self.client._perform_json("GET", "/custom-page/%s" % self.custom_page_id)
        return GovernCustomPageDefinition(self.client, self.custom_page_id, result)


class GovernCustomPageDefinition(object):
    """
    The definition of a custom page.
    Do not create this directly, use :meth:`~dataikuapi.govern.custom_page.GovernCustomPage.get_definition`
    """

    def __init__(self, client, custom_page_id, definition):
        self.client = client
        self.custom_page_id = custom_page_id
        self.definition = definition

    def get_raw(self):
        """
        :return: the raw content of the custom page as a dict
        :rtype: dict
        """
        return self.definition
