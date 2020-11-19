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
    # Plugin settings
    ########################################################

    def get_settings(self):
        """
        Get the plugin settings
        """
        return self.client._perform_json("GET", "/plugins/%s/settings" % (self.plugin_id))

    def set_settings(self, plugin_settings):
        """
        Set the plugin settings

        :param plugin_settings: the new plugin settings
        """
        return self.client._perform_json("POST", "/plugins/%s/settings" % (self.plugin_id), body=plugin_settings)

    ########################################################
    # Plugin code env
    ########################################################

    def create_code_env(self):
        """
        Create a new plugin code-env
        """
        return self.client._perform_json("POST", "/plugins/%s/code-env/actions/create" % (self.plugin_id))

    def update_code_env(self):
        """
        Update the current plugin code-env
        """
        return self.client._perform_json("POST", "/plugins/%s/code-env/actions/update" % (self.plugin_id))

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

    def delete_file(self, path):
        """
        Get a file from the plugin folder
        
        Args:
            path: the name of the file, from the root of the plugin

        Returns:
            the file's content, as a stream
        """
        return self.client._perform_raw("DELETE", "/plugins/%s/contents/%s" % (self.plugin_id, path)).raw

    ########################################################
    # Dev plugin Git integration
    ########################################################

    def pull_rebase(self):
        """
        Pull the latest version from the current branch of the plugin. Aborts if merge fails.
        """
        return self.client._perform_json("POST", "/plugins/%s/actions/pullRebase" % (self.plugin_id))

    def push(self):
        """
        Push from the current branch of the plugin.
        """
        return self.client._perform_json("POST", "/plugins/%s/actions/push" % (self.plugin_id))

    def fetch(self):
        """
        Fetch new content from remote repository.
        """
        return self.client._perform_json("POST", "/plugins/%s/actions/fetch" % (self.plugin_id))

    def reset_to_local_head_state(self):
        """
        Drop uncommitted changes and resets the current branch to local HEAD.
        """
        return self.client._perform_json("POST", "/plugins/%s/actions/resetToLocalHeadState" % (self.plugin_id))

    def reset_to_remote_head_state(self):
        """
        Delete all of your non-pushed work on the current branch and resets it to the remote state.
        """
        return self.client._perform_json("POST", "/plugins/%s/actions/resetToRemoteHeadState" % (self.plugin_id))

    def get_remote(self):
        """
        Gets the URL of the Git remote origin for your local repository.
        """
        return self.client._perform_json("GET", "/plugins/%s/gitRemote" % (self.plugin_id))

    def set_remote(self, repository_URL):
        """
        Sets the URL of the Git remote origin for your local repository.

        :param str repository_URL: the repository URL
        """
        return self.client._perform_json("POST", "/plugins/%s/gitRemote" % (self.plugin_id), body={'repositoryUrl': repository_URL})

    def delete_remote(self):
        """
        Removes the URL of the Git remote origin for your local repository.
        """
        return self.client._perform_json("DELETE", "/plugins/%s/gitRemote" % (self.plugin_id))

    def get_branches(self):
        """
        Retrieves the list of available branches on your repository.
        """
        return self.client._perform_json("GET", "/plugins/%s/gitBranches" % (self.plugin_id))

    def get_active_branch(self):
        """
        Gets the active branch on your local repository.
        """
        return self.client._perform_json("GET", "/plugins/%s/activeGitBranch")

    def set_active_branch(self, branch, creation=False):
        """
        Sets the active branch on your local repository.

        :param str branch: the branch name
        :param bool creation: should it be created before checkout
        """
        return self.client._perform_json("POST", "/plugins/%s/activeGitBranch" % (self.plugin_id), body={'branch': branch, 'creation': creation})

