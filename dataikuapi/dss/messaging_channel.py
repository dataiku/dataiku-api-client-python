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
            return DSSMailMessagingChannel(self.client, self._data)
        else:
            return DSSMessagingChannel(self.client, self._data)


class DSSMessagingChannelSettings(object):
    """
    Settings class for a DSS messaging channel.

    .. important::

        Do not instantiate this class directly, use :meth:`DSSMessagingChannel.get_settings`.

    Use :meth:`save` to save your changes.
    """

    def __init__(self, channel, settings):
        self.channel = channel
        self.settings = settings

    def get_raw(self):
        """
        Get the messaging channel settings. Requires admin privileges.

        :returns: the settings (ie configuration), as a dict.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Save the changes to the settings on the messaging channel. Requires admin privileges.

        Usage example:

        .. code-block:: python

            channel = client.get_messaging_channel("my_channel_id")
            channel_settings = channel.get_settings()
            channel_settings.get_raw()["webhookUrl"] = "https://www.example.org/"
            channel_settings.save()

        """
        self.channel.client._perform_empty(
            "PUT",
            "/messaging-channels/%s/settings" % self.channel.id,
            body=self.settings,
        )


class DSSMessagingChannel(object):
    """
    A handle to interact with a messaging channel on the DSS instance.

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

    def get_settings(self):
        """
        Returns the settings of this messaging channel as a :class:`DSSMessagingChannelSettings`.

        You must use :meth:`~DSSMessagingChannelSettings.save()` on the returned object to make your changes effective
        on the messaging channel.

        .. code-block:: python

            # Example: change sender
            channel = client.get_messaging_channel("my_channel_id")
            channel_settings = channel.get_settings()
            channel_settings.get_raw()["sender"] = "someone@example.org"
            channel_settings.save()

        :returns: the settings of the messaging channel
        :rtype: :class:`DSSMessagingChannelSettings`
        """
        data = self.client._perform_json(
            "GET", "/messaging-channels/%s/settings" % self.id
        )
        return DSSMessagingChannelSettings(self, data)

    def delete(self):
        """
        Deletes this messaging channel. Requires admin privileges.

        .. code-block:: python

            channel = client.get_messaging_channel("my_channel_id")
            channel.delete()
        """
        self.client._perform_empty("DELETE", "/messaging-channels/%s" % self.id)


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
        self._use_current_user_as_sender = data.get("useCurrentUserAsSender", None)

    @property
    def sender(self):
        """
        Sender for the messaging channel, if present

        :rtype: str
        """
        return self._sender

    @property
    def use_current_user_as_sender(self):
        """
        Indicates whether the messaging channel will use the address of the current user as sender.
        If True and the current user has no associated email address, the sender property is used instead.

        :rtype: bool
        """
        return self._use_current_user_as_sender

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


class DSSMessagingChannelCreator(object):
    """
    Helper to create new messaging channels.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, channel_type, client):
        self.client = client
        self.type = channel_type
        self.id = None
        self.channel_configuration = {}

    def with_id(self, channel_id):
        """
        Add an ID to the messaging-channel-to-be-created.

        :param string channel_id: unique ID
        """
        self.id = channel_id
        return self

    def create(self):
        """
        Creates the new messaging channel, and return a handle to interact with it. Requires admin privileges.

        :rtype: :class:`DSSMessagingChannel`
        :return: The created messaging channel object, such as :class:`DSSMessagingChannel`, or a :class:`DSSMessagingChannel` for a mail channel
        """
        return self.client.create_messaging_channel(
            self.type, self.id, self.channel_configuration
        )


