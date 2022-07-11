class GovernBlueprintRoleAssignment(object):
    """
    A handle to interact with a blueprint permission the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.GovernRolesPermissionsEditor.get_role_assignment`
    """

    def __init__(self, client, role_assignment):
        self.client = client
        self.role_assignment = role_assignment

    @property
    def id(self):
        """
        Gets blueprint_id relative to this role assignment object.
        :rtype: str
        """
        return self.role_assignment["blueprintId"]

    def get_raw(self):
        """
        Gets the raw content of the permissions for this blueprint. This returns a reference to the raw permissions,
         not a copy, so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.role_assignment

    def get_role_assignments_rules(self):
        """
        Get the role assignment rules that apply for this blueprint

        :return: A python dict containing the role assignments rules
`       :rtype: dict`
        """
        return self.role_assignment["roleAssignmentsRules"]

    def get_inherit_blueprint_id(self):
        """
        Get the blueprint id from which the rule inherit.

        :return: str inherit blueprint id
        :rtype: str
        """
        return self.role_assignment["inheritBlueprintId"]

    def get_inherit_artifact_field_id(self):
        """
        Get the artifact field id from which the artifact inherit

        :return: str inherit artifact field id
        :rtype: str
        """
        return self.role_assignment["inheritArtifactFieldId"]

    def save(self):
        """
        Save this role assignment.

        """
        self.role_assignment = self.client._perform_json("PUT", "/admin/blueprint-role-assignments/%s/" % (
            self.id), body=self.role_assignment)
