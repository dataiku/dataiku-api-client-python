class GovernAdminBlueprintRoleAssignments(object):
    """
    A handle to interact with the blueprint role assignments
    Do not create this directly, use :meth:`dataikuapi.govern.admin_roles_permission_editor.GovernAdminRolesPermissionsEditor.get_role_assignments`
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
        return self.role_assignments["blueprintId"]

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
`       :rtype: dict`
        """
        return self.role_assignments["roleAssignmentsRules"]

    def get_inherit_blueprint_id(self):
        """
        Get the blueprint id from which the rule inherit.

        :return: str inherit blueprint id
        :rtype: str
        """
        return self.role_assignments["inheritBlueprintId"]

    def get_inherit_artifact_field_id(self):
        """
        Get the artifact field id from which the artifact inherit

        :return: str inherit artifact field id
        :rtype: str
        """
        return self.role_assignments["inheritArtifactFieldId"]

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
