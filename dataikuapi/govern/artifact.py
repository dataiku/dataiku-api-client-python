from dataikuapi.govern.blueprint import GovernBlueprintVersion

class GovernArtifact(object):
    """
    A handle to interact with an artifact on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_artifact`
    """

    def __init__(self, client, artifact_id):
        self.client = client
        self.artifact_id = artifact_id

    def get_definition(self):
        """
        Retrieve the artifact definition and return it as an object.

        :return: the corresponding artifact definition object
        :rtype: :class:`~dataikuapi.govern.artifact.GovernArtifactDefinition`
        """
        artifact = self.client._perform_json("GET", "/artifact/%s" % self.artifact_id)
        return GovernArtifactDefinition(self.client, self.artifact_id, artifact["artifact"])

    def list_signoffs(self):
        """
        List all the sign-offs from the different steps of the workflow for this current artifact.

        :return: the list of sign-offs
        :rtype: list of :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffListItem`
        """
        signoffs = self.client._perform_json("GET", "/artifact/%s/signoffs" % self.artifact_id)
        return [GovernArtifactSignoffListItem(self.client, self.artifact_id, signoff) for signoff in signoffs]

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
    
    def create_signoff(self, step_id):
        """
        Create a sign-off for the given stepId.
        The step must be ongoing and must not hold an existing sign-off.
        Note: the sign-offs of all steps are created automatically when the artifact is created based on the blueprint version sign-off configurations;
        thus this call is useful when the configuration has been added after the creation of the artifact.
        
        :return: the created :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff`
        """
        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/create" % (self.artifact_id, step_id))
        return GovernArtifactSignoff(self.client, self.artifact_id, step_id)

class GovernArtifactDefinition(object):
    """
    The definition of an artifact.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.artifact.GovernArtifact.get_definition`
    """

    def __init__(self, client, artifact_id, definition):
        self.client = client
        self.artifact_id = artifact_id
        self.definition = definition

    def get_blueprint_version(self):
        """
        Retrieve the blueprint version handle of this artifact

        :return: the blueprint version handle
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion`
        """
        return GovernBlueprintVersion(self.client, self.definition["blueprintVersionId"]["blueprintId"], self.definition["blueprintVersionId"]["versionId"])

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


