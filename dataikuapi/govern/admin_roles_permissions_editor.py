from dataikuapi.govern.models.admin.admin_blueprint_permissions import GovernAdminBlueprintPermissions
from dataikuapi.govern.models.admin.admin_blueprint_role_assignment import GovernAdminBlueprintRoleAssignments
from dataikuapi.govern.models.admin.admin_default_permissions import GovernAdminDefaultPermissions
from dataikuapi.govern.models.admin.admin_role import GovernAdminRole


class GovernAdminRolesPermissionsEditor(object):
    """
    Handle to edit the roles and permissions
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_admin_roles_permissions_editor()`
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
        :rtype: :class:`dataikuapi.govern.models.admin_role.GovernAdminRole`
        """
        return GovernAdminRole(self.client, role_id)

    def create_role(self, new_identifier, role_label, role_description=""):
        """
        Creates a new role for the Govern instance and returns the handle to interact with it.

        :param str new_identifier: Identifier of the new role
        :param str role_label: Label of the new role
        :param str role_description: Description of the new role
        :rtype: :class: `dataikuapi.govern.models.admin_role.GovernAdminRole`
        """
        result = self.client._perform_json("POST", "/admin/roles/", params={"newIdentifier": new_identifier},
                                           body={"label": role_label, "description": role_description})
        return GovernAdminRole(self.client, result['id'])

    def list_role_assignments(self):
        """
        List the role assignments Govern instance, each as a dict. Each dict contains at least a 'blueprintId' field

        :returns: a list of role assignments for each blueprint as a Python list of dict
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-role-assignments")

    def get_role_assignments(self, blueprint_id):
        """
        Get the role assignment for a specific blueprint. Returns a handle to interact with it.

        :param str blueprint_id: id of the blueprint
        :returns: a list of role assignment
        :rtype: :class:`dataikuapi.govern.models.admin_blueprint_role_assignment.GovernAdminBlueprintRoleAssignments`
        """
        assignments = self.client._perform_json("GET", "/admin/blueprint-role-assignments/%s" % (
            blueprint_id))
        return GovernAdminBlueprintRoleAssignments(self.client, assignments)

    def create_role_assignment(self, role_assignment):
        """
        Creates a role assignment on the Govern instance and returns the handle to interact with it.

        :param: dict role_assignment: Blueprint permission as a Python dict
        :returns: the newly created role assignment.
        :rtype: :class:`dataikuapi.govern.models.admin_blueprint_role_assignment.GovernAdminBlueprintRoleAssignments``
        """
        result = self.client._perform_json("POST", "/admin/blueprint-role-assignments", body=role_assignment)
        return GovernAdminBlueprintRoleAssignments(self.client, result)

    def get_default_permissions(self):
        """
        Get the default permissions. Returns a handle to interact with the permissions

        :returns: a permission object
        :rtype: :class:`dataikuapi.govern.models.admin_blueprint_permissions.GovernAdminBlueprintPermissions`
        """
        permissions = self.client._perform_json("GET", "/admin/blueprint-permissions/default")
        return GovernAdminDefaultPermissions(self.client, permissions)

    def list_blueprint_permissions(self):
        """
        List permissions on the Govern instance, each as a dict. Each dict contains at least a 'blueprintId' field

        :returns: a list of blueprint permissions
        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/admin/blueprint-permissions")

    def get_blueprint_permissions(self, blueprint_id):
        """
        Get the permissions for a specific blueprint. Returns a handle to interact with the permissions

        :param str blueprint_id: id of the blueprint for which you need the permissions
        :returns: a permission object
        :rtype: :class:`dataikuapi.govern.models.admin_blueprint_permissions.GovernAdminBlueprintPermissions`
        """
        permissions = self.client._perform_json("GET", "/admin/blueprint-permissions/%s" % (
            blueprint_id))
        return GovernAdminBlueprintPermissions(self.client, permissions)

    def create_blueprint_permission(self, blueprint_permission):
        """
        Creates a blueprint permission on the Govern instance and returns the handle to interact with it.

        :param: dict blueprint_permission: Blueprint permission as a Python dict
        :returns: the newly created blueprint_permission
        :rtype: :class:`dataikuapi.govern.models.admin_blueprint_permissions.GovernAdminBlueprintPermissions`
        """
        result = self.client._perform_json("POST", "/admin/blueprints-permissions", body=blueprint_permission)
        return GovernAdminBlueprintPermissions(self.client, result)
