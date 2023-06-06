from .future import DSSFuture
import json, warnings
from datetime import datetime


class DSSConnectionListItem(dict):
    """
    An item in a list of connections. 
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.list_connections` instead.
    """
    def __init__(self, client, data):
        super(DSSConnectionListItem, self).__init__(data)
        self.client = client

    def to_connection(self):
        """
        Gets a handle corresponding to this item

        :rtype: :class:`DSSConnection`
        """
        return DSSConnection(self.client, self["name"])

    @property
    def name(self):
        """
        Get the identifier of the connection.

        :rtype: string
        """
        return self["id"]
   
    @property
    def type(self):
        """
        Get the type of the connection.

        :return: a DSS connection type, like PostgreSQL, EC2, Azure, ...
        :rtype: string
        """
        return self["label"]

class DSSConnectionInfo(dict):
    """
    A class holding read-only information about a connection.

    .. important::

        Do not instantiate directly, use :meth:`DSSConnection.get_info` instead.

    The main use case of this class is to retrieve the decrypted credentials for a connection,
    if allowed by the connection permissions.

    Depending on the connection kind, the credential may be available using :meth:`get_basic_credential` 
    or :meth:`get_aws_credential`.
    """
    def __init__(self, data):
        super(DSSConnectionInfo, self).__init__(data)

    def get_type(self):
        """
        Get the type of the connection

        :return: a connection type, for example Azure, Snowflake, GCS, ...
        :rtype: string
        """
        return self["type"]

    def get_params(self):
        """
        Get the parameters of the connection, as a dict

        :return: the parameters, as a dict. Each connection type has different sets of fields. 
        :rtype: dict
        """
        return self["params"]

    def get_basic_credential(self):
        """
        Get the basic credential (user/password pair) for this connection, if available

        :return: the credential, as a dict containing "user" and "password"
        :rtype: dict
        """
        if not "resolvedBasicCredential" in self:
            raise ValueError("No basic credential available")
        return self["resolvedBasicCredential"]

    def get_aws_credential(self):
        """
        Get the AWS credential for this connection, if available.

        The AWS credential can either be a keypair or a STS token triplet.

        :return: the credential, as a dict containing "accessKey", "secretKey", and "sessionToken" (only in the case of STS token)
        :rtype: dict
        """
        if not "resolvedAWSCredential" in self:
            raise ValueError("No AWS credential available")
        return self["resolvedAWSCredential"]


class DSSConnection(object):
    """
    A connection on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_connection` instead.
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name

    ########################################################
    # Location info
    ########################################################

    def get_location_info(self):
        """
        Get information about this connection.

        .. caution::

            Deprecated, use :meth:`~get_info()`
        """
        warnings.warn("DSSConnection.get_location_info is deprecated, please use get_info", DeprecationWarning)
        return self.get_info()

    def get_info(self, contextual_project_key=None):
        """
        Get information about this connection.

        .. note::

            This call requires permissions to read connection details

        :param string contextual_project_key: (optional) project key to use to resolve variables

        :return: an object containing connection information
        :rtype: :class:`DSSConnectionInfo`
        """
        additional_params = { "contextualProjectKey": contextual_project_key } if contextual_project_key is not None else None
        return DSSConnectionInfo(self.client._perform_json(
            "GET", "/connections/%s/info" % self.name, params=additional_params))
    
    ########################################################
    # Connection deletion
    ########################################################
    
    def delete(self):
        """
        Delete the connection
        """
        return self.client._perform_empty(
            "DELETE", "/admin/connections/%s" % self.name)

    def get_settings(self):
        """
        Get the settings of the connection.

        You must use :meth:`~DSSConnectionSettings.save()` on the returned object to make your changes effective
        on the connection.

        Usage example

        .. code-block:: python

            # make details of a connection accessible to some groups
            connection = client.get_connection("my_connection_name")
            settings = connection.settings()
            settings.set_readability(False, "group1", "group2")
            settings.save()

        :return: the settings of the connection
        :rtype: :class:`DSSConnectionSettings`
        """
        settings = self.client._perform_json(
            "GET", "/admin/connections/%s" % self.name)
        return DSSConnectionSettings(self, settings)

    def get_definition(self):
        """
        Get the connection's raw definition.

        .. caution::

            Deprecated, use :meth:`get_settings()` instead.

        The exact structure of the returned dict is not documented and depends on the connection
        type. Create connections using the DSS UI and call :meth:`get_definition` to see the 
        fields that are in it.

        .. note:: 

            This method returns a dict with passwords and secrets in their encrypted form. If you need
            credentials, consider using :meth:`get_info()` and :meth:`dataikuapi.dss.admin.DSSConnectionInfo.get_basic_credential()`.

        :return: a connection definition, as a dict. See :meth:`DSSConnectionSettings.get_raw()`
        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/connections/%s" % self.name)
    
    def set_definition(self, definition):
        """
        Set the connection's definition.
        
        .. caution::

            Deprecated, use :meth:`get_settings()` then :meth:`DSSConnectionSettings.save()` instead.

        .. important::

            You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        Usage example

        .. code-block:: python

            # make details of a connection accessible to some groups
            connection = client.get_connection("my_connection_name")
            definition = connection.get_definition()
            definition['detailsReadability']['readableBy'] = 'ALLOWED'
            definition['detailsReadability']['allowedGroups'] = ['group1', 'group2']
            connection.set_definition(definition)

        :param dict definition: the definition for the connection, as a dict.
        """
        return self.client._perform_json(
            "PUT", "/admin/connections/%s" % self.name,
            body = definition)
    
    ########################################################
    # Security
    ########################################################
    
    def sync_root_acls(self):
        """
        Resync root permissions on this connection path. 

        This is only useful for HDFS connections when DSS has User Isolation activated with "DSS-managed HDFS ACL"

        :return: a handle to the task of resynchronizing the permissions
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)
    
    def sync_datasets_acls(self):
        """
        Resync permissions on datasets in this connection path. 

        This is only useful for HDFS connections when DSS has User Isolation activated with "DSS-managed HDFS ACL"
        
        :return: a handle to the task of resynchronizing the permissions
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

class DSSConnectionSettings(object):
    """
    Settings of a DSS connection.

    .. important::

        Do not instantiate directly, use :meth:`DSSConnection.get_settings` instead.

    Use :meth:`save` to save your changes
    """

    def __init__(self, connection, settings):
        self.connection = connection
        self.settings = settings
        
    def get_raw(self):
        """
        Get the raw settings of the connection.

        :return: a connection definition, as a dict. Notable fields are:

                    * **type** : type of the connection (for example PostgreSQL, Azure, ...)
                    * **params** : dict of the parameters specific to the connection type
                    * **allowWrite** : if False, DSS will not perform write operations on the connection
                    * **allowManagedDatasets** : whether DSS will allow creating managed datasets on the connection
                    * **allowManagedFolders** : whether DSS will allow creating managed folders on the connection
                    * **credentialsMode** : whether the credentials of the connection are per-user ("PER_USER") or global for all users ("GLOBAL")
                    * **usableBy** : defines which DSS users can use the connection. Possible values: ALL, ALLOWED
                    * **allowedGroups** : if **usableBy** is "ALLOWED", a list of group names
                    * **detailsReadability** : definition of which DSS users can access the details of the connection, in particular the credentials in it

                        * **readableBy** : defines which users can access the details. Possible values: NONE, ALL, ALLOWED.
                        * **allowedGroups** : if **readableBy** is "ALLOWED", a list of group names

                    * **indexingSettings** : for SQL-like connection, what to index
                    * **maxActivities** : maximum number of concurrent activities in all jobs of the instance that use the connection
                    * **useGlobalProxy** : if a proxy is defined in the DSS general settings, whether to use it or not

        :rtype: dict
        """
        return self.settings

    @property
    def type(self):
        """
        Get the type of the connection.

        :return: a DSS connection type, like PostgreSQL, EC2, Azure, ...
        :rtype: string
        """
        return self.settings['type']

    @property
    def allow_managed_datasets(self):
        """
        Whether managed datasets can use the connection.

        :rtype: boolean
        """
        return self.settings['allowManagedDatasets']

    @allow_managed_datasets.setter
    def allow_managed_datasets(self, new_value):
        self.settings["allowManagedDatasets"] = new_value

    @property
    def allow_managed_folders(self):
        """
        Whether managed datasets can use the connection.

        :rtype: boolean
        """
        return self.settings['allowManagedFolders']

    @allow_managed_folders.setter
    def allow_managed_folders(self, new_value):
        self.settings["allowManagedFolders"] = new_value

    @property
    def allow_write(self):
        """
        Whether data can be written to this connection.

        If not, the connection is read-only from DSS point of view.

        :rtype: boolean
        """
        return self.settings['allowWrite']

    @allow_write.setter
    def allow_write(self, new_value):
        self.settings["allowWrite"] = new_value

    
    @property
    def details_readability(self):
        """
        Get the access control to connection details.

        :return: an handle on the access control definition.
        :rtype: :class:`DSSConnectionDetailsReadability`
        """
        return DSSConnectionDetailsReadability(self.settings["detailsReadability"])

    @property
    def usable_by(self):
        """
        Get the mode of access control.

        This controls usage of the connection, that is, reading and/or writing data
        from/to the connection.

        :return: one ALL (anybody) or ALLOWED (ie. only users from groups in :meth:`usable_by_allowed_groups()`)
        :rtype: string
        """
        return self.settings["usableBy"]

    @property
    def usable_by_allowed_groups(self):
        """
        Get the groups allowed to use the connection

        Only applies if :meth:`usable_by()` is ALLOWED.

        :return: a list of group names
        :rtype: list[string]
        """
        return self.settings["allowedGroups"]

    def set_usability(self, all, *groups):
        """
        Set who can use the connection.

        :param boolean all: if True, anybody can use the connection
        :param *string groups: a list of groups that can use the connection
        """
        if all:
            self.settings["usableBy"] = 'ALL' 
        else:
            self.settings["usableBy"] = 'ALLOWED' 
            self.settings["allowedGroups"] = groups

    def save(self):
        """
        Save the changes to the connection's settings
        """
        self.connection.client._perform_json(
            "PUT", "/admin/connections/%s" % self.connection.name,
            body = self.settings)

