class GovernAdminRole(object):
    """
    A handle to interact with the roles of the instance as an admin.
    Do not create this directly, use :meth:`~dataikuapi.govern.roles_permissions_editor.GovernRolesPermissionsEditor.get_role
    """

    def __init__(self, client, role_id):
        self.client = client
        self.role_id = role_id

    @property
    def id(self):
        """
        Return the id of the role.

        :rtype: str
        """
        return self.role_id

    def get_role_info(self):
        """
        Return the information of the role as an object

        :returns: the information of the role.
        :rtype: :class:`dataikuapi.govern.models.admin.admin_role.GovernAdminRoleInfo`
        """

        role_info = self.client._perform_json(
            "GET", "/admin/role/%s" % self.role_id)
        return GovernAdminRoleInfo(self.client, self.role_id, role_info)


class GovernAdminRoleInfo(object):
    """
    An object with all the information on a role.
    Do not create this directly, use :meth:`~dataikuapi.govern.models.admin.admin_role.get_role_info()
    """

    def __init__(self, client, role_id, role_info):
        self.client = client
        self.role_id = role_id
        self.role_info = role_info

    def get_raw(self):
        """
        Get raw information of the role.

        :return: the raw definition of role, as a dict. Modifications made to the returned object are reflected
        when saving
        :rtype: dict
        """
        return self.role_info

    @property
    def id(self):
        """
        Gets the id of the related role.

        :rtype: str
        """
        return self.role_id

    @property
    def label(self):
        """
        Gets the label of the role.

        :rtype: str
        """
        return self.role_info["label"]

    @property
    def description(self):
        """
        Gets the description of the role.

        :rtype: str
        """
        return self.role_info["description"]

    @label.setter
    def label(self, label):
        """
        Set the label of the role

        :param str label: the new label to set
        """
        self.role_info["label"] = label

    @description.setter
    def description(self, description):
        """
        Set the label of the role

        :param str description: the new description to set
        """
        self.role_info["description"] = description

    def save(self):
        """
        Save this information back to the role
        """
        self.role_info = self.client._perform_json(
            "PUT", "/admin/role/%s" % self.role_id, body=self.role_info)
