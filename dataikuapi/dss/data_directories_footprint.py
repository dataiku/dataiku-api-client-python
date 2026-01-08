
from .future import DSSFuture

class Footprint(dict):
    """
    Helper class to access values of the data directories footprint
    """
    def __init__(self, data):
        super(Footprint, self).__init__(data)

    @staticmethod
    def _wrap(f):
        if f is None:
            return None
        if isinstance(f, Footprint):
            return f
        return Footprint(f)
    
    @staticmethod
    def _nice_size(v, unit=None):
        if unit == 'B':
            return v
        elif unit == 'KB':
            return 1.0 * v / 1024
        elif unit == 'MB':
            return 1.0 * v / (1024 * 1024)
        elif unit == 'GB':
            return 1.0 * v / (1024 * 1024 * 1024)
        else:
            # smart mode
            if v < 1500:
                return '%d B' % v
            elif v < 1500 * 1024:
                return '%.2f KB' % (1.0 * v / 1024)
            elif v < 1500 * 1024 * 1024:
                return '%.2f MB' % (1.0 * v / (1024 * 1024))
            else:
                return '%.2f GB' % (1.0 * v / (1024 * 1024 * 1024))

    @property
    def size(self):
        """
        Get the size of this footprint item in bytes
        """
        return self.__getitem__("size")
    @property
    def human_readable_size(self):
        """
        Get a printable size of this footprint item
        """
        return self._nice_size(self.__getitem__("size"))
    def get_size(self, unit=None):
        """
        Get the size of this footprint item

        :param unit: desired unit in which the size should be expressed. Can be 'B', 'KB', 'MB', 'GB'. If not set,
                     a unit is chosen automatically
        :return: if *unit* is specified, a number; else, a string.
        """
        return self._nice_size(self.__getitem__("size"), unit)
    @property
    def nb_files(self):
        """
        Get the number of files in this footprint item
        """
        return self.__getitem__("nbFiles")
    @property
    def nb_folders(self):
        """
        Get the number of folders in this footprint item
        """
        return self.__getitem__("nbFolders")
    @property
    def nb_errors(self):
        """
        Get the number of errors in this footprint item.

        Errors happen when a file or folder inside the footprint item is not accessible, for example in case of permission
        issues.
        """
        return self.__getitem__("nbErrors")
    @property
    def details(self):
        """
        Drill down into this data directories footprint

        :return: a dict of footprints
        """
        if self.__contains__("items"):
            l = self.__getitem__("items")
            if l is None:
                l = []
            # this is a list of footprints. Find the type of item by checking the first one
            if len(l) == 0:
                return {}
            first = l[0]
            if 'projectKey' in first:
                # project footprints
                key_builder = lambda x : x.get("projectKey", "N/A")
            elif 'path' in first:
                # unknown data footprints
                key_builder = lambda x : x.get("path", "N/A")
            elif 'language' in first:
                # code env footprints
                key_builder = lambda x : '%s (%s)' % (x.get("name", "N/A"), x.get("language", "N/A"))
            elif 'type' in first:
                # plugin footprints
                key_builder = lambda x : '%s (%s)' % (x.get("name", "N/A"), x.get("type", "N/A"))
            else:
                # dunno what this is...
                raise Exception("Unexpected data directory footprint type")
            ret = {}
            for item in l:
                ret[key_builder(item)] = Footprint._wrap(item)
            return ret
        else:
            # skip nbFiles, nbErrors, size, projectKey, language... with the isinstance(..., dict) check
            return {k:Footprint._wrap(self.__getitem__(k)) for k in self.__iter__() if isinstance(self.__getitem__(k), dict)}

class DSSDataDirectoriesFootprint(object):
    """
    Handle to analyze the footprint of data directories

    .. warning::
        Do not create this class directly, use :meth:`dataikuapi.DSSClient.get_data_directories_footprint`
    """

    def __init__(self, client):
        self.client = client

    def _compute_footprint(self, url, show_summary_only=False, wait=True, value_wrapper=None):
        f = self.client._perform_json("GET", url, params={
            "summaryOnly": show_summary_only
        })
        future = DSSFuture.from_resp(self.client, f)
        if wait:
            res = future.wait_for_result()
            if value_wrapper is not None:
                return value_wrapper(res)
            else:
                return res
        else:
            return future

    def _use_datadir_listing(self, file_path, datadir_root='/data/dataiku/dss_data'):
        if file_path is not None and len(file_path) > 0:
            self.client._perform_empty("POST", "/directories-footprint/fake-fs-walk-with-datadir-listing", params={
                "datadirListing": file_path,
                "datadirRoot": datadir_root
            })
        else:
            self.client._perform_empty("POST", "/directories-footprint/unfake-fs-walk-with-datadir-listing", params={})


    def compute_global_only_footprint(self, wait=True):
        """
        Compute the global data directories footprints, returning directories size in bytes.
        Global directories are instance-wide directories like code envs, plugins, libs.

        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)
        :return: If wait is False, a :class:`dataikuapi.dss.future.DSSFuture` representing the listing process. If wait is True, a :class:`dataikuapi.dss.data_directories_footprint.Footprint`
        """

        return self._compute_footprint("/directories-footprint/global", False, wait, lambda x:Footprint(x))


    def compute_project_footprint(self, project_key, wait=True):
        """
        Lists data directories footprints for the given project, returning directories size in bytes.
        Project directories are owned by a single project like managed datasets or managed folders, code studios, scenarios.

        :param string project_key: the project key
        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)
        :return: If wait is False, a :class:`dataikuapi.dss.future.DSSFuture` representing the listing process. If wait is True, a :class:`dataikuapi.dss.data_directories_footprint.Footprint`
        """
        def wrap_res(f):
            if 'projects' in f and 'items' in f["projects"] and len(f["projects"]["items"]) > 0:
                return Footprint(f["projects"]["items"][0])
            else:
                return Footprint(f) # probably no projects at all
        return self._compute_footprint("/directories-footprint/projects/" + project_key, False, wait, wrap_res)

    def compute_all_dss_footprint(self, wait=True):
        """
        Lists all the DSS data directories footprints, returning directories size in bytes.
        This includes all the projects.

        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)
        :return: If wait is False, a :class:`dataikuapi.dss.future.DSSFuture` representing the listing process. If wait is True, a :class:`dataikuapi.dss.data_directories_footprint.Footprint`
        """
        return self._compute_footprint("/directories-footprint/all-dss", False, wait, lambda x:Footprint(x))

    def compute_unknown_footprint(self, show_summary_only=True, wait=True):
        """
        Lists the unknown data directories footprints, returning directories size in bytes
        Unknown directories are any directory that does not belong to DSS

        :param bool show_summary_only: only show the aggregate per location found (defaults to **False**)
        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)
        :return: If wait is False, a :class:`dataikuapi.dss.future.DSSFuture` representing the listing process. If wait is True, a :class:`dataikuapi.dss.data_directories_footprint.Footprint`
        """
        def wrap_res(f):
            if 'unknown' in f:
                return Footprint(f["unknown"])
            else:
                return Footprint(f) # probably no unknown data at all
        return self._compute_footprint("/directories-footprint/unknown", show_summary_only, wait, wrap_res)
