class GovernArtifact(object):
    def __init__(self, client, artifact_id, artifact):
        """
        A handle to interact with an artifact on the Govern instance.
        Do not create this directly, use :meth:`dataikuapi.GovernClient.get_artifact`
        """
        self.client = client
        self.artifact_id = artifact_id
        self.artifact = artifact

    def get_raw(self):
        """
        Gets the raw content of the artifact. This returns a reference to the artifact so changes made to the returned
        object will be reflected when saving.

        :rtype: dict
        """
        return self.artifact

    @property
    def id(self):
        """
        Return the artifact id.

        :return: the artifact id as a Python str
        """
        return self.artifact_id

    @property
    def name(self):
        """
        Return the artifact name.

        :return: the artifact name as a Python str
        """
        return self.artifact.get("name")

    @property
    def fields(self):
        """
        Return the artifact fields.

        :return: the artifact fields as a Python dict
        """
        return self.artifact.get("fields")

    @property
    def attachments(self):
        """
        Return the artifact attachments.

        :return: the artifact attachments as a Python dict
        """
        return self.artifact.get("attachments")

    @property
    def blueprint_version_id(self):
        """
        Return the artifact blueprint version id.

        :return: the artifact blueprint version id as a Python dict
        """
        return self.artifact.get("blueprintVersionId")

    @property
    def status(self):
        """
        Return the artifact status.

        :return: the artifact status as a Python dict
        """
        return self.artifact.get("status")

    @name.setter
    def name(self, name):
        """
        Set the artifact name.

        :param str name: the artifact name

        :return: None
        """
        self.artifact["name"] = name

    def save(self):
        """
        Save this settings back to the artifact.
        """
        self.artifact = self.client._perform_json("PUT", "/artifact/%s" % self.artifact_id, body=self.artifact)

    def delete(self):
        """
        Delete the artifact

        :return: None
        """
        self.client._perform_empty("DELETE", "/artifact/%s" % self.artifact_id)