class MailMessagingChannelCreator(DSSMessagingChannelCreator):
    """
    Helper to create new mail messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, channel_type, client):
        super().__init__(channel_type, client)

    def with_current_user_as_sender(self, use_current_user_as_sender):
        """
        Add a "use current user as sender" option to the messaging-channel-to-be-created.

        :param bool use_current_user_as_sender: True to use the email of the user triggering the action as sender, False otherwise. Has precedence over 'sender' property.
        """
        self.channel_configuration["useCurrentUserAsSender"] = (
            use_current_user_as_sender
        )

    def with_sender(self, sender):
        """
        Add a sender to the messaging-channel-to-be-created.

        :param string sender: sender email, use an adhoc provided email if not provided.
        """
        self.channel_configuration["sender"] = sender

    def with_authorized_domains(self, authorized_domains):
        """
        Add authorized domains to the messaging-channel-to-be-created.

        :param list[str] authorized_domains: comma-separated list of authorized domains for "To" addresses.
        """
        self.channel_configuration["authorizedDomain"] = ",".join(authorized_domains)


class SMTPMessagingChannelCreator(MailMessagingChannelCreator):
    """
    Helper to create new SMTP messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("smtp", client)

    def with_host(self, host):
        """
        Add a host to the messaging-channel-to-be-created.

        :param string host: host to connect to.
        """
        self.channel_configuration["host"] = host

    def with_port(self, port):
        """
        Add a port to the messaging-channel-to-be-created.

        :param long port: port to connect to.
        """
        self.channel_configuration["port"] = port

    def with_ssl(self, use_ssl):
        """
        Add SSL option to the messaging-channel-to-be-created.

        :param bool use_ssl: True to use SSL, False otherwise.
        """
        self.channel_configuration["useSSL"] = use_ssl

    def with_tls(self, use_tls):
        """
        Add TLS option to the messaging-channel-to-be-created.

        :param bool use_tls: True to use TLS, False otherwise.
        """
        self.channel_configuration["useTLS"] = use_tls

    def with_session_properties(self, session_properties):
        """
        Add session properties to the messaging-channel-to-be-created.

        :param list[dict] session_properties: Array of dictionaries with "key" and "value" keys set for session extra properties.
        """
        self.channel_configuration["sessionProperties"] = session_properties

    def with_login(self, login):
        """
        Add a login to the messaging-channel-to-be-created.

        :param string login: user login.
        """
        self.channel_configuration["login"] = login

    def with_password(self, password):
        """
        Add a password to the messaging-channel-to-be-created.

        :param string password: user password.
        """
        self.channel_configuration["password"] = password


class AWSSESMailMessagingChannelCreator(MailMessagingChannelCreator):
    """
    Helper to create new AWS SES mail messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("aws-ses-mail", client)

    def with_access_key(self, access_key):
        """
        Add an access key to the messaging-channel-to-be-created.

        :param string access_key: AWS access key.
        """
        self.channel_configuration["accessKey"] = access_key

    def with_secret_key(self, secret_key):
        """
        Add a secret key to the messaging-channel-to-be-created.

        :param string secret_key: AWS secret key.
        """
        self.channel_configuration["secretKey"] = secret_key

    def with_region_or_endpoint(self, region_or_endpoint):
        """
        Add a region or an endpoint to the messaging-channel-to-be-created.

        :param string region_or_endpoint: AWS region or custom endpoint.
        """
        self.channel_configuration["regionOrEndpoint"] = region_or_endpoint


class MicrosoftGraphMailMessagingChannelCreator(MailMessagingChannelCreator):
    """
    Helper to create new Microsoft Graph mail messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("microsoft-graph-mail", client)

    def with_client_id(self, client_id):
        """
        Add a client ID to the messaging-channel-to-be-created.

        :param string client_id: Microsoft application ID.
        """
        self.channel_configuration["clientId"] = client_id

    def with_tenant_id(self, tenant_id):
        """
        Add a tenant ID to the messaging-channel-to-be-created.

        :param string tenant_id: Microsoft directory ID.
        """
        self.channel_configuration["tenantId"] = tenant_id

    def with_client_secret(self, client_secret):
        """
        Add a client secret to the messaging-channel-to-be-created.

        :param string client_secret: Account used to sent mails with this channel. Must be a User Principal Name with a valid Microsoft 365 license.
        """
        self.channel_configuration["clientSecret"] = client_secret


