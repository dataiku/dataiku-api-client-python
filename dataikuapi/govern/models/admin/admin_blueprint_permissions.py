class GovernAdminBlueprintPermissions(object):
    """
    A handle to interact with blueprint permissions for a specific blueprint
    Do not create this directly, use :meth:`dataikuapi.govern.admin_roles_permission_editor.GovernAdminRolesPermissionsEditor.get_blueprint_permissions`
    """

    def __init__(self, client, permissions):
        self.client = client
        self.permissions = permissions

    @property
    def id(self):
        return self.permissions.get("blueprintId")

    def get_raw(self):
        """
        Gets the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.permissions

    def get_everyone_permissions(self):
        """
        Get the permissions that apply to everyone for this blueprint

        :return: A python dict containing everyone's permissions
        :rtype: dict
        """
        return self.permissions.get("everyonePermissions")

    def list_role_permissions(self):
        """
        Get the permissions that apply to specific roles for this blueprint.

        :return: A python dict with the different roles as keys and permission for this role as values
        :rtype: dict
        """
        return self.permissions.get("rolePermissions")

    def get_role_permissions(self, role_id):
        """
        Get the permissions that apply to a specific role.

        :param str role_id: Identifier of the role.
        :return: A python dict with the permissions for this role or None if there is none.
        :rtype: dict
        """
        return self.permissions.get("rolePermissions").get(role_id)

    def save(self):
        """
        Save this permission back to the blueprint permission definition.

        :return: None
        """
        self.permissions = self.client._perform_json("PUT", "/admin/blueprint-permissions/%s/" % self.id,
                                                     body=self.permissions)

    def delete_permissions(self):
        """
        Delete the permissions for this blueprint

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-permissions/%s" % (
            self.id))
