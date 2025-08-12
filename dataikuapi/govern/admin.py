from .future import GovernFuture
import json, warnings
from datetime import datetime
from ..utils import _timestamp_ms_to_zoned_datetime

class GovernUser(object):
    """
    A handle for a user on the Dataiku Govern instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_user` instead.
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
        Get the settings of the user. You must be admin to call this method.

        You must use :meth:`~GovernUserSettings.save()` on the returned object to make your changes effective
        on the user.

        Usage example

        .. code-block:: python

            # disable some user
            user = client.get_user('the_user_login')
            settings = user.get_settings()
            settings.enabled = False
            settings.save()

        :return: the settings of the user
        :rtype: :class:`GovernUserSettings`
        """
        raw = self.client._perform_json("GET", "/admin/users/%s" % self.login)
        return GovernUserSettings(self.client, self.login, raw)

    def get_activity(self):
        """
        Gets the activity of the user. You must be admin to call this method.

        :return: the user's activity
        :rtype: :class:`GovernUserActivity`
        """
        activity = self.client._perform_json("GET", "/admin/users/%s/activity" % self.login)
        return GovernUserActivity(self.client, self.login, activity)

    def get_info(self):
        """
        Gets basic information about the user. You do not need to be admin to call this method

        :rtype: :class:`GovernUserInfo`
        """
        raw = self.client._perform_json("GET", "/users/%s" % self.login)
        return GovernUserInfo(raw)

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

    ########################################################
    # Legacy
    ########################################################

    def get_definition(self):
        """
        Get the definition of the user

        .. caution::

            Deprecated, use :meth:`get_settings` instead

        :return: the user's definition, as a dict. Notable fields are

                    * **login** : identifier of the user, can't be modified
                    * **enabled** : whether the user can log into Dataiku Govern
                    * **groups** : list of group names this user belongs to

        :rtype: dict
        """
        warnings.warn("GovernUser.get_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("GET", "/admin/users/%s" % self.login)

    def set_definition(self, definition):
        """
        Set the user's definition.

        .. caution::

            Deprecated, use :meth:`dataikuapi.govern.admin.GovernUserSettings.save()` instead

        .. important::

            You should only use :meth:`set_definition` with an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        .. note::

            This call requires an API key with admin rights

        The fields that may be changed in a user definition are:

                * email
                * displayName
                * enabled
                * groups
                * userProfile
                * password (not returned by :meth:`get_definition()` but can be set)
                * userProperties
                * adminProperties

        :param dict definition: the definition for the user, as a dict
        """
        warnings.warn("GovernUser.set_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = definition)

    def get_client_as(self):
        """
        Get an API client that has the permissions of this user.

        This allows administrators to impersonate actions on behalf of other users, in order to perform
        actions on their behalf.

        :return: a client through which calls will be run as the user
        :rtype: :class:`dataikuapi.GovernClient`
        """
        from dataikuapi.govern_client import GovernClient

        if self.client.api_key is not None:
            return GovernClient(self.client.host, self.client.api_key, extra_headers={"X-DKU-ProxyUser":  self.login}, no_check_certificate=not self.client._session.verify, client_certificate=self.client._session.cert)
        elif self.client.internal_ticket is not None:
            client_as = GovernClient(self.client.host, internal_ticket = self.client.internal_ticket,
                                         extra_headers={"X-DKU-ProxyUser":  self.login}, client_certificate=self.client._session.cert)
            client_as._session.verify = self.client._session.verify
            return client_as
        else:
            raise ValueError("Don't know how to proxy this client")


class GovernOwnUser(object):
    """
    A handle to interact with your own user
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_own_user` instead.
    """
    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Get your own settings

        You must use :meth:`~GovernOwnUserSettings.save()` on the returned object to make your changes effective
        on the user.

        :rtype: :class:`GovernOwnUserSettings`
        """
        raw = self.client._perform_json("GET", "/current-user")
        return GovernOwnUserSettings(self.client, raw)


class GovernUserSettingsBase(object):
    """
    Settings for a Dataiku Govern user.
    
    .. important::

        Do not instantiate directly, use :meth:`GovernUser.get_settings` or :meth:`GovernOwnUser.get_settings` instead.
    """
    def __init__(self, settings):
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of the user.

        Modifications made to the returned object are reflected when saving.

        :return: the dict of the settings (not a copy). Notable fields are:

                    * **login** : identifier of the user, can't be modified
                    * **enabled** : whether the user can log into Dataiku Govern
                    * **groups** : list of group names this user belongs to

        :rtype: dict
        """
        return self.settings

    @property
    def user_properties(self):
        """
        Get the user properties for this user. 

        .. important::

            Do not set this property, modify the dict in place

        User properties can be seen and modified by the user themselves. A contrario admin
        properties are for administrators' eyes only.

        :rtype: dict
        """
        return self.settings["userProperties"]


class GovernGlobalApiKey(object):
    """
    A global API key on the Dataiku Govern instance
    """
    def __init__(self, client, key, id_):
        self.client = client
        self.key = key
        self.id_ = id_

    ########################################################
    # Key deletion
    ########################################################

    def delete(self):
        """
        Delete the api key

        .. note::

            This call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/global-api-keys/%s" % self.id_)

    ########################################################
    # Key description
    ########################################################

    def get_definition(self):
        """
        Get the API key's definition

        .. note::

            This call requires an API key with admin rights

        .. note::

            If the secure API keys feature is enabled, the secret key of this
            API key will not be present in the returned dict

        :return: the API key definition, as a dict. The dict additionally contains the definition of the
                 permissions attached to the key.

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/global-api-keys/%s" % self.id_)

    def set_definition(self, definition):
        """
        Set the API key's definition

        .. note::

            This call requires an API key with admin rights

        .. important::

            You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
            not create a new dict. You may not use this method to update the 'key' field.

        Usage example

        .. code-block:: python

            # make an API key able to admin Dataiku Govern
            key = client.get_global_api_key('my_api_key_secret')
            definition = key.get_definition()
            definition["globalPermissions"]["admin"] = True
            key.set_definition(definition)

        :param dict definition: the definition for the API key
        """
        return self.client._perform_empty(
            "PUT", "/admin/global-api-keys/%s" % self.id_,
            body = definition)


class GovernUserSettings(GovernUserSettingsBase):
    """
    Settings for a Dataiku Govern user.

    .. important::

        Do not instantiate directly, use :meth:`GovernUser.get_settings` instead.
    """
    def __init__(self, client, login, settings):
        super(GovernUserSettings, self).__init__(settings)
        self.client = client
        self.login = login

    @property
    def admin_properties(self):
        """
        Get the admin properties for this user. 

        .. important::

            Do not set this property, modify the dict in place

        Admin properties can be seen and modified only by administrators, not by the user themselves.

        :rtype: dict
        """
        return self.settings["adminProperties"]

    @property
    def enabled(self):
        """
        Whether this user is enabled.
        
        :rtype: boolean
        """
        return self.settings["enabled"]

    @enabled.setter
    def enabled(self, new_value):
        self.settings["enabled"] = new_value

    @property
    def creation_date(self):
        """
        Get the timestamp of when the user was created

        :return: the creation date
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.settings["creationDate"] if "creationDate" in self.settings else None
        return _timestamp_ms_to_zoned_datetime(timestamp)

    def save(self):
        """
        Saves the settings
        """
        self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = self.settings)


class GovernOwnUserSettings(GovernUserSettingsBase):
    """
    Settings for the current Dataiku Govern user.
    
    .. important::

        Do not instantiate directly, use :meth:`GovernOwnUser.get_settings()` instead.
    """
    def __init__(self, client, settings):
        super(GovernOwnUserSettings, self).__init__(settings)
        self.client = client

    def save(self):
        """
        Saves the settings
        """
        self.client._perform_empty("PUT", "/current-user", body = self.settings)


class GovernUserActivity(object):
    """
    Activity for a Dataiku Govern user.

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
                    * **lastSuccessfulLogin** : timestamp in milliseconds of the last time the user logged into Dataiku Govern
                    * **lastFailedLogin** : timestamp in milliseconds of the last time Dataiku Govern recorded a login failure for this user
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
        return _timestamp_ms_to_zoned_datetime(timestamp)

    @property
    def last_failed_login(self):
        """
        Get the last failed login of the user

        Returns None if there were no failed login for this user.

        :return: the last failed login
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastFailedLogin"]
        return _timestamp_ms_to_zoned_datetime(timestamp)

    @property
    def last_session_activity(self):
        """
        Get the last session activity of the user

        The last session activity is the last time the user opened a new Dataiku Govern tab or 
        refreshed his session.

        Returns None if there is no session activity yet.

        :return: the last session activity
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSessionActivity"]
        return _timestamp_ms_to_zoned_datetime(timestamp)


class GovernUserInfo(object):
    """
    Basic information about a Dataiku Govern user
    
    .. important::

        Do not instantiate directly, use :meth:`GovernUser.get_info` or :meth:`GovernClient.list_users_info`
    """
    def __init__(self, raw):
        self._raw = raw

    def get_raw(self):
        """
        Get the raw info of the user.
        :rtype: dict
        """
        return self._raw

    @property
    def login(self):
        return self._raw["login"]
    @property
    def display_name(self):
        return self._raw["displayName"]
    @property
    def groups(self):
        """
        :rtype: list
        """
        return self._raw["groups"]
    @property
    def email(self):
        return self._raw["email"]
    @property
    def enabled(self):
        return self._raw["enabled"]


class GovernGroupInfo(object):
    """
    Basic information about a Dataiku Govern group
    
    .. important::

        Do not instantiate directly, use :meth:`GovernClient.list_groups_info`
    """
    def __init__(self, raw):
        self._raw = raw

    def get_raw(self):
        """
        Get the raw info of the group.
        :rtype: dict
        """
        return self._raw

    @property
    def name(self):
        return self._raw["name"]


class GovernAuthorizationMatrix(object):
    """
    The authorization matrix of all groups and enabled users of the Dataiku Govern instance.

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
    A group on the Dataiku Govern instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_group` instead.
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name
    
    ########################################################
    # Group deletion
    ########################################################
    
    def delete(self):
        """
        Deletes the group
        """
        return self.client._perform_empty(
            "DELETE", "/admin/groups/%s" % self.name)
    

    def get_definition(self):
        """
        Get the group's definition (name, description, admin abilities, type, ldap name mapping)
        
        :return: the group's definition. Top-level fields are:

                    * **name** : name of the group
                    * **sourceType** : type of group. Possible values: LOCAL, LDAP

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)
    
    def set_definition(self, definition):
        """
        Set the group's definition.

        .. important::

            You should only use :meth:`set_definition` with an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        :param dict definition: the definition for the group, as a dict
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body = definition)


class GovernGeneralSettings(object):
    """
    The general settings of the Dataiku Govern instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_general_settings` instead.
    """
    def __init__(self, client):
        self.client = client
        self.settings = self.client._perform_json("GET", "/admin/general-settings")
    
    ########################################################
    # Update settings on instance
    ########################################################
    
    def save(self):
        """
        Save the changes that were made to the settings on the Dataiku Govern instance

        .. note::

            This call requires an API key with admin rights
        """
        return self.client._perform_empty("PUT", "/admin/general-settings", body = self.settings)

    ########################################################
    # Value accessors
    ########################################################
    
    def get_raw(self):
        """
        Get the settings as a dictionary

        :return: the settings
        :rtype: dict
        """
        return self.settings


class GovernGlobalApiKeyListItem(dict):
    """
    An item in a list of global API keys.
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.list_global_api_keys` instead.
    """
    def __init__(self, client, data):
        super(GovernGlobalApiKeyListItem, self).__init__(data)
        self.client = client

    def to_global_api_key(self):
        """
        Gets a handle corresponding to this item

        :rtype: :class:`GovernGlobalApiKey`
        """
        return GovernGlobalApiKey(self.client, self["key"], self["id"])

    @property
    def id(self):
        """
        Get the identifier of the API key

        :rtype: string
        """
        return self["id"]
   
    @property
    def user_for_impersonation(self):
        """
        Get the user associated to the API key

        :rtype: string
        """
        return self.get("dssUserForImpersonation")
   
    @property
    def key(self):
        """
        Get the API key

        If the secure API keys feature is enabled, this key field will not be available

        :rtype: string
        """
        return self["key"]
   
    @property
    def label(self):
        """
        Get the label of the API key

        :rtype: string
        """
        return self["label"]
   
    @property
    def description(self):
        """
        Get the description of the API key

        :rtype: string
        """
        return self.get("description")
   
    @property
    def created_on(self):
        """
        Get the timestamp of when the API key was created

        :rtype: :class:`datetime.datetime`
        """
        timestamp = self["createdOn"]
        return _timestamp_ms_to_zoned_datetime(timestamp)
   
    @property
    def created_by(self):
        """
        Get the login of the user who created the API key

        :rtype: string
        """
        return self["createdBy"]


class GovernGlobalUsageSummary(object):
    """
    The summary of the usage of the Dataiku Govern instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.GovernClient.get_global_usage_summary` instead.
    """
    def __init__(self, data):
        self.data = data

    @property
    def raw(self):
        """
        Get the usage summary structure

        :rtype: dict
        """
        return self.data
