from .dataset import DSSDataset
from .recipe import DSSRecipe
from .managedfolder import DSSManagedFolder
from .savedmodel import DSSSavedModel
from .job import DSSJob
from .scenario import DSSScenario
from .apiservice import DSSAPIService
import sys

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

        Returns a dict with two keys:
        - usages, a list of (elementKind, elementType, objectType, projectKey, objectId) tuples
        - missingTypes, a list of (missingType, objectType, projectKey, objectId) tuples

        Each element of the usages list contains:
        - an elementKind of the plugin element, such as webapps, python-probes, python-checks, etc.
        - an elementType of the plugin element,
        - the objectType and objectId of the object using this plugin element, along with their projectKey,
        if pertinent. Some objects, for instance clusters, are not contained in a project.

        Some custom types may not be found during the analysis. This typically occurs when a plugin was removed,
        while still being used. This prevents further analysis of the object relying on this type and may hide
        some uses of the plugin. Thus, those missingTypes are enumerated in the missingTypes list, which
        includes the missingType along with the same information on the object as for usages.

        :param str project_key: optional key of project where to look for usages. Default is None and looking in all projects.
        :return: dict
        """
        params = {}
        if project_key:
            params["projectKey"] = project_key
        return self.client._perform_json("POST", "/plugins/{pluginId}/actions/listUsages".format(pluginId=self.plugin_id), body=params)

    def prepare_delete(self):
        """
        Request pre-deletion checks, as aggregated information on the usage of the plugin.

        Information is provided as a dict with the following entries:
        - projectCount: count of projects using at least an element of this plugin
        - usedElemCount: count of elements of this plugin in use
        - objectAnalysisErrors: count of errors encountered while analyzing usages.

        Detailed information can be obtained by calling :func:`list_usages`.
        :return: dict
        """

        return self.client._perform_json("POST", "/plugins/{pluginId}/actions/prepareDelete".format(pluginId=self.plugin_id))

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
