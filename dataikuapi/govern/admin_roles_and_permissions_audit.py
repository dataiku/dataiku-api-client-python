class GovernAdminRolesAndPermissionsAudit(object):
    """
    Handle to get audit information on the computed roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_roles_and_permissions_audit`
    """

    def __init__(self, client):
        self.client = client

    def audit_blueprint_admin_roles_permissions(self, auth_identifier, blueprint_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context and blueprint.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str blueprint_id: id of the blueprint
        :returns: audit information for this specific authentication context and blueprint.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint",
                                         body={"authIdentifier": auth_identifier, "blueprintId": blueprint_id})

    def audit_blueprint_version_roles(self, auth_identifier, blueprint_id, version_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context at a specific
        blueprint version level.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str blueprint_id: id of the blueprint
        :param str version_id: id of the blueprint version
        :returns: audit information for this specific authentication context and blueprint version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint-version",
                                         body={"userLogin": auth_identifier,
                                               "blueprintVersionId": {"blueprintId": blueprint_id,
                                                                      "versionId": version_id}})

    def audit_artifact_existing_roles(self, auth_identifier, artifact_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context and existing
        artifact.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str artifact_id: id of the artifact
        :returns: audit information for this specific authentication context and artifact.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-existing-artifact",
                                         body={"userLogin": auth_identifier, "artifactId": artifact_id})

    def audit_artifact_deleted_roles(self, auth_identifier, blueprint_id, version_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context and the deleted
        artifact of a blueprint version.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str blueprint_id: id of the blueprint
        :param str version_id: id of the blueprint version
        :returns: audit information for the deleted artifact of this blueprint_version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-deleted-artifact",
                                         body={"userLogin": auth_identifier,
                                               "blueprintVersionId": {"blueprintId": blueprint_id,
                                                                      "versionId": version_id}})