class DSSConnectionDetailsReadability(object):
    """
    Handle on settings for access to connection details.

    Connection details mostly cover credentials, and giving access to the
    credentials is necessary to some workloads. Typically, having Spark processes
    access data directly implies giving credentials to these Spark processes, 
    which in turn implies that the user can access the connection's details.
    """
    def __init__(self, data):
        self._data = data

    @property
    def readable_by(self):
        """
        Get the mode of access control.

        :return: one of NONE (nobody), ALL (anybody) or ALLOWED (ie. only users from groups in :meth:`allowed_groups()`)
        :rtype: string
        """
        return self._data["readableBy"]

    @property
    def allowed_groups(self):
        """
        Get the groups allowed to access connection details.

        Only applies if :meth:`readable_by()` is ALLOWED.

        :return: a list of group names
        :rtype: list[string]
        """
        return self._data["allowedGroups"]

    def set_readability(self, all, *groups):
        """
        Set who can get details from the connection.

        To make the details readable by nobody, pass all=False and no group.

        :param boolean all: if True, anybody can use the connection
        :param *string groups: a list of groups that can use the connection
        """
        if all:
            self._data["readableBy"] = 'ALL' 
        elif groups is None or len(groups) == 0:
            self._data["readableBy"] = 'NONE' 
        else:
            self._data["readableBy"] = 'ALLOWED' 
            self._data["allowedGroups"] = groups


