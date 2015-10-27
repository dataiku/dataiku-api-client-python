from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader


class DSSManagedFolder(object):
    """
    A managed folder on the DSS instance
    """
    def __init__(self, client, project_key, odb_id):
        self.client = client
        self.project_key = project_key
        self.odb_id = odb_id

    ########################################################
    # Managed folder deletion
    ########################################################
    
    def delete(self):
        """
        Delete the managed folder
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id))



    ########################################################
    # Managed folder definition
    ########################################################
    
    def get_definition(self):
        """
        Get the definition of the managed folder
        
        Returns:
            the definition, as a JSON object
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/" % (self.project_key, self.odb_id))

    def set_definition(self, definition):
        """
        Set the definition of the managed folder
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/managedfolders/%s/" % (self.project_key, self.odb_id),
                body=definition)


    ########################################################
    # Managed folder contents
    ########################################################
    
    def list_contents(self):
        """
        Get the list of files in the managed folder
        
        Returns:
            the list of files, as a JSON object
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/contents" % (self.project_key, self.odb_id))

    def get_file(self, path):
        """
        Get a file from the managed folder
        
        Returns:
            the file's content, as a stream
        """
        return self.client._perform_raw(
                "GET", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, path))

    def put_file(self, name, f):
        """
        Upload the file to the managed folder
        
        Args:
            f: the file contents, as a stream
            name: the name of the file
        """
        return self.client._perform_json_upload(
                "POST", "/projects/%s/managedfolders/%s/contents/" % (self.project_key, self.odb_id),
                name, f)


