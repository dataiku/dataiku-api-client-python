from ..utils import DataikuException
import sys

if sys.version_info >= (3,0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote

class DSSLibrary(object):
    """
    A handle to manage the library of a project
    It saves locally a copy of taxonomy to help navigate in the library
    All modifications done through this object and related library items are done locally and on remote.
    Note: Taxonomy modifications done outside this library are not reflected locally.
          You should reload the library in this case.
    """
    def __init__(self, client, project_key):
        """Do not call directly, use :meth:`dataikuapi.dss.project.DSSProject.get_library`"""
        self.client = client
        self.project_key = project_key
        self.root = self._build_node_("/", None, self.client._perform_json("GET", "/projects/%s/libraries/contents" % (self.project_key)))

    def _build_node_(self, name, parent, children):
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
            item._add_child_(self._build_node_(child["name"], item, child.get("children")))
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
        return self.root.get_file(path)

    def get_folder(self, path):
        """
        Retrieves a folder in the library
        :param: str path: the folder path
        :returns: the folder in the given path
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        return self.root.get_folder(path)


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
        """Do not call directly, use :meth:`dataikuapi.dss.projectlibrary.DSSLibrary.get_file()`
        or :meth:`dataikuapi.dss.projectlibrary.DSSLibrary.get_folder()`"""
        self.client = client
        self.project_key = project_key
        self.name = name
        self.parent = parent
        self.children = children

    @property
    def path(self):
        if self.parent is None:
            return self.name
        return self._clean_path_(self.parent.path + "/" + self.name)

    def is_root(self):
        return self.parent is None and self.name == "/"

    def _clean_path_(self, path):
        return path.replace("//", "/")

    def delete(self):
        """
        Deletes this item from library
        """
        if self.is_root():
            raise Exception("Cannot delete root folder")

        self.client._perform_empty("DELETE", "/projects/%s/libraries/contents/%s" % (self.project_key, dku_quote_fn(self.path)))
        self.parent._remove_child_(self)
        self.parent = None

    def rename(self, new_name):
        """
        Rename the folder
        :param: str new_name: the new name of the item
        """
        if self.is_root():
            raise Exception("Cannot rename root folder")

        self.client._perform_empty("POST", "/projects/%s/libraries/contents-actions/rename/" % self.project_key, body={"oldPath": self.path, "newName": new_name})
        self.name = new_name

    def move_to(self, destination_folder):
        """
        Move a library item to another folder
        :param: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder` destination_folder: the folder where we want to move the current item
        """
        if self.is_root():
            raise DataikuException("Cannot move root folder")
        if destination_folder is None:
            raise DataikuException("Destination folder cannot be None")
        if not isinstance(destination_folder, DSSLibraryFolder):
            raise DataikuException("Destination should be a folder")

        self.client._perform_empty("POST", "/projects/%s/libraries/contents-actions/move" % self.project_key,
                                   body={"oldPath": self.path, "newPath": destination_folder.path})
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
        Create a new file in the library folder
        :param: str file_name: the file name
        :returns: the new file
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFile`
        """
        file_name = file_name.strip()
        if self.is_root():
            new_path = dku_quote_fn(file_name)
        else:
            new_path = dku_quote_fn(self.path + "/" + file_name)
        try:
            existing_file = self.client._perform_json("GET", "/projects/%s/libraries/contents/%s" % (self.project_key, new_path))
        except:
            existing_file = None
        finally:
            if existing_file is not None:
                raise DataikuException("File %s already exists" % file_name)
        self.client._perform_empty("POST", "/projects/%s/libraries/contents/%s" % (self.project_key, new_path))
        return self._create_library_item_(self, file_name, True)

    def add_folder(self, folder_name):
        """
        Create a folder in the library
        :param: str folder_name: the name of the folder to add
        :returns: the new folder
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        folder_name = folder_name.strip()
        if self.is_root():
            new_path = dku_quote_fn(folder_name)
        else:
            new_path = dku_quote_fn(self.path + "/" + folder_name)
        self.client._perform_empty("POST", "/projects/%s/libraries/folders/%s" % (self.project_key, new_path))
        return self._create_library_item_(self, folder_name, False)


    def _create_library_item_(self, item, path, create_file):
        if path.startswith("/"):
            path = path[1:]

        path_split = path.split('/', 1)

        if path_split[0] == ".":
            return self._create_library_item_(item, path_split[1], create_file)

        if path_split[0] == "..":
            return self._create_library_item_(item.parent, path_split[1], create_file)

        if len(path_split) > 1 and path_split[1]:
            # Check if the path is a child's sub path
            for c in item.children:
                if c.name == path_split[0]:
                    return self._create_library_item_(c, path_split[1], create_file)
            # Path element not present in folder. We should create it
            folder = DSSLibraryFolder(self.client, self.project_key, path_split[0], item, set())
            item.children.add(folder)
            return self._create_library_item_(folder, path_split[1], create_file)
        else:
            # It is a direct child
            if create_file:
                new_item = DSSLibraryFile(self.client, self.project_key, path_split[0], item)
            else:
                new_item = DSSLibraryFolder(self.client, self.project_key, path_split[0], item, set())
            item.children.add(new_item)
            return new_item

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

    def get_file(self, path):
        """
        Retrieves a file in the library
        :param: str path: the file path
        :returns: the file in the given path
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFile`
        """
        item = self._get_item_recursively_(self, path)
        if item is not None:
            if item.children is None:
                return item
            else:
                raise DataikuException("The item %s is a folder, not a file " % path)
        return None

    def get_folder(self, path):
        """
        Retrieves a folder in the library
        :param: str path: the folder path
        :returns: the folder in the given path
        :rtype: :class:`dataikuapi.dss.projectlibrary.DSSLibraryFolder`
        """
        item = self._get_item_recursively_(self, path)
        if item is not None:
            if item.children is not None:
                return item
            else:
                raise DataikuException("The item %s is a file, not a folder " % path)
        return None

    def _get_item_recursively_(self, item, path):
        if not path or item is None:
            return None
        if path == "/":
            return item

        if path.startswith("/"):
            path = path[1:]
        path_split = path.split('/', 1)

        if path_split[0] == ".":
            if len(path_split) > 1:
                return self._get_item_recursively_(item, path_split[1])
            else:
                return item

        if path_split[0] == "..":
            if item.parent is None:
                raise DataikuException("Path %s is not valid" % path)
            if len(path_split) > 1:
                return self._get_item_recursively_(item.parent, path_split[1])
            else:
                return item.parent

        if item.children is None:
            return None

        for c in item.children:
            if c.name == path_split[0]:
                if len(path_split) > 1:
                    return self._get_item_recursively_(c, path_split[1])
                else:
                    return c
        return None

class DSSLibraryFile(DSSLibraryItem):
    """
    A handle to manage a library file
    """
    def __init__(self, client, project_key, name, parent):
        """Do not call directly, use :meth:`dataikuapi.dss.projectlibrary.DSSLibrary.get_file`"""
        super(DSSLibraryFile, self).__init__(client, project_key, name, parent, None)

    def read(self):
        """
        Get the file contents from DSS
        :returns: the contents of the file
        """
        return self.client._perform_json("GET", "/projects/%s/libraries/contents/%s" % (self.project_key, dku_quote_fn(self.path)))["data"]

    def write(self, data):
        """
        Updates the the contents of the file with the given data
        """
        self.client._perform_empty("POST", "/projects/%s/libraries/contents/%s" % (self.project_key, dku_quote_fn(self.path)), raw_body=data)
