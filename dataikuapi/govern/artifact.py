from dataikuapi.govern.blueprint import GovernBlueprintVersion

class GovernArtifact(object):
    """
    A handle to interact with an artifact on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_artifact`
    """

    def __init__(self, client, artifact_id):
        self.client = client
        self.artifact_id = artifact_id

    def get_blueprint_version(self):
        """
        Retrieve the blueprint version handle of this artifact

        :return: the blueprint version handle
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion`
        """
        artifact = self.client._perform_json("GET", "/artifact/%s" % self.artifact_id)
        return GovernBlueprintVersion(self.client, artifact["blueprintVersion"]["id"]["blueprintId"], artifact["blueprintVersion"]["id"]["versionId"])

    def get_definition(self):
        """
        Retrieve the artifact definition and return it as an object.

        :return: the corresponding artifact definition object
        :rtype: :class:`~dataikuapi.govern.artifact.GovernArtifactDefinition`
        """
        artifact = self.client._perform_json("GET", "/artifact/%s" % self.artifact_id)
        return GovernArtifactDefinition(self.client, self.artifact_id, artifact["artifact"])

    def list_signoffs(self, as_objects=True):
        """
        List all the signoffs from the different steps of the workflow for this current artifact.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff`,
        else returns a list of dict. Each dict contains at least a field "stepId" indicating the identifier the sign-off
        :return: the list of sign-offs, each as a dict or an object. Each dict contains at least an "stepId" field
        :rtype: list of :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff` or list of dict, see param as_objects
        """
        signoffs = self.client._perform_json("GET", "/artifact/%s/signoffs" % self.artifact_id)
        if as_objects:
            return [GovernArtifactSignoff(self.client, self.artifact_id, signoff["stepId"]) for signoff in signoffs]
        else:
            return signoffs

    def get_signoff(self, step_id):
        """
        Get the sign-off for a specific step of the workflow for this current artifact.

        :param str step_id: id of the step to retrieve the sign-off from
        :return: the corresponding :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff`
        """
        return GovernArtifactSignoff(self.client, self.artifact_id, step_id)

    def delete(self):
        """
        Delete the artifact

        :return: None
        """
        self.client._perform_empty("DELETE", "/artifact/%s" % self.artifact_id)


class GovernArtifactDefinition(object):
    """
    The definition of an artifact.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.artifact.GovernArtifact.get_definition`
    """

    def __init__(self, client, artifact_id, definition):
        self.client = client
        self.artifact_id = artifact_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the artifact. This returns a reference to the artifact so changes made to the returned
        object will be reflected when saving.

        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the artifact.
        """
        self.definition = self.client._perform_json("PUT", "/artifact/%s" % self.artifact_id, body=self.definition)["artifact"]


class GovernArtifactSignoff(object):
    """
    Handle to interact with the sign-off of a specific workflow step.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifact.get_signoff`
    """

    def __init__(self, client, artifact_id, step_id):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id

    def get_definition(self):
        """
        Get the last sign-off cycle definition or this specific workflow step.

        :return: sign-off cycle as python dict
        :rtype: dict
        """
        return self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))

    def get_details(self):
        """
        Get the last sign-off cycle details for this specific workflow step.
        This contains a list of computed users included in feedback ground and in the approval.

        :return: sign-off cycle details as python dict
        :rtype: dict
        """
        return self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff/details" % (self.artifact_id, self.step_id))

    def update_status(self, signoff_status, users_to_notify=None):
        """
        Change the status of the last cycle of the sign-off, takes as input the target status and optionally a list of users to notify.
        Only the users included in the groups of feedback and approval are able to give feedback or approval and can be notified,
        the complete list is available using: :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_details`.
        For the feedback, the users will be notified as part of a chosen group of feedback and the group must be specified.

        :param str signoff_status: target feedback status to be chosen from: NOT_STARTED, WAITING_FOR_FEEDBACK, WAITING_FOR_APPROVAL, APPROVED, REJECTED, ABANDONED
        :param list of dict users_to_notify: (Optional) List of the user to notify as part of the status change
        (WAITING_FOR_FEEDBACK will involve the feedback groups, WAITING_FOR_APPROVAL will involve the final approval).
        The list should be a list of dict containing two keys "userLogin" and "groupId" for each user to notify.
        The "groupId" key is mandatory for feedback notification and forbidden for the final approval notification.
        All users that are not in the sign-off configuration will be ignored.
        :return: None
        """
        if users_to_notify is None:
            users_to_notify = []

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/update-status" % (self.artifact_id, self.step_id),
            body={"targetStatus": signoff_status, "usersToSendEmailTo": users_to_notify})

    def add_feedback(self, group_id, feedback_status, comment=None):
        """
        Add a feedback for a specific feedback group of the last cycle of the sign-off. Takes as input a step_id, a group_id (the feedback group id), a
        feedback status and an optional comment

        :param str group_id: id of the feedback group
        :param str feedback_status: feedback status to be chosen from: APPROVED, MINOR_ISSUE, MAJOR_ISSUE
        :param str comment: (Optional) feedback comment
        :return: None
        """
        body = {"status": feedback_status}
        if comment is not None:
            body["comment"] = comment

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/add-feedback" % (self.artifact_id, self.step_id),
            params={"groupId": group_id}, body=body)

    def delegate_feedback(self, group_id, users_container):
        """
        Delegate a feedback to specific users for the last cycle of the sign-off. Takes as input a group_id (the feedback group that should
        have done the feedback originally), and an users container definition to delegate to.

        :param str group_id: id of the feedback group
        :param dict users_container: a dict representing the users to delegate to.
        Use :meth:`~dataikuapi.govern.users_container.GovernUserUsersContainer.build` to build a users container definition for a single user.
        :return: None
        """

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-feedback" % (self.artifact_id, self.step_id),
            params={"groupId": group_id}, body=users_container)

    def add_approval(self, approval_status, comment=None):
        """
        Add the final approval of the last cycle of the sign-off. Takes as input a step_id, a feedback status and an optional comment

        :param str approval_status: approval status to be chosen from: APPROVED, REJECTED, ABANDONED
        :param str comment: (Optional) approval comment
        :return: None
        """

        body = {"status": approval_status}
        if comment is not None:
            body["comment"] = comment

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/add-approval" % (self.artifact_id, self.step_id), body=body)

    def delegate_approval(self, users_container):
        """
        Delegate the approval to specific users for the last cycle of the sign-off. Takes as input an users container definition to delegate to.

        :param str users_container: a dict representing the users to delegate to.
        Use :meth:`~dataikuapi.govern.users_container.GovernUserUsersContainer.build` to build a users container definition for a single user.
        :return: None
        """

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-approval" % (self.artifact_id, self.step_id),
            body=users_container)

