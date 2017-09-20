from .dataset import DSSDataset
from .recipe import DSSRecipe
from .managedfolder import DSSManagedFolder
from .savedmodel import DSSSavedModel
from .job import DSSJob
from .scenario import DSSScenario
from .apiservice import DSSAPIService
import sys

class DSSPlugin(object):
    """
    A plugin on the DSS instance
    """
    def __init__(self, client, plugin_id):
       self.client = client
       self.plugin_id = plugin_id

    ########################################################
    # plugin upload/update as zip
    ########################################################

    def upload(self, file_path):
        """
        Upload the given file as a plugin

        Note: this call requires an API key with admin rights
        
        :param: file_path : the path to the zip file of the plugin
        """
        with open(file_path, 'rb') as f:
            return self.client._perform_json_upload("POST", "/plugins/%s/upload" % (self.plugin_id), 'plugin.zip', f).text

    def update(self, file_path):
        """
        Update the plugin with the given file

        Note: this call requires an API key with admin rights
        
        :param: file_path : the path to the zip file of the plugin
        """
        with open(file_path, 'rb') as f:
            return self.client._perform_json_upload("POST", "/plugins/%s/update" % (self.plugin_id), 'plugin.zip', f).text

    ########################################################
    # Managing the dev plugin's contents
    ########################################################

    def list_files(self):
        """
        Get the hierarchy of files in the plugin
        
        Returns:
            the plugins's contents
        """
        return self.client._perform_json("GET", "/plugins/%s/contents" % (self.plugin_id))

    def get_file(self, path):
        """
        Get a file from the plugin folder
        
        Args:
            path: the name of the file, from the root of the plugin

        Returns:
            the file's content, as a stream
        """
        return self.client._perform_raw("GET", "/plugins/%s/contents/%s" % (self.plugin_id, path)).raw

    def put_file(self, path, f):
        """
        Update a file in the plugin folder
        
        Args:
            f: the file contents, as a stream
            path: the name of the file, from the root of the plugin
        """

        file_name = path.split('/')[-1]
        data = f.read() # eat it all, because making it work with a path variable and a MultifilePart in swing looks complicated
        return self.client._perform_empty("POST", "/plugins/%s/contents/%s" % (self.plugin_id, path), raw_body=data)

        