class DSSUser(object):
    """
    A handle for a user on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_user` instead.
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
        Get the settings of the user.

        You must use :meth:`~DSSUserSettings.save()` on the returned object to make your changes effective
        on the user.

        Usage example

        .. code-block:: python

            # disable some user
            user = client.get_user('the_user_login')
            settings = user.get_settings()
            settings.enabled = False
            settings.save()

        :return: the settings of the user
        :rtype: :class:`DSSUserSettings`
        """
        raw = self.client._perform_json("GET", "/admin/users/%s" % self.login)
        return DSSUserSettings(self.client, self.login, raw)

    def get_activity(self):
        """
        Gets the activity of the user.

        :return: the user's activity
        :rtype: :class:`DSSUserActivity`
        """
        activity = self.client._perform_json("GET", "/admin/users/%s/activity" % self.login)
        return DSSUserActivity(self.client, self.login, activity)

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
                    * **enabled** : whether the user can log into DSS
                    * **email** : email of the user
                    * **displayName** : name of the user in the UI
                    * **groups** : list of group names this user belongs to
                    * **sourceType** : how the user logs in. Possible values: LOCAL, LOCAL_NO_AUTH, LDAP, SAAS, PAM
                    * **userProfile** : name of the license profile the user belongs to 
                    * **credentials** : dict of connection name or plugin preset name to credentials
                    * **secrets** : list of secrets, as name/value pairs
                    * **adminProperties** and **userProperties** : dicts of arbitrary properties
                    * **activeWebSocketSesssions** : number of tabs currently open by the user (informative only, not modifiable)

        :rtype: dict
        """
        warnings.warn("DSSUser.get_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("GET", "/admin/users/%s" % self.login)

    def set_definition(self, definition):
        """
        Set the user's definition.

        .. caution::

            Deprecated, use :meth:`dataikuapi.dss.admin.DSSUserSettings.save()` instead

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
                * secrets
                * credentials

        :param dict definition: the definition for the user, as a dict
        """
        warnings.warn("DSSUser.set_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = definition)

    def get_client_as(self):
        """
        Get an API client that has the permissions of this user.

        This allows administrators to impersonate actions on behalf of other users, in order to perform
        actions on their behalf.

        :return: a client through which calls will be run as the user
        :rtype: :class:`dataikuapi.DSSClient`
        """
        from dataikuapi.dssclient import DSSClient

        if self.client.api_key is not None:
            return DSSClient(self.client.host, self.client.api_key, extra_headers={"X-DKU-ProxyUser":  self.login})
        elif self.client.internal_ticket is not None:
            return DSSClient(self.client.host, internal_ticket = self.client.internal_ticket,
                                         extra_headers={"X-DKU-ProxyUser":  self.login})
        else:
            raise ValueError("Don't know how to proxy this client")


class DSSOwnUser(object):
    """
    A handle to interact with your own user
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_own_user` instead.
    """
    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Get your own settings

        You must use :meth:`~DSSOwnUserSettings.save()` on the returned object to make your changes effective
        on the user.

        :rtype: :class:`DSSOwnUserSettings`
        """
        raw = self.client._perform_json("GET", "/current-user")
        return DSSOwnUserSettings(self.client, raw)


class DSSUserSettingsBase(object):
    """
    Settings for a DSS user.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSUser.get_settings` or :meth:`DSSOwnUser.get_settings` instead.
    """
    def __init__(self, settings):
        self.settings = settings

    def get_raw(self):
        """
        Get the the raw settings of the user

        Modifications made to the returned object are reflected when saving.

        :return: the dict of the settings (not a copy). Notable fields are:

                    * **login** : identifier of the user, can't be modified
                    * **enabled** : whether the user can log into DSS
                    * **email** : email of the user
                    * **displayName** : name of the user in the UI
                    * **groups** : list of group names this user belongs to
                    * **sourceType** : how the user logs in. One of: LOCAL, LOCAL_NO_AUTH, LDAP, SAAS, PAM
                    * **userProfile** : name of the license profile the user belongs to 
                    * **credentials** : dict of connection name or plugin preset name to credentials
                    * **secrets** : list of secrets, as name/value pairs
                    * **adminProperties** and **userProperties** : dicts of arbitrary properties
                    * **activeWebSocketSesssions** : number of tabs currently open by the user (informative only, not modifiable)

        :rtype: dict
        """
        return self.settings

    def add_secret(self, name, value):
        """
        Add a user secret.

        If there was already a secret with the same name, it is replaced

        :param string name: name of the secret
        :param string value: name of the value
        """
        self.remove_secret(name)
        return self.settings["secrets"].append({"name": name, "value": value, "secret": True})

    def remove_secret(self, name):
        """
        Remove a user secret based on its name

        If no secret of the given name exists, the method does nothing.

        :param string name: name of the secret        
        """
        self.settings["secrets"] = [x for x in self.settings["secrets"] if x["name"] != name]

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

    def set_basic_connection_credential(self, connection, login, password):
        """
        Set per-user-credentials for a connection that takes a user/password pair.

        :param string connection: name of the connection
        :param string login: login of the credentials
        :param string password: password of the credentials
        """
        self.settings["credentials"][connection] = {
            "type": "BASIC",
            "user": login,
            "password": password
        }

    def remove_connection_credential(self,connection):
        """
        Remove per-user-credentials for a connection

        If no credentials for the givent connection exists, this method does nothing

        :param string connection: name of the connection
        """
        if connection in self.settings["credentials"]:
            del self.settings["credentials"][connection]

    def set_basic_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name, login, password):
        """
        Set per-user-credentials for a plugin preset that takes a user/password pair

        :param string plugin_id: identifier of the plugin
        :param string param_set_id: identifier of the parameter set to which the preset belongs
        :param string preset_id: identifier of the preset
        :param string param_name: name of the credentials parameter in the preset
        :param string login: login of the credentials
        :param string password: password of the credentials
        """
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        self.settings["credentials"][name] = {
            "type": "BASIC",
            "user": login,
            "password": password
        }

    def set_oauth2_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name, refresh_token):
        """
        Set per-user-credentials for a plugin preset that takes a OAuth refresh token

        :param string plugin_id: identifier of the plugin
        :param string param_set_id: identifier of the parameter set to which the preset belongs
        :param string preset_id: identifier of the preset
        :param string param_name: name of the credentials parameter in the preset
        :param string refresh_token: value of the refresh token
        """
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        self.settings["credentials"][name] = {
            "type": "OAUTH_REFRESH_TOKEN",
            "refreshToken": refresh_token
        }

    def remove_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name):
        """
        Remove per-user-credentials for a plugin preset

        :param string plugin_id: identifier of the plugin
        :param string param_set_id: identifier of the parameter set to which the preset belongs
        :param string preset_id: identifier of the preset
        :param string param_name: name of the credentials parameter in the preset
        """
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        if name in self.settings["credentials"]:
            del self.settings["credentials"][name]


class DSSUserSettings(DSSUserSettingsBase):
    """
    Settings for a DSS user.

    .. important::

        Do not instantiate directly, use :meth:`DSSUser.get_settings` instead.
    """
    def __init__(self, client, login, settings):
        super(DSSUserSettings, self).__init__(settings)
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
        return datetime.fromtimestamp(timestamp / 1000) if timestamp else None

    def save(self):
        """
        Saves the settings
        """
        self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = self.settings)


class DSSOwnUserSettings(DSSUserSettingsBase):
    """
    Settings for the current DSS user.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSOwnUser.get_settings()` instead.
    """
    def __init__(self, client, settings):
        super(DSSOwnUserSettings, self).__init__(settings)
        self.client = client

    def save(self):
        """
        Saves the settings
        """
        self.client._perform_empty("PUT", "/current-user", body = self.settings)


class DSSUserActivity(object):
    """
    Activity for a DSS user.

    .. important::

        Do not instantiate directly, use :meth:`DSSUser.get_activity` or :meth:`dataikuapi.DSSClient.list_users_activity()` instead.
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
                    * **lastSuccessfulLogin** : timestamp in milliseconds of the last time the user logged into DSS
                    * **lastFailedLogin** : timestamp in milliseconds of the last time DSS recorded a login failure for this user
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

        The last session activity is the last time the user opened a new DSS tab or 
        refreshed his session.

        Returns None if there is no session activity yet.

        :return: the last session activity
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSessionActivity"]
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None


class DSSAuthorizationMatrix(object):
    """
    The authorization matrix of all groups and enabled users of the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_authorization_matrix` instead.
    """
    def __init__(self, authorization_matrix):
        self.authorization_matrix = authorization_matrix

    @property
    def raw(self):
        """
        Get the raw authorization matrix as a dict

        :return: the authorization matrix. There are 2 parts in the matrix, each as a top-level field and with similar structures,
                 the **perUser** and **perGroup**:

                    * **users** (resp. **groups**) : list of user (resp. group) names
                    * **mayXXXX** (with different permissions as "XXXX") : list of booleans of the same length as **users** (resp. **groups**) indicating where the corresponding user has the permission
                    * **projectsGrants** : list of project permissions, each as a dict of:

                        * **projectKey** and **projectName** : identifiers of the project
                        * **grants** : list of dict of the same length as **users** (resp. **groups**) indicating which grants the corresponding user has on the project

        :rtype: dict
        """
        return self.authorization_matrix


class DSSGroup(object):
    """
    A group on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_group` instead.
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
                    * **description** : description of the group
                    * **canObtainAPITicketFromCookiesForGroupsRegex** : users in the group can impersonate users from groups whose name match this regex
                    * **admin** : whether users in the group have administrative rights in DSS
                    * **mayXXXX** : whether users in the group has the "XXXX" permission

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


class DSSGeneralSettings(object):
    """
    The general settings of the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_general_settings` instead.
    """
    def __init__(self, client):
        self.client = client
        self.settings = self.client._perform_json("GET", "/admin/general-settings")
    
    ########################################################
    # Update settings on instance
    ########################################################
    
    def save(self):
        """
        Save the changes that were made to the settings on the DSS instance

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

    def add_impersonation_rule(self, rule, is_user_rule=True):
        """
        Add a rule to the impersonation settings

        :param object rule: an impersonation rule, either a :class:`dataikuapi.dss.admin.DSSUserImpersonationRule`
                            or a :class:`dataikuapi.dss.admin.DSSGroupImpersonationRule`, or a plain dict
        :param boolean is_user_rule: when the rule parameter is a dict, whether the rule is for users or groups
        """
        rule_raw = rule
        if isinstance(rule, DSSUserImpersonationRule):
            rule_raw = rule.raw
            is_user_rule = True
        elif isinstance(rule, DSSGroupImpersonationRule):
            rule_raw = rule.raw
            is_user_rule = False
        impersonation = self.settings['impersonation']
        if is_user_rule:
            impersonation['userRules'].append(rule_raw)
        else:
            impersonation['groupRules'].append(rule_raw)

    def get_impersonation_rules(self, dss_user=None, dss_group=None, unix_user=None, hadoop_user=None, project_key=None, scope=None, rule_type=None, is_user=None, rule_from=None):
        """
        Retrieve the user or group impersonation rules that match the parameters

        :param string dss_user: a DSS user name
        :param string dss_group: a DSS group name
        :param string rule_from: a regex (which will be applied to user or group names)
        :param string unix_user: a name to match the target UNIX user
        :param string hadoop_user: a name to match the target Hadoop user
        :param string project_key: a project key
        :param string scope: project-scoped ('PROJECT') or global ('GLOBAL')
        :param string type: the rule user or group matching method ('IDENTITY', 'SINGLE_MAPPING', 'REGEXP_RULE')
        :param boolean is_user: True if only user-level rules should be considered, False for only group-level rules, None to consider both
        """
        user_matches = self.settings['impersonation']['userRules'] if is_user == None or is_user == True else []
        if dss_user is not None:
            user_matches = [m for m in user_matches if dss_user == m.get('dssUser', None)]
        if rule_from is not None:
            user_matches = [m for m in user_matches if rule_from == m.get('ruleFrom', None)]
        if unix_user is not None:
            user_matches = [m for m in user_matches if unix_user == m.get('targetUnix', None)]
        if hadoop_user is not None:
            user_matches = [m for m in user_matches if hadoop_user == m.get('targetHadoop', None)]
        if project_key is not None:
            user_matches = [m for m in user_matches if project_key == m.get('projectKey', None)]
        if rule_type is not None:
            user_matches = [m for m in user_matches if rule_type == m.get('type', None)]
        if scope is not None:
            user_matches = [m for m in user_matches if scope == m.get('scope', None)]
        group_matches = self.settings['impersonation']['groupRules'] if is_user == None or is_user == False else []
        if dss_group is not None:
            group_matches = [m for m in group_matches if dss_group == m.get('dssGroup', None)]
        if rule_from is not None:
            group_matches = [m for m in group_matches if rule_from == m.get('ruleFrom', None)]
        if unix_user is not None:
            group_matches = [m for m in group_matches if unix_user == m.get('targetUnix', None)]
        if hadoop_user is not None:
            group_matches = [m for m in group_matches if hadoop_user == m.get('targetHadoop', None)]
        if rule_type is not None:
            group_matches = [m for m in group_matches if rule_type == m.get('type', None)]

        all_matches = []
        for m in user_matches:
            all_matches.append(DSSUserImpersonationRule(m))
        for m in group_matches:
            all_matches.append(DSSGroupImpersonationRule(m))
        return all_matches

    def remove_impersonation_rules(self, dss_user=None, dss_group=None, unix_user=None, hadoop_user=None, project_key=None, scope=None, rule_type=None, is_user=None, rule_from=None):
        """
        Remove the user or group impersonation rules that matches the parameters from the settings

        :param string dss_user: a DSS user name
        :param string dss_group: a DSS group name
        :param string rule_from: a regex (which will be applied to user or group names)
        :param string unix_user: a name to match the target UNIX user
        :param string hadoop_user: a name to match the target Hadoop user
        :param string project_key: a project key
        :param string scope: project-scoped ('PROJECT') or global ('GLOBAL')
        :param string type: the rule user or group matching method ('IDENTITY', 'SINGLE_MAPPING', 'REGEXP_RULE')
        :param boolean is_user: True if only user-level rules should be considered, False for only group-level rules, None to consider both
        """
        for m in self.get_impersonation_rules(dss_user, dss_group, unix_user, hadoop_user, project_key, scope, rule_type, is_user, rule_from):
            if isinstance(m, DSSUserImpersonationRule):
                self.settings['impersonation']['userRules'].remove(m.raw)
            elif isinstance(m, DSSGroupImpersonationRule):
                self.settings['impersonation']['groupRules'].remove(m.raw)

    ########################################################
    # Admin actions
    ########################################################

    def push_container_exec_base_images(self):
        """
        Push the container exec base images to their repository
        """
        resp = self.client._perform_json("POST", "/admin/container-exec/actions/push-base-images")
        if resp is None:
            raise Exception('Container exec base image push returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Container exec base image push failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp


class DSSUserImpersonationRule(object):
    """
    An user-level rule items for the impersonation settings
    """
    def __init__(self, raw=None):
        self.raw = raw if raw is not None else {'scope':'GLOBAL','type':'IDENTITY'}

    def scope_global(self):
        """
        Make the rule apply to all projects
        """
        self.raw['scope'] = 'GLOBAL'
        return self

    def scope_project(self, project_key):
        """
        Make the rule apply to a given project

        :param string project_key: the project this rule applies to
        """
        self.raw['scope'] = 'PROJECT'
        self.raw['projectKey'] = project_key
        return self

    def user_identity(self):
        """
        Make the rule map each DSS user to a UNIX user of the same name
        """
        self.raw['type'] = 'IDENTITY'
        return self

    def user_single(self, dss_user, unix_user, hadoop_user=None):
        """
        Make the rule map a given DSS user to a given UNIX user

        :param string dss_user: a DSS user
        :param string unix_user: a UNIX user
        :param string hadoop_user: a hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'SINGLE_MAPPING'
        self.raw['dssUser'] = dss_user
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self

    def user_regexp(self, regexp, unix_user, hadoop_user=None):
        """
        Make the rule map a DSS users matching a given regular expression to a given UNIX user

        :param string regexp: a regular expression to match DSS user names
        :param string unix_user: a UNIX user
        :param string hadoop_user: a hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'REGEXP_RULE'
        self.raw['ruleFrom'] = regexp
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self


class DSSGroupImpersonationRule(object):
    """
    A group-level rule items for the impersonation settings
    """
    def __init__(self, raw=None):
        self.raw = raw if raw is not None else {'type':'IDENTITY'}

    def group_identity(self):
        """
        Make the rule map each DSS user to a UNIX user of the same name
        """
        self.raw['type'] = 'IDENTITY'
        return self

    def group_single(self, dss_group, unix_user, hadoop_user=None):
        """
        Make the rule map a given DSS user to a given UNIX user

        :param string dss_group: a DSS group
        :param string unix_user: a UNIX user
        :param string hadoop_user: a hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'SINGLE_MAPPING'
        self.raw['dssGroup'] = dss_group
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self

    def group_regexp(self, regexp, unix_user, hadoop_user=None):
        """
        Make the rule map a DSS users matching a given regular expression to a given UNIX user

        :param string regexp: a regular expression to match DSS groups
        :param string unix_user: a UNIX user
        :param string hadoop_user: a hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'REGEXP_RULE'
        self.raw['ruleFrom'] = regexp
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self


class DSSCodeEnv(object):
    """
    A code env on the DSS instance.
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_code_env` instead.
    """
    def __init__(self, client, env_lang, env_name):
        self.client = client
        self.env_lang = env_lang
        self.env_name = env_name
    
    ########################################################
    # Env deletion
    ########################################################
    
    def delete(self):
        """
        Delete the code env
        
        .. note::

            This call requires an API key with admin rights
        """
        resp = self.client._perform_json(
            "DELETE", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name))
        if resp is None:
            raise Exception('Env deletion returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env deletion failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

        
    ########################################################
    # Code env description
    ########################################################
    
    def get_definition(self):
        """
        Get the code env's definition

        .. caution::
  
            Deprecated, use :meth:`get_settings` instead
  
        .. note::

            This call requires an API key with admin rights
        
        :return: the code env definition
        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name))

    def set_definition(self, env):
        """
        Set the code env's definition. The definition should come from a call to :meth:`get_definition`

        .. caution::
  
            Deprecated, use :meth:`get_settings` then :meth:`DSSDesignCodeEnvSettings.save()` or
            :meth:`DSSAutomationCodeEnvSettings.save()` instead

        Fields that can be updated in design node:

        * env.permissions, env.usableByAll, env.desc.owner
        * env.specCondaEnvironment, env.specPackageList, env.externalCondaEnvName, env.desc.installCorePackages,
          env.desc.corePackagesSet, env.desc.installJupyterSupport, env.desc.yarnPythonBin, env.desc.yarnRBin
          env.desc.envSettings, env.desc.allContainerConfs, env.desc.containerConfs, 
          env.desc.allSparkKubernetesConfs, env.desc.sparkKubernetesConfs

        Fields that can be updated in automation node (where {version} is the updated version):

        * env.permissions, env.usableByAll, env.owner, env.envSettings
        * env.{version}.specCondaEnvironment, env.{version}.specPackageList, env.{version}.externalCondaEnvName, 
          env.{version}.desc.installCorePackages, env.{version}.corePackagesSet, env.{version}.desc.installJupyterSupport
          env.{version}.desc.yarnPythonBin, env.{version}.desc.yarnRBin, env.{version}.desc.allContainerConfs, 
          env.{version}.desc.containerConfs, env.{version}.desc.allSparkKubernetesConfs, 
          env.{version}.{version}.desc.sparkKubernetesConfs

        .. note::

            This call requires an API key with admin rights
        
        .. important::

            You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        :param dict data: a code env definition

        :return: the updated code env definition
        :rtype: dict
        """
        return self.client._perform_json(
            "PUT", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name), body=env)

    def get_version_for_project(self, project_key):
        """
        Resolve the code env version for a given project

        .. note::

            Version will only be non-empty for versioned code envs actually used by the project

        :param string project_key: project to get the version for

        :return: the code env version full reference for the version of the code env that the project use. Fields are

                    * **lang** : language of the code env (PYTHON or R)
                    * **name** : name of the code env
                    * **version** : identifier of the version
                    * **projectKey** : project key
                    * **bundleId** : identifier of the active bundle in the project

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/%s/version" % (self.env_lang, self.env_name, project_key))


    def get_settings(self):
        """
        Get the settings of this code env.

        .. important::

            You must use :meth:`DSSCodeEnvSettings.save()` on the returned object to make your changes effective
            on the code env.

        .. code-block:: python

            # Example: setting the required packagd
            codeenv = client.get_code_env("PYTHON", "code_env_name")
            settings = codeenv.get_settings()
            settings.set_required_packages("dash==2.0.0", "bokeh<2.0")
            settings.save()
            # then proceed to update_packages()

        :rtype: :class:`DSSDesignCodeEnvSettings` or :class:`DSSAutomationCodeEnvSettings`
        """
        data = self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name))

        # you can't just use deploymentMode to check if it's an automation code
        # env, because some modes are common to both types of nodes. So we rely 
        # on a non-null field that only the automation code envs have
        if data.get("versions", None) is not None:
            return DSSAutomationCodeEnvSettings(self, data)
        else:
            return DSSDesignCodeEnvSettings(self, data)

   
    ########################################################
    # Code env actions
    ########################################################

    def set_jupyter_support(self, active):
        """
        Update the code env jupyter support
        
        .. note::

            This call requires an API key with admin rights
        
        :param boolean active: True to activate jupyter support, False to deactivate
        """
        resp = self.client._perform_json(
            "POST", "/admin/code-envs/%s/%s/jupyter" % (self.env_lang, self.env_name),
            params = {'active':active})
        if resp is None:
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env update failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def update_packages(self, force_rebuild_env=False):
        """
        Update the code env packages so that it matches its spec
        
        .. note::

            This call requires an API key with admin rights

        :param boolean force_rebuild_env: whether to rebuild the code env from scratch

        :return: list of messages collected during the operation. Fields are:

                    * **anyMessage** : whether there is at least 1 message
                    * **success**, **warning**, **error** and **fatal** : whether there is at least one message of the corresponding category
                    * **messages** : list of messages. Each message is a dict, with at least **severity** and **message** sufields.

        :rtype: dict
        """
        resp = self.client._perform_json(
            "POST", "/admin/code-envs/%s/%s/packages" % (self.env_lang, self.env_name),
            params={"forceRebuildEnv": force_rebuild_env})
        if resp is None:
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env update failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def update_images(self, env_version=None):
        """
        Rebuild the docker image of the code env
        
        .. note::

            This call requires an API key with admin rights

        :param string env_version: (optional) version of the code env. Applies only to versioned code envs.

        :return: list of messages collected during the operation. Fields are:

                    * **anyMessage** : whether there is at least 1 message
                    * **success**, **warning**, **error** and **fatal** : whether there is at least one message of the corresponding category
                    * **messages** : list of messages. Each message is a dict, with at least **severity** and **message** sufields.

        :rtype: dict
        """
        resp = self.client._perform_json(
            "POST", "/admin/code-envs/%s/%s/images" % (self.env_lang, self.env_name),
            params={"envVersion": env_version})
        if resp is None:
            raise Exception('Env image build returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env image build failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def list_usages(self):
        """
        List usages of the code env in the instance

        :return: a list of objects where the code env is used. Each usage has fields:

                    * **envLang** and **envName** : identifiers of the code env
                    * **envUsage** : type of usage. Possible values: PROJECT, RECIPE, NOTEBOOK, PLUGIN, SCENARIO, SCENARIO_STEP, SCENARIO_TRIGGER, DATASET_METRIC, DATASET_CHECK, DATASET, WEBAPP, REPORT, API_SERVICE_ENDPOINT, SAVED_MODEL, MODEL, CODE_STUDIO_TEMPLATE
                    * **projectKey** and **objectId** : identifier of the object where the code env is used
                    * **accessible** : if False, the **projectKey** and **objectId** are obfuscated and point to an object of a project that the user can't access

        :rtype: list[dict]
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/usages" % (self.env_lang, self.env_name))

    def list_logs(self):
        """
        List logs of the code env in the instance

        :return: a list of log descriptions. Each log description has fields:

                    * **name** : name of the log file
                    * **totalSize** : size in bytes of the log
                    * **lastModified** : timestamp in milliseconds of the last change to the log
                    * **tail** : structure holding the tail of the log file

        :rtype: list[dict]
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/logs" % (self.env_lang, self.env_name))

    def get_log(self, log_name):
        """
        Get the logs of the code env
        
        :param string log_name: name of the log to fetch
            
        :return: the raw log
        :rtype: string
        """
        return self.client._perform_text(
            "GET", "/admin/code-envs/%s/%s/logs/%s" % (self.env_lang, self.env_name, log_name))


class DSSCodeEnvSettings(object):
    """
    Base settings class for a DSS code env.

    .. important::

        Do not instantiate directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """

    def __init__(self, codeenv, settings):
        self.codeenv = codeenv
        self.settings = settings

    @property
    def env_lang(self):
        """
        Get the language of the code env

        :return: a language (possible values: PYTHON, R)
        :rtype: string
        """
        return self.codeenv.env_lang

    @property
    def env_name(self):
        """
        Get the name of the code env

        :rtype: string
        """
        return self.codeenv.env_name

    def save(self):
        """
        Save the changes to the code env's settings
        """
        self.codeenv.client._perform_json(
            "PUT", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name), body=self.settings)


