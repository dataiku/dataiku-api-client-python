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
        :rtype: list of :class:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage` or list of
        dict, see parameter as_objects
        """
        pages = self.client._perform_json("GET", "/admin/custom-pages")

        if as_objects:
            return [GovernAdminCustomPage(self.client, page["id"], page) for page in pages]
        else:
            return pages

    def get_custom_page(self, custom_page_id):
        """
        Get a custom page

        :param str custom_page_id: id of the custom page to retrieve
        :return: A custom page as an object
        :rtype: :class:`dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPage`
        """
        result = self.client._perform_json("GET", "/admin/custom-page/%s" % custom_page_id)

        return GovernAdminCustomPage(self, custom_page_id, result)


class GovernAdminCustomPage(object):
    """
    A handle to interact with a custom page
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_custom_page_editor.GovernAdminCustomPageEditor.get_custom_page`
    """

    def __init__(self, client, custom_page_id, custom_page):
        self.client = client
        self.custom_page_id = custom_page_id
        self.custom_page = custom_page

    def get_raw(self):
        """
        Gets the raw content of the custom page. This returns a reference to the custom page so changes made to the
        returned object will be reflected when saving.

        :rtype: dict
        """
        return self.custom_page


    @property
    def name(self):
        """
        Return the name of the custom page.

        :return: the name of the custom page as a Python str.
        """
        return self.custom_page.get("name")

    @property
    def index(self):
        """
        Return the index of the custom page.

        :return: the index of the custom page as a Python integer.
        """
        return self.custom_page.get("index")

    @property
    def icon(self):
        """
        Return the icon of the custom page.

        :return: the icon of the custom page as a Python integer.
        """
        return self.custom_page.get("icon")

    @name.setter
    def name(self, name):
        """
        Set the name of the custom page

        :param str name: the new name.
        :return: None
        """
        self.custom_page["name"] = name

    @index.setter
    def index(self, index):
        """
        Set the index of the custom page

        :param str index: the new index.
        :return: None
        """
        self.custom_page["index"] = index

    @icon.setter
    def icon(self, icon):
        """
        Set the icon of the custom page

        :param str icon: the new icon.
        :return: None
        """
        self.custom_page["icon"] = icon

    def save(self):
        """
        Save this settings back to the custom page.

        :return: None
        """
        self.custom_page = self.client._perform_json("PUT", "/admin/custom-page/%s" % (
            self.custom_page_id), body=self.custom_page)

    def delete(self):
        """
        Delete the custom page.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/custom-page/%s" % self.custom_page_id)


class GovernCustomPage(object):
    """
    A non-admin handle to interact with a custom page
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_custom_page`
    """

    def __init__(self, client, custom_page_id, custom_page):
        self.client = client
        self.custom_page_id = custom_page_id
        self.custom_page = custom_page

    def get_raw(self):
        """
        Gets the raw content of the custom page.

        :rtype: dict
        """
        return self.custom_page


    @property
    def name(self):
        """
        Return the name of the custom page.

        :return: the name of the custom page as a Python str.
        """
        return self.custom_page.get("name")

    @property
    def index(self):
        """
        Return the index of the custom page.

        :return: the index of the custom page as a Python integer.
        """
        return self.custom_page.get("index")

    @property
    def icon(self):
        """
        Return the icon of the custom page.

        :return: the icon of the custom page as a Python integer.
        """
        return self.custom_page.get("icon")

