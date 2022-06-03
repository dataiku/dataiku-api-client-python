import datetime

from .future import DSSFuture
import json, warnings
from datetime import datetime


class DSSConnectionInfo(dict):
    """A class holding read-only information about a connection.
    Do not create this object directly, use :meth:`DSSConnection.get_info` instead.

    The main use case of this class is to retrieve the decrypted credentials for a connection,
    if allowed by the connection permissions.

    Depending on the connection kind, the credential may be available using :meth:`get_basic_credential` 
    or :meth:`get_aws_credential`.
    """
    def __init__(self, data):
        super(DSSConnectionInfo, self).__init__(data)

    def get_type(self):
        """Returns the type of the connection"""
        return self["type"]

    def get_params(self):
        """Returns the parameters of the connection, as a dict"""
        return self["params"]

    def get_basic_credential(self):
        """
        Returns the basic credential (user/password pair) for this connection, if available

        :returns: the credential, as a dict containing "user" and "password"
        :rtype dict
        """
        if not "resolvedBasicCredential" in self:
            raise ValueError("No basic credential available")
        return self["resolvedBasicCredential"]

    def get_aws_credential(self):
        """
        Returns the AWS credential for this connection, if available.
        The AWS credential can either be a keypair or a STS token triplet

        :returns: the credential, as a dict containing "accessKey", "secretKey", and "sessionToken" (only in the case of STS token)
        :rtype dict
        """
        if not "resolvedAWSCredential" in self:
            raise ValueError("No AWS credential available")
        return self["resolvedAWSCredential"]


class DSSConnection(object):
    """
    A connection on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_connection` instead.
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name

    ########################################################
    # Location info
    ########################################################

    def get_location_info(self):
        """Deprecated, use get_info"""
        warnings.warn("DSSConnection.get_location_info is deprecated, please use get_info", DeprecationWarning)
        return self.get_info()

    def get_info(self, contextual_project_key=None):
        """
        Gets information about this connection.

        Note: this call requires permissions to read connection details

        :param contextual_project_key: optional project key use to resolve variables
        :returns: a :class:`DSSConnectionInfo` containing connection information
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

    def get_definition(self):
        """
        Get the connection's definition (type, name, params, usage restrictions)
        
        :returns: The connection definition, as a dict.

        The exact structure of the returned dict is not documented and depends on the connection
        type. Create connections using the DSS UI and call :meth:`get_definition` to see the 
        fields that are in it.
        """
        return self.client._perform_json(
            "GET", "/admin/connections/%s" % self.name)
    
    def set_definition(self, description):
        """
        Set the connection's definition.
        
        You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
        not create a new dict.

        :param dict the definition for the connection, as a dict.
        """
        return self.client._perform_json(
            "PUT", "/admin/connections/%s" % self.name,
            body = description)
    
    ########################################################
    # Security
    ########################################################
    
    def sync_root_acls(self):
        """
        Resync root permissions on this connection path. This is only useful for HDFS connections
        when DSS has User Isolation activated with "DSS-managed HDFS ACL"

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of resynchronizing the permissions
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)
    
    def sync_datasets_acls(self):
        """
        Resync permissions on datasets in this connection path. This is only useful for HDFS connections
        when DSS has User Isolation activated with "DSS-managed HDFS ACL"
        
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of resynchronizing the permissions
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)