class DSSCodeEnvPackageListBearer(object):
    def get_required_packages(self, as_list=False):
        """
        Get the list of required packages, as a single string

        :param boolean as_list: if True, return the spec as a list of lines; if False, return as a single multiline string

        :return: a list of packages specifications
        :rtype: list[string] or string
        """
        x = self.settings.get("specPackageList", "")
        return x.split('\n') if as_list else x

    def set_required_packages(self, *packages):
        """
        Set the list of required packages

        :param list[string] packages: a list of packages specifications
        """
        self.settings["specPackageList"] = '\n'.join(packages)

    def get_required_conda_spec(self, as_list=False):
        """
        Get the list of required conda packages, as a single string

        :param boolean as_list: if True, return the spec as a list of lines; if False, return as a single multiline string

        :return: a list of packages specifications
        :rtype: list[string] or string
        """
        x = self.settings.get("specCondaEnvironment", "")
        return x.split('\n') if as_list else x

    def set_required_conda_spec(self, *spec):
        """
        Set the list of required conda packages

        :param list[string] spec: a list of packages specifications
        """
        self.settings["specCondaEnvironment"] = '\n'.join(packages)

class DSSCodeEnvContainerConfsBearer(object):
    def get_built_for_all_container_confs(self):
        """
        Whether the code env creates an image for each container config

        :rtype: boolean
        """
        return self.settings.get("allContainerConfs", False)

    def get_built_container_confs(self):
        """
        Get the list of container configs for which the code env builds an image (if not all)

        :return: a list of container configuration names
        :rtype: list[string]
        """
        return self.settings.get("containerConfs", [])

    def set_built_container_confs(self, *configs, **kwargs):
        """
        Set the list of container configs for which the code env builds an image

        :param boolean all: if True, an image is built for each config
        :param list[string] configs: list of configuration names to build images for
        """
        all = kwargs.get("all", False)
        self.settings['allContainerConfs'] = all
        if not all:
            self.settings['containerConfs'] = configs

    def built_for_all_spark_kubernetes_confs(self):
        """
        Whether the code env creates an image for each managed Spark over Kubernetes config
        """
        return self.settings.get("allSparkKubernetesConfs", False)
    
    def get_built_spark_kubernetes_confs(self):
        """
        Get the list of managed Spark over Kubernetes configs for which the code env builds an image (if not all)

        :return: a list of spark configuration names
        :rtype: list[string]
        """
        return self.settings.get("sparkKubernetesConfs", [])
    
    def set_built_spark_kubernetes_confs(self, *configs, **kwargs):
        """
        Set the list of managed Spark over Kubernetes configs for which the code env builds an image

        :param boolean all: if True, an image is built for each config
        :param list[string] configs: list of configuration names to build images for
        """
        all = kwargs.get("all", False)
        self.settings['allSparkKubernetesConfs'] = all
        if not all:
            self.settings['sparkKubernetesConfs'] = configs


