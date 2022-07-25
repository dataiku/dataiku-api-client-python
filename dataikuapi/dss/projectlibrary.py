class DSSLibrary(object):
    """
    A handle to manage the wiki of a project
    """
    def __init__(self, client, project_key):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_library`"""
        self.client = client
        self.project_key = project_key

    def list_files(self):
        """
        Get the hierarchy of files in the library
        """
        return self.client._perform_json("GET", "/projects/%s/libraries/contents" % (self.project_key))

    def get_file(self, path):
        """
        Get a file from the libraries folder

        :param str path: the path of the file, relative to the root of the library

        :return: a file-like object containing the file's content
        """
        return self.client._perform_json("GET", "/projects/%s/libraries/contents/%s" % (self.project_key, path))

    def put_file(self, path, f):
        """
        Update a file in the library folder

        :param file-like f: the file contents, as a file-like object
        :param str path: the path of the file, relative ot the root of the library
        """
        data = f.read()
        return self.client._perform_empty("POST", "/projects/%s/libraries/contents/%s" % (self.project_key, path), raw_body=data)

    def delete_file(self, path):
        """
        Delete a file in the library folder

        :param str path: the path of the file, relative ot the root of the library
        """
        return self.client._perform_empty("DELETE", "/projects/%s/libraries/contents/%s" % (self.project_key, path))

    def add_folder(self, path):
        """
        Create a folder in the library

        :param str path: the path of the folder, relative ot the root of the library
        """
        return self.client._perform_empty("POST", "/projects/%s/libraries/folders/%s" % (self.project_key, path))

    def rename_file(self, path, new_name):
        """
        Rename a file/folder in the library

        :param str path: the path of the file/folder, relative ot the root of the library
        :param str new_name: the parameters containing the new name of the file/folder
        """
        return self.client._perform_empty("POST", "/projects/%s/libraries/contents/rename/%s" % (self.project_key, path), body={"newName": new_name})

    def move_file(self, path, new_path):
        """
        Move a file/folder in the library

        :param str path: the path of the file/folder, relative ot the root of the library
        :param str new_path: the new path relative at the root of the library
        """
        return self.client._perform_empty("POST", "/projects/%s/libraries/contents/move/%s" % (self.project_key, path), body={"newPath": new_path})