class DSSUser(object):
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

        :rtype: :class:`DSSUserSettings`
        """
        raw = self.client._perform_json("GET", "/admin/users/%s" % self.login)
        return DSSUserSettings(self.client, self.login, raw)

    def get_activity(self):
        """
        Gets the activity of the user

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
        Deprecated, use get_settings instead

        Get the user's definition (login, type, display name, permissions, ...)

        :return: the user's definition, as a dict
        """
        warnings.warn("DSSUser.get_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("GET", "/admin/users/%s" % self.login)

    def set_definition(self, definition):
        """
        Deprecated, use get_settings instead

        Set the user's definition.
        Note: this call requires an API key with admin rights

        You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
        not create a new dict.

        The fields that may be changed in a user definition are:

                * email
                * displayName
                * groups
                * userProfile
                * password 

        :param dict definition: the definition for the user, as a dict
        """
        warnings.warn("DSSUser.set_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = definition)

    def get_client_as(self):
        """
        Gets a :class:`dataikuapi.DSSClient` that has the permissions of this user.

        This allows administrators to impersonate actions on behalf of other users, in order to perform
        actions on their behalf
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
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_own_user` instead.
    """
    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Get your own settings

        :rtype: :class:`DSSOwnUserSettings`
        """
        raw = self.client._perform_json("GET", "/current-user")
        return DSSOwnUserSettings(self.client, raw)


class DSSUserSettingsBase(object):
    """
    Settings for a DSS user.
    Do not create this object directly, use :meth:`DSSUser.get_settings` or :meth:`DSSOwnUser.get_settings` instead.
    """
    def __init__(self, settings):
        self.settings = settings

    def get_raw(self):
        """
        :return: the raw settings of the user, as a dict. Modifications made to the returned object are reflected when saving
        :rtype: dict
        """
        return self.settings

    def add_secret(self, name, value):
        """
        Adds a user secret.
        If there was already a secret with the same name, it is replaced
        """
        self.remove_secret(name)
        return self.settings["secrets"].append({"name": name, "value": value, "secret": True})

    def remove_secret(self, name):
        """Removes a user secret based on its name"""
        self.settings["secrets"] = [x for x in self.settings["secrets"] if x["name"] != name]

    @property
    def user_properties(self):
        """
        The user properties (editable by the user) for this user. Do not set this property, modify the dict in place

        :rtype dict
        """
        return self.settings["userProperties"]

    def set_basic_connection_credential(self, connection, user, password):
        """Sets per-user-credentials for a connection that takes a user/password pair"""
        self.settings["credentials"][connection] = {
            "type": "BASIC",
            "user": user,
            "password": password
        }

    def remove_connection_credential(self,connection):
        """Removes per-user-credentials for a connection"""
        if connection in self.settings["credentials"]:
            del self.settings["credentials"][connection]

    def set_basic_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name, user, password):
        """Sets per-user-credentials for a plugin preset that takes a user/password pair"""
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        self.settings["credentials"][name] = {
            "type": "BASIC",
            "user": user,
            "password": password
        }

    def set_oauth2_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name, refresh_token):
        """Sets per-user-credentials for a plugin preset that takes a OAuth refresh token"""
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        self.settings["credentials"][name] = {
            "type": "OAUTH_REFRESH_TOKEN",
            "refreshToken": refresh_token
        }

    def remove_plugin_credential(self, plugin_id, param_set_id, preset_id, param_name):
        """Removes per-user-credentials for a plugin preset"""
        name = json.dumps(["PLUGIN", plugin_id, param_set_id, preset_id, param_name])[1:-1]

        if name in self.settings["credentials"]:
            del self.settings["credentials"][name]


class DSSUserSettings(DSSUserSettingsBase):
    """
    Settings for a DSS user.
    Do not create this object directly, use :meth:`DSSUser.get_settings` instead.
    """
    def __init__(self, client, login, settings):
        super(DSSUserSettings, self).__init__(settings)
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
        self.client._perform_json("PUT", "/admin/users/%s" % self.login, body = self.settings)


class DSSOwnUserSettings(DSSUserSettingsBase):
    """
    Settings for the current DSS user.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_own_user` instead.
    """
    def __init__(self, client, settings):
        super(DSSOwnUserSettings, self).__init__(settings)
        self.client = client

    def save(self):
        """Saves the settings"""
        self.client._perform_empty("PUT", "/current-user", body = self.settings)


class DSSUserActivity(object):
    """
    Activity for a DSS user.
    Do not create this object directly, use :meth:`DSSUser.get_activity` or :meth:`DSSClient.list_users_activity` instead.
    """
    def __init__(self, client, login, activity):
        self.client = client
        self.login = login
        self.activity = activity

    def get_raw(self):
        """
        Get the raw activity of the user as a dict.

        :return: the raw activity
        :rtype: dict
        """
        return self.activity

    @property
    def last_successful_login(self):
        """
        Get the last successful login of the user as a :class:`datetime.datetime`
        
        Returns None if there was no successful login for this user.

        :return: the last successful login
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSuccessfulLogin"]
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None

    @property
    def last_failed_login(self):
        """
        Get the last failed login of the user as a :class:`datetime.datetime`

        Returns None if there were no failed login for this user.

        :return: the last failed login
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastFailedLogin"]
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None

    @property
    def last_session_activity(self):
        """
        Get the last session activity of the user as a :class:`datetime.datetime`, i.e. the last time
        the user opened a new DSS tab or refreshed his session.

        Returns None if there is no session activity yet.

        :return: the last session activity
        :rtype: :class:`datetime.datetime` or None
        """
        timestamp = self.activity["lastSessionActivity"]
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None


class DSSGroup(object):
    """
    A group on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_group` instead.
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
        
        :return: the group's definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)
    
    def set_definition(self, definition):
        """
        Set the group's definition.

        You should only :meth:`set_definition` using an object that you obtained through :meth:`get_definition`, 
        not create a new dict.

        Args:
            definition: the definition for the group, as a dict
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body = definition)


class DSSGeneralSettings(object):
    """
    The general settings of the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_general_settings` instead.
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
        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty("PUT", "/admin/general-settings", body = self.settings)

    ########################################################
    # Value accessors
    ########################################################
    
    def get_raw(self):
        """
        Get the settings as a dictionary
        """
        return self.settings

    def add_impersonation_rule(self, rule, is_user_rule=True):
        """
        Add a rule to the impersonation settings

        :param rule: an impersonation rule, either a :class:`dataikuapi.dss.admin.DSSUserImpersonationRule`
            or a :class:`dataikuapi.dss.admin.DSSGroupImpersonationRule`, or a plain dict
        :param is_user_rule: when the rule parameter is a dict, whether the rule is for users or groups
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

    def get_impersonation_rules(self, dss_user=None, dss_group=None, unix_user=None, hadoop_user=None, project_key=None, scope=None, rule_type=None, is_user=None):
        """
        Retrieve the user or group impersonation rules that matches the parameters

        :param dss_user: a DSS user or regular expression to match DSS user names
        :param dss_group: a DSS group or regular expression to match DSS groups
        :param unix_user: a name to match the target UNIX user
        :param hadoop_user: a name to match the target Hadoop user
        :param project_key: a project_key
        :param scope: project-scoped ('PROJECT') or global ('GLOBAL')
        :param type: the rule user or group matching method ('IDENTITY', 'SINGLE_MAPPING', 'REGEXP_RULE')
        :param is_user: True if only user-level rules should be considered, False for only group-level rules, None to consider both
        """
        user_matches = self.settings['impersonation']['userRules'] if is_user == None or is_user == True else []
        if dss_user is not None:
            user_matches = [m for m in user_matches if dss_user == m.get('dssUser', None)]
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

    def remove_impersonation_rules(self, dss_user=None, dss_group=None, unix_user=None, hadoop_user=None, project_key=None, scope=None, rule_type=None, is_user=None):
        """
        Remove the user or group impersonation rules that matches the parameters from the settings

        :param dss_user: a DSS user or regular expression to match DSS user names
        :param dss_group: a DSS group or regular expression to match DSS groups
        :param unix_user: a name to match the target UNIX user
        :param hadoop_user: a name to match the target Hadoop user
        :param project_key: a project_key
        :param scope: project-scoped ('PROJECT') or global ('GLOBAL')
        :param type: the rule user or group matching method ('IDENTITY', 'SINGLE_MAPPING', 'REGEXP_RULE')
        :param is_user: True if only user-level rules should be considered, False for only group-level rules, None to consider both
        """
        for m in self.get_impersonation_rules(dss_user, dss_group, unix_user, hadoop_user, project_key, scope, rule_type, is_user):
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
    Helper to build user-level rule items for the impersonation settings
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

        Args:
            project_key : the project this rule applies to
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

        Args:
            dss_user : a DSS user
            unix_user : a UNIX user
            hadoop_user : a Hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'SINGLE_MAPPING'
        self.raw['dssUser'] = dss_user
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self

    def user_regexp(self, regexp, unix_user, hadoop_user=None):
        """
        Make the rule map a DSS users matching a given regular expression to a given UNIX user

        Args:
            regexp : a regular expression to match DSS user names
            unix_user : a UNIX user
            hadoop_user : a Hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'REGEXP_RULE'
        self.raw['ruleFrom'] = regexp
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self