class DSSDesignCodeEnvSettings(DSSCodeEnvSettings, DSSCodeEnvPackageListBearer, DSSCodeEnvContainerConfsBearer):
    """
    Base settings class for a DSS code env on a design node.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """
    def __init__(self, codeenv, settings):
        super(DSSDesignCodeEnvSettings, self).__init__(codeenv, settings)

    def get_raw(self):
        """
        Get the raw code env settings

        The structure depends on the type of code env. Notable fields are:

          * **envLang** and **envName** : identifiers of the code env
          * **desc** : definition of the code env, persisted on disk

              * **deploymentMode** : type of code env. Possible values: DSS_INTERNAL, DESIGN_MANAGED, DESIGN_NON_MANAGED, PLUGIN_MANAGED, PLUGIN_NON_MANAGED, EXTERNAL_CONDA_NAMED
              * **conda** : if True, the code env is created using Conda. If False, using virtualenv (for Python) or by linking to the system R (for R)
              * **externalCondaEnvName** : for EXTERNAL_CONDA_NAMED code envs, the name of the associated conda env
              * **envSettings** : settings for the building of the code env

                  * **inheritGlobalSettings** : if True, values come from the instance general settings
                  * **condaInstallExtraOptions** : extra command line options to pass to `conda install`
                  * **condaCreateExtraOptions** : extra command line options to pass to `conda create`
                  * **pipInstallExtraOptions** : extra command line options to pass to `pip install`
                  * **virtualenvCreateExtraOptions** : extra command line options to pass to `virtualenv`
                  * **cranMirrorURL** : URL of CRAN mirror to use to pull package

              * **allContainerConfs** : if True, build container images for all container configs on code env updates. If False, build images only for configs in **containerConfs**
              * **containerConfs** : list of container config names
              * **allSparkKubernetesConfs** :  if True, build container images for all spark configs on code env updates. If False, build images only for configs in **sparkKubernetesConfs**
              * **sparkKubernetesConfs** : list of spark config names
              * **rebuildDependentCodeStudioTemplates** : which code studio templates to rebuild on code env updates. Possible values are ASK (open modal to ask for user input), ALL, NONE
              * **owner** : login of the owner of the code env
              * **usableByAll** : if True, all users can use the code env. If false, **permissions** apply
              * **permissions** : list of permissions items. Each item has a group name and booleans for each permission

              * **yarnPythonBin** or **yarnRBin** : path to Python (resp. R) on the cluster nodes, for use in Spark jobs running on Yarn
              * **pythonInterpreter** : type of Python used. Possible values: PYTHON27, PYTHON34, PYTHON35, PYTHON36, PYTHON37, PYTHON38, PYTHON39, PYTHON310, PYTHON311, CUSTOM
              * **customInterpreter** : if **pythonInterpreter** is "CUSTOM", the path to the Python binary
              * **corePackagesSet** : which set of core packages to instal in the code env. Possible values: LEGACY_PANDAS023, PANDAS10, PANDAS11, PANDAS12, PANDAS13
              * **installJupyterSupport** : if True, the packages necessary for using the code env in notebooks are installed
              * **dockerImageResources** : behavior w.r.t. code env resources. Possible values: INIT (run initialization script), COPY (copy resources), NONE

          * several fields from **desc** are also copied to the top-level, notably **deploymentMode** and the fields around permission handling.
          * **canUpdateCodeEnv** and **canManageUsersCodeEnv** : (read-only) indicate whether the current user can update the code env or manage its permissions
          * **resourcesInitScript** : for Python code env, the contents resource script
          * **info** : (read-only) for Python code env, a dict with a **pythonVersion** field
          * **specPackageList** and **specCondaEnvironment** : list of packages requested by the user, as strings
          * **actualPackageList** and **actualCondaEnvironment** : (read-only) actual packages in the code env, as strings
          * **mandatoryPackageList** and **mandatoryCondaEnvironment** : (read-only) base packages added automatically by DSS on update, as strings

        :return: code env settings
        :rtype: dict
        """
        return self.settings

