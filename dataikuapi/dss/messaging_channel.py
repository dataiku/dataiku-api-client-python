import json


class DSSMessagingChannelListItem(object):
    """
    A generic messaging channel in DSS.

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_messaging_channels`

    """

    def __init__(self, client, data):
        self.client = client
        self._data = data
        if data is None:
            self._data = dict()
        else:
            self._data = data
        self._id = data.get("id", None)
        self._type = data.get("type", None)
        self._family = data.get("family", None)

    @property
    def id(self):
        """
        ID of the messaging channel

        :type: str
        """
        return self._id

    @property
    def type(self):
        """
        Type of the messaging channel

        :type: str
        """
        return self._type

    @property
    def family(self):
        """
        Family of the messaging channel where relevant - e.g. "mail"

        :type: str
        """
        return self._family

    def get_raw(self):
        """
        :return: Gets the raw representation of this :class:`DSSMessagingChannelListItem`, any edit is reflected in the object.

        :rtype: dict
        """
        return self._data

    def __repr__(self):
        return self.__class__.__name__ + "(" + self._data.__repr__() + ")"

    def get_as_messaging_channel(self):
        """
        :return: The same messaging channel but as the appropriate object type

        :rtype: DSSMessagingChannel
        """
        if self._family == 'mail':
            return DSSMailMessagingChannel(self, self._data)
        else:
            return DSSMessagingChannel(self, self._data)


class DSSMessagingChannel(object):
    """
    A handle to interact with a messaging channel on the DSS instance.
    A generic DSS messaging channel

    .. important::

        Do not instantiate this class directly, use :meth:`dataikuapi.DSSClient.get_messaging_channel`
    """

    def __init__(self, client, data=None):
        self.client = client
        if data is None:
            self._data = dict()
        else:
            self._data = data
        self._id = data.get("id", None)
        self._type = data.get("type", None)
        self._family = data.get("family", None)

    @property
    def id(self):
        """
        ID of the messaging channel

        :rtype: str
        """
        return self._id

    @property
    def type(self):
        """
        Type of the messaging channel

        :rtype: str
        """
        return self._type

    @property
    def family(self):
        """
        Family of the messaging channel where relevant - e.g. "mail"

        :type: str
        """
        return self._family


class DSSMailMessagingChannel(DSSMessagingChannel):
    """
    A handle to interact with an email messaging channel on the DSS instance - 
    a subclass of :class:`DSSMessagingChannel`

    .. important::

        Do not instantiate this class directly, use :meth:`dataikuapi.DSSClient.get_messaging_channel`
    """

    def __init__(self, client, data):
        super().__init__(client, data)
        self._sender = data.get("sender", None)

    @property
    def sender(self):
        """
        Sender for the messaging channel, if present

        :rtype: str
        """
        return self._sender

    def send(self, project_key, to, subject, body, attachments=None, plain_text=False, sender=None, cc=None, bcc=None):
        """
        Send an email with or without attachments to a list of recipients

        .. code-block:: python
        
            channel = client.get_messaging_channel("mail-channel-id")
            channel.send("PROJECT_KEY", ["john.doe@dataiku.com", "jane.doe@dataiku.com"], "Hello there!", "<html><body>Some HTML body</body></html>")

            channel = client.get_messaging_channel("other-mail-channel-id")
            for file in paths:
            with open(file) as f:
                # Optionally include file type ("text/csv")
                attachments.append(file, f.read(), "text/csv")
            channel.send("PROJECT_KEY", ["joe@dataiku.com"], "Subject", "Body in plain text",  attachments=attachments, False)

        :param project_key: project issuing the email. The user must have "Write content" permission on the specified project.
        :type project_key: str
        :param to: email addresses of recipients
        :type to: list[str]
        :param subject: email subject
        :type subject: str
        :param body: email body (in plain text or HTML format)
        :type body: str
        :param attachments: files to be attached to the mail, defaults to None
        :type attachments: list[BufferedReader]
        :param plain_text: True to send email as plain text, False to send it as HTML. Defaults to False.
        :type plain_text: bool
        :param sender: sender email address. Use None to use the sender defined at the channel level.
        :type sender: str
        :param cc: email addresses of recipients in carbon copy
        :type cc: list[str]
        :param bcc: email addresses of recipients in blind carbon copy
        :type bcc: list[str]
        """
        payload = {
            "from": sender,
            "to": to,
            "cc": cc,
            "bcc": bcc,
            "subject": subject,
            "body": body,
            "plainText": plain_text
        }
        files = [
            ('message', ('send-payload.json', json.dumps(payload), 'application/json')),
        ]
        if attachments:
            for attachment in attachments:
                files.append(('attachments', attachment))

        self.client._perform_http("POST", "/messaging-channels/%s/actions/send?projectKey=%s" % (self.id, project_key), stream=False, files=files)
