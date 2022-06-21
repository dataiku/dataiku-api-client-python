class GovernBlueprintPermission(object):
    """
    A handle to interact with a blueprint permission the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.governClient.rolesPermissionsSettings.get_blueprint_permission`
    """

    def __init__(self, client, permission):
        self.client = client
        self.permission = permission

    @property
    def id(self):
        return self.permission["blueprintId"]

    def get_raw(self):
        """
        Gets the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
         not a copy, so changes made to the returned object will be reflected when saving.
        :rtype: dict
        """
        return self.permission

    def get_everyone_permissions(self):
        """
        Get the permissions that apply to everyone for this blueprint
        :return: A python dict containing everyone's permissions
        """
        return self.permission["everyonePermissions"]

    def list_role_permissions(self):
        """
        Get the permissions that apply to specific roles for this blueprint.
        :return: A python dict with the different roles as keys and permission for this role as values
        """
        return self.permission["rolePermissions"]

    def get_role_permission(self, role_id):
        """
        Get the permissions that apply to a specific role.
        :param str role_id: Identifier of the role.
        :return: A python dict with the permissions for this role.
        """
        return self.permission["rolePermissions"][role_id]

    def save(self):
        """
        Save this permission back to the blueprint permission definition.
        """
        self.permission = self.client._perform_json("PUT", "/admin/blueprint-permissions/%s/" % self.id,
                                                    body=self.permission)