class DSSAutomationCodeEnvSettings(DSSCodeEnvSettings, DSSCodeEnvContainerConfsBearer):
    """
    Base settings class for a DSS code env on an automation node.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """
    def __init__(self, codeenv, settings):
        super(DSSAutomationCodeEnvSettings, self).__init__(codeenv, settings)

    def get_raw(self):
        """
        Get the raw code env settings

        The structure depends on the type of code env. Notable fields are:

          * **envLang** and **envName** : identifiers of the code env
          * **deploymentMode** : type of code env. Possible values: DSS_INTERNAL, PLUGIN_MANAGED, PLUGIN_NON_MANAGED, AUTOMATION_VERSIONED, AUTOMATION_SINGLE, AUTOMATION_NON_MANAGED_PATH, EXTERNAL_CONDA_NAMED
          * **allContainerConfs** : if True, build container images for all container configs on code env updates. If False, build images only for configs in **containerConfs**
          * **containerConfs** : list of container config names
          * **allSparkKubernetesConfs** :  if True, build container images for all spark configs on code env updates. If False, build images only for configs in **sparkKubernetesConfs**
          * **sparkKubernetesConfs** : list of spark config names
          * **rebuildDependentCodeStudioTemplates** : which code studio templates to rebuild on code env updates. Possible values are ASK (open modal to ask for user input), ALL, NONE
          * **owner** : login of the owner of the code env
          * **usableByAll** : if True, all users can use the code env. If false, **permissions** apply
          * **permissions** : list of permissions items. Each item has a group name and booleans for each permission
          * **envSettings** : settings for the building of the code env

              * **overrideImportedEnvSettings** : if False, values come from the instance general settings
              * **condaInstallExtraOptions** : extra command line options to pass to `conda install`
              * **condaCreateExtraOptions** : extra command line options to pass to `conda create`
              * **pipInstallExtraOptions** : extra command line options to pass to `pip install`
              * **virtualenvCreateExtraOptions** : extra command line options to pass to `virtualenv`
              * **cranMirrorURL** : URL of CRAN mirror to use to pull package

          * **canUpdateCodeEnv** and **canManageUsersCodeEnv** : (read-only) indicate whether the current user can update the code env or manage its permissions
          * **currentVersion** : when **deploymentMode** is "AUTOMATION_SINGLE", the single version. Use :meth:`get_version()` to access
          * **versions** : when **deploymentMode** is "AUTOMATION_VERSIONED", a list of code env versions. Use :meth:`get_version()` to access
          * **noVersion** : when **deploymentMode** is neither "AUTOMATION_SINGLE" nor "AUTOMATION_VERSIONED", the spec of the code env. Use :meth:`get_version()` to access

        :return: code env settings
        :rtype: dict
        """
        return self.settings

    def get_version(self, version_id=None):
        """
        Get a specific code env version (for versioned envs) or the single version

        :param string version_id: for versioned code env, identifier of the desired version 

        :return: the settings of a code env version
        :rtype: :class:`DSSAutomationCodeEnvVersionSettings`
        """
        deployment_mode = self.settings.get("deploymentMode", None)
        if deployment_mode in ['AUTOMATION_SINGLE']:
            return DSSAutomationCodeEnvVersionSettings(self.codeenv, self.settings.get('currentVersion', {}))
        elif deployment_mode in ['AUTOMATION_VERSIONED']:
            versions = self.settings.get("versions", [])
            version_ids = [v.get('versionId') for v in versions]
            if version_id is None:
                raise Exception("A version id is required in a versioned code env. Existing ids: %s" % ', '.join(version_ids))
            for version in versions:
                if version_id == version.get("versionId"):
                    return DSSAutomationCodeEnvVersionSettings(self.codeenv, version)
            raise Exception("Version %s not found in : %s" % (version_id, ', '.join(version_ids)))
        elif deployment_mode in ['PLUGIN_NON_MANAGED', 'PLUGIN_MANAGED', 'AUTOMATION_NON_MANAGED_PATH', 'EXTERNAL_CONDA_NAMED']:
            return DSSAutomationCodeEnvVersionSettings(self.codeenv, self.settings.get('noVersion', {}))
        else:
            raise Exception("Unexpected deployment mode %s for an automation node code env. Alter the settings directly with get_raw()", deployment_mode)

class DSSAutomationCodeEnvVersionSettings(DSSCodeEnvPackageListBearer):
    """
    Base settings class for a DSS code env version on an automation node.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSAutomationCodeEnvSettings.get_version` instead.

    Use :meth:`save` on the :class:`DSSAutomationCodeEnvSettings` to save your changes
    """
    def __init__(self, codeenv_settings, version_settings):
        self.codeenv_settings = codeenv_settings
        self.settings = version_settings

    def get_raw(self):
        """
        Get the raw code env version settings

        The structure depends on the type of code env. Notable fields are:

          * **versionId** : identifier of the code env version
          * **path** : (read-only) location of the version on disk
          * **desc** : definition of the code env, persisted on disk

              * **versionId** : type of code env. Possible values: DSS_INTERNAL, DESIGN_MANAGED, DESIGN_NON_MANAGED, PLUGIN_MANAGED, PLUGIN_NON_MANAGED, EXTERNAL_CONDA_NAMED
              * **conda** : if True, the code env is created using Conda. If False, using virtualenv (for Python) or by linking to the system R (for R)
              * **externalCondaEnvName** : for EXTERNAL_CONDA_NAMED code envs, the name of the associated conda env
              * **yarnPythonBin** or **yarnRBin** : path to Python (resp. R) on the cluster nodes, for use in Spark jobs running on Yarn
              * **pythonInterpreter** : type of Python used. Possible values: PYTHON27, PYTHON34, PYTHON35, PYTHON36, PYTHON37, PYTHON38, PYTHON39, PYTHON310, PYTHON311, CUSTOM
              * **customInterpreter** : if **pythonInterpreter** is "CUSTOM", the path to the Python binary
              * **corePackagesSet** : which set of core packages to instal in the code env. Possible values: LEGACY_PANDAS023, PANDAS10, PANDAS11, PANDAS12, PANDAS13
              * **installJupyterSupport** : if True, the packages necessary for using the code env in notebooks are installed
              * **dockerImageResources** : behavior w.r.t. code env resources. Possible values: INIT (run initialization script), COPY (copy resources), NONE

          * **resourcesInitScript** : for Python code env, the contents resource script
          * **info** : (read-only) for Python code env, a dict with a **pythonVersion** field
          * **specPackageList** and **specCondaEnvironment** : list of packages requested by the user, as strings
          * **actualPackageList** and **actualCondaEnvironment** : (read-only) actual packages in the code env, as strings
          * **mandatoryPackageList** and **mandatoryCondaEnvironment** : (read-only) base packages added automatically by DSS on update, as strings

        :return: code env settings
        :rtype: dict
        """
        return self.settings

class DSSGlobalApiKey(object):
    """
    A global API key on the DSS instance
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

        .. note::

            This call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/globalAPIKeys/%s" % self.key)

    ########################################################
    # Key description
    ########################################################

    def get_definition(self):
        """
        Get the API key's definition

        .. note::

            This call requires an API key with admin rights

        :return: the API key definition. Top-level fields are:

                    * **id** : identifier of the key
                    * **key** : value of the key
                    * **label** : label of the key
                    * **description** : longer description of the key
                    * **createdOn** : timestamp of creation, in milliseconds   
                    * **createdBy** : login of user who created the key   
                    * **dssUserForImpersonation** : login of user that the key impersonates
                    * **adminProperties** : dict of properties set by administrators
                    * **userProperties** : dict of properties set by users with access to the key
                    * **globalPermissions** : dict of instance-wide permissions (each field is a boolean for a permission)
                    * **execSQLLike** : whether the key can run SQL queries
                    * **projectFolders** : dict of project folder identifier to dict of permissions on that project folder
                    * **projects** : dict of project key to dict of permissions on that project
                    * **codeEnvs** : dict of code env name to dict of permissions on that code env
                    * **clusters** : dict of cluster name to dict of permissions on that cluster
                    * **codeStudioTemplates** : dict of code studio template identifier to dict of permissions on that code studio template
                    * **plugins** : dict of plugin identifier to dict of permissions on that plugin
                    * **pluginPresets** : dict of preset identifier to dict of permissions on that preset
                    * **pluginParameterSets** : dict of parameter set name to dict of permissions on that parameter set
                    * **unscopedDatasets** : list of dict giving permissions to specific datasets

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/globalAPIKeys/%s" % (self.key))

    def set_definition(self, definition):
        """
        Set the API key's definition.

        .. note::

            This call requires an API key with admin rights

        .. important::

            You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        Usage example

        .. code-block:: python

            # make an API key able to create projects
            key = client.get_global_api_key('my_api_key_secret')
            definition = key.get_definition()
            definition["globalPermissions"]["mayCreateProjects"] = True
            key.set_definition(definition)

        :param dict definition: the definition for the API key
        """
        return self.client._perform_empty(
            "PUT", "/admin/globalAPIKeys/%s" % self.key,
            body = definition)


class DSSGlobalApiKeyListItem(dict):
    """
    An item in a list of personal API key. 
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.list_global_api_keys` instead.
    """
    def __init__(self, client, data):
        super(DSSGlobalApiKeyListItem, self).__init__(data)
        self.client = client

    def to_global_api_key(self):
        """
        Gets a handle corresponding to this item

        :rtype: :class:`DSSGlobalApiKey`
        """
        return DSSGlobalApiKey(self.client, self["key"])

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
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None
   
    @property
    def created_by(self):
        """
        Get the login of the user who created the API key

        :rtype: string
        """
        return self["createdBy"]

