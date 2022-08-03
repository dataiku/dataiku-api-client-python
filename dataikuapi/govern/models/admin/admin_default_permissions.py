class GovernAdminDefaultPermissions(object):
    """
    A handle to interact with the default permissions
    Do not create this directly, use :meth:`dataikuapi.govern.admin_roles_permission_editor.GovernAdminRolesPermissionsEditor.get_default_permissions()`
    """

    def __init__(self, client, permissions):
        self.client = client
        self.permissions = permissions

    def get_raw(self):
        """
        Gets the raw content of the default permissions. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.permissions

    def get_everyone_permissions(self):
        """
        Get the default permissions that apply to everyone

        :return: A python dict containing everyone's permissions
        :rtype: dict
        """
        return self.permissions.get("everyonePermissions")

    def list_role_permissions(self):
        """
        Get the default permissions that apply to specific roles.

        :return: A python dict with the different roles as keys and permission for this role as values
        :rtype: dict
        """
        return self.permissions.get("rolePermissions")

    def get_role_permissions(self, role_id):
        """
        Get the default permissions that apply to a specific role.

        :param str role_id: Identifier of the role.
        :return: A python dict with the permissions for this role.
        :rtype: dict
        """
        return self.permissions.get("rolePermissions").get(role_id)

    def save(self):
        """
        Save the default permissions

        :return: None
        """
        self.permissions = self.client._perform_json("PUT", "/admin/blueprint-permissions/default/",
                                                     body=self.permissions)
