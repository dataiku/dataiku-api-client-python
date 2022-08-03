class GovernAdminCustomPage(object):
    """
    A handle to interact with a custom page on the Govern instance.
    Do not not create this directly, use :meth:`dataikuapi.governClient.get_custom_page`
    """

    def __init__(self, client, custom_page_id, custom_page):
        """
        A handle to interact with an artifact on the Govern instance.
        Do not create this directly, use :meth:`dataikuapi.governClient.get_artifact`
        """
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
    def id(self):
        """
        Return the artifact id.

        :return: the artifact id as a Python str
        """
        return self.custom_page_id

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

    def save(self):
        """
        Save this settings back to the custom page.
        """
        self.custom_page = self.client._perform_json("PUT", "/admin/custom-page/%s" % (
            self.custom_page_id), body=self.custom_page)

    def delete_custom_page(self):
        """
        Delete the custom page.

        :return: None
        """
        self.client._perform_empty('DELETE', '/admin/custom-page/%s' % self.custom_page_id)