class DSSPersonalApiKey(object):
    """
    A personal API key on the DSS instance.
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_personal_api_key` instead.
    """
    def __init__(self, client, id_):
        self.client = client
        self.id_ = id_

    ########################################################
    # Key description
    ########################################################

    def get_definition(self):
        """
        Get the API key's definition
        
        :return: the personal API key definition. Top level fields are:

                    * **id** : identifier of the key
                    * **key** : value of the key
                    * **user** : login of the user that this key acts on behalf of 
                    * **label** : label of the key
                    * **description** : longer description of the key
                    * **createdOn** : timestamp of creation, in milliseconds   
                    * **createdBy** : login of the user who create the key 

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/personal-api-keys/%s" % (self.id_))

    ########################################################
    # Key deletion
    ########################################################

    def delete(self):
        """
        Delete the API key
        """
        return self.client._perform_empty(
            "DELETE", "/personal-api-keys/%s" % self.id_)


class DSSPersonalApiKeyListItem(dict):
    """
    An item in a list of personal API key. 
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.list_personal_api_keys` or :meth:`dataikuapi.DSSClient.list_all_personal_api_keys` instead.
    """
    def __init__(self, client, data):
        super(DSSPersonalApiKeyListItem, self).__init__(data)
        self.client = client

    def to_personal_api_key(self):
        """
        Gets a handle corresponding to this item

        :rtype: :class:`DSSPersonalApiKey`
        """
        return DSSPersonalApiKey(self.client, self["id"])

    @property
    def id(self):
        """
        Get the identifier of the API key

        :rtype: string
        """
        return self["id"]
   
    @property
    def user(self):
        """
        Get the user associated to the API key

        :rtype: string
        """
        return self["user"]
   
    @property
    def key(self):
        """
        Get the API key

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
        return self["description"]
   
    @property
    def created_on(self):
        """
        Get the timestamp of when the API key was created

        :rtype: :class:`datetime.datetime`
        """
        timestamp = self["createdOn"]
        return datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None
   
    @property
    def created_by(self):
        """
        Get the login of the user who created the API key

        :rtype: string
        """
        return self["createdBy"]


class DSSCluster(object):
    """
    A handle to interact with a cluster on the DSS instance.
    
    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_cluster` instead.
    """
    def __init__(self, client, cluster_id):
        self.client = client
        self.cluster_id = cluster_id
    
    ########################################################
    # Cluster deletion
    ########################################################
    
    def delete(self):
        """
        Deletes the cluster.

        .. important::

            This does not previously stop it.
        """
        self.client._perform_empty(
            "DELETE", "/admin/clusters/%s" % (self.cluster_id))

        
    ########################################################
    # Cluster description
    ########################################################
    
    def get_settings(self):
        """
        Get the cluster's settings. This includes opaque data for the cluster if this is 
        a started managed cluster.

        The returned object can be used to save settings.

        :return: a :class:`DSSClusterSettings` object to interact with cluster settings
        :rtype: :class:`DSSClusterSettings`
        """
        settings = self.client._perform_json(
            "GET", "/admin/clusters/%s" % (self.cluster_id))
        return DSSClusterSettings(self.client, self.cluster_id, settings)

    def get_definition(self):
        """
        Get the cluster's definition. This includes opaque data for the cluster if this is 
        a started managed cluster.

        .. caution::

            Deprecated, use :meth:`get_settings()`

        :return: the definition of the cluster. Fields are:

                    * **id** : unique identifier of the cluster
                    * **name** : name of the cluster, in the UI
                    * **architecture** : kind of cluster (either HADOOP or KUBERNETES)
                    * **origin** : agent who created the cluster (either MANUAL or SCENARIO)
                    * **type** : type of cluster. Can be "manual" or a plugin cluster element type
                    * **params** : for clusters from plugin components, the settings shown in the cluster's form.
                    * **state** : (read-only) current state of the cluster. Possible values are NONE, STARTING, RUNNING, STOPPING
                    * **data** : when in **state** "RUNNING", a dict of data for use by the cluster's plugin component. Contents depend on each cluster type.
                    * **owner**, **usableByAll** and **permissions** : definition of permissions on cluster
                    * **canUpdateCluster** : (read-only) whether the user can update the cluster's settings or state
                    * **canManageUsersCluster** : (read-only) whether the user can manage the cluster's permissions
                    * **XXXXSettings** : dict of settings (resp. override mask) for XXXX in Hadoop, Hive, Impala, Spark and Container. These settings apply on top of the corresponding settings in the instance's general settings

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/admin/clusters/%s" % (self.cluster_id))

    def set_definition(self, cluster):
        """
        Set the cluster's definition. The definition should come from a call to the get_definition()
        method. 

        .. caution::

            Deprecated, use :meth:`DSSClusterSettings.save()`

        .. important::

            You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
            not create a new dict.

        :param dict cluster: a cluster definition

        :return: the updated cluster definition
        :rtype: dict
        """
        return self.client._perform_json(
            "PUT", "/admin/clusters/%s" % (self.cluster_id), body=cluster)

    def get_status(self):
        """
        Get the cluster's status and usage

        :return: The cluster status, as a :class:`DSSClusterStatus` object
        :rtype: :class:`DSSClusterStatus`
        """
        status = self.client._perform_json("GET", "/admin/clusters/%s/status" % (self.cluster_id))
        return DSSClusterStatus(self.client, self.cluster_id, status)
   
    ########################################################
    # Cluster actions
    ########################################################

    def start(self):
        """
        Starts or attaches the cluster

        .. caution::

            This operation is only valid for a managed cluster.
        """
        resp = self.client._perform_json(
            "POST", "/admin/clusters/%s/actions/start" % (self.cluster_id))
        if resp is None:
            raise Exception('Cluster operation returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster operation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def stop(self, terminate=True, force_stop=False):
        """
        Stops or detaches the cluster

        This operation is only valid for a managed cluster.

        :param boolean terminate: whether to delete the cluster after stopping it
        :param boolean force_stop: whether to try to force stop the cluster, useful if DSS expects 
                                   the cluster to already be stopped
        """
        resp = self.client._perform_json(
            "POST", "/admin/clusters/%s/actions/stop" % (self.cluster_id),
            params={'terminate': terminate, 'forceStop': force_stop})
        if resp is None:
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster operation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def run_kubectl(self, args):
        """
        Runs an arbitrary kubectl command on the cluster.

        .. caution::

            This operation is only valid for a Kubernetes cluster.

        .. note::

            This call requires an API key with DSS instance admin rights

        :param string args: the arguments to pass to kubectl (without the "kubectl")

        :return: a dict containing the return value, standard output, and standard error of the command
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/admin/clusters/%s/k8s/actions/run-kubectl" % self.cluster_id,
            body={'args': args})

    def delete_finished_jobs(self, delete_failed=False, namespace=None, label_filter=None, dry_run=False):
        """
        Runs a kubectl command to delete finished jobs.

        .. caution::

            This operation is only valid for a Kubernetes cluster.

        :param boolean delete_failed: if True, delete both completed and failed jobs, otherwise only delete completed jobs
        :param string namespace: the namespace in which to delete the jobs, if None, uses the namespace set in kubectl's current context
        :param string label_filter: delete only jobs matching a label filter
        :param boolean dry_run: if True, execute the command as a "dry run"

        :return: a dict containing whether the deletion succeeded, a list of deleted job names, and
                 debug info for the underlying kubectl command
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/admin/clusters/%s/k8s/jobs/actions/delete-finished" % self.cluster_id,
            params={'deleteFailed': delete_failed, 'namespace': namespace, 'labelFilter': label_filter, 'dryRun': dry_run})

    def delete_finished_pods(self, namespace=None, label_filter=None, dry_run=False):
        """
        Runs a kubectl command to delete finished (succeeded and failed) pods.

        .. caution::

            This operation is only valid for a Kubernetes cluster.

        :param string namespace: the namespace in which to delete the pods, if None, uses the namespace set in kubectl's current context
        :param string label_filter: delete only pods matching a label filter
        :param boolean dry_run: if True, execute the command as a "dry run"

        :return: a dict containing whether the deletion succeeded, a list of deleted pod names, and
            debug info for the underlying kubectl command
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/admin/clusters/%s/k8s/pods/actions/delete-finished" % self.cluster_id,
            params={'namespace': namespace, 'labelFilter': label_filter, 'dryRun': dry_run})

    def delete_all_pods(self, namespace=None, label_filter=None, dry_run=False):
        """
        Runs a kubectl command to delete all pods.

        .. caution::

            This operation is only valid for a Kubernetes cluster.

        :param string namespace: the namespace in which to delete the pods, if None, uses the namespace set in kubectl's current context
        :param string label_filter: delete only pods matching a label filter
        :param boolean dry_run: if True, execute the command as a "dry run"

        :return: a dict containing whether the deletion succeeded, a list of deleted pod names, and
            debug info for the underlying kubectl command
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/admin/clusters/%s/k8s/pods/actions/delete-all" % self.cluster_id,
            params={'namespace': namespace, 'labelFilter': label_filter, 'dryRun': dry_run})


