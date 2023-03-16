from ..utils import DataikuException
from .future import DSSFuture

class DSSPluginSettings(object):
    """
    The settings of a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPlugin.get_settings`.
    """

    def __init__(self, client, plugin_id, settings):
        self.client = client
        self.plugin_id = plugin_id
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings object.

        .. note::

            This method returns a reference to the settings, not a copy. Changing values in the reference
            then calling :meth:`save()` results in these changes being saved.

        :return: the settings as a dict. Top-level fields are:

                    * **permissions** : list of permissions, per group, as a list of dict, each with fields

                        * **group** : name of a DSS group
                        * **admin** : whether the group can administer the plugin (edit settings and presets)

                    * **defaultPermission** : default permissions for the plugin, as a dict. The dict has the same fields as in **permissions**, minus the **group**
                    * **detailsNotVisible** : if True, only **presets** and **accessibleParameterSetDescs** are filled
                    * **config** : plugin-level settings (deprecated)
                    * **codeEnvName** : name of the code env currently associated to the plugin
                    * **accessibleParameterSetDescs** : list of parameter set definitions that the user can make presets for. Each definition is a dict (see :meth:`DSSPluginParameterSet.desc()`)
                    * **presets** : list of presets (see :meth:`DSSPluginParameterSet.presets()`)
                    * **parameterSets** : list of settings for the parameter sets, as a list of dict (see :meth:`DSSPluginParameterSet.settings()`)
                    * **appTemplates** : list of settings for the Dataiku App templates in this plugin, as a list of dict. Each dict has keys:

                        * **name** : name of the template
                        * **remapping** : settings to remap connections and code envs upon instantiation of the app template, as a dict. The dict has fields:

                            * **connections** : list of remappings for connections, as a list of dict with fields **source** and **target**, applied to connection names
                            * **codeEnvs** : list of remappings for code envs, as a list of dict with fields **source** and **target**, applied to code env names

        :rtype: dict
        """
        return self.settings

    def list_parameter_set_names(self):
        """
        List the names of the parameter sets defined in this plugin.

        :rtype: list[string]
        """
        return [d["id"] for d in self.settings.get("accessibleParameterSetDescs", [])]

    def get_parameter_set(self, parameter_set_name):
        """
        Get a parameter set in this plugin.

        :param string parameter_set_name: name of the parameter set

        :return: a handle on the parameter set
        :rtype: :class:`DSSPluginParameterSet`
        """
        desc = None
        data = None
        for ps in self.settings.get("accessibleParameterSetDescs", []):
            if ps["id"] == parameter_set_name:
                desc = ps
        for ps in self.settings.get("parameterSets", []):
            if ps["name"] == parameter_set_name:
                data = ps
        if desc is None or data is None:
            return None
        return DSSPluginParameterSet(desc, data, self.settings["presets"])

    def set_code_env(self, code_env_name):
        """
        Set the name of the code env to use for this plugin.

        :param string code_env_name: name of a code env 
        """
        self.settings["codeEnvName"] = code_env_name

    def save(self):
        """
        Save the settings to DSS.
        """
        self.client._perform_empty("POST", "/plugins/%s/settings" % (self.plugin_id), body=self.settings)


class DSSPluginParameterSet(object):
    """
    A parameter set in a plugin.

    The values in this class can be modified directly, and changes will be taken into account 
    when calling :meth:`DSSPluginSettings.save()`.
    """
    def __init__(self, desc, settings, presets):
        self._desc = desc
        self._settings = settings
        self._presets = presets

    @property
    def desc(self):
        """
        Get the raw definition of the parameter set.

        :return: a parameter set definition, as a dict of:

                        * **id** : name of the parameter set
                        * **ownerPluginId** : name of the plugin
                        * **elementType** : unique identifier of the parameter set on the DSS instance, built from plugin and parameter set names
                        * **folderName** : name of the folder holding the parameter set files, inside the plugin directory
                        * **desc** : the parameter set's contents as a dict. See `the doc <https://doc.dataiku.com/dss/latest/plugins/reference/params.html#preset-parameters>`_

        :rtype: dict
        """
        return self.desc

    @property
    def settings(self):
        """
        Get the settings of the parameter set.

        These settings control the behavior of the parameter set, and comprise notably the permissions,
        but not the presets of this parameter set.

        :return: the settings of the parameter set, as a dict of:

                        * **name** : name of the parameter set in the plugin
                        * **type** : identifier of the parameter set (unique on the DSS instance)
                        * **permissions** : list of permissions, per group, as a list of dict. Unless given access via **permissions**, only admins of the plugin can add presets for the parameter set. Each dict has fields:

                            * **group** : name of a DSS group
                            * **definableInline** : whether presets of this parameter set can be defined directly in the forms of the plugin components that use them
                            * **definableAtProjectLevel** : whether project-level presets can be made of this parameter set

                        * **defaultPermission** : default permissions for the parameter set, as a dict. The dict has the same fields as in **permissions**, minus the **group**

        :rtype: dict
        """
        return self._settings

    def list_preset_names(self):
        """
        List the names of the presets of this parameter set.

        :rtype: list[string]
        """
        return [p["name"] for p in self._presets if p["type"] == self._settings["type"]]
        
    def get_preset(self, preset_name):
        """
        Get a preset of this parameter set.

        :param string preset_name: name of a preset

        :return: a preset definition, as a dict of:

                        * **type** : type of the parameter set this preset belongs to (type being the instance-wide unique identifier)
                        * **name** : preset name
                        * **description** : preset description
                        * **owner** : login of the owner of the preset
                        * **permissions** : list of permissions, per group, as a list of dict, each with fields

                            * **group** : name of a DSS group
                            * **use** : whether the group can use the preset

                        * **defaultPermission** : default permissions for the plugin, as a dict. The dict has the same fields as in **permissions**, minus the **group**
                        * **config** : values of the preset, as a dict. Each key of the dict is the name of some parameter in the definition of the parameter set
                        * **pluginConfig** : plugin-level values of the preset, as a dict. These values can only be set in the plugin's settings, not in the components using the preset.

        :rtype: dict
        """
        for p in self._presets:
            if p["name"] == preset_name and p["type"] == self._settings["type"]:
                return p
        return None

    def delete_preset(self, preset_name):
        """
        Remove a preset from this plugin's settings

        :param string preset_name: name for the preset to remove
        """
        preset = self.get_preset(preset_name)
        if preset is not None:
            self._presets.remove(preset)

    def create_preset(self, preset_name):
        """
        Create a new preset of this parameter set in the plugin settings.

        :param string preset_name: name for the preset to create

        :return: a preset definition, as a dict (see :meth:`get_preset()`)
        :rtype: dict
        """
        for p in self._presets:
            if p["name"] == preset_name:
                raise Exception("A preset of the same name already exists")
        # since self._presets is directly the list from the plugin settings, this adds the preset to the plugin
        self._presets.append({"name":preset_name, "type":self._settings["type"], "config":{}, "pluginConfig":{}, "defaultPermissions":{}, "permissions":[]})
        return self.get_preset(preset_name)

class DSSPlugin(object):
    """
    A plugin on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_plugin()`
    """
    def __init__(self, client, plugin_id):
        self.client = client
        self.plugin_id = plugin_id

    ########################################################
    # Settings
    ########################################################

    def get_settings(self):
        """
        Get the plugin-level settings.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :return: a handle on the settings
        :rtype: :class:`DSSPluginSettings`
        """
        settings = self.client._perform_json("GET", "/plugins/%s/settings" % (self.plugin_id))
        return DSSPluginSettings(self.client, self.plugin_id, settings)

    ########################################################
    # Code env
    ########################################################

    def create_code_env(self, python_interpreter=None, conda=False):
        """
        Start the creation of the code env of the plugin.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        If not passing any value to **python_interpreter**, the default defined by the plugin 
        will be used.

        Usage example:

        .. code-block:: python

            # create a default code env for the plugin
            plugin = client.get_plugin('the-plugin-id')
            future = plugin.create_code_env()
            creation = future.wait_for_result()
            # take the name of the new code env
            env_name = creation["envName"]
            # set it as the current plugin code env
            settings = plugin.get_settings()
            settings.set_code_env(env_name)
            settings.save()

        :param string python_interpreter: which version of python to use. Possible values: PYTHON27, PYTHON34, PYTHON35, PYTHON36, PYTHON37, PYTHON38, PYTHON39, PYTHON310, PYTHON311
        :param boolean conda: if True use conda to create the code env, if False use virtualenv and pip.

        :return: a handle on the operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/code-env/actions/create" % (self.plugin_id), body={
            "deploymentMode" : "PLUGIN_MANAGED",
            "conda": conda,
            "pythonInterpreter": python_interpreter
        })
        return DSSFuture.from_resp(self.client, ret)


    def update_code_env(self):
        """
        Start an update of the code env of the plugin.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        Usage example:

        .. code-block:: python

            # update the plugin code env after updating the plugin
            plugin = client.get_plugin('the-plugin-id')
            future = plugin.update_code_env()
            future.wait_for_result()

        :return: a handle on the operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/code-env/actions/update" % (self.plugin_id))
        return DSSFuture.from_resp(self.client, ret)


    ########################################################
    # Plugin update
    ########################################################

    def update_from_zip(self, fp):
        """
        Update the plugin from a plugin archive (as a file object).

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param file-like fp: A file-like object pointing to a plugin archive zip
        """
        files = {'file': fp }
        self.client._perform_json("POST", "/plugins/%s/actions/updateFromZip" % (self.plugin_id), files=files)

    def update_from_store(self):
        """
        Update the plugin from the Dataiku plugin store.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        Usage example:

        .. code-block:: python

            # update a plugin that was installed from the store
            plugin = client.get_plugin("my-plugin-id")
            future = plugin.update_from_store()
            future.wait_for_result()

        :return: a handle on the operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/actions/updateFromStore" % (self.plugin_id))
        return DSSFuture.from_resp(self.client, ret)

    def update_from_git(self, repository_url, checkout = "master", subpath=None):
        """
        Updates the plugin from a Git repository. 

        .. note::

            DSS must be setup to allow access to the repository.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        Usage example:
        
        .. code-block:: python

            # update a plugin that was installed from git
            plugin = client.get_plugin("my-plugin-id") 
            future = plugin.update_from_git("git@github.com:myorg/myrepo")
            future.wait_for_result()

        :param string repository_url: URL of a Git remote
        :param string checkout: branch/tag/SHA1 to commit. For example "master"
        :param string subpath: Optional, path within the repository to use as plugin. Should contain a 'plugin.json' file

        :return: a handle on the operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture` 
        """
        ret = self.client._perform_json("POST", "/plugins/%s/actions/updateFromGit" % (self.plugin_id), body={
            "gitRepositoryUrl": repository_url,
            "gitCheckout" : checkout,
            "gitSubpath": subpath
        })
        return DSSFuture.from_resp(self.client, ret)

    ########################################################
    # Plugin uninstall/delete
    ########################################################

    def list_usages(self, project_key=None):
        """
        Get the list of usages of the plugin.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param string project_key: optional key of project where to look for usages. Default is None and looking in all projects.

        :rtype: :class:`DSSPluginUsages`
        """
        return DSSPluginUsages(
            self.client._perform_json("GET", "/plugins/{pluginId}/actions/listUsages".format(pluginId=self.plugin_id),
                                      params={"projectKey": project_key})
        )

    def delete(self, force=False):
        """
        Delete a plugin.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param boolean force: if True, plugin will be deleted even if usages are found or errors occurred during usages
                              analysis. Default: False.

        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """

        params = {
            "force": force
        }
        ret = self.client._perform_json("POST", "/plugins/{pluginId}/actions/delete".format(pluginId=self.plugin_id),
                                        body=params)
        return DSSFuture.from_resp(self.client, ret)

    ########################################################
    # Managing the dev plugin's contents
    ########################################################

    def list_files(self):
        """
        Get the hierarchy of files in the plugin.

        .. note::

            Dev plugins only

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :return: list of files or directories, each one a dict. Directories have a **children** field for recursion. Each dict has fields **name** and **path** (the path from the root of the plugin files)
        :rtype: dict
        """
        return self.client._perform_json("GET", "/plugins/%s/contents" % (self.plugin_id))

    def get_file(self, path):
        """
        Get a file from the plugin folder.

        .. note::

            Dev plugins only

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        Usage example:

        .. code-block:: python

            # read the code env desc of a plugin
            plugin = client.get_plugin("my-plugin-name")
            with plugin.get_file('code-env/python/desc.json') as fp:
                desc = json.load(fp)

        :param string path: the path of the file, relative to the root of the plugin

        :return: the file's content
        :rtype: file-like
        """
        return self.client._perform_raw("GET", "/plugins/%s/contents/%s" % (self.plugin_id, path)).raw

    def put_file(self, path, f):
        """
        Update a file in the plugin folder.
        
        .. note::

            Dev plugins only

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param file-like f: the file contents, as a file-like object
        :param string path: the path of the file, relative ot the root of the plugin
        """
        file_name = path.split('/')[-1]
        data = f.read() # eat it all, because making it work with a path variable and a MultifilePart in swing looks complicated
        self.client._perform_empty("POST", "/plugins/%s/contents/%s" % (self.plugin_id, path), raw_body=data)

    def rename_file(self, path, new_name):
        """
        Rename a file/folder in the plugin.

        .. note::

            Dev plugins only

        :param string path: the path of the file/folder, relative ot the root of the plugin
        :param string new_name: the new name of the file/folder
        """
        self.client._perform_empty("POST", "/plugins/%s/contents-actions/rename" % self.plugin_id, body={"oldPath": path, "newName": new_name})

    def move_file(self, path, new_path):
        """
        Move a file/folder in the plugin.

        .. note::

            Dev plugins only

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param string path: the path of the file/folder, relative ot the root of the plugin
        :param string new_path: the new path relative at the root of the plugin
        """
        self.client._perform_empty("POST", "/plugins/%s/contents-actions/move" % self.plugin_id, body={"oldPath": path, "newPath": new_path})

class DSSPluginUsage(object):
    """
    Information on a usage of an element of a plugin.

    .. important::

        Do no instantiate directly, use :meth:`dataikuapi.dss.plugin.DSSPlugin.list_usages()`
    """
    def __init__(self, data):
        self._data = data

    @property
    def element_kind(self):
        """
        Get the type of the plugin component.

        :return: a kind of plugin component, like 'python-clusters', 'python-connectors', 'python-fs-providers', 'webapps', ...
        :rtype: string
        """
        return self._data["elementKind"]
    
    @property
    def element_type(self):
        """
        Get the identifier of the plugin component.

        :rtype: string
        """
        return self._data["elementType"]
    
    @property
    def object_id(self):
        """
        Get the identifier of the object using the plugin component.

        :rtype: string
        """
        return self._data["objectId"]
    
    @property
    def object_type(self):
        """
        Get the type of the object using the plugin component.

        :return: a type of DSS object, like 'CLUSTER', 'DATASET', 'RECIPE', ...
        :rtype: string
        """
        return self._data["objectType"]
    
    @property
    def project_key(self):
        """
        Get the project key of the object using the plugin component.

        :rtype: string
        """
        return self._data["projectKey"]
    

class DSSMissingType(object):
    """
    Information on a type not found while analyzing usages of a plugin.

    Missing types can occur when plugins stop defining a given component, for example during development,
    and DSS object still use the now-removed component.

    .. important::

        Do no instantiate directly, use :meth:`dataikuapi.dss.plugin.DSSPlugin.list_usages()`
    """
    def __init__(self, data):
        self._data = data

    @property
    def missing_type(self):
        """
        Get the type of the plugin component.

        :rtype: string
        """
        return self._data["missingType"]
    
    @property
    def object_id(self):
        """
        Get the identifier of the object using the plugin component.

        :rtype: string
        """
        return self._data["objectId"]
    
    @property
    def object_type(self):
        """
        Get the type of the object using the plugin component.

        :return: a type of DSS object, like 'CLUSTER', 'DATASET', 'RECIPE', ...
        :rtype: string
        """
        return self._data["objectType"]
    
    @property
    def project_key(self):
        """
        Get the project key of the object using the plugin component

        :rtype: string
        """
        return self._data["projectKey"]

class DSSPluginUsages(object):
    """
    Information on the usages of a plugin.

    .. important::

        Do no instantiate directly, use :meth:`dataikuapi.dss.plugin.DSSPlugin.list_usages()`

    Some custom types may not be found during usage analysis, typically when a plugin was removed
    but is still used. This prevents some detailed analysis and may hide some uses. This information is 
    provided in :meth:`missing_types()`.
    """
    def __init__(self, data):
        """
        Initialize a DSSPluginUsages from a dict of its properties

        :param dict data: the usages as json dict
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
        Get the raw plugin usages.

        :return: a summary of the usages, as a dict with fields **usages** and **missingTypes**.
        :rtype: dict
        """
        return self._data

    @property
    def usages(self):
        """
        Get the list of usages of components of the plugin.

        :return: list of usages, each a :class:`DSSPluginUsage`
        :rtype: list
        """
        return self._usages

    @property
    def missing_types(self):
        """
        Get the list of usages of missing components of the plugin.

        :return: list of missing component types, each a :class:`DSSMissingType`
        :rtype: list
        """
        return self._missing_types
    

    def maybe_used(self):
        """
        Whether the plugin maybe in use.

        :return: True if usages were found, False if errors were encountered during analysis
        :rtype: boolean
        """
        return not (not self.usages and not self.missing_types)
