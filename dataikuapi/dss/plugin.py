class DSSPluginSettings(object):
    """
    The settings of a plugin.
    """

    def __init__(self, client, plugin_id, settings):
        """Do not call this directly, use :meth:`DSSPlugin.get_settings`"""
        self.client = client
        self.plugin_id = plugin_id
        self.settings = settings

    def get_raw(self):
        """Returns the raw settings object"""
        return self.settings

    def set_code_env(self, code_env_name):
        """Sets the name of the code env to use for this plugin"""
        self.settings["codeEnvName"] = code_env_name

    def save(self):
        """Saves the settings to DSS"""
        self.client._perform_empty("POST", "/plugins/%s/settings" % (self.plugin_id), body=self.settings)


class DSSPlugin(object):
    """
    A plugin on the DSS instance
    """
    def __init__(self, client, plugin_id):
       self.client = client
       self.plugin_id = plugin_id

    ########################################################
    # Settings
    ########################################################

    def get_settings(self):
        """Return the plugin-level settings

        :return: a :class:`DSSPluginSettings`
        """
        settings = self.client._perform_json("GET", "/plugins/%s/settings" % (self.plugin_id))
        return DSSPluginSettings(self.client, self.plugin_id, settings)

    ########################################################
    # Code env
    ########################################################

    def create_code_env(self, python_interpreter=None, conda=False):
        """
        Starts the creation of the code env of the plugin

        :return: a :class:`dataikuapi.dssfuture.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/code-env/actions/create" % (self.plugin_id), body={
            "deploymentMode" : "PLUGIN_MANAGED",
            "conda": conda,
            "pythonInterpreter": python_interpreter
        })
        return self.client.get_future(ret["jobId"])


    def update_code_env(self):
        """
        Starts an update of the code env of the plugin

        :return: a :class:`dataikuapi.dss.future.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/code-env/actions/update" % (self.plugin_id))
        return self.client.get_future(ret["jobId"])


    ########################################################
    # Plugin update
    ########################################################

    def update_from_zip(self, fp):
        """
        Updates the plugin from a plugin archive (as a file object)

        :param object fp: A file-like object pointing to a plugin archive zip
        """
        files = {'file': fp }
        self.client._perform_json("POST", "/plugins/%s/actions/updateFromZip" % (self.plugin_id), files=files)

    def update_from_store(self):
        """
        Updates the plugin from the Dataiku plugin store

        :return: a :class:`~dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/plugins/%s/actions/updateFromStore" % (self.plugin_id))
        return self.client.get_future(ret["jobId"])

    def update_from_git(self, repository_url, checkout = "master", subpath=None):
        """
        Updates the plugin from a Git repository. DSS must be setup to allow access to the repository.

        :param str repository_url: URL of a Git remote
        :param str checkout: branch/tag/SHA1 to commit. For example "master"
        :param str subpath: Optional, path within the repository to use as plugin. Should contain a 'plugin.json' file
        :return: a :class:`~dataikuapi.dss.future.DSSFuture`
        """
        ret = self.client._perform_json("POST", "/plugins/%s/actions/updateFromGit" % (self.plugin_id), body={
            "gitRepositoryUrl": repository_url,
            "gitCheckout" : checkout,
            "gitSubpath": subpath
        })
        return self.client.get_future(ret["jobId"])

    ########################################################
    # Plugin uninstall/delete
    ########################################################

    def list_usages(self, project_key=None):
        """
        Get the list of usages of the plugin.

        :param str project_key: optional key of project where to look for usages. Default is None and looking in all projects.
        :return: a :class:`DSSPluginUsages`
        """
        return DSSPluginUsages(
            self.client._perform_json("GET", "/plugins/{pluginId}/actions/listUsages".format(pluginId=self.plugin_id),
                                      params={"projectKey": project_key})
        )

    def delete(self, force=False):
        """
        Delete a plugin.

        If not forced (default), pre-deletion checks will be run (as by :func:`prepare_delete` and the deletion will be
        performed if and only if no usage of the plugin is detected and no error occurred during usages analysis.

        :param bool force: if True, plugin will be deleted even if usages are found or errors occurred during usages
        analysis. Default is False.
        :return: a :class:`dataikuapi.dssfuture.DSSFuture`
        """

        params = {
            "force": force
        }
        ret = self.client._perform_json("POST", "/plugins/{pluginId}/actions/delete".format(pluginId=self.plugin_id),
                                        body=params)
        if "projectCount" in ret:
            raise Exception("Plugin has usages or analysis errors.")
        return self.client.get_future(ret.get("jobId", None))

    ########################################################
    # Managing the dev plugin's contents
    ########################################################

    def list_files(self):
        """
        Get the hierarchy of files in the plugin (dev plugins only)
        """
        return self.client._perform_json("GET", "/plugins/%s/contents" % (self.plugin_id))

    def get_file(self, path):
        """
        Get a file from the plugin folder (dev plugins only)

        :param str path: the path of the file, relative to the root of the plugin

        :return: a file-like object containing the file's content
        """
        return self.client._perform_raw("GET", "/plugins/%s/contents/%s" % (self.plugin_id, path)).raw

    def put_file(self, path, f):
        """
        Update a file in the plugin folder (dev plugins only)
        
        :param file-like f: the file contents, as a file-like object
        :param str path: the path of the file, relative ot the root of the plugin
        """
        file_name = path.split('/')[-1]
        data = f.read() # eat it all, because making it work with a path variable and a MultifilePart in swing looks complicated
        return self.client._perform_empty("POST", "/plugins/%s/contents/%s" % (self.plugin_id, path), raw_body=data)