class DSSGroupImpersonationRule(object):
    """
    Helper to build group-level rule items for the impersonation settings
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

        Args:
            dss_group : a DSS group
            unix_user : a UNIX user
            hadoop_user : a Hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'SINGLE_MAPPING'
        self.raw['dssGroup'] = dss_group
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self

    def group_regexp(self, regexp, unix_user, hadoop_user=None):
        """
        Make the rule map a DSS users matching a given regular expression to a given UNIX user

        Args:
            regexp : a regular expression to match DSS groups
            unix_user : a UNIX user
            hadoop_user : a Hadoop user (optional, defaults to unix_user)
        """
        self.raw['type'] = 'REGEXP_RULE'
        self.raw['ruleFrom'] = regexp
        self.raw['targetUnix'] = unix_user
        self.raw['targetHadoop'] = hadoop_user
        return self


class DSSCodeEnv(object):
    """
    A code env on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_code_env` instead.
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
        Note: this call requires an API key with admin rights
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

        Note: this call requires an API key with admin rights
        
        :returns: the code env definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name))

    def set_definition(self, env):
        """
        Set the code env's definition. The definition should come from a call to :meth:`get_definition`

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

        Note: this call requires an API key with admin rights
        
        :param dict data: a code env definition
        :return: the updated code env definition, as a dict
        """
        return self.client._perform_json(
            "PUT", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name), body=env)

    def get_version_for_project(self, project_key):
        """
        Resolve the code env version for a given project

        Note: version will only be non-empty for versioned code envs actually used by the project

        :returns: the code env reference, with a version field
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/%s/version" % (self.env_lang, self.env_name, project_key))


    def get_settings(self):
        """
        Returns the settings of this code env as a :class:`DSSCodeEnvSettings`, or one of its subclasses.

        Known subclasses of :class:`DSSCodeEnvSettings` include :class:`DSSDesignCodeEnvSettings` 
        and :class:`DSSAutomationCodeEnvSettings`

        You must use :meth:`~DSSCodeEnvSettings.save()` on the returned object to make your changes effective
        on the code env.

        .. code-block:: python

            # Example: setting the required packagd
            codeenv = client.get_code_env("PYTHON", "code_env_name")
            settings = codeenv.get_settings()
            settings.set_required_packages("dash==2.0.0", "bokeh<2.0")
            settings.save()
            # then proceed to update_packages()

        :rtype: :class:`DSSCodeEnvSettings`
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
        
        Note: this call requires an API key with admin rights
        
        :param active: True to activate jupyter support, False to deactivate
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
        
        Note: this call requires an API key with admin rights
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
        
        Note: this call requires an API key with admin rights
        """
        resp = self.client._perform_json(
            "POST", "/admin/code-envs/%s/%s/images" % (self.env_lang, self.env_name),
            params={"envVersion": env_version})
        if resp is None:
            raise Exception('Env image build returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env image build failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def list_usages(self, env_version=None):
        """
        List usages of the code env in the instance

        :return: a list of objects where the code env is used
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/usages" % (self.env_lang, self.env_name), params={"envVersion": env_version})

    def list_logs(self, env_version=None):
        """
        List logs of the code env in the instance

        :return: a list of log descriptions
        """
        return self.client._perform_json(
            "GET", "/admin/code-envs/%s/%s/logs" % (self.env_lang, self.env_name), params={"envVersion": env_version})

    def get_log(self, log_name):
        """
        Get the logs of the code env
        
        Args:
            log_name: name of the log to fetch
            
           Returns:
               the log, as a string
        """
        return self.client._perform_text(
            "GET", "/admin/code-envs/%s/%s/logs/%s" % (self.env_lang, self.env_name, log_name))


class DSSCodeEnvSettings(object):
    """
    Base settings class for a DSS code env.
    Do not create this object directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """

    def __init__(self, codeenv, settings):
        self.codeenv = codeenv
        self.settings = settings

    def get_raw(self):
        """Get the raw code env settings as a dict"""
        return self.settings

    @property
    def env_lang(self):
        return self.codeenv.env_lang

    @property
    def env_name(self):
        return self.codeenv.env_name

    def save(self):
        self.codeenv.client._perform_json(
            "PUT", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name), body=self.settings)


class DSSCodeEnvPackageListBearer(object):
    def get_required_packages(self, as_list=False):
        """
        Return the list of required packages, as a single string

        :param boolean as_list: if True, return the spec as a list of lines; if False, return as a single multiline string
        """
        x = self.settings.get("specPackageList", "")
        return x.split('\n') if as_list else x
    def set_required_packages(self, *packages):
        """
        Set the list of required packages
        """
        self.settings["specPackageList"] = '\n'.join(packages)

    def get_required_conda_spec(self, as_list=False):
        """
        Return the list of required conda packages, as a single string

        :param boolean as_list: if True, return the spec as a list of lines; if False, return as a single multiline string
        """
        x = self.settings.get("specCondaEnvironment", "")
        return x.split('\n') if as_list else x
    def set_required_conda_spec(self, *spec):
        """
        Set the list of required conda packages
        """
        self.settings["specCondaEnvironment"] = '\n'.join(packages)

class DSSCodeEnvContainerConfsBearer(object):
    def get_built_for_all_container_confs(self):
        """
        Return whether the code env creates an image for each container config
        """
        return self.settings.get("allContainerConfs", False)
    def get_built_container_confs(self):
        """
        Return the list of container configs for which the code env builds an image (if not all)
        """
        return self.settings.get("containerConfs", [])
    def set_built_container_confs(self, *configs, **kwargs):
        """
        Set the list of container configs for which the code env builds an image

        :param boolean all: if True, an image is built for each config
        :param list configs: list of configuration names to build images for
        """
        all = kwargs.get("all", False)
        self.settings['allContainerConfs'] = all
        if not all:
            self.settings['containerConfs'] = configs
    def built_for_all_spark_kubernetes_confs(self):
        """
        Return whether the code env creates an image for each managed Spark over Kubernetes config
        """
        return self.settings.get("allSparkKubernetesConfs", False)
    def get_built_spark_kubernetes_confs(self):
        """
        Return the list of managed Spark over Kubernetes configs for which the code env builds an image (if not all)
        """
        return self.settings.get("sparkKubernetesConfs", [])
    def set_built_spark_kubernetes_confs(self, *configs, **kwargs):
        """
        Set the list of managed Spark over Kubernetes configs for which the code env builds an image

        :param boolean all: if True, an image is built for each config
        :param list configs: list of configuration names to build images for
        """
        all = kwargs.get("all", False)
        self.settings['allSparkKubernetesConfs'] = all
        if not all:
            self.settings['sparkKubernetesConfs'] = configs


class DSSDesignCodeEnvSettings(DSSCodeEnvSettings, DSSCodeEnvPackageListBearer, DSSCodeEnvContainerConfsBearer):
    """
    Base settings class for a DSS code env on a design node.
    Do not create this object directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """
    def __init__(self, codeenv, settings):
        super(DSSDesignCodeEnvSettings, self).__init__(codeenv, settings)


class DSSAutomationCodeEnvSettings(DSSCodeEnvSettings, DSSCodeEnvContainerConfsBearer):
    """
    Base settings class for a DSS code env on an automation node.
    Do not create this object directly, use :meth:`DSSCodeEnv.get_settings` instead.

    Use :meth:`save` to save your changes
    """
    def __init__(self, codeenv, settings):
        super(DSSAutomationCodeEnvSettings, self).__init__(codeenv, settings)

    def get_version(self, version_id=None):
        """
        Get a specific code env version (for versioned envs) or the single
        version

        :param string version_id: for versioned code env, identifier of the desired version 

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
    Do not create this object directly, use :meth:`DSSAutomationCodeEnvSettings.get_version` instead.

    Use :meth:`save` on the :class:`DSSAutomationCodeEnvSettings` to save your changes
    """
    def __init__(self, codeenv_settings, version_settings):
        self.codeenv_settings = codeenv_settings
        self.settings = version_settings


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

        Returns:
            the code env definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/admin/globalAPIKeys/%s" % (self.key))

    def set_definition(self, definition):
        """
        Set the API key's definition.

        Note: this call requires an API key with admin rights

        Args:
            definition: the definition for the API key, as a JSON object.                        
        """
        return self.client._perform_empty(
            "PUT", "/admin/globalAPIKeys/%s" % self.key,
            body = definition)


class DSSPersonalApiKey(object):
    """
    A personal API key on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_personal_api_key` instead.
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
        
        :returns: the personal API key definition, as a JSON object
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
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.list_personal_api_keys` or :meth:`dataikuapi.DSSClient.list_all_personal_api_keys` instead.
    """
    def __init__(self, client, data):
        super(DSSPersonalApiKeyListItem, self).__init__(data)
        self.client = client

    def to_personal_api_key(self):
        """Gets the :class:`DSSPersonalApiKey` corresponding to this item"""
        return DSSPersonalApiKey(self.client, self["id"])

    @property
    def id(self):
        return self["id"]
   
    @property
    def user(self):
        return self["user"]
   
    @property
    def key(self):
        return self["key"]
   
    @property
    def label(self):
        return self["label"]
   
    @property
    def description(self):
        return self["description"]
   
    @property
    def created_on(self):
        timestamp = self["createdOn"]
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp > 0 else None
   
    @property
    def created_by(self):
        return self["createdBy"]


class DSSCluster(object):
    """
    A handle to interact with a cluster on the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_cluster` instead.
    """
    def __init__(self, client, cluster_id):
        self.client = client
        self.cluster_id = cluster_id
    
    ########################################################
    # Cluster deletion
    ########################################################
    
    def delete(self):
        """
        Deletes the cluster. This does not previously stop it.
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

        :returns: a :class:`DSSClusterSettings` object to interact with cluster settings
        :rtype: :class:`DSSClusterSettings`
        """
        settings = self.client._perform_json(
            "GET", "/admin/clusters/%s" % (self.cluster_id))
        return DSSClusterSettings(self.client, self.cluster_id, settings)

    def set_definition(self, cluster):
        """
        Set the cluster's definition. The definition should come from a call to the get_definition()
        method. 

      
        :param cluster: a cluster definition

        Returns:
            the updated cluster definition, as a JSON object
        """
        return self.client._perform_json(
            "PUT", "/admin/clusters/%s" % (self.cluster_id), body=cluster)

    def get_status(self):
        """
        Get the cluster's status and usage

        :returns: The cluster status, as a :class:`DSSClusterStatus` object
        :rtype: :class:`DSSClusterStatus`
        """
        status = self.client._perform_json("GET", "/admin/clusters/%s/status" % (self.cluster_id))
        return DSSClusterStatus(self.client, self.cluster_id, status)
   
    ########################################################
    # Cluster actions
    ########################################################

    def start(self):
        """
        Starts or attaches the cluster.

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

        :param bool terminate: whether to delete the cluster after stopping it
        :param bool force_stop: whether to try to force stop the cluster,
            useful if DSS expects the cluster to already be stopped
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

        This operation is only valid for a Kubernetes cluster.

        Note: this call requires an API key with DSS instance admin rights

        :param str args: the arguments to pass to kubectl (without the "kubectl")
        :return: a dict containing the return value, standard output, and standard error of the command
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/admin/clusters/%s/k8s/actions/run-kubectl" % self.cluster_id,
            body={'args': args})

    def delete_finished_jobs(self, delete_failed=False, namespace=None, label_filter=None, dry_run=False):
        """
        Runs a kubectl command to delete finished jobs.

        This operation is only valid for a Kubernetes cluster.

        :param bool delete_failed: if True, delete both completed and failed jobs, otherwise only delete completed jobs
        :param str namespace: the namespace in which to delete the jobs, if None, uses the namespace set in kubectl's current context
        :param str label_filter: delete only jobs matching a label filter
        :param bool dry_run: if True, execute the command as a "dry run"
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

        This operation is only valid for a Kubernetes cluster.

        :param str namespace: the namespace in which to delete the pods, if None, uses the namespace set in kubectl's current context
        :param str label_filter: delete only pods matching a label filter
        :param bool dry_run: if True, execute the command as a "dry run"
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

        This operation is only valid for a Kubernetes cluster.

        :param str namespace: the namespace in which to delete the pods, if None, uses the namespace set in kubectl's current context
        :param str label_filter: delete only pods matching a label filter
        :param bool dry_run: if True, execute the command as a "dry run"
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
    Do not create this object directly, use :meth:`DSSCluster.get_settings` instead.
    """
    def __init__(self, client, cluster_id, settings):
        self.client = client
        self.cluster_id = cluster_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        Fields that can be updated:
         - permissions, usableByAll, owner
         - params
        """
        return self.settings

    def get_plugin_data(self):
        """
        If this is a managed attached cluster, returns the opaque data returned by the cluster's start
        operation. Else, returns None.

        You should generally not modify this
        """
        return self.settings.get("data", None)

    def save(self):
        """Saves back the settings to the cluster"""
        return self.client._perform_json(
            "PUT", "/admin/clusters/%s" % (self.cluster_id), body=self.settings)


class DSSClusterStatus(object):
    """
    The status of a cluster.
    Do not create this object directly, use :meth:`DSSCluster.get_status` instead.
    """
    def __init__(self, client, cluster_id, status):
        self.client = client
        self.cluster_id = cluster_id
        self.status = status

    def get_raw(self):
        """
        Gets the whole status as a raw dictionary.
        """
        return self.status


class DSSInstanceVariables(dict):
    """
    Dict containing the instance variables. The variables can be modified directly in the dict and persisted using its :meth:`save` method.

    Do not create this object directly, use :meth:`dataikuapi.DSSClient.get_global_variables` instead.
    """
    def __init__(self, client, variables):
        super(dict, self).__init__()
        self.update(variables)
        self.client = client

    def save(self):
        """
        Save the changes made to the instance variables.

        Note: this call requires an API key with admin rights.
        """
        return self.client._perform_empty("PUT", "/admin/variables/", body=self)


class DSSGlobalUsageSummary(object):
    """
    The summary of the usage of the DSS instance.
    Do not create this object directly, use :meth:`dataikuapi.dss.DSSClient.get_global_usage_summary` instead.
    """
    def __init__(self, data):
        self.data = data

    @property
    def raw(self):
        return self.data

    @property
    def projects_count(self):
        return self.data["projects"]

    @property
    def total_datasets_count(self):
        return self.data["datasets"]["all"]

    @property
    def total_recipes_count(self):
        return self.data["recipes"]["all"]

    @property
    def total_jupyter_notebooks_count(self):
        return self.data["notebooks"]["nbJupyterNotebooks"]

    @property
    def total_sql_notebooks_count(self):
        return self.data["notebooks"]["nbSqlNotebooks"]

    @property
    def total_scenarios_count(self):
        return self.data["scenarios"]["all"]

    @property
    def total_active_with_trigger_scenarios_count(self):
        return self.data["scenarios"]["activeWithTriggers"]


class DSSCodeStudioTemplateListItem(object):
    """An item in a list of code studio templates. Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_code_studio_templates`"""
    def __init__(self, client, data):
        self.client = client
        self._data = data

    def to_code_studio_template(self):
        """Gets the :class:`DSSCodeStudioTemplate` corresponding to this code studio template """
        return DSSCodeStudioTemplate(self.client, self._data["id"])

    @property
    def label(self):
        return self._data["label"]
    @property
    def id(self):
        return self._data["id"]
    @property
    def build_for_configs(self):
        return self._data.get("buildFor", [])
    @property
    def last_built(self):
        ts = self._data.get("lastBuilt", 0)
        if ts > 0:
            return datetime.fromtimestamp(ts / 1000)
        else:
            return None

class DSSCodeStudioTemplate(object):
    """
    A handle to interact with a code studio template on the DSS instance
    """
    def __init__(self, client, template_id):
        """Do not call that directly, use :meth:`dataikuapi.DSSClient.get_code_studio_template`"""
        self.client = client
        self.template_id = template_id
            
    ########################################################
    # Template description
    ########################################################
    
    def get_settings(self):
        """
        Get the template's settings. 

        :returns: a :class:`DSSCodeStudioTemplateSettings` object to interact with code studio template settings
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

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of building the image
        """
        future_response = self.client._perform_json("POST", "/admin/code-studios/%s/build" % (self.template_id))
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

class DSSCodeStudioTemplateSettings(object):
    """
    The settings of a code studio template
    """
    def __init__(self, client, template_id, settings):
        """Do not call directly, use :meth:`DSSCodeStudioTemplate.get_settings`"""
        self.client = client
        self.template_id = template_id
        self.settings = settings

    def get_raw(self):
        """
        Gets all settings as a raw dictionary. This returns a reference to the raw settings, not a copy,
        """
        return self.settings

    def get_built_for_all_container_confs(self):
        """
        Return whether the template an image for each container config
        """
        return self.settings.get("allContainerConfs", False)

    def get_built_container_confs(self):
        """
        Return the list of container configs for which the template builds an image (if not all)
        """
        return self.settings.get("containerConfs", [])

    def set_built_container_confs(self, *configs, **kwargs):
        """
        Set the list of container configs for which the template builds an image

        :param boolean all: if True, an image is built for each config
        :param list configs: list of configuration names to build images for
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

