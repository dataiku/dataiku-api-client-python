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
        return DSSPluginUsages.build(
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

    object_id, object_type and project_key are usually provided, excepted for some global
    types, such as cluster types.
    """
    def __init__(self, element_kind, element_type, object_id, object_type, project_key):
        """

        :param str element_kind:
        :param str element_type:
        :param str object_id:
        :param str object_type:
        :param str project_key:
        """
        self.element_kind = element_kind
        self.element_type = element_type
        self.object_id = object_id
        self.object_type = object_type
        self.project_key = project_key

    @staticmethod
    def build(json_object):
        return DSSPluginUsage(
            json_object["elementKind"],
            json_object["elementType"],
            json_object.get("objectId", None),
            json_object.get("objectType", None),
            json_object.get("projectKey", None)
        )


class DSSMissingType(object):
    """
    Information on a type not found while analyzing usages of a plugin.

    object_id, object_type and project_key are usually provided, excepted for some global
    types, such as cluster types.
    """
    def __init__(self, missing_type, object_id, object_type, project_key):
        """

        :param str missing_type: the missing type
        :param str object_id: the object using the missing type (can be None)
        :param str object_type: the type of the object using the missing type (can be None)
        :param str project_key: the project key where the type was found missing (can be None)
        """
        self.missing_type = missing_type
        self.object_id = object_id
        self.object_type = object_type
        self.project_key = project_key

    @staticmethod
    def build(json_object):
        return DSSMissingType(
            json_object["missingType"],
            json_object.get("objectId", None),
            json_object.get("objectType", None),
            json_object.get("projectKey", None)
        )


class DSSPluginUsages(object):
    """
    Information on the usages of a plugin.

    Contains both usages (a list of instances of :class:`DSSPluginUsage`) and analysis errors, if any
    (a list of instances of :class:`DSSMissingType`).

    Some custom types may not be found during usage analysis, typically when a plugin was removed
    but is still used. This prevents some detailed analysis and may hide some uses.
    This information is provided in missingTypes.
    """
    def __init__(self, usages, missing_types):
        """
        :param list(:class:`DSSPluginUsage`) usages: plugin usages
        :param list(:class:`DSSMissingType`) missing_types:
        """
        self.usages = usages
        self.missing_types = missing_types

    @staticmethod
    def build(json_object):
        usages = []
        missing_types = []
        for json_usage in json_object.get("usages", []):
            usages.append(DSSPluginUsage.build(json_usage))
        for json_missing_type in json_object.get("missingTypes"):
            missing_types.append(DSSMissingType.build(json_missing_type))
        return DSSPluginUsages(usages, missing_types)
