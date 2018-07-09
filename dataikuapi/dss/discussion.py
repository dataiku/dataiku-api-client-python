import json
import sys

if sys.version_info >= (3,0):
  import urllib.parse
  dku_quote_fn = urllib.parse.quote
else:
  import urllib
  dku_quote_fn = urllib.quote

class DSSObjectDiscussions(object):
    """
    A handle to manage discussions on a DSS object
    """
    def __init__(self, client, project_key, object_type, object_id):
        """Do not call directly, use :meth:`dataikuapi.dssclient.DSSClient.get_object_discussions` or on any commentable DSS object"""
        self.client = client
        self.project_key = project_key
        self.object_type = object_type
        self.object_id = object_id
        # encode in UTF-8 if its python2 and unicode
        if sys.version_info < (3,0) and isinstance(self.object_id, unicode):
            self.object_id = self.object_id.encode('utf-8')

    def list_discussions(self):
        """
        Get the list of discussions on the object

        :returns: list of discussions on the object
        :rtype: list of :class:`dataikuapi.dss.discussion.DSSDiscussion`
        """
        data = self.client._perform_json("GET", "/projects/%s/discussions/%s/%s/" % (self.project_key, self.object_type, self.object_id))
        return [DSSDiscussion(self.client, self.project_key, self.object_type, self.object_id, discu_data['id'], discu_data, False) for discu_data in data]

    def create_discussion(self, topic, message):
        """
        Create a new discussion

        :param str topic: the discussion topic
        :param str message: the markdown formatted first message
        :returns: the newly created discussion
        :rtype: :class:`dataikuapi.dss.discussion.DSSDiscussion`
        """
        creation_data = {
            "topic" : topic,
            "reply" : message
        }
        discu_data = self.client._perform_json("POST", "/projects/%s/discussions/%s/%s/" % (self.project_key, self.object_type, self.object_id), body=creation_data)
        return DSSDiscussion(self.client, self.project_key, self.object_type, self.object_id, discu_data['id'], discu_data, True)

    def get_discussion(self, discussion_id):
        """
        Get a specific discussion

        :param str discussion_id: the discussion ID
        :returns: the discussion
        :rtype: :class:`dataikuapi.dss.discussion.DSSDiscussion`
        """
        discu_data = self.client._perform_json("GET", "/projects/%s/discussions/%s/%s/%s" % (self.project_key, self.object_type, self.object_id, discussion_id))
        return DSSDiscussion(self.client, self.project_key, self.object_type, self.object_id, discussion_id, discu_data, True)

class DSSDiscussion(object):
    """Do not call directly, use :meth:`dataikuapi.dss.discussion.DSSObjectDiscussions.get_discussion`"""
    def __init__(self, client, project_key, object_type, object_id, discussion_id, discussion_data, discussion_data_has_replies):
        """
        :param DSSClient client: an api client to connect to the DSS backend
        :param str project_key: identifier of the project to access
        :param str object_type: DSS object type
        :param str object_id: DSS object ID
        :param str discussion_id: identified of the discussion
        :param dict discussion_data: the discussion data
        :param bool discussion_data_has_replies: a flag that indicates if the replies has been loaded
        """
        self.client = client
        self.project_key = project_key
        self.object_type = object_type
        self.object_id = object_id
        self.discussion_id = discussion_id
        self.discussion_data = discussion_data
        self.discussion_data_has_replies = discussion_data_has_replies

    def _get_with_replies(self):
        """
        Reload the discussion data from the backend including the replies
        """
        self.discussion_data = self.client._perform_json("GET", "/projects/%s/discussions/%s/%s/%s" % (self.project_key, self.object_type, self.object_id, self.discussion_id))
        self.discussion_data_has_replies = True

    def get_metadata(self):
        """
        Get the discussion metadata

        :returns: the discussion metadata
        :rtype: dict
        """
        metadata = dict(self.discussion_data)
        if "replies" in metadata:
            del metadata["replies"]
        return metadata

    def set_metadata(self, discussion_metadata):
        """
        Update the discussion metadata

        :param dict discussion_metadata: the discussion metadata
        """
        if not self.discussion_data_has_replies:
            self._get_with_replies()

        edited_metadata = dict(discussion_metadata)
        edited_metadata["replies"] = self.discussion_data["replies"]

        self.discussion_data = self.client._perform_json("PUT", "/projects/%s/discussions/%s/%s/%s" % (self.project_key, self.object_type, self.object_id, self.discussion_id), body=edited_metadata)
        self.discussion_data_has_replies = True

    def get_replies(self):
        """
        Get the list of replies in this discussion

        :returns: a list of replies
        :rtype: list of :class:`dataikuapi.dss.discussion.DSSDiscussionReply`
        """
        if not self.discussion_data_has_replies:
            self._get_with_replies()

        return [DSSDiscussionReply(reply_data) for reply_data in self.discussion_data["replies"]]

    def add_reply(self, text):
        """
        Add a reply to a discussion

        :param str text: the markdown formatted text to reply
        """
        reply_data = {
            "reply": text
        }
        self.discussion_data = self.client._perform_json("POST", "/projects/%s/discussions/%s/%s/%s/replies/" % (self.project_key, self.object_type, self.object_id, self.discussion_id), body=reply_data)
        self.discussion_data_has_replies = True

class DSSDiscussionReply(object):
    """
    A read-only handle to access a discussion reply
    """
    def __init__(self, reply_data):
        """Do not call directly, use :meth:`dataikuapi.dss.discussion.DSSDiscussion.get_replies`"""
        self.reply_data = reply_data

    def get_raw_data(self):
        """
        Get the reply raw data

        :returns: the reply data
        :rtype: dict
        """
        return self.reply_data

    def get_text(self):
        """
        Get the reply text

        :returns: the reply text
        :rtype: str
        """
        return self.reply_data["text"]

    def get_author(self):
        """
        Get the reply author

        :returns: the author ID
        :rtype: str
        """
        return self.reply_data["author"]

    def get_timestamp(self):
        """
        Get the reply timestamp

        :returns: the reply timestamp
        :rtype: long
        """
        return self.reply_data["time"]

    def get_edited_timestamp(self):
        """
        Get the last edition timestamp

        :returns: the last edition timestamp
        :rtype: long
        """
        return self.reply_data["editedOn"]
