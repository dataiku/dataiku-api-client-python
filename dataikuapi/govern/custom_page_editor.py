from dataikuapi.govern.models.admin.admin_custom_page import GovernAdminCustomPage


class CustomPageEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_custom_page_editor()`
    """

    def __init__(self, client):
        self.client = client

    def list_custom_pages(self, as_objects=True):
        """
        Lists custom pages on the Govern instance.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`dataikuapi.govern.models.admin.admin_custom_page.GovernAdminCustomPage`,
         else returns a list of dict. Each dict contains at least a field "id" indicating the identifier of the custom page
        :returns: a list of custom pages
        :rtype: list of :class: `dataikuapi.govern.models.admin.admin_custom_page.GovernAdminCustomPage` or list of
        dict, see param as_objects
        """
        pages = self._perform_json('GET', '/custom-pages')

        if as_objects:
            return [GovernAdminCustomPage(self.client, page['id'], page) for page in pages]
        else:
            return pages

    def get_custom_page(self, custom_page_id):
        """
        Retrieve a custom page from a Govern node

        :param str custom_page_id: id of the custom page to retrieve
        :return: the object representing the custom page
        :rtype: a :class: `dataikuapi.govern.models.admin.admin_custom_page.GovernAdminCustomPage`
        """
        result = self._perform_json('GET', '/customPage/%s' % custom_page_id)

        return GovernAdminCustomPage(self, custom_page_id, result)

    def delete_custom_page(self, custom_page_id):
        """
        Delete a custom page from a Govern node

        :param str custom_page_id: id of the custom page to delete
        """
        self._perform_empty('DELETE', '/custom-page/%s' % custom_page_id)
