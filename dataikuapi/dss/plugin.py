from ..utils import DataikuException
from .future import DSSFuture


class DSSPluginSettingsBase(object):
    """
    Base class for plugin settings.
    
    .. important::

        Do not instantiate directly, use either :meth:`DSSPlugin.get_settings` or :meth:`DSSPlugin.get_project_settings`.
    """

    def __init__(self, client, plugin_id, settings, project_key=None):
        self.client = client
        self.plugin_id = plugin_id
        self.settings = settings
        self.project_key = project_key

    def get_raw(self):
        """
        Get the raw settings object.

        .. note::

            This method returns a reference to the settings, not a copy. Changing values in the reference
            then calling :meth:`save()` results in these changes being saved.

        :return: the settings as a dict. The instance-level settings consist of the plugin code env's name,
                 the presets and the permissions to use the plugin components. The project-level settings consist of the
                 presets and the parameter set descriptions.
        :rtype: dict
        """
        return self.settings

    def list_parameter_set_names(self):
        """
        List the names of the parameter sets defined in this plugin.

        :rtype: list[string]
        """
        return [d["id"] for d in self.settings.get("accessibleParameterSetDescs", [])]

    def _list_parameter_sets(self):
        ret = []
        for parameter_set_name in self.list_parameter_set_names():
            parameter_set = self.get_parameter_set(parameter_set_name)
            if parameter_set is not None:
                ret.append(parameter_set)
        return ret

    def _get_parameter_set(self, parameter_set_name):
        desc = None
        data = None
        for ps in self.settings.get("accessibleParameterSetDescs", []):
            if ps["id"] == parameter_set_name:
                desc = ps
        for ps in self.settings.get("parameterSets", []):
            if ps["name"] == parameter_set_name:
                data = ps
        if desc is None:
            return None
        if data is None:
            # make  a fake one, for example for project-level settings
            data = {'type':desc["elementType"]}
        presets_of_parameter_set = [p for p in self.settings["presets"] if p["type"] == data["type"]]
        return self._make_parameter_set(desc, data, presets_of_parameter_set)

    def _make_parameter_set(self, desc, data, presets_of_parameter_set):
        return DSSPluginParameterSet(self, desc, data, presets_of_parameter_set)

    def save(self):
        """
        Save the settings to DSS.
        """
        self.client._perform_empty("POST", "/plugins/%s/settings" % (self.plugin_id),
                                   params={"projectKey": self.project_key},
                                   body=self.settings)


class DSSPluginSettings(DSSPluginSettingsBase):
    """
    The settings of a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPlugin.get_settings`.
    """

    def __init__(self, client, plugin_id, settings):
        super().__init__(client, plugin_id, settings)

    def set_code_env(self, code_env_name):
        """
        Set the name of the code env to use for this plugin.

        :param string code_env_name: name of a code env 
        """
        self.settings["codeEnvName"] = code_env_name

    def list_parameter_sets(self):
        """
        List the parameter sets defined in this plugin.

        :rtype: list[:class:`DSSPluginParameterSet`]
        """
        return self._list_parameter_sets()

    def get_parameter_set(self, parameter_set_name):
        """
        Get a parameter set in this plugin.

        :param string parameter_set_name: name of the parameter set

        :return: a handle on the parameter set
        :rtype: :class:`DSSPluginParameterSet`
        """
        return self._get_parameter_set(parameter_set_name)

    def _make_parameter_set(self, desc, data, presets_of_parameter_set):
        return DSSPluginParameterSet(self, desc, data, presets_of_parameter_set)

