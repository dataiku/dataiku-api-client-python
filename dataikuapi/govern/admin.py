class GovernUser(object):
    """
    A handle for a user on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_user` instead.
    """
    def __init__(self, client, login):
        self.client = client
        self.login = login

    def delete(self):
        """
        Deletes the user
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)

    def get_settings(self):
        """
        Gets the settings of the user

        :rtype: :class:`GovernUserSettings`
        """
        raw = self.client._perform_json("GET", "/admin/users/%s" % self.login)
        return GovernUserSettings(self.client, self.login, raw)


class GovernOwnUser(object):
    """
    A handle to interact with your own user
    Do not create this object directly, use :meth:`dataikuapi.GovernClient.get_own_user` instead.
    """
    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Get your own settings

        :rtype: :class:`DSSOwnUserSettings`
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

    @property
    def user_properties(self):
        """
        The user properties (editable by the user) for this user. Do not set this property, modify the dict in place

        :rtype dict
        """
        return self.settings["userProperties"]


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
    def admin_properties(self):
        """
        The user properties (not editable by the user) for this user. Do not set this property, modify the dict in place

        :rtype: dict
        """
        return self.settings["adminProperties"]

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

    def save(self):
        """Saves the settings"""
        self.client._perform_json("PUT", "/admin/users/%s" % self.login, body=self.settings)


class GovernOwnUserSettings(GovernUserSettingsBase):
    """
    Settings for the current Govern user.
    Do not create this object directly, use :meth:`dataikuapi.GovernClient.get_own_user` instead.
    """
    def __init__(self, client, settings):
        super(GovernOwnUserSettings, self).__init__(settings)
        self.client = client

    def save(self):
        """Saves the settings back to the current user"""
        self.client._perform_empty("PUT", "/current-user", body=self.settings)


class GovernGroup(object):
    """
    A group on the Govern instance.
    Do not create this object directly, use :meth:`dataikuapi.GovernClient.get_group` instead.
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def delete(self):
        """
        Deletes the group
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
        :returns: a dict - the definition of the group
        :rtype: dict
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body=definition)
