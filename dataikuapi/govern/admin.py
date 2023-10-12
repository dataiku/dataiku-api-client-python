from datetime import datetime
from dataikuapi.govern.future import GovernFuture

class GovernUser(object):
    """
    A handle for a user on the Govern instance.
    Do not create this object directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_user` instead.
    """

    def __init__(self, client, login):
        self.client = client
        self.login = login

    def delete(self):
        """
        Delete the user
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)

    def get_settings(self):
        """
        Get the settings of the user

        :rtype: :class:`GovernUserSettings`
        """
        raw = self.client._perform_json("GET", "/admin/users/%s" % self.login)
        return GovernUserSettings(self.client, self.login, raw)

    def get_activity(self):
        """
        Gets the activity of the user.

        :return: the user's activity
        :rtype: :class:`GovernUserActivity`
        """
        activity = self.client._perform_json("GET", "/admin/users/%s/activity" % self.login)
        return GovernUserActivity(self.client, self.login, activity)

    def get_client_as(self):
        """
        Get a :class:`~dataikuapi.govern_client.GovernClient` that has the permissions of this user.

        This allows administrators to impersonate actions on behalf of other users, in order to perform
        actions on their behalf
        """
        from dataikuapi.govern_client import GovernClient

        if self.client.api_key is not None:
            return GovernClient(self.client.host, self.client.api_key, extra_headers={"X-DKU-ProxyUser": self.login})
        elif self.client.internal_ticket is not None:
            return GovernClient(self.client.host, internal_ticket=self.client.internal_ticket,
                                extra_headers={"X-DKU-ProxyUser": self.login})
        else:
            raise ValueError("Don't know how to proxy this client")

    ########################################################
    # Supplier interaction
    ########################################################

    def start_resync_from_supplier(self):
        """
        Starts a resync of the user from an external supplier (LDAP, Azure AD or custom auth)
        :return: a :class:`dataikuapi.govern.future.GovernFuture` representing the sync process
        :rtype: :class:`dataikuapi.govern.future.GovernFuture`
        """
        future_resp = self.client._perform_json("POST", "/admin/users/%s/actions/resync" % self.login)
        return GovernFuture.from_resp(self.client, future_resp)


class GovernOwnUser(object):
    """
    A handle to interact with your own user
    Do not create this object directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_own_user` instead.
    """

    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Get your own settings

        :rtype: :class:`GovernOwnUserSettings`
        """
        raw = self.client._perform_json("GET", "/current-user")
        return GovernOwnUserSettings(self.client, raw)


class GovernUserSettingsBase(object):
    """
    Settings for a Govern user.
    Do not create this object directly, use :meth:`GovernUser.get_settings` or :meth:`GovernOwnUser.get_settings` instead.
    """

    def __init__(self, settings):
        self.settings = settings

    def get_raw(self):
        """
        :return: the raw settings of the user, as a dict. Modifications made to the returned object are reflected when saving
        :rtype: dict
        """
        return self.settings


class GovernUserSettings(GovernUserSettingsBase):
    """
    Settings for a Govern user.
    Do not create this object directly, use :meth:`GovernUser.get_settings` instead.
    """

    def __init__(self, client, login, settings):
        super(GovernUserSettings, self).__init__(settings)
        self.client = client
        self.login = login

    @property
    def enabled(self):
        """
        Whether this user is enabled

        :rtype: boolean
        """
        return self.settings["enabled"]

    @enabled.setter
    def enabled(self, new_value):
        self.settings["enabled"] = new_value

    @property
    def creation_date(self):
        """
        Get the creation date of the user as a :class:`datetime.datetime`

        :return: the creation date
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.settings["creationDate"] if "creationDate" in self.settings else None
        return datetime.fromtimestamp(timestamp / 1000) if timestamp else None

    def save(self):
        """Saves the settings"""
        self.client._perform_json("PUT", "/admin/users/%s" % self.login, body=self.settings)


class GovernOwnUserSettings(GovernUserSettingsBase):
    """
    Settings for the current Govern user.
    Do not create this object directly, use :meth:`GovernOwnUser.get_settings` instead.
    """

    def __init__(self, client, settings):
        super(GovernOwnUserSettings, self).__init__(settings)
        self.client = client

    def save(self):
        """Saves the settings back to the current user"""
        self.client._perform_empty("PUT", "/current-user", body=self.settings)


class GovernUserActivity(object):
    """
    Activity for a Govern user.

    .. important::

        Do not instantiate directly, use :meth:`GovernUser.get_activity` or :meth:`dataikuapi.GovernClient.list_users_activity()` instead.
    """
    def __init__(self, client, login, activity):
        self.client = client
        self.login = login
        self.activity = activity

    def get_raw(self):
        """
        Get the raw activity of the user as a dict.

        :return: the raw activity. Fields are

                    * **login** : the login of the user for this activity
                    * **lastSuccessfulLogin** : timestamp in milliseconds of the last time the user logged into Govern
                    * **lastFailedLogin** : timestamp in milliseconds of the last time Govern recorded a login failure for this user
                    * **lastSessionActivity** : timestamp in milliseconds of the last time the user opened a tab

        :rtype: dict
        """
        return self.activity

    @property
    def last_successful_login(self):
        """
        Get the last successful login of the user
        
        Returns None if there was no successful login for this user.

        :return: the last successful login
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSuccessfulLogin"]
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None

    @property
    def last_failed_login(self):
        """
        Get the last failed login of the user

        Returns None if there were no failed login for this user.

        :return: the last failed login
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastFailedLogin"]
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None

    @property
    def last_session_activity(self):
        """
        Get the last session activity of the user

        The last session activity is the last time the user opened a new Govern tab or 
        refreshed his session.

        Returns None if there is no session activity yet.

        :return: the last session activity
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSessionActivity"]
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None


class GovernAuthorizationMatrix(object):
    """
    The authorization matrix of all groups and enabled users of the Govern instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_authorization_matrix` instead.
    """
    def __init__(self, authorization_matrix):
        self.authorization_matrix = authorization_matrix

    @property
    def raw(self):
        """
        Get the raw authorization matrix as a dict

        :return: the authorization matrix. There are 2 parts in the matrix, each as a top-level field and with similar structures, **perUser** and **perGroup**.
        :rtype: dict
        """
        return self.authorization_matrix


class GovernGroup(object):
    """
    A group on the Govern instance.
    Do not create this object directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_group` instead.
    """

    def __init__(self, client, name):
        self.client = client
        self.name = name

    def delete(self):
        """
        Delete the group
        """
        return self.client._perform_empty(
            "DELETE", "/admin/groups/%s" % self.name)

    def get_definition(self):
        """
        Get the group's definition (name, description, admin abilities, type, ldap name mapping)

        :return: the group's definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)

    def set_definition(self, definition):
        """
        Set the group's definition.

        You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`,
        not create a new dict.
        :param: dict definition: the definition for the group, as a dict
        :return: a dict - the definition of the group
        :rtype: dict
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body=definition)


