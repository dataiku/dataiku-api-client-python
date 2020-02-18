from .future import DSSFuture
import json

class DSSConnectionInfo(dict):
    """A class holding read-only information about a connection.
    This class should not be created directly. Instead, use :meth:`DSSConnection.get_info`

    The main use case of this class is to retrieve the decrypted credentials for a connection,
    if allowed by the connection permissions.

    Depending on the connection kind, the credential may be available using :meth:`get_basic_credential` 
    or :meth:`get_aws_credential`

    """
    def __init__(self, data):
        """Do not call this directly, use :meth:`DSSConnection.get_info`"""
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
    A connection on the DSS instance
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name

    ########################################################
    # Location info
    ########################################################

    def get_location_info(self):
        """Deprecated, use get_info"""
        return self.get_info()

    def get_info(self):
        """
        Gets information about this connection.

        Note: this call requires either an admin API key or
        a personal API key that corresponds to a user who 
        belongs to a group who has the rights to read connection
        details

        :returns: a :class:`DSSConnectionInfo` containing connection information
        """
        return DSSConnectionInfo(self.client._perform_json(
            "GET", "/connections/%s/info" % self.name))
    
    ########################################################
    # Connection deletion
    ########################################################
    
    def delete(self):
        """
        Delete the connection

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/connections/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get the connection's definition (type, name, params, usage restrictions)
        Note: this call requires an API key with admin rights
        
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
        Note: this call requires an API key with admin rights
        
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
        when DSS is in multi-user-security mode.
        Note: this call requires an API key with admin rights
        
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture`  handle to the task of resynchronizing the permissions
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)
    
    def sync_datasets_acls(self):
        """
        Resync permissions on datasets in this connection path. This is only useful for HDFS connections
        when DSS is in multi-user-security mode.
        Note: this call requires an API key with admin rights
        
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture`  handle to the task of resynchronizing the permissions
        """
        future_response = self.client._perform_json(
            "POST", "/admin/connections/%s/sync" % self.name,
            body = {'root':True})
        return DSSFuture(self.client, future_response.get('jobId', None), future_response)
    
        
class DSSUser(object):
    """
    A handle for a user on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.DSSClient.get_user`
    """
    def __init__(self, client, login):
        self.client = client
        self.login = login

    ########################################################
    # User deletion
    ########################################################

    def delete(self):
        """
        Deletes the user
        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)

    ########################################################
    # User description
    ########################################################

    def get_definition(self):
        """
        Get the user's definition (login, type, display name, permissions, ...)
        Note: this call requires an API key with admin rights

        :return: the user's definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/users/%s" % self.login)

    def set_definition(self, definition):
        """
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
        return self.client._perform_json(
            "PUT", "/admin/users/%s" % self.login,
            body = definition)
            
class DSSGroup(object):
    """
    A group on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.DSSClient.get_group`
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
        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/groups/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get the group's definition (name, description, admin abilities, type, ldap name mapping)
        Note: this call requires an API key with admin rights
        
        :return: the group's definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)
    
    def set_definition(self, definition):
        """
        Set the group's definition.
        Note: this call requires an API key with admin rights

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
    Do not create this directly, use :meth:`dataikuapi.DSSClient.get_general_settings`
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
    Do not create this directly, use :meth:`dataikuapi.DSSClient.get_code_env`
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
          env.desc.installJupyterSupport, env.desc.yarnPythonBin

        Fields that can be updated in automation node (where {version} is the updated version):

        * env.permissions, env.usableByAll, env.owner
        * env.{version}.specCondaEnvironment, env.{version}.specPackageList, env.{version}.externalCondaEnvName, 
          env.{version}.desc.installCorePackages, env.{version}.desc.installJupyterSupport, env.{version}.desc.yarnPythonBin

        Note: this call requires an API key with admin rights
        
        :param dict data: a code env definition
        :return: the updated code env definition, as a dict
        """
        return self.client._perform_json(
            "PUT", "/admin/code-envs/%s/%s" % (self.env_lang, self.env_name), body=env)
    
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

    def update_packages(self):
        """
        Update the code env packages so that it matches its spec
        
        Note: this call requires an API key with admin rights
        """
        resp = self.client._perform_json(
            "POST", "/admin/code-envs/%s/%s/packages" % (self.env_lang, self.env_name))
        if resp is None:
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Env update failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp


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

class DSSCluster(object):
    """
    A handle to interact with a cluster on the DSS instance
    """
    def __init__(self, client, cluster_id):
        """Do not call that directly, use :meth:`dataikuapi.dss.DSSClient.get_cluster`"""
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
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster operation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

    def stop(self, terminate=True):
        """
        Stops or detaches the cluster

        This operation is only valid for a managed cluster.
        :param boolean terminate: whether to delete the cluster after stopping it
        """
        resp = self.client._perform_json(
            "POST", "/admin/clusters/%s/actions/stop" % (self.cluster_id),
            params = {'terminate':terminate})
        if resp is None:
            raise Exception('Env update returned no data')
        if resp.get('messages', {}).get('error', False):
            raise Exception('Cluster operation failed : %s' % (json.dumps(resp.get('messages', {}).get('messages', {}))))
        return resp

class DSSClusterSettings(object):
    def __init__(self, client, cluster_id, settings):
        """Do not call directly, use :meth:`DSSCluster.get_settings`"""
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
    def __init__(self, client, cluster_id, status):
        """Do not call directly, use :meth:`DSSCluster.get_Status`"""
        self.client = client
        self.cluster_id = cluster_id
        self.status = status

    def get_raw(self):
        """
        Gets the whole status as a raw dictionary.
        """
        return self.status