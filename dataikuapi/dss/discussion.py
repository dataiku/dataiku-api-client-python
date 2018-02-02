import json

class DSSObjectDiscussions(object):
    """
    A handle to manage discussions on a DSS object
    """
    def __init__(self, client, project_key, object_type, object_id):
        self.client = client
        self.project_key = project_key
        self.object_type = object_type
        self.object_id = object_id

    ##########################
    # Discussions on an object
    ##########################
    def list_discussions(self):
        """
        Get list of discussions

        Returns:
            array of discussions on a DSS object
        """
        return self.client._perform_json("GET", "/projects/%s/discussions/%s/%s/" % (self.project_key, self.object_type, self.object_id))

    def create_discussion(self, discussion_creator):
        """
        Create a discussion

        Args:
            A DSSDiscussionCreator object containing the discussion definition

        Returns:
            The newly created discussion
        """
        return self.client._perform_json("POST", "/projects/%s/discussions/%s/%s/" % (self.project_key, self.object_type, self.object_id), body=discussion_creator.get_data())

    def get_discussion(self, discussion_id):
        """
        Get a specific discussion

        Returns:
            a discussion
        """
        return DSSDiscussion(self.client, self.project_key, self.object_type, self.object_id, discussion_id)

class DSSDiscussion(object):
    """
    A handle to manage a single discussion
    """
    def __init__(self, client, project_key, object_type, object_id, discussion_id):
        self.client = client
        self.project_key = project_key
        self.object_type = object_type
        self.object_id = object_id
        self.discussion_id = discussion_id

    ########################
    # Single discussion
    ########################
    def get(self):
        """
        Get the discussion details

        Returns:
            The specific discussion
        """
        return self.client._perform_json("GET", "/projects/%s/discussions/%s/%s/%s" % (self.project_key, self.object_type, self.object_id, self.discussion_id))

    def set(self, discussion_details):
        """
        Update the discussion

        Args:
            The discussion definition as retrieved by the getter

        Returns:
            The updated discussion
        """
        return self.client._perform_json("PUT", "/projects/%s/discussions/%s/%s/%s" % (self.project_key, self.object_type, self.object_id, self.discussion_id), body=discussion_details)

    def add_reply(self, reply):
        """
        Add a reply to a discussion

        Args:
            The reply message content

        Returns:
            The updated discussion with details
        """
        reply_data = {
            "reply": reply
        }
        return self.client._perform_json("POST", "/projects/%s/discussions/%s/%s/%s/replies/" % (self.project_key, self.object_type, self.object_id, self.discussion_id), body=reply_data)

class DSSDiscussionCreator(object):
    """
    A helper to create discussion
    """
    def __init__(self, topic, first_message):
        self.data = {
            "topic" : topic,
            "reply" : first_message
        }

    def get_data(self):
        return self.data

    def set_topic(self, topic):
        self.data["topic"] = topic

    def set_first_message(self, first_message):
        self.data["reply"] = first_message