class GovernArtifactSignoffListItem(object):
    """
    An item in a list of sign-offs.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifact.list_signoffs`
    """

    def __init__(self, client, artifact_id, data):
        self.client = client
        self.artifact_id = artifact_id
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the sign-off list item

        :return: the raw content of the sign-off list item as a dict
        :rtype: dict
        """
        return self._data

    def to_signoff(self):
        """
        Gets the :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff` corresponding to this sign-off object

        :return: the sign-off object
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoff`
        """
        return GovernArtifactSignoff(self.client, self.artifact_id, self._data["signoffId"]["stepId"])


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
        Get the definition of the sign-off for this specific workflow step.

        :return: the sign-off definition
        :rtype: :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffDefinition`
        """
        definition = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))
        return GovernArtifactSignoffDefinition(self.client, self.artifact_id, self.step_id, definition)

    def get_recurrence_configuration(self):
        """
        Get the recurrence configuration of the sign-off for this specific workflow step.

        :return: the sign-off recurrence configuration
        :rtype: :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffRecurrenceConfiguration`
        """
        definition = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))
        return GovernArtifactSignoffRecurrenceConfiguration(self.client, self.artifact_id, self.step_id, definition.get("configuration", {}).get("recurrenceConfiguration", {}))

    def get_details(self):
        """
        Get the sign-off details for this specific workflow step.
        This contains a list of computed users included in feedback groups and in the approval.

        :return: sign-off details
        :rtype: :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffDetails`
        """
        details = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff/details" % (self.artifact_id, self.step_id))
        return GovernArtifactSignoffDetails(self.client, self.artifact_id, self.step_id, details)

    def update_status(self, signoff_status, users_to_notify=None, reload_conf_for_reset=False):
        """
        Change the status of the sign-off, takes as input the target status, optionally a list of users to notify and a boolean to indicate if the sign-off configuration should be updated from the blueprint version.
        Only the users included in the groups of feedback and approval are able to give feedback or approval and can be notified,
        the complete list is available using: :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_details`.
        For the feedback, the users will be notified as part of a chosen group of feedback and the group must be specified.

        :param str signoff_status: target feedback status to be chosen from: NOT_STARTED, WAITING_FOR_FEEDBACK, WAITING_FOR_APPROVAL, APPROVED, REJECTED, ABANDONED
        :param users_to_notify: (Optional) List of the user to notify as part of the status change
            (WAITING_FOR_FEEDBACK will involve the feedback groups, WAITING_FOR_APPROVAL will involve the final approval).
            The list should be a list of dict containing two keys "userLogin" and "groupId" for each user to notify.
            The "groupId" key is mandatory for feedback notification and forbidden for the final approval notification.
            All users that are not in the sign-off configuration will be ignored.
        :param boolean reload_conf_for_reset: (Optional, defaults to **False**) Usefull only when the target status is NOT_STARTED.
            If True the current sign-off configuration will be overwritten by the one coming from the blueprint version, all delegated users will be reset.
            If False the current sign-off configuration will remain the same, allowing all delegated users to be retained but any changes to the sign-off configuration in the blueprint version will not be reflected.
        :type users_to_notify: list of dict
        :return: None
        """
        if users_to_notify is None:
            users_to_notify = []

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/update-status" % (self.artifact_id, self.step_id),
            body={"targetStatus": signoff_status, "usersToSendEmailTo": users_to_notify, "reloadConfForReset": reload_conf_for_reset})

    def list_feedbacks(self):
        """
        List all the feedbacks of this current sign-off.

        :return: the list of feedbacks
        :rtype: list of :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedbackListItem`
        """
        definition = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))
        return [GovernArtifactSignoffFeedbackListItem(self.client, self.artifact_id, self.step_id, feedback["id"], feedback) for feedback in definition.get("feedbackResponses", [])]

    def get_feedback(self, feedback_id):
        """
        Get a specific feedback review of this sign-off.

        :param str feedback_id: ID of the feedback review to retrieve from the sign-off
        :return: the corresponding :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedback`
        """
        return GovernArtifactSignoffFeedback(self.client, self.artifact_id, self.step_id, feedback_id)

    def add_feedback(self, group_id, feedback_status, comment=None):
        """
        Add a feedback review for a specific feedback group of the sign-off. Takes as input a group_id (the feedback group id), a feedback status and an optional comment.

        :param str group_id: ID of the feedback group
        :param str feedback_status: feedback status to be chosen from: APPROVED, MINOR_ISSUE, MAJOR_ISSUE
        :param str comment: (Optional) feedback comment
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedback`
        """
        body = {"status": feedback_status}
        if comment is not None:
            body["comment"] = comment

        feedback_data = self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/feedback" % (self.artifact_id, self.step_id),
            params={"groupId": group_id}, body=body)
        return GovernArtifactSignoffFeedback(self.client, self.artifact_id, self.step_id, feedback_data["id"])

    def delegate_feedback(self, group_id, users_container):
        """
        Delegate the feedback to specific users for the sign-off. Takes as input a group_id (the feedback group that should
        have done the feedback originally), and an users container definition to delegate to.

        :param str group_id: ID of the feedback group
        :param dict users_container: a dict representing the users to delegate to.
            Use :meth:`~dataikuapi.govern.users_container.GovernUserUsersContainer.build` to build a users container definition for a single user.
        :return: None
        """
        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-feedback" % (self.artifact_id, self.step_id),
            params={"groupId": group_id}, body=users_container)

    def get_approval(self):
        """
        Get the current approval of this sign-off.

        :return: the corresponding :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffApproval`
        """
        return GovernArtifactSignoffApproval(self.client, self.artifact_id, self.step_id)

    def add_approval(self, approval_status, comment=None):
        """
        Add the final approval of the sign-off. Takes as input an approval status and an optional comment.

        :param str approval_status: approval status to be chosen from: APPROVED, REJECTED, ABANDONED
        :param str comment: (Optional) approval comment
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffApproval`
        """
        body = {"status": approval_status}
        if comment is not None:
            body["comment"] = comment

        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/approval" % (self.artifact_id, self.step_id), body=body)
        return GovernArtifactSignoffApproval(self.client, self.artifact_id, self.step_id)

    def delegate_approval(self, users_container):
        """
        Delegate the approval to specific users of the sign-off. Takes as input an users container definition to delegate to.

        :param str users_container: a dict representing the users to delegate to.
            Use :meth:`~dataikuapi.govern.users_container.GovernUserUsersContainer.build` to build a users container definition for a single user.
        :return: None
        """
        self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/delegate-approval" % (self.artifact_id, self.step_id),
            body=users_container)


