from dataikuapi.govern.models.admin.admin_role import GovernAdminRole
from dataikuapi.govern.models.blueprint_permission import GovernBlueprintPermission
from dataikuapi.govern.models.blueprint_role_assignment import GovernBlueprintRoleAssignment


class GovernRolesPermissionsEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_roles_permissions_editor()`
    """

    def __init__(self, client):
        self.client = client

    def list_roles(self):
        """
        Lists roles on the Govern instance.

        :returns: a list of roles
        :rtype: list of :class: `dataikuapi.govern.models.role.Role`
        """
        roles = self.client._perform_json("GET", "/admin/roles")
        return [GovernAdminRole(self.client, role['id']) for role in roles]

    def get_role(self, role_id):
        """
        Returns a specific role on the Govern instance

        :param str role_id: Identifier of the role to get
        :rtype: :class:`dataikuapi.govern.models.admin_role.GovernAdminRole
        """
        return GovernAdminRole(self.client, role_id)

    def create_role(self, new_identifier, role_label, role_description=""):
        """
        Creates a new role for the Govern instance and returns the handle to interact with it.

        :param str new_identifier: Identifier of the new role
        :param str role_label: Label of the new role
        :param str role_description: Description of the new role
        :rtype: :class:`GovernAPIRole
        """
        result = self.client._perform_json("POST", "/admin/roles/", params={"newIdentifier": new_identifier},
                                           body={"label": role_label, "description": role_description})
        return GovernAdminRole(self.client, result['id'])

    def delete_role(self, role_id):
        """
        Delete an artifact from a Govern node

        :param str role_id: id of the role to delete
        """

        self.client._perform_empty("DELETE", "/admin/role/%s" % role_id)

    def list_permissions(self):
        """
        List permissions on the Govern instance

        :returns: a list of blueprint permissions
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-permissions")

    def get_permission(self, blueprint_id):
        """
        Get the permissions for a specific blueprint. Returns a handle to interact with the permissions

        :param str blueprint_id: id of the blueprint for which you need the permissions
        :returns: a permission object
        :rtype: :class:`dataikuapi.govern.models.blueprint_permission.GovernBlueprintPermission`
        """
        permission = self.client._perform_json("GET", "/admin/blueprint-permissions/%s" % (
            blueprint_id))
        return GovernBlueprintPermission(self.client, permission)

    def create_permission(self, blueprint_permission):
        """
        Creates a blueprint permission on the Govern instance and returns the handle to interact with it.

        :param: dict blueprint_permission: Blueprint permission as a Python dict
        :returns: the newly created blueprint_permission
        :rtype: :class:`dataikuapi.govern.models.blueprint_permission.GovernBlueprintPermission`
        """
        result = self.client._perform_json("POST", "/admin/blueprints-permissions", body=blueprint_permission)
        return GovernBlueprintPermission(self.client, result)

    def delete_permission(self, blueprint_id):
        """
        Delete the permissions for a specific blueprint

        :param: str blueprint_id the blueprint id of the permission to delete
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-permissions/%s" % (
            blueprint_id))

    def list_role_assignments(self):
        """
        List the role assignments Govern instance.

        :returns: a list of role assignments for each blueprint as a Python list of dict
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-role-assignments")

    def get_role_assignment(self, blueprint_id):
        """
        Get the role assignment for a specific blueprint. Returns a handle to interact with it.
        TODO: the endpoints returns a 404 when not assignment exist.
        :param str blueprint_id: id of the blueprint
        :returns: a list of role assignment
        :rtype: :class:`dataikuapi.govern.models.blueprint_role_assignment.GovernBlueprintRoleAssignment`
        """
        assignment = self.client._perform_json("GET", "/admin/blueprint-role-assignment/%s" % (
            blueprint_id))
        return GovernBlueprintRoleAssignment(self.client, assignment)

    def create_role_assignment(self, role_assignment):
        """
        Creates a role assignment on the Govern instance and returns the handle to interact with it.

        :param: dict role_assignment: Blueprint permission as a Python dict
        :returns: the newly created role assignment.
        :rtype: :class:`dataikuapi.govern.models.blueprint_role_assignment.GovernBlueprintRoleAssignment``
        """
        result = self.client._perform_json("POST", "/admin/blueprint-role-assignments", body=role_assignment)
        return GovernBlueprintRoleAssignment(self.client, result)

    def delete_role_assignment(self, blueprint_id):
        """
        Delete the role assignment for a specific blueprint.

        :param: str blueprint_id the blueprint id of the assignment to delete
        """
        self.client._perform_empty("DELETE", "/admin/blueprint-role-assignments/%s" % (
            blueprint_id))