class ProxyableMessagingChannelCreator(DSSMessagingChannelCreator):
    """
    Helper to create new proxyable messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, channel_type, client):
        super().__init__(channel_type, client)

    def with_proxy(self, use_proxy):
        """
        Add a proxy to the messaging-channel-to-be-created.

        :param bool use_proxy: True to use DSS's proxy settings to connect, False otherwise.
        """
        self.channel_configuration["useProxy"] = use_proxy


class WebhookMessagingChannelCreator(ProxyableMessagingChannelCreator):
    """
    Helper to create new webhook-using messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, channel_type, client):
        super().__init__(channel_type, client)

    def with_webhook_url(self, webhook_url):
        """
        Add a webhook url to the messaging-channel-to-be-created.

        :param string webhook_url: webhook URL for "WEBHOOK" mode.
        """
        self.channel_configuration["webhookUrl"] = webhook_url


class SlackMessagingChannelCreator(WebhookMessagingChannelCreator):
    """
    Helper to create new Slack messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("slack", client)

    def with_mode(self, mode):
        """
        Add a mode to the messaging-channel-to-be-created.

        :param string mode: connection mode. Can be "WEBHOOK" or "API".
        """
        self.channel_configuration["mode"] = mode

    def with_authorization_token(self, authorization_token):
        """
        Add an authorization token to the messaging-channel-to-be-created.

        :param string authorization_token: authorization token for "API" mode.
        """
        self.channel_configuration["authorizationToken"] = authorization_token

    def with_channel(self, channel_id):
        """
        Add a Slack channel ID to the messaging-channel-to-be-created.

        :param string channel_id: Slack channel ID.
        """
        self.channel_configuration["channel"] = channel_id


class MSTeamsMessagingChannelCreator(WebhookMessagingChannelCreator):
    """
    Helper to create new Microsoft Teams messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("msft-teams", client)

    def with_webhook_type(self, webhook_type):
        """
        Add a webhook type to the messaging-channel-to-be-created.

        :param string webhook_type: type of webhook to use. Can be "WORKFLOWS" or "OFFICE365" (legacy).
        """
        self.channel_configuration["webhookType"] = webhook_type


class GoogleChatMessagingChannelCreator(WebhookMessagingChannelCreator):
    """
    Helper to create new Google Chat messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("google-chat", client)

    def with_webhook_key(self, webhook_key):
        """
        Add a webhook key to the messaging-channel-to-be-created.

        :param string webhook_key: key parameter for the webhook URL (mandatory if not included in the URL).
        """
        self.channel_configuration["webhookKey"] = webhook_key

    def with_webhook_token(self, webhook_token):
        """
        Add a webhook token to the messaging-channel-to-be-created.

        :param string webhook_token: token parameter for the webhook URL (mandatory if not included in the URL).
        """
        self.channel_configuration["webhookToken"] = webhook_token


class TwilioMessagingChannelCreator(ProxyableMessagingChannelCreator):
    """
    Helper to create new Twilio messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("twilio", client)

    def with_account_sid(self, account_sid):
        """
        Add an account SID to the messaging-channel-to-be-created.

        :param string account_sid: Twilio account SID.
        """
        self.channel_configuration["accountSid"] = account_sid

    def with_auth_token(self, auth_token):
        """
        Add an authorization token to the messaging-channel-to-be-created.

        :param string auth_token: authorization token.
        """
        self.channel_configuration["authToken"] = auth_token

    def with_from_number(self, from_number):
        """
        Add a "from number" option to the messaging-channel-to-be-created.

        :param long from_number: Twilio from number.
        """
        self.channel_configuration["fromNumber"] = from_number


class ShellMessagingChannelCreator(DSSMessagingChannelCreator):
    """
    Helper to create new shell messaging channels

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.new_messaging_channel()` instead.
    """

    def __init__(self, client):
        super().__init__("shell", client)

    def with_type(self, execution_type):
        """
        Add an execution type to the messaging-channel-to-be-created.

        :param string execution_type: Type of shell execution. Can be "COMMAND" or "FILE".
        """
        self.channel_configuration["type"] = execution_type

    def with_command(self, command):
        """
        Add a command to the messaging-channel-to-be-created.

        :param string command: command to execute. In "FILE" mode this string will be passed to the `-c` switch.
        """
        self.channel_configuration["command"] = command

    def with_script(self, script):
        """
        Add a script to the messaging-channel-to-be-created.

        :param string script: script content to execute for mode "FILE".
        """
        self.channel_configuration["script"] = script