class GovernArtifactSignoffDefinition(object):
    """
    The definition of a sign-off.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_definition`
    """

    def __init__(self, client, artifact_id, step_id, definition):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the sign-off definition.

        :rtype: dict
        """
        return self.definition


class GovernArtifactSignoffRecurrenceConfiguration(object):
    """
    The recurrence configuration of a sign-off.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_recurrence_configuration`
    """

    def __init__(self, client, artifact_id, step_id, recurrence_configuration):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.recurrence_configuration = recurrence_configuration

    def get_raw(self):
        """
        Get the raw content of the sign-off recurrence configuration.
        This returns a reference that can be modified to be saved later.
        The returned dict can be empty if the recurrence configuration was not already configured.

        :rtype: dict
        """
        return self.recurrence_configuration

    def save(self):
        """
        Save the recurrence configuration back to the sign-off.
        The recurrence configuration must have the following properties:

        * ``activated`` (boolean)
        * ``days`` (int)
        * ``weeks`` (int)
        * ``months`` (int)
        * ``years`` (int)
        * ``reloadConf`` (boolean)

        :return: None
        """
        signoff = self.client._perform_json("POST", "/artifact/%s/workflow/step/%s/signoff/schedule-reset" % (self.artifact_id, self.step_id), body=self.recurrence_configuration)
        self.recurrence_configuration = signoff.get("configuration", {}).get("recurrenceConfiguration", {})


class GovernArtifactSignoffDetails(object):
    """
    The details of a sign-off.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_details`
    """

    def __init__(self, client, artifact_id, step_id, details):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.details = details

    def get_raw(self):
        """
        Get the raw content of the sign-off details.

        :rtype: dict
        """
        return self.details


class GovernArtifactSignoffFeedbackListItem(object):
    """
    An item in a list of feedback reviews.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.list_feedbacks`
    """

    def __init__(self, client, artifact_id, step_id, feedback_id, data):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.feedback_id = feedback_id
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the feedback review.

        :rtype: dict
        """
        return self._data
    
    def to_feedback(self):
        """
        Gets the :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedback` corresponding to this feedback object

        :return: the feedback object
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedback`
        """
        return GovernArtifactSignoffFeedback(self.client, self.artifact_id, self.step_id, self.feedback_id)
    

class GovernArtifactSignoffFeedback(object):
    """
    Handle to interact with a feedback.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_feedback`
    """

    def __init__(self, client, artifact_id, step_id, feedback_id):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.feedback_id = feedback_id

    def get_definition(self):
        """
        Get the feedback definition.

        :return: the feedback definition object
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedbackDefinition`
        """
        definition = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))
        feedback_data = next((feedback for feedback in definition.get("feedbackResponses", []) if feedback.get("id") == self.feedback_id), None)
        if feedback_data is None:
            raise ValueError("Unable to find a feedback with id '%s'" % (self.feedback_id))
        return GovernArtifactSignoffFeedbackDefinition(self.client, self.artifact_id, self.step_id, self.feedback_id, feedback_data)

    def delete(self):
        """
        Delete this feedback review

        :return: None
        """
        self.client._perform_empty("DELETE", "/artifact/%s/workflow/step/%s/signoff/feedback/%s" % (self.artifact_id, self.step_id, self.feedback_id))


class GovernArtifactSignoffFeedbackDefinition(object):
    """
    The definition of a feedback review.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoffFeedback.get_definition`
    """

    def __init__(self, client, artifact_id, step_id, feedback_id, definition):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.feedback_id = feedback_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the feedback definition.
        This returns a reference to the feedback so changes made to the `status` and `comment` properties will be reflected when saving.

        :rtype: dict
        """
        return self.definition
    
    def save(self):
        """
        Save this feedback review back to the sign-off

        :return: None
        """
        body = {"status": self.definition.get("status")}
        comment = self.definition.get("comment")
        if comment is not None:
            body["comment"] = comment

        self.definition = self.client._perform_json("PUT", "/artifact/%s/workflow/step/%s/signoff/feedback/%s" % (self.artifact_id, self.step_id, self.feedback_id), body=body)


class GovernArtifactSignoffApproval(object):
    """
    Handle to interact with an approval.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoff.get_approval`
    """

    def __init__(self, client, artifact_id, step_id):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id

    def get_definition(self):
        """
        Get the approval definition.

        :return: the approval definition object
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifactSignoffApprovalDefinition`
        """
        definition = self.client._perform_json("GET", "/artifact/%s/workflow/step/%s/signoff" % (self.artifact_id, self.step_id))
        if "approverResponse" not in definition or definition.get("approverResponse") is None:
            raise ValueError("Unable to find the approver response")
        return GovernArtifactSignoffApprovalDefinition(self.client, self.artifact_id, self.step_id, definition["approverResponse"])
        
    def delete(self):
        """
        Delete this approval.

        :return: None
        """
        self.client._perform_empty("DELETE", "/artifact/%s/workflow/step/%s/signoff/approval" % (self.artifact_id, self.step_id))


class GovernArtifactSignoffApprovalDefinition(object):
    """
    The definition of an approval.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact.GovernArtifactSignoffApproval.get_definition`
    """

    def __init__(self, client, artifact_id, step_id, definition):
        self.client = client
        self.artifact_id = artifact_id
        self.step_id = step_id
        self.definition = definition

    def get_raw(self):
        """
        Get the raw content of the approval.
        This returns a reference to the approval so changes made to the `status` and `comment` properties will be reflected when saving.

        :rtype: dict
        """
        return self.definition
    
    def save(self):
        """
        Save this approval back to the sign-off

        :return: None
        """
        body = {"status": self.definition.get("status")}
        comment = self.definition.get("comment")
        if comment is not None:
            body["comment"] = comment

        self.definition = self.client._perform_json("PUT", "/artifact/%s/workflow/step/%s/signoff/approval" % (self.artifact_id, self.step_id), body=body)
