class GovernAdminCustomPagesHandler(object):
    """
    Handle to edit the custom pages
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_custom_pages_handler`
    """

    def __init__(self, client):
        self.client = client

    def list_custom_pages(self):
        """
        List custom pages

        :return: A list of custom pages
        :rtype: list of :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPageListItem`
        """
        pages = self.client._perform_json("GET", "/admin/custom-pages")
        return [GovernAdminCustomPageListItem(self.client, page) for page in pages]

    def get_custom_page(self, custom_page_id):
        """
        Get a custom page

        :param str custom_page_id: ID of the custom page to retrieve
        :return: A custom page as an object
        :rtype: :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPage`
        """
        return GovernAdminCustomPage(self.client, custom_page_id)

    def create_custom_page(self, new_identifier, custom_page):
        """
        Create a custom page

        :param str new_identifier: the new identifier for this custom page. Allowed characters are letters, digits, hyphen, and underscore.
        :param dict custom_page: the custom page definition.
        :return: the handle of the created custom page
        :rtype: :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPage`
        """
        result = self.client._perform_json("POST", "/admin/custom-pages", params={"newIdentifier": new_identifier}, body=custom_page)
        return GovernAdminCustomPage(self.client, result["id"])

    def get_custom_pages_order(self):
        """
        Retrieves the order of display of the custom pages by their id

        :return: the order of the pages
        :rtype: list[string]
        """
        order = self.client._perform_json("GET", "/admin/custom-pages/order")
        return order

    def save_custom_pages_order(self, custom_pages_order):
        """
        Update the order of display of the custom pages.

        :param custom_pages_order: list[string] new custom pages order. Must contain ids of all the custom pages
        :return: updated custom pages order
        :rtype: list[string]
        """
        order = self.client._perform_json("PUT", "/admin/custom-pages/order", body=custom_pages_order)
        return order

class GovernAdminCustomPageListItem(object):
    """
    An item in a list of custom pages.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPagesHandler.list_custom_pages`
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
        Gets the :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPage` corresponding to this custom page object

        :return: the custom page object
        :rtype: a :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPage`
        """
        return GovernAdminCustomPage(self.client, self._data["id"])


class GovernAdminCustomPage(object):
    """
    A handle to interact with a custom page as an administrator.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPagesHandler.get_custom_page`
    """

    def __init__(self, client, custom_page_id):
        self.client = client
        self.custom_page_id = custom_page_id

    def get_definition(self):
        """
        Get the definition of the custom page, to modify the definition call :meth:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPageDefinition.save`
        on the returned object.

        :return: A custom page definition as an object
        :rtype: :class:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPageDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/custom-page/%s" % self.custom_page_id)
        return GovernAdminCustomPageDefinition(self.client, self.custom_page_id, definition)

    def delete(self):
        """
        Delete the custom page

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/custom-page/%s" % self.custom_page_id)


class GovernAdminCustomPageDefinition(object):
    """
    The definition of a custom page.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_pages_handler.GovernAdminCustomPage.get_definition`
    """

    def __init__(self, client, custom_page_id, definition):
        self.client = client
        self.custom_page_id = custom_page_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the custom page. This returns a reference to the custom page so changes made to the
        returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the custom page.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/custom-page/%s" % self.custom_page_id, body=self.definition)