class GovernGlobalApiKey(object):
    """
    A global API key on the Govern instance
    """

    def __init__(self, client, key):
        self.client = client
        self.key = key

    ########################################################
    # Key deletion
    ########################################################

    def delete(self):
        """
        Delete the api key

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/globalAPIKeys/%s" % self.key)

    ########################################################
    # Key description
    ########################################################

    def get_definition(self):
        """
        Get the API key's definition

        Note: this call requires an API key with admin rights

        :return: a dict - the definition of the API key
        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/globalAPIKeys/%s" % (self.key))

    def set_definition(self, definition):
        """
        Set the API key's definition.

        Note: this call requires an API key with admin rights

        :param: dict definition: the definition for the API key, as a dict
        :return: a dict - the definition of the API key
        :rtype: dict
        """
        return self.client._perform_empty(
            "PUT", "/admin/globalAPIKeys/%s" % self.key,
            body=definition)


class GovernGeneralSettings(object):
    """
    The general settings of the Govern instance.
    Do not create this object directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_general_settings` instead.
    """

    def __init__(self, client):
        self.client = client
        self.settings = self.client._perform_json("GET", "/admin/general-settings")

    ########################################################
    # Update settings on instance
    ########################################################

    def save(self):
        """
        Save the changes that were made to the settings on the Govern instance
        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty("PUT", "/admin/general-settings", body=self.settings)

    ########################################################
    # Value accessors
    ########################################################

    def get_raw(self):
        """
        Get the settings as a dictionary
        """
        return self.settings