class DSSPluginUsage(object):
    """
    Information on a usage of an element of a plugin.
    """
    def __init__(self, data):
        """
        Instantiate a DSSPluginUsage from the dict of its properties.
        :param dict data: dict of properties
        """
        self._data = data

    def get_raw(self):
        """
        Get plugin usage as a dictionary
        :rtype: dict
        """
        return self._data

    @property
    def element_kind(self):
        """
        Element kind (webapps, python-formats,...)
        :return: the element kind
        :rtype: str
        """
        return self._data["elementKind"]

    @property
    def element_type(self):
        """
        Element type
        :return: the element type
        :rtype: str
        """
        return self._data["elementType"]

    @property
    def object_id(self):
        """
        :return: Id of the object using the plugin element
        :rtype: str or none
        """
        return self._data.get("objectId", None)

    @property
    def object_type(self):
        """
        :return: Type of the object using the plugin element
        :rtype: str or none
        """
        return self._data.get("objectType", None)

    @property
    def project_key(self):
        """
        :return: Project key of the object using the plugin element
        :rtype: str or none
        """
        return self._data.get("projectKey", None)


class DSSMissingType(object):
    """
    Information on a type not found while analyzing usages of a plugin.
    """
    def __init__(self, data):
        """
        Instantiate a DSSMissingType from the dict of its properties
        :param dict data: dictionary of properties
        """
        self._data = data

    def get_raw(self):
        """
        Get missing type as a dictionary
        :rtype: dict
        """
        return self._data

    @property
    def missing_type(self):
        """
        :return: the missing type
        :rtype: str
        """
        return self._data["missingType"]

    @property
    def object_id(self):
        """
        :return: Id of the object depending on the missing type
        :rtype: str or none
        """
        return self._data.get("objectId", None)

    @property
    def object_type(self):
        """
        :return: Type of the object depending on the missing type
        :rtype: str or none
        """
        return self._data.get("objectType", None)

    @property
    def project_key(self):
        """
        :return: Project key of the object depending on the missing type
        :rtype: str or none
        """
        return self._data.get("projectKey", None)


class DSSPluginUsages(object):
    """
    Information on the usages of a plugin.

    Contains both usages (a list of :class:`DSSPluginUsage`) and analysis errors, if any
    (a list of :class:`DSSMissingType`).

    Some custom types may not be found during usage analysis, typically when a plugin was removed
    but is still used. This prevents some detailed analysis and may hide some uses.
    This information is provided in missingTypes.
    """
    def __init__(self, data):
        """
        Initialize a DSSPluginUsages from a dict of its properties

        :param dict data: the usages as json dict
        :param list(:class:`DSSPluginUsage`) usages: plugin usages
        :param list(:class:`DSSMissingType`) missing_types:
        """
        self._data = data
        self._usages = []
        self._missing_types = []
        for json_usage in data.get("usages", []):
            self._usages.append(DSSPluginUsage(json_usage))
        for json_missing_type in data.get("missingTypes"):
            self._missing_types.append(DSSMissingType(json_missing_type))

    def get_raw(self):
        """
        Get plugin usages as a dictionary.
        :rtype: dict
        """
        return self._data

    def needs_force_delete(self):
        """
        Returns true the deletion of the plugin should be forced, as usages of the plugin were found, or errors
        encoutered during analysis.
        :return:
        """
        return not (not self._usages and not self._missing_types)

    @property
    def usages(self):
        """
        List of plugin usages
        :return: plugin usages
        :rtype: list(:class:`DSSPluginUsage`)
        """
        return self._usages

    @property
    def missing_types(self):
        """
        List of missing types
        :return: missing types
        :rtype: list(:class:`DSSMissingType` )
        """
        return self._missing_types
