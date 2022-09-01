class GovernAdminRolesPermissionsEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_roles_permissions_editor`
    """

    def __init__(self, client):
        self.client = client

    def list_roles(self, as_objects=True):
        """
        List roles

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`,
         else returns a list of dict. Each dict contains a field "id" indicating the identifier of the role.
        :return: a list of roles
        :rtype: list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole` or list of dict, see parameter as_objects
        """
        roles = self.client._perform_json("GET", "/admin/roles")

        if as_objects:
            return [GovernAdminRole(self.client, role["id"]) for role in roles]
        else:
            return roles

    def get_role(self, role_id):
        """
        Return a specific role on the Govern instance

        :param str role_id: Identifier of the role
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
        """
        return GovernAdminRole(self.client, role_id)

    def create_role(self, new_identifier, role):
        """
        Create a new role and returns the handle to interact with it.

        :param str new_identifier: Identifier of the new role. Allowed characters are letters, digits, hyphen, and underscore.
        :param dict role: The definition of the role.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
        """
        result = self.client._perform_json("POST", "/admin/roles/", params={"newIdentifier": new_identifier}, body=role)
        return GovernAdminRole(self.client, result["id"])

    def list_role_assignments(self, as_objects=True):
        """
        List the role assignments,each as a dict. Each dict contains at least a "blueprintId" field

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`,
        else returns a list of dict. Each dict contains a field "blueprintId" indicating the identifier of the blueprint
        :return: A list of role assignments for each blueprint
        :rtype: list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments` or list of dict, see parameter as_objects
        """
        assignments_list = self.client._perform_json("GET", "/admin/blueprint-role-assignments")

        if as_objects:
            return [GovernAdminBlueprintRoleAssignments(self.client, assignments["blueprintId"]) for assignments in assignments_list]
        else:
            return assignments_list

    def get_role_assignments(self, blueprint_id):
        """
        Get the role assignments for a specific blueprint. Returns a handle to interact with it.

        :param str blueprint_id: id of the blueprint
        :return: A object representing the role assignments for this blueprint
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        return GovernAdminBlueprintRoleAssignments(self.client, blueprint_id)

    def create_role_assignments(self, role_assignments):
        """
        Create a role assignments on the Govern instance and returns the handle to interact with it.

        :param: dict role_assignment: Blueprint permission as a dict
        :return: The newly created role assignment.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        result = self.client._perform_json("POST", "/admin/blueprint-role-assignments", body=role_assignments)
        return GovernAdminBlueprintRoleAssignments(self.client, result["blueprintId"])

    def get_default_permissions_definition(self):
        """
        Get the default permissions definition.

        :return: A permissions object
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminDefaultPermissionsDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint-permissions/default")
        return GovernAdminDefaultPermissionsDefinition(self.client, definition)

    def list_blueprint_permissions(self, as_objects=True):
        """
        List permissions, each as a dict. Each dict contains at least a "blueprintId" field

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_role_permissions_editor.GovernAdminBlueprintPermissions`,
        else returns a list of dict. Each dict contains a field "blueprintId"
        :return: A list of blueprint permissions
        :rtype: list of :class:`~dataikuapi.govern.admin_role_permissions_editor.GovernAdminBlueprintPermissions` or list of dict, see parameter as_objects
        """

        permissions_list = self.client._perform_json("GET", "/admin/blueprint-permissions")

        if as_objects:
            return [GovernAdminBlueprintPermissions(self.client, permissions["blueprintId"]) for permissions in permissions_list]
        else:
            return permissions_list

    def get_blueprint_permissions(self, blueprint_id):
        """
        Get the permissions for a specific blueprint. Returns a handle to interact with the permissions

        :param str blueprint_id: id of the blueprint for which you need the permissions
        :return: A permissions object for the specific blueprint
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """

        return GovernAdminBlueprintPermissions(self.client, blueprint_id)

    def create_blueprint_permissions(self, blueprint_permission):
        """
        Create blueprint permissions and returns the handle to interact with it.

        :param: dict blueprint_permission: Blueprint permission as a dict
        :return: the newly created permissions object
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """
        result = self.client._perform_json("POST", "/admin/blueprint-permissions", body=blueprint_permission)
        return GovernAdminBlueprintPermissions(self.client, result["blueprintId"])


class GovernAdminRole(object):
    """
    A handle to interact with the roles of the instance as an admin.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernRolesPermissionsEditor.get_role`
    """

    def __init__(self, client, role_id):
        self.client = client
        self.role_id = role_id

    def get_definition(self):
        """
        Return the information of the role as an object

        :return: the information of the role.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRoleDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/role/%s" % self.role_id)
        return GovernAdminRoleDefinition(self.client, self.role_id, definition)

    def delete(self):
        """
        Delete the role

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/role/%s" % self.role_id)


class GovernAdminRoleDefinition(object):
    """
    The definition of a specific role.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole.get_role_info`
    """

    def __init__(self, client, role_id, definition):
        self.client = client
        self.role_id = role_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw information of the role.

        :return: the raw definition of role, as a dict. Modifications made to the returned object are reflected when saving
        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this information back to the role

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/role/%s" % self.role_id, body=self.definition)


class GovernAdminBlueprintRoleAssignments(object):
    """
    A handle to interact with the blueprint role assignments for a specific blueprint
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_role_assignments`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Get the role assignments definition. Returns a handle to interact with it.

        :return: The role assignments for a specific blueprint.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint-role-assignments/%s" % self.blueprint_id)
        return GovernAdminBlueprintRoleAssignmentsDefinition(self.client, self.blueprint_id, definition)

    def delete(self):
        """
        Delete the role assignments for a specific blueprint.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-role-assignments/%s" % self.blueprint_id)


class GovernAdminBlueprintRoleAssignmentsDefinition(object):
    """
    The role assignments for a specific blueprint.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content definition of the assignments for this blueprint. This returns a reference to the raw
        assignments, not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this role assignments.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint-role-assignments/%s" % self.blueprint_id, body=self.definition)


class GovernAdminBlueprintPermissions(object):
    """
    A handle to interact with blueprint permissions for a specific blueprint
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_blueprint_permissions`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Get the blueprint permissions definition. Returns a handle to interact with it.

        :return: The permissions definition for a specific blueprint.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissionsDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint-permissions/%s" % self.blueprint_id)
        return GovernAdminBlueprintPermissionsDefinition(self.client, self.blueprint_id, definition)

    def delete(self):
        """
        Delete the permissions for this blueprint and use default permissions instead.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-permissions/%s" % self.blueprint_id)


class GovernAdminBlueprintPermissionsDefinition(object):
    """
    The permissions for a specific blueprint.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this permission back to the blueprint permission definition.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint-permissions/%s" % self.blueprint_id, body=self.definition)


class GovernAdminDefaultPermissionsDefinition(object):
    """
    The default permissions of the instance
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_default_permissions`
    """

    def __init__(self, client, definition):
        self.client = client
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the default permissions. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save the default permissions

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint-permissions/default", body=self.definition)
