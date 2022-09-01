class GovernAdminRolesAndPermissionsAudit(object):
    """
    Handle to get audit information on the computed roles and permissions
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_roles_and_permissions_audit`
    """

    def __init__(self, client):
        self.client = client

    def audit_level_blueprint(self, auth_identifier, blueprint_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context at a specific blueprint level.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str blueprint_id: id of the blueprint
        :return: audit information for this specific authentication context and blueprint.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint",
                                         body={"authIdentifier": auth_identifier, "blueprintId": blueprint_id})

    def audit_level_blueprint_version(self, auth_identifier, blueprint_version_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context at a specific
        blueprint version level.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param dict blueprint_version_id: id of the blueprint version containing "blueprintId" and "versionId" keys.
        Use :meth:`~dataikuapi.govern.blueprint.BlueprintVersionId.build` to build this blueprint verison ID definition.
        :return: audit information for this specific authentication context and blueprint version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint-version",
                                         body={"authIdentifier": auth_identifier, "blueprintVersionId": blueprint_version_id})

    def audit_level_artifact_existing(self, auth_identifier, artifact_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context and existing
        artifact.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param str artifact_id: id of the artifact
        :return: audit information for this specific authentication context and artifact.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-artifact-existing",
                                         body={"authIdentifier": auth_identifier, "artifactId": artifact_id})

    def audit_level_artifact_deleted(self, auth_identifier, blueprint_version_id):
        """
        Get the assigned roles and permissions audit information for a specific authentication context and the deleted
        artifact of a blueprint version.

        :param str auth_identifier: identifier of the authentication context (the login of the user)
        :param dict blueprint_version_id: id of the blueprint version containing "blueprintId" and "versionId" keys.
        Use :meth:`~dataikuapi.govern.blueprint.BlueprintVersionId.build` to build this blueprint verison ID definition.
        :return: audit information for the deleted artifact of this blueprint_version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-artifact-deleted",
                                         body={"authIdentifier": auth_identifier, "blueprintVersionId": blueprint_version_id})
