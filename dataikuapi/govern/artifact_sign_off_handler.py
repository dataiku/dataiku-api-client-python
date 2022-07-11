class GovernArtifactSignOffHandler(object):
    """
    Handle to interact with the different steps of a workflow.
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_artifact_sign_off_handler()`
    """

    def __init__(self, client, artifact_id):
        self.client = client
        self.artifact_id = artifact_id

    def get_details(self, step_id):
        """
        Get the signoff cycle detail for a specific step of the workflow for this current artifact. This contains a list
        of the feedback groups and a list of the approval users.

        :param str step_id: id of the step
        :returns: sign off cycle details as python dict
        :rtype: dict
        """

        return self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff/details" % (self.artifact_id,
                                                                                                   step_id))

    def list_signoffs(self):
        """
        List all the signoffs from the different steps of the workflow for this current artifact.

        :returns: a list of sign off as python dict
        :rtype: list of dicts
        """

        return self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % self.artifact_id)

    def get_signoff(self, step_id):
        """
        Get the signoffs for a specific step of the workflow for this current artifact.

        :param str step_id: id of the step
        :returns: sign off as python dict
        :rtype: dict
        """
        return self.client._perform_json("GET", "/artifact/%s/signoffs/%s" % (self.artifact_id, step_id))

    def delegate_feedback(self, step_id, group_id, user_login):
        """
        Delegate a feedback to a specific user. Takes as input a step_id, a group_id (the feedback group that should
        have done the feedback originally), and a user login that will be the delegated user.

        :param str step_id: id of the step
        :param str group_id: id of the feedback group
        :param str user_login: delegated user
        :returns: sign off cycle as a python dict
        :rtype: dict
        """

        return self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-feedback" % (
            self.artifact_id, step_id), params={"groupId": group_id}, body={"type": "user", "login": user_login})

    def add_feedback(self, step_id, group_id, status, comment=None):
        """
        Add a feedback to a specific feedback group. Takes as input a step_id, a group_id (the feedback group id), a
        feedback status and an optional comment

        :param str step_id: id of the step
        :param str group_id: id of the feedback group
        :param str status: feedback status to be chosen from: APPROVED, MINOR_ISSUE, MAJOR_ISSUE
        :param str comment: (Optional) feedback comment
        :returns: sign off cycle as a python dict
        :rtype: dict
        """
        body = {"status": status}
        if comment is not None:
            body["comment"] = comment

        return self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/add-feedback" % (
            self.artifact_id, step_id), params={"groupId": group_id}, body=body)

    def delegate_approval(self, step_id, user_login):
        """
        Delegate an approval to a specific user. Takes as input a step_id, and a user login that will be in charge of
        the approval.

        :param str step_id: id of the step
        :param str user_login: delegated user
        :returns: sign off cycle as a python dict
        :rtype: dict
        """

        return self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-approval" % (
            self.artifact_id, step_id), body={"type": "user", "login": user_login})

    def add_approval(self, step_id, status, comment=None):
        """
        Add an approval on a step. Takes as input a step_id, a feedback status and an optional comment

        :param str step_id: id of the step
        :param str status: feedback status to be chosen from: APPROVED, REJECTED, ABANDONED
        :param str comment: (Optional) approval comment
        :returns: sign off cycle as a python dict
        :rtype: dict
        """

        body = {"status": status}
        if comment is not None:
            body["comment"] = comment

        return self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/add-approval" % (
            self.artifact_id, step_id), body=body)

    def update_status(self, step_id, status, users_to_notify):
        """
        Change the status of the sign-off, takes as input a list of pairs user, group_id to notify. The user will be
        notified as part of the group group_id.

        :param str step_id: id of the step
        :param str status: target feedback status to be chosen from: NOT_STARTED, WAITING_FOR_FEEDBACK, WAITING_FOR_APPROVAL,
        APPROVED, REJECTED, ABANDONED;
        :param list of dict users_to_notify: List of the user to notify. The list should be a list of dict containing
        two keys "userLogin" and "groupId" for each user to notify. Each user will be notified as part of the given
        group.
        :returns: sign off cycle as a python dict
        :rtype: dict
        """

        return self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/add-approval" % (
            self.artifact_id, step_id), body={"targetStatus": status, "usersToSendEmailTo": users_to_notify})
