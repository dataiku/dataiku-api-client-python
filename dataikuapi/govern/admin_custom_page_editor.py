class GovernAdminCustomPageEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_custom_page_editor`
    """

    def __init__(self, client):
        self.client = client

    def list_custom_pages(self, as_objects=True):
        """
        List custom pages

        :param boolean as_objects: (Optional) If True, this method returns a list of :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage`,
        else returns a list of dict. Each dict contains at least a field "id"
        :returns: A list of custom pages
        :rtype: list of :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage` or list of dict, see parameter as_objects
        """
        pages = self.client._perform_json("GET", "/admin/custom-pages")

        if as_objects:
            return [GovernAdminCustomPage(self.client, page["id"]) for page in pages]
        else:
            return pages

    def get_custom_page(self, custom_page_id):
        """
        Get a custom page

        :param str custom_page_id: id of the custom page to retrieve
        :return: A custom page as an object
        :rtype: :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage`
        """
        return GovernAdminCustomPage(self.client, custom_page_id)

    def create_custom_page(self, new_identifier, custom_page):
        """
        Creates a custom page

        :param str new_identifier: the new identifier for this custom page
        :param dict custom_page: the custom page definition
        :returns: the handle of the created custom page
        :rtype: :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage`
        """
        result = self.client._perform_json("POST", "/admin/custom-pages", params={"newIdentifier": new_identifier}, body=custom_page)
        return GovernAdminCustomPage(self.client, result["id"])


class GovernAdminCustomPage(object):
    """
    A handle to interact with a custom page as an administrator
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageEditor.get_custom_page`
    """

    def __init__(self, client, custom_page_id):
        self.client = client
        self.custom_page_id = custom_page_id

    def get_definition(self):
        """
        Get the definition of the custom page, to modify the definition call :meth:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageDefinition.save`
        on the returned object.

        :return: A custom page definition as an object
        :rtype: :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageDefinition`
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
    A handle to interact with the definition of a custom page.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage.get_definition`
    """

    def __init__(self, client, custom_page_id, definition):
        self.client = client
        self.custom_page_id = custom_page_id
        self.definition = definition

    def get_raw(self):
        """
        Gets the raw content of the custom page. This returns a reference to the custom page so changes made to the
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
