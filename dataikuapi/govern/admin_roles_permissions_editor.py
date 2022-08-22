class GovernAdminRolesPermissionsEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_roles_permissions_editor`
    """

    def __init__(self, client):
        self.client = client

    def list_roles(self):
        """
        List roles

        :returns: a list of roles
        :rtype: list of :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
        """
        roles = self.client._perform_json("GET", "/admin/roles")
        return [GovernAdminRole(self.client, role['id']) for role in roles]

    def get_role(self, role_id):
        """
        Returns a specific role on the Govern instance

        :param str role_id: Identifier of the role
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole`
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
        return GovernAdminRole(self.client, result['id'])

    def list_role_assignments(self):
        """
        List the role assignments,each as a dict. Each dict contains at least a "blueprintId" field

        :returns: A list of role assignments for each blueprint as a Python list of dict
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-role-assignments")

    def get_role_assignments(self, blueprint_id):
        """
        Get the role assignments for a specific blueprint. Returns a handle to interact with it.

        :param str blueprint_id: id of the blueprint
        :returns: A list of role assignments
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        assignments = self.client._perform_json("GET", "/admin/blueprint-role-assignments/%s" % (
            blueprint_id))
        return GovernAdminBlueprintRoleAssignments(self.client, assignments)

    def create_role_assignments(self, role_assignments):
        """
        Create a role assignments on the Govern instance and returns the handle to interact with it.

        :param: dict role_assignment: Blueprint permission as a Python dict
        :returns: The newly created role assignment.
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintRoleAssignments`
        """
        result = self.client._perform_json("POST", "/admin/blueprint-role-assignments", body=role_assignment)
        return GovernAdminBlueprintRoleAssignments(self.client, result)

    def get_default_permissions(self):
        """
        Get the default permissions. Returns a handle to interact with the permissions

        :returns: A permissions object
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminDefaultPermissions`
        """
        permissions = self.client._perform_json("GET", "/admin/blueprint-permissions/default")
        return GovernAdminDefaultPermissions(self.client, permissions)

    def list_blueprint_permissions(self):
        """
        List permissions, each as a dict. Each dict contains at least a 'blueprintId' field

        :returns: A list of blueprint permissions
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-permissions")

    def get_blueprint_permissions(self, blueprint_id):
        """
        Get the permissions for a specific blueprint. Returns a handle to interact with the permissions

        :param str blueprint_id: id of the blueprint for which you need the permissions
        :returns: A permissions object for the specific blueprint
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """
        permissions = self.client._perform_json("GET", "/admin/blueprint-permissions/%s" % (
            blueprint_id))
        return GovernAdminBlueprintPermissions(self.client, permissions)

    def create_blueprint_permissions(self, blueprint_permission):
        """
        Creates blueprint permissions and returns the handle to interact with it.

        :param: dict blueprint_permission: Blueprint permission as a Python dict
        :returns: the newly created permissions object
        :rtype: :class:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminBlueprintPermissions`
        """
        result = self.client._perform_json("POST", "/admin/blueprints-permissions", body=blueprint_permission)
        return GovernAdminBlueprintPermissions(self.client, result)


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
        return GovernAdminRoleInfo(self.client, self.role_id, role_info)


class GovernAdminRoleDefinition(object):
    """
    An object with all the information on a role.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRole.get_role_info`
    """

    def __init__(self, client, role_id, role_info):
        self.client = client
        self.role_id = role_id
        self.role_definition = role_definition

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
        return self.role_info.get("label")

    @property
    def description(self):
        """
        Gets the description of the role.

        :rtype: str
        """
        return self.role_info.get("description")

    @label.setter
    def label(self, label):
        """
        Set the label of the role

        :param str label: the new label to set
        :return: None
        """
        self.role_info["label"] = label

    @description.setter
    def description(self, description):
        """
        Set the label of the role

        :param str description: the new description to set
        :return: None
        """
        self.role_info["description"] = description

    def save(self):
        """
        Save this information back to the role

        :return: None
        """
        self.role_info = self.client._perform_json(
            "PUT", "/admin/role/%s" % self.role_id, body=self.role_info)

    def delete_role(self):
        """
        Delete the role

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/role/%s" % self.role_id)


class GovernAdminBlueprintRoleAssignments(object):
    """
    A handle to interact with the blueprint role assignments
    Do not create this directly, use :meth:`dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_role_assignments`
    """

    def __init__(self, client, role_assignments):
        self.client = client
        self.role_assignments = role_assignments

    @property
    def id(self):
        """
        Gets blueprint_id relative to this role assignment object.

        :rtype: str
        """
        return self.role_assignments.get("blueprintId")

    def get_raw(self):
        """
        Gets the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
        not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.role_assignments

    def get_role_assignments_rules(self):
        """
        Get the role assignment rules that apply for this blueprint

        :return: A python dict containing the role assignments rules
`       :rtype: dict
        """
        return self.role_assignments.get("roleAssignmentsRules")

    def get_inherit_blueprint_id(self):
        """
        Get the blueprint id from which the rule inherit.

        :return: inherit blueprint id
        :rtype: str
        """
        return self.role_assignments.get("inheritBlueprintId")

    def get_inherit_artifact_field_id(self):
        """
        Get the artifact field id from which the artifact inherit

        :return: inherit artifact field id
        :rtype: str
        """
        return self.role_assignments.get("inheritArtifactFieldId")

    def save(self):
        """
        Save this role assignment.

        :return: None
        """
        self.role_assignments = self.client._perform_json("PUT", "/admin/blueprint-role-assignments/%s/" % (
            self.id), body=self.role_assignments)

    def delete_role_assignments(self):
        """
        Delete the role assignments for a specific blueprint.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-role-assignments/%s" % (
            self.id))


class GovernAdminBlueprintPermissions(object):
    """
    A handle to interact with blueprint permissions for a specific blueprint
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_roles_permissions_editor.GovernAdminRolesPermissionsEditor.get_blueprint_permissions`
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
        return self.permissions.get("rolePermissions", {}).get(role_id)

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
        return self.permissions.get("rolePermissions", {}).get(role_id)

    def save(self):
        """
        Save the default permissions

        :return: None
        """
        self.permissions = self.client._perform_json("PUT", "/admin/blueprint-permissions/default/",
                                                     body=self.permissions)
