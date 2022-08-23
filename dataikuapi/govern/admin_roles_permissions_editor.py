class GovernAdminRolesPermissionsEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_roles_permissions_editor()`
    """

    def __init__(self, client):
        self.client = client

    def list_roles(self, as_objects=True):
        """
        List roles

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`,
         else returns a list of dict. Each dict contains a field "id" indicating the identifier of the role.
        :returns: a list of roles
        :rtype: list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole` or list of dict
        """
        roles = self.client._perform_json("GET", "/admin/roles")

        if as_objects:
            return [GovernAdminRole(self.client, role["id"]) for role in roles]
        else:
            return roles

    def get_role(self, role_id):
        """
        Returns a specific role on the Govern instance

        :param str role_id: Identifier of the role
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
        """
        return GovernAdminRole(self.client, role_id)

    def create_role(self, new_identifier, role_label, role_description=""):
        """
        Creates a new role and returns the handle to interact with it.

        :param str new_identifier: Identifier of the new role
        :param str role_label: Label of the new role
        :param str role_description: (Optional) Description of the new role
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
        """
        result = self.client._perform_json("POST", "/admin/roles/", params={"newIdentifier": new_identifier},
                                           body={"label": role_label, "description": role_description})
        return GovernAdminRole(self.client, result["id"])

    def list_role_assignments(self, as_objects=True):
        """
        List the role assignments,each as a dict. Each dict contains at least a "blueprintId" field

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`,
        else returns a list of dict. Each dict contains a field "blueprintId" indicating the identifier of the blueprint
        :returns: A list of role assignments for each blueprint as a Python list of dict
        :rtype: list of dict
        """
        assignments_list = self.client._perform_json("GET", "/admin/blueprint-role-assignments")

        if as_objects:
            return [GovernAdminBlueprintRoleAssignments(self.client, assignments["blueprintId"]) for assignments in
                    assignments_list]
        else:
            return assignments_list

    def get_role_assignments(self, blueprint_id):
        """
        Get the role assignments for a specific blueprint. Returns a handle to interact with it.

        :param str blueprint_id: id of the blueprint
        :returns: A object representing the role assignments for this blueprint
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """

        return GovernAdminBlueprintRoleAssignments(self.client, blueprint_id)

    def create_role_assignments(self, role_assignments):
        """
        Create a role assignments on the Govern instance and returns the handle to interact with it.

        :param: dict role_assignment: Blueprint permission as a Python dict
        :returns: The newly created role assignment.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        result = self.client._perform_json("POST", "/admin/blueprint-role-assignments", body=role_assignments)

        return GovernAdminBlueprintRoleAssignments(self.client, result["blueprintId"])

    def get_default_permissions(self):
        """
        Get the default permissions. Returns a handle to interact with the permissions

        :returns: A permissions object
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminDefaultPermissions`
        """
        permissions = self.client._perform_json("GET", "/admin/blueprint-permissions/default")
        return GovernAdminDefaultPermissions(self.client, permissions)

    def list_blueprint_permissions(self, as_objects=True):
        """
        List permissions, each as a dict. Each dict contains at least a "blueprintId" field

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_role_permissions_editor.GovernAdminBlueprintPermissions`,
        else returns a list of dict. Each dict contains a field "blueprintId"
        :returns: A list of blueprint permissions
        :rtype: list of dict or list of :class:`~dataikuapi.govern.admin_role_permissions_editor.GovernAdminBlueprintPermissions`
        """

        permissions_list = self.client._perform_json("GET", "/admin/blueprint-permissions")

        if as_objects:
            return [GovernAdminBlueprintPermissions(self.client, permissions.get("blueprintId")) for permissions in
                    permissions_list]
        else:
            return permissions_list

    def get_blueprint_permissions(self, blueprint_id):
        """
        Get the permissions for a specific blueprint. Returns a handle to interact with the permissions

        :param str blueprint_id: id of the blueprint for which you need the permissions
        :returns: A permissions object for the specific blueprint
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """

        return GovernAdminBlueprintPermissions(self.client, blueprint_id)

    def create_blueprint_permissions(self, blueprint_permission):
        """
        Creates blueprint permissions and returns the handle to interact with it.

        :param: dict blueprint_permission: Blueprint permission as a Python dict
        :returns: the newly created permissions object
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """
        result = self.client._perform_json("POST", "/admin/blueprints-permissions", body=blueprint_permission)
        return GovernAdminBlueprintPermissions(self.client, result.get("blueprintId"))


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

        :returns: the information of the role.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRoleDefinition`
        """

        role_info = self.client._perform_json(
            "GET", "/admin/role/%s" % self.role_id)
        return GovernAdminRoleDefinition(self.client, self.role_id, role_info)

    def delete(self):
        """
        Delete the role

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/role/%s" % self.role_id)


class GovernAdminRoleDefinition(object):
    """
    An object with all the information on a role.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole.get_role_info`
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

    def save(self):
        """
        Save this information back to the role

        :return: None
        """
        self.role_info = self.client._perform_json(
            "PUT", "/admin/role/%s" % self.role_id, body=self.role_info)


class GovernAdminBlueprintRoleAssignments(object):
    """
    A handle to interact with the blueprint role assignments
    Do not create this directly, use :meth:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_role_assignments`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Get the role assignments definition. Returns a handle to interact with it.

        :returns: The role assignments for a specific blueprint.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        assignments = self.client._perform_json("GET", "/admin/blueprint-role-assignments/%s" % (
            self.blueprint_id))
        return GovernAdminBlueprintRoleAssignmentsDefinition(self.client, self.blueprint_id, assignments)

    def delete(self):
        """
        Delete the role assignments for a specific blueprint.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-role-assignments/%s" % self.blueprint_id)


class GovernAdminBlueprintRoleAssignmentsDefinition(object):
    """
    A handle to interact with the definition of role assignments for a blueprint.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments.get_definition()`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Gets the raw content definition of the assignments for this blueprint. This returns a reference to the raw
        assignments, not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this role assignments.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint-role-assignments/%s/" % (
            self.blueprint_id), body=self.definition)


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

        :returns: The permissions definition for a specific blueprint.
        :rtype: :class:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissionsDefinition`
        """

        definition = self.client._perform_json("GET", "/admin/blueprint-permissions/%s" % (
            self.blueprint_id))
        return GovernAdminBlueprintRoleAssignmentsDefinition(self.client, self.blueprint_id, definition)

    def delete(self):
        """
        Delete the permissions for this blueprint

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-permissions/%s" % self.blueprint_id)


class GovernAdminBlueprintPermissionsDefinition(object):
    """
    A handle to interact with the definition of the permissions for a given blueprint.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions.get_definition()`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.definition = definition
        self.blueprint_id = blueprint_id

    def get_raw(self):
        """
        Gets the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this permission back to the blueprint permission definition.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint-permissions/%s/" % self.blueprint_id,
                                                    body=self.definition)


class GovernAdminDefaultPermissions(object):
    """
    A handle to interact with the default permissions
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_default_permissions`
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

    def save(self):
        """
        Save the default permissions

        :return: None
        """
        self.permissions = self.client._perform_json("PUT", "/admin/blueprint-permissions/default/",
                                                     body=self.permissions)
