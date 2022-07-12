class GovernAdminRolesAudit(object):
    """
    Handle to get audit information the roles and permissions
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_roles_audit()`
    """

    def __init__(self, client):
        self.client = client

    def audit_blueprint_roles(self, user_login, blueprint_id):
        """
        Get the assigned roles and permissions information for a specific user at a specific blueprint level.

        :param str user_login: login of the user
        :param str blueprint_id: id of the blueprint
        :returns: audit information for this pair user, blueprint.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint",
                                         body={"userLogin": user_login, "blueprintId": blueprint_id})

    def audit_blueprint_version_roles(self, user_login, blueprint_id, version_id):
        """
        Get the assigned roles and permissions information for a specific user at a specific blueprint version level.

        :param str user_login: login of the user
        :param str blueprint_id: id of the blueprint
        :param str version_id: id of the blueprint version
        :returns: audit information for this pair user, blueprint version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-blueprint-version",
                                         body={"userLogin": user_login,
                                               "blueprintVersionId": {"blueprintId": blueprint_id,
                                                                      "versionId": version_id}})

    def audit_artifact_existing_roles(self, user_login, artifact_id):
        """
        Get the assigned roles and permissions information for a specific user at a specific artifact level.

        :param str user_login: login of the user
        :param str artifact_id: id of the artifact
        :returns: audit information for this pair user, artifact.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-existing-artifact",
                                         body={"userLogin": user_login, "artifactId": artifact_id})

    def audit_artifact_deleted_roles(self, user_login, blueprint_id, version_id):
        """
        Get the assigned roles and permissions information for the deleted artifact of a blueprint version and for a
        specific user.

        :param str user_login: login of the user
        :param str blueprint_id: id of the blueprint
        :param str version_id: id of the blueprint version
        :returns: audit information for the deleted artifact of this blueprint_version.
        :rtype: dict
        """

        return self.client._perform_json("POST", "/admin/roles-audit/level-deleted-artifact",
                                         body={"userLogin": user_login,
                                               "blueprintVersionId": {"blueprintId": blueprint_id,
                                                                      "versionId": version_id}})