class DSSClusterSettings(object):
    """
    The settings of a cluster.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSCluster.get_settings` instead.
    """
    def __init__(self, client, cluster_id, settings):
        self.client = client
        self.cluster_id = cluster_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. 

        Changes made to the returned object will be reflected when saving.

        Fields that can be updated:

         * **permissions**, **usableByAll**, **owner**
         * **params**

        :return: reference to the raw settings, not a copy. See :meth:`DSSCluster.get_definition()`
        :rtype: dict
        """
        return self.settings

    def get_plugin_data(self):
        """
        Get the opaque data returned by the cluster's start.

        .. caution::

            You should generally not modify this

        :return: the data stored by the plugin in the cluster, None if the cluster is not created by a plugin
        :rtype: dict
        """
        return self.settings.get("data", None)

    def save(self):
        """
        Saves back the settings to the cluster
        """
        return self.client._perform_json(
            "PUT", "/admin/clusters/%s" % (self.cluster_id), body=self.settings)


class DSSClusterStatus(object):
    """
    The status of a cluster.
    
    .. important::

        Do not instantiate directly, use :meth:`DSSCluster.get_status` instead.
    """
    def __init__(self, client, cluster_id, status):
        self.client = client
        self.cluster_id = cluster_id
        self.status = status

    def get_raw(self):
        """
        Gets the whole status as a raw dictionary.

        :return: status information, with fields:

                    * **state** : current state of the cluster. Possible values are NONE, STARTING, RUNNING, STOPPING
                    * **clusterType** : type of cluster. Can be "manual" or a plugin cluster element type
                    * **usages** : list of usages of the cluster. Each usage is a dict with either **projectKey** (when cluster is set in the project's settings), or **scenarioId**, **scenarioProjectKey** and **scenarioRunId** (when the cluster is created and used by a scenario run)
                    * **otherProjectUsagesCount** : number of projects that use the cluster but that the user cannot access (these projects are not in **usages**)
                    * **otherScenarioUsagesCount** : number of scenarios that use the cluster but that the user cannot access (these scenarios are not in **usages**)
                    * **error** : if the cluster start failed, a dict with error information

        :rtype: dict
        """
        return self.status


class DSSInstanceVariables(dict):
    """
    Dict containing the instance variables. 

    The variables can be modified directly in the dict and persisted using its :meth:`save` method.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_global_variables` instead.
    """
    def __init__(self, client, variables):
        super(dict, self).__init__()
        self.update(variables)
        self.client = client

    def save(self):
        """
        Save the changes made to the instance variables.

        .. note::

            This call requires an API key with admin rights.
        """
        return self.client._perform_empty("PUT", "/admin/variables/", body=self)


class DSSGlobalUsageSummary(object):
    """
    The summary of the usage of the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_global_usage_summary` instead.
    """
    def __init__(self, data):
        self.data = data

    @property
    def raw(self):
        """
        Get the usage summary structure

        The summary report has top-level fields per object type, like **projectSummaries** or **datasets**, each 
        containing counts, usually a **all** global count, then several **XXXXByType** dict with counts by object
        sub-type (for example, for datasets the sub-type would be the type of the connection they're using)

        :rtype: dict
        """
        return self.data

    @property
    def projects_count(self):
        """
        Get the number of projects on the instance

        :rtype: int
        """
        return self.data["projects"]

    @property
    def total_datasets_count(self):
        """
        Get the number of datasets on the instance

        :rtype: int
        """
        return self.data["datasets"]["all"]

    @property
    def total_recipes_count(self):
        """
        Get the number of recipes on the instance

        :rtype: int
        """
        return self.data["recipes"]["all"]

    @property
    def total_jupyter_notebooks_count(self):
        """
        Get the number of code nobteooks on the instance

        :rtype: int
        """
        return self.data["notebooks"]["nbJupyterNotebooks"]

    @property
    def total_sql_notebooks_count(self):
        """
        Get the number of sql notebooks on the instance

        :rtype: int
        """
        return self.data["notebooks"]["nbSqlNotebooks"]

    @property
    def total_scenarios_count(self):
        """
        Get the number of scenarios on the instance

        :rtype: int
        """
        return self.data["scenarios"]["all"]

    @property
    def total_active_with_trigger_scenarios_count(self):
        """
        Get the number of active scenarios on the instance

        :rtype: int
        """
        return self.data["scenarios"]["activeWithTriggers"]


class DSSCodeStudioTemplateListItem(object):
    """
    An item in a list of code studio templates. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.list_code_studio_templates`
    """
    def __init__(self, client, data):
        self.client = client
        self._data = data

    def to_code_studio_template(self):
        """
        Get the handle corresponding to this code studio template

        :rtype: :class:`DSSCodeStudioTemplate`
        """
        return DSSCodeStudioTemplate(self.client, self._data["id"])

    @property
    def label(self):
        """
        Get the label of the template

        :rtype: string
        """
        return self._data["label"]

    @property
    def id(self):
        """
        Get the identifier of the template

        :rtype: string
        """
        return self._data["id"]

    @property
    def build_for_configs(self):
        """
        Get the list of container configurations this template is built for

        :return: a list of configuration name
        :rtype: list[string]
        """
        return self._data.get("buildFor", [])

    @property
    def last_built(self):
        """
        Get the timestamp of the last build of the template

        :return: a timestamp, or None if the template was never built
        :rtype: :class:`datetime.datetime`
        """
        ts = self._data.get("lastBuilt", 0)
        if ts > 0:
            return datetime.fromtimestamp(ts / 1000)
        else:
            return None

class DSSCodeStudioTemplate(object):
    """
    A handle to interact with a code studio template on the DSS instance

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_code_studio_template`.
    """
    def __init__(self, client, template_id):
        self.client = client
        self.template_id = template_id
            
    ########################################################
    # Template description
    ########################################################
    
    def get_settings(self):
        """
        Get the template's settings. 

        :return: a :class:`DSSCodeStudioTemplateSettings` object to interact with code studio template settings
        :rtype: :class:`DSSCodeStudioTemplateSettings`
        """
        settings = self.client._perform_json("GET", "/admin/code-studios/%s" % (self.template_id))
        return DSSCodeStudioTemplateSettings(self.client, self.template_id, settings)

    ########################################################
    # Building
    ########################################################
    
    def build(self):
        """
        Build or rebuild the template. 

        .. note::

            This call needs an API key which has an user to impersonate set, or a personal API key.

        :return: a handle to the task of building the image
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        future_response = self.client._perform_json("POST", "/admin/code-studios/%s/build" % (self.template_id))
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

class DSSCodeStudioTemplateSettings(object):
    """
    The settings of a code studio template

    .. important::

        Do not instantiate directly, use :meth:`DSSCodeStudioTemplate.get_settings`
    """
    def __init__(self, client, template_id, settings):
        self.client = client
        self.template_id = template_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. 

        :return: a reference to the raw settings, not a copy. Keys are

                    * **id** : unique identifier of the template
                    * **type** : type of the template. Builtin values are 'manual' and 'block_based'; more types can be added via plugin components
                    * **label** : label of the template in the UI
                    * **icon** : icon to use for code studios on this template
                    * **tags** : list of tags (strings)
                    * **isEditor** : whether the template defines a code studio that can be used to edit objects in DSS
                    * **owner**, **defaultPermission** and **permissions** : definition of the permissions on the template
                    * **defaultContainerConf** : container config to use on code studios created on this template
                    * **allowContainerConfOverride** : if True, the container config of code studios on this template can be overriden at the project level
                    * **allContainerConfs** : if True, build the container images for all configs of the instance
                    * **containerConfs** : if **allContainerConfs** is False, a list of container config names to build images for
                    * **params** : definition of the contents of the template. Depends on the **type**

        :rtype: dict
        """
        return self.settings

    def get_built_for_all_container_confs(self):
        """
        Whether the template an image for each container config

        :rtype: boolean
        """
        return self.settings.get("allContainerConfs", False)

    def get_built_container_confs(self):
        """
        Get the list of container configs for which the template builds an image (if not all)

        :return: a list of container configuration names
        :rtype: list[string]
        """
        return self.settings.get("containerConfs", [])

    def set_built_container_confs(self, *configs, **kwargs):
        """
        Set the list of container configs for which the template builds an image

        :param boolean all: if True, an image is built for each config
        :param list[string] configs: list of configuration names to build images for
        """
        all = kwargs.get("all", False)
        self.settings['allContainerConfs'] = all
        if not all:
            self.settings['containerConfs'] = configs

    def save(self):
        """
        Saves the settings of the code studio template
        """
        self.client._perform_empty("PUT", "/admin/code-studios/%s" % (self.template_id), body=self.settings)