class DSSPluginProjectSettings(DSSPluginSettingsBase):
    """
    The project-level settings of a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPlugin.get_project_settings`.
    """
    
    def __init__(self, client, plugin_id, settings, project_key):
        super().__init__(client, plugin_id, settings, project_key)

    def start_save(self):
        """
        Save the settings to DSS.
        Returns with a future representing the post actions done asynchronously (e.g. rebuild cde image for visual recipes)

        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the save post process
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        resp = self.client._perform_json("POST", "/plugins/%s/settings/future" % (self.plugin_id), body=self.settings)
        return DSSFuture.from_resp(self.client, resp)


    def list_parameter_sets(self):
        """
        List the parameter sets defined in this plugin.

        :rtype: list[:class:`DSSPluginProjectParameterSet`]
        """
        return self._list_parameter_sets()

    def get_parameter_set(self, parameter_set_name):
        """
        Get a parameter set in this plugin.

        :param string parameter_set_name: name of the parameter set

        :return: a handle on the parameter set
        :rtype: :class:`DSSPluginProjectParameterSet`
        """
        return self._get_parameter_set(parameter_set_name)

    def _make_parameter_set(self, desc, data, presets_of_parameter_set):
        return DSSPluginProjectParameterSet(self, desc, data, presets_of_parameter_set)

class DSSPluginParameterSetBase(object):
    """
    A parameter set in a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPluginSettings.get_parameter_set()` or :meth:`DSSPluginSettings.list_parameter_sets().
        For project-level settings, use :meth:`DSSPluginProjectSettings.get_parameter_set()` or :meth:`DSSPluginProjectSettings.list_parameter_sets()`

    The values in this class can be modified directly, and changes will be taken into account 
    when calling :meth:`DSSPluginSettings.save()` (or :meth:`DSSPluginProjectSettings.save()`
    """
    def __init__(self, plugin_settings, desc, settings, presets):
        self._plugin_settings = plugin_settings
        self._desc = desc
        self._settings = settings
        self._presets = presets

    @property
    def desc(self):
        """
        Get the raw definition of the parameter set.

        :return: a parameter set definition, as a dict. The parameter set's contents is a **desc** sub-dict. 
                 See `the doc <https://doc.dataiku.com/dss/latest/plugins/reference/params.html#preset-parameters>`_

        :rtype: dict
        """
        return self._desc

    @property
    def settings(self):
        """
        Get the settings of the parameter set.

        These settings control the behavior of the parameter set, and comprise notably the permissions,
        but not the presets of this parameter set.

        :return: the settings of the parameter set, as a dict. The parameter set's settings consist of the permissions 
                 controlling whether the presets of the parameter set can be created inline or at the project level.

        :rtype: dict
        """
        return self._settings

    def list_preset_names(self):
        """
        List the names of the presets of this parameter set.

        :rtype: list[string]
        """
        return [p["name"] for p in self._presets]

    def list_presets(self):
        """
        List the presets of this parameter set.

        :rtype: list[:class:`DSSPluginPreset`]
        """
        return [DSSPluginPreset(self._plugin_settings, p, self._desc) for p in self._presets]

    def get_preset(self, preset_name):
        """
        Get a preset of this parameter set.

        :param string preset_name: name of a preset

        :return: a handle on the preset definition, or None if the preset doesn't exist
        :rtype: :class:`DSSPluginPreset`
        """
        for p in self._presets:
            if p["name"] == preset_name:
                return DSSPluginPreset(self._plugin_settings, p, self._desc)
        return None

    def delete_preset(self, preset_name):
        """
        Remove a preset from this plugin's settings

        :param string preset_name: name for the preset to remove
        """
        preset = self.get_preset(preset_name)
        if preset is not None:
            # note: preset out of get_preset is a DSSPluginPreset, so it's
            # not the object present in the lists
            self._plugin_settings.settings["presets"].remove(preset._settings)
            self._presets.remove(preset._settings)
        else:
            raise Exception("Preset '%s' not found" % preset_name)

    def create_preset(self, preset_name, with_defaults=False):
        """
        Create a new preset of this parameter set in the plugin settings.

        :param string preset_name: name for the preset to create
        :param bool with_defaults: if True, fill the new preset with the default value for each parameter

        :return: a preset definition, as a :class:`DSSPluginPreset` (see :meth:`get_preset()`)
        :rtype: dict
        """
        for p in self._presets:
            if p["name"] == preset_name:
                raise Exception("A preset of the same name already exists")
        new_preset = {"name":preset_name, "type":self._settings["type"], "config":{}, "pluginConfig":{}, "defaultPermission":{}, "permissions":[]}
        if with_defaults:
            for p in self._desc["desc"]["params"]:
                v = p.get("defaultValue")
                if v is not None:
                    new_preset["config"][p["name"]] = v
            for p in self._desc["desc"]["pluginParams"]:
                v = p.get("defaultValue")
                if v is not None:
                    new_preset["pluginConfig"][p["name"]] = v
        self._plugin_settings.settings["presets"].append(new_preset)
        self._presets.append(new_preset)
        return self.get_preset(preset_name)

    def save(self):
        """
        Save the settings to DSS.
        """
        self._plugin_settings.save()


class DSSPluginParameterSet(DSSPluginParameterSetBase):
    """
    A parameter set in a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPluginSettings.get_parameter_set()` or :meth:`DSSPluginSettings.list_parameter_sets()`.

    The values in this class can be modified directly, and changes will be taken into account
    when calling :meth:`DSSPluginSettings.save()`
    """
    def __init__(self, plugin_settings, desc, settings, presets):
        self._plugin_settings = plugin_settings
        self._desc = desc
        self._settings = settings
        self._presets = presets

    @property
    def definable_inline(self):
        """
        Whether presets for this parameter set can be defined directly in the form of the datasets, recipes, ...

        :rtype: bool
        """
        return self._settings["defaultPermission"].get("definableInline", False)

    @definable_inline.setter
    def definable_inline(self, definable):
        self._settings["defaultPermission"]['definableInline'] = definable

    @property
    def definable_at_project_level(self):
        """
        Whether presets for this parameter set can be defined at the project level

        :rtype: bool
        """
        return self._settings["defaultPermission"].get("definableAtProjectLevel", False)

    @definable_at_project_level.setter
    def definable_at_project_level(self, definable):
        self._settings["defaultPermission"]['definableAtProjectLevel'] = definable


class DSSPluginProjectParameterSet(DSSPluginParameterSetBase):
    """
    A parameter set in a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPluginProjectSettings.get_parameter_set()` or :meth:`DSSPluginProjectSettings.list_parameter_sets()`


    The values in this class can be modified directly, and changes will be taken into account
    when calling or :meth:`DSSPluginProjectSettings.save()`
    """
    def __init__(self, plugin_settings, desc, settings, presets):
        self._plugin_settings = plugin_settings
        self._desc = desc
        self._settings = settings
        self._presets = presets


class DSSPluginPreset(dict):
    """
    A preset of a parameter set in a plugin.

    .. important::

        Do not instantiate directly, use :meth:`DSSPluginParameterSet.get_preset()` , :meth:`DSSPluginParameterSet.list_presets()`
        or :meth:`DSSPluginParameterSet.create_preset()`. For project-level presets, use :meth:`DSSPluginProjectParameterSet.get_preset()` ,
        :meth:`DSSPluginProjectParameterSet.list_presets()` or :meth:`DSSPluginProjectParameterSet.create_preset()`

    The values in this class can be modified directly, and changes will be taken into account
    when calling :meth:`DSSPluginSettings.save()`.
    """
    def __init__(self, plugin_settings, settings, parameter_set_desc):
        super(DSSPluginPreset, self).__init__(settings)
        self._plugin_settings = plugin_settings
        self._settings = settings
        self._parameter_set_desc = parameter_set_desc

    def __repr__(self):
        return "DSSPluginPreset(name={}, plugin={}, parameter_set={})".format(
            self._settings["name"],
            self._plugin_settings.plugin_id,
            self._parameter_set_desc["id"]
        )

    def get_raw(self):
        """
        Get the raw settings of the preset object.

        .. note::

            This method returns a reference to the preset, not a copy. Changing values in the reference
            then calling :meth:`save()` results in these changes being saved.

        :return: the preset's complete settings
        :rtype: dict
        """
        return self._settings

    @property
    def name(self):
        """
        Get the name of the preset.

        :return: the name of the preset
        :rtype: string
        """
        return self._settings["name"]

    @property
    def config(self):
        """
        Get the raw config of the preset object.

        .. note::

            This method returns a reference to the preset, not a copy. Changing values in the reference
            then calling :meth:`save()` results in these changes being saved.

        :return: the preset's config as a dict. Each parameter of the parameter set is a field in the dict.
        :rtype: dict
        """
        return self._settings["config"]

    @property
    def plugin_config(self):
        """
        Get the raw admin-level config of the preset object. Admin-level config parameters are not shown in
        the UI to non-admin users.

        .. note::

            This method returns a reference to the preset, not a copy. Changing values in the reference
            then calling :meth:`save()` results in these changes being saved.

        :return: the preset's admin config as a dict. Each parameter of the parameter set is a field in the dict.
        :rtype: dict
        """
        return self._settings["pluginConfig"]

    @property
    def owner(self):
        """
        The DSS user that owns this preset

        :rtype: string
        """
        return self._settings["owner"]

    @owner.setter
    def owner(self, login):
        self._settings["owner"] = login

    @property
    def usable_by_all(self):
        """
        Whether the preset is usable by any DSS user

        :rtype: bool
        """
        return self._settings["defaultPermission"].get("use", False)

    @usable_by_all.setter
    def usable_by_all(self, use):
        self._settings["defaultPermission"]['use'] = use

    def get_permission_item(self, group):
        """
        Get permissions on the preset for a given group

        :param string group: the name of the DSS group you want to check permissions for.
        :return: the permissions as a dict
        :rtype: dict
        """
        if group is None:
            return self._settings["defaultPermission"]
        else:
            for p in self._settings["permissions"]:
                if p["group"] == group:
                    return p
            return None

    def is_usable_by(self, group):
        """
        Get whether the preset is usable by DSS users in a group

        :param string group: the name of the DSS group you want to check permissions for.

        :return: True if the preset can be used by DSS users belonging to *group*. If *group* is None
                 then returns True if the preset can be used by any DSS user (like :meth:`usable_by_all`)
        :rtype: bool
        """
        permission_item = self.get_permission_item(group)
        if permission_item is None:
            return self._settings["defaultPermission"]["use"]
        else:
            return permission_item["use"]

    def set_usable_by(self, group, use):
        """
        Set whether the preset is usable by DSS users in a group

        :param string group: the name of the DSS group you want to change permissions for.
        :param bool use: whether the group should be allowed to use the preset or not
        """
        permission_item = self.get_permission_item(group)
        if permission_item is None:
            # group can't be None here
            self._settings["permissions"].append({"group":group, "use":use})
        else:
            permission_item["use"] = use

    def save(self):
        """
        Save the settings to DSS.
        """
        self._plugin_settings.save()

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

    def get_project_settings(self, project_key):
        """
        Get the project-level settings.

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :return: a handle on the project-level settings
        :rtype: :class:`DSSPluginProjectSettings`
        """
        settings = self.client._perform_json("GET", "/plugins/%s/settings" % (self.plugin_id),
                                             params={"projectKey": project_key})
        return DSSPluginProjectSettings(self.client, self.plugin_id, settings, project_key)

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

        :param string python_interpreter: which version of python to use. Possible values: PYTHON27, PYTHON34, PYTHON35, PYTHON36, PYTHON37, PYTHON38, PYTHON39, PYTHON310, PYTHON311, PYTHON312
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

    def start_update_from_zip(self, fp):
        """
        Update the plugin from a plugin archive (as a file object).
        Returns immediately with a future representing the process done asynchronously

        .. note::

            This call requires an API key with either:

                * DSS admin permissions
                * permission to develop plugins
                * tied to a user with admin privileges on the plugin

        :param file-like fp: A file-like object pointing to a plugin archive zip
        :return: A :class:`~dataikuapi.dss.future.DSSFuture` representing the update process
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        files = {'file': fp }
        f = self.client._perform_json("POST", "/plugins/%s/actions/future/updateFromZip" % (self.plugin_id), files=files)
        return DSSFuture.from_resp(self.client, f)

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
