from ..utils import DataikuException


class DSSLibrary(object):
    """
    A handle to manage the library items of a project
    It saves locally a copy of taxonomy to help navigate in the library
    All modifications done through this object and related library items are done locally and on remote.

    Note: Taxonomy modifications done outside this library are not reflected locally.
          You should reload the library in this case.
    """
    def __init__(self, client, project_key):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_library`"""
        self.client = client
        self.project_key = project_key
        self.reload()

    def reload(self):
        """
        Reload the library hierarchy.
        """
        taxonomy = self.client._perform_json("GET", "/projects/%s/libraries/contents" % (self.project_key))
        self.root = self.__build_node__("/", None, taxonomy)

    def __build_node__(self, name, parent, children):
        """
        Helper that builds the tree recursively

        :param: str name: the name of the library item
        :param: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder` parent: the parent of the library item
        :param: list children: the children of the library item
        :returns: a new node corresponding to an item in the library
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryItem`
        """
        if children is None:
            return DSSLibraryFile(self.client, self.project_key, name, parent)

        item = DSSLibraryFolder(self.client, self.project_key, name, parent, set())
        for child in children:
            item._add_child_(self.__build_node__(child["name"], item, child.get("children")))
        return item

    def list(self, folder_path="/"):
        """
        Lists the contents in the given library folder or on the root if no folder is given.

        :param: str folder_path: the folder path (optional). If no path is given, it is defaulted to the root path.
        :returns: the list of contents in the library folder
        :rtype: list of :class:`dataikuapi.dss.projectlibrary.DSSLibraryItem`
        """
        return self.get_folder(folder_path).list()

    def get_file(self, path):
        """
        Retrieves a file in the library

        :param: str path: the file path
        :returns: the file in the given path
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFile`
        """
        item = self.get_item(path)
        if item is not None:
            if item.children is None:
                return item
            else:
                raise DataikuException("The item %s is not a file : " % path)
        return None

    def get_folder(self, path):
        """
        Retrieves a folder in the library

        :param: str path: the folder path
        :returns: the folder in the given path
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        item = self.get_item(path)
        if item is not None:
            if item.children is not None:
                return item
            else:
                raise DataikuException("The item %s is not a folder : " % path)
        return None

    def get_item(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return self.__get_item_helper__(self.root, path)

    def __get_item_helper__(self, item, path):
        if item.name == path:
            return item
        if item.children is None:
            return None
        if path.startswith(item.name):
            sub_path = path[len(item.name):]
            if sub_path.startswith("/"):
                sub_path = sub_path[1:]
            for c in item.children:
                sub_child = self.__get_item_helper__(c, sub_path)
                if sub_child is not None:
                    return sub_child
        return None


    def add_file(self, file_name):
        """
        Create a file in the library root folder

        :param: str file_name: the file name
        :returns: the new file
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFile`
        """
        return self.root.add_file(file_name)

    def add_folder(self, folder_name):
        """
        Create a folder in the library root folder

        :param: str file_name: the file name
        :returns: the new folder
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        return self.root.add_folder(folder_name)

class DSSLibraryItem(object):

    """
    A handle to manage a library item
    """
    def __init__(self, client, project_key, name, parent, children):
        """Do not call directly, use :class:`dataikuapi.dss.projectlibrary.DSSLibrary`"""
        self.client = client
        self.project_key = project_key
        self.name = name
        self.parent = parent
        self.children = children

    def get_path(self):
        if self.parent is None:
            return self.name
        return self._clean_path_(self.parent.get_path() + "/" + self.name)

    def _clean_path_(self, path):
        return path.replace("//", "/")

    def delete(self):
        """
        Deletes this item from library
        """
        self.client._perform_empty("DELETE", "/projects/%s/libraries/contents/%s" % (self.project_key, self.get_path()))
        self.parent._remove_child_(self)

    def rename(self, new_name):
        """
        Rename the folder

        :param: str new_name: the new name of the item
        """
        self.client._perform_empty("PUT", "/projects/%s/libraries/contents/rename/%s" % (self.project_key, self.get_path()), body={"newName": new_name})
        self.name = new_name

    def move_to(self, destination_folder):
        """
        Move a library item to a folder

        :param: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder` destination_folder: the folder where we want to move the current item
        """
        self.client._perform_empty("PUT", "/projects/%s/libraries/contents/move/%s" % (self.project_key, self.get_path()),
                                   body={"newPath": destination_folder.get_path()})
        self.parent._remove_child_(self)
        destination_folder._add_child_(self)
        self.parent = destination_folder


class DSSLibraryFolder(DSSLibraryItem):
    """
    A handle to manage a library folder
    """
    def __init__(self, client, project_key, name, parent, children):
        """Do not call directly, use :class:`dataikuapi.dss.projectlibrary.DSSLibrary.get_folder`"""
        super(DSSLibraryFolder, self).__init__(client, project_key, name, parent, children)

    def get_child(self, name):
        """
        Retrieve the sub item by its name

        :param: str name: the name of the sub item
        :returns: the sub item
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryItem`
        """
        for c in self.children:
            if c.name == name:
                return c
        return None

    def add_file(self, file_name):
        """
        Create a file in the library folder

        :param: str file_name: the file name
        :returns: the new file
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFile`
        """
        if "/" in file_name:
            raise DataikuException("File name %s contains invalid character '/'" % file_name)
        new_path = self._clean_path_(self.get_path() + "/" + file_name)
        self.client._perform_empty("POST", "/projects/%s/libraries/contents/%s" % (self.project_key, new_path))
        file = DSSLibraryFile(self.client, self.project_key, file_name, self)
        self.children.add(file)
        return file

    def add_folder(self, folder_name):
        """
        Create a folder in the library

        :param: str folder_name: the name of the folder to add
        :returns: the new folder
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        if "/" in folder_name:
            raise DataikuException("Folder name %s contains invalid character '/'" % folder_name)
        new_path = self._clean_path_(self.get_path() + "/" + folder_name)
        self.client._perform_empty("POST", "/projects/%s/libraries/folders/%s" % (self.project_key, new_path))
        folder = DSSLibraryFolder(self.client, self.project_key, folder_name, self, set())
        self.children.add(folder)
        return folder

    def list(self):
        """
        Gets the contents of this folder sorted by name

        :returns: a sorted list of items
        :rtype: list of :class:`dataikuapi.dss.projectlibrary.DSSLibraryItem`
        """
        return sorted(list(self.children), key=lambda x: x.name)

    def _add_child_(self, child):
        """
        Adds the given child from this folder
        """
        self.children.add(child)

    def _remove_child_(self, child):
        """
        Removes the given child from this folder
        """
        self.children.remove(child)


class DSSLibraryFile(DSSLibraryItem):

    """
    A handle to manage a library file
    """
    def __init__(self, client, project_key, name, parent):
        """Do not call directly, use :meth:`dataikuapi.dss.projectlibrary.DSSLibrary.get_file`"""
        super(DSSLibraryFile, self).__init__(client, project_key, name, parent, None)

    def get_data(self):
        """
        Get the file contents

        :returns: the contents of the file
        :rtype: str
        """
        return self.client._perform_json("GET", "/projects/%s/libraries/contents/%s" % (self.project_key, self.get_path()))["data"]

    def save(self, file):
        """
        Updates the library file with the contents of the given file
        """
        data = file.read()
        self.client._perform_empty("POST", "/projects/%s/libraries/contents/%s" % (self.project_key, self.get_path()), raw_body=data)