from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings
import json
import sys
import os
from requests import utils
from .metrics import ComputedMetrics
from .future import DSSFuture
from .discussion import DSSObjectDiscussions
from .dataset import DSSDataset

try:
    basestring
except NameError:
    basestring = str

class DSSManagedFolder(object):
    """
    A handle to interact with a managed folder on the DSS instance.

    .. important::

        Do not create this class directly, instead use :meth:`dataikuapi.dss.project.get_managed_folder`
    """
    def __init__(self, client, project_key, odb_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.odb_id = odb_id

    @property
    def id(self):
        """
        Returns the internal identifier of the managed folder, which is a 8-character random string, not 
        to be confused with the managed folder's name.

        :rtype: string
        """
        return self.odb_id
    
    ########################################################
    # Managed folder deletion
    ########################################################
    
    def delete(self):
        """
        Delete the managed folder from the flow, and objects using it (recipes or labeling tasks)

        .. attention::

            This call doesn't delete the managed folder's contents
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id))


    ########################################################
    # Managed folder renaming
    ########################################################

    def rename(self, new_name):
        """
        Rename the managed folder

        :param str new_name: the new name of the managed folder

        .. note::

            The new name cannot be made of whitespaces only.
        """
        body = {
            "id": self.odb_id,
            "newName": new_name
        }
        return self.client._perform_empty(
            "POST",
            u"/projects/{}/actions/renameManagedFolder".format(self.project_key),
            body=body
        )

    ########################################################
    # Managed folder definition
    ########################################################
    
    def get_definition(self):
        """
        Get the definition of this managed folder. The definition contains name, description
        checklists, tags, connection and path parameters, metrics and checks setup.

        .. caution::

            Deprecated. Please use :meth:`get_settings`


        :returns: the managed folder definition.
        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id))

    def set_definition(self, definition):
        """
        Set the definition of this managed folder.

        .. caution::

            Deprecated. Please use :meth:`get_settings` then :meth:`~DSSManagedFolderSettings.save()`

        .. note::

            the fields `id` and `projectKey` can't be modified

        Usage example:

        .. code-block:: python

            folder_definition = folder.get_definition()
            folder_definition['tags'] = ['tag1','tag2']
            folder.set_definition(folder_definition)

        :param dict definition: the new state of the definition for the folder. You should only set a definition object
                                that has been retrieved using the :meth:`get_definition` call

        :returns: a message upon successful completion of the definition update. Only contains one `msg` field
        :rtype: dict
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id),
                body=definition)

    def get_settings(self):
        """
        Returns the settings of this managed folder as a :class:`DSSManagedFolderSettings`.

        You must use :meth:`~DSSManagedFolderSettings.save()` on the returned object to make your changes effective
        on the managed folder.

        .. code-block:: python

            # Example: activating discrete partitioning
            folder = project.get_managed_folder("my_folder_id")
            settings = folder.get_settings()
            settings.add_discrete_partitioning_dimension("country")
            settings.save()

        :returns: the settings of the managed folder
        :rtype: :class:`DSSManagedFolderSettings`
        """
        data = self.client._perform_json("GET", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id))
        return DSSManagedFolderSettings(self, data)

    ########################################################
    # Managed folder contents
    ########################################################
    
    def list_contents(self):
        """
        Get the list of files in the managed folder
        
        Usage example:

        .. code-block:: python

            for content in folder.list_contents()['items']:
                last_modified_seconds = content["lastModified"] / 1000
                last_modified_str = datetime.fromtimestamp(last_modified_seconds).strftime("%Y-%m-%d %H:%m:%S")
                print("size=%s mtime=%s %s" % (content["size"], last_modified_str, content["path"]))

        :returns: the list of files, in the `items` field. Each item has fields:

                    * **path** : path of the file inside the folder
                    * **size** : size of the file in bytes
                    * **lastModified** : last modification time, in milliseconds since epoch

        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/contents" % (self.project_key, self.odb_id))

    def get_file(self, path):
        """
        Get a file from the managed folder
        
        Usage example:

        .. code-block:: python

            with folder.get_file("/kaggle_titanic_train.csv") as fd:
                df = pandas.read_csv(fd.raw)

        :param string path: the path of the file to read within the folder

        :returns: the HTTP request to stream the data from 
        :rtype: :class:`requests.models.Response`
        """
        return self.client._perform_raw(
                "GET", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)))

    def delete_file(self, path):
        """
        Delete a file from the managed folder

        :param string path: the path of the file to read within the folder

        .. note::

            No error is raised if the file doesn't exist

        """
        return self.client._perform_empty(
                "DELETE", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)))

    def put_file(self, path, f):
        """
        Upload the file to the managed folder. If the file already exists in the folder, it is overwritten.

        Usage example:

        .. code-block:: python

            with open("./some_local.csv") as fd:
                uploaded = folder.put_file("/target.csv", fd).json()
                print("Uploaded %s bytes" % uploaded["size"])

        :param string path: the path of the file to write within the folder
        :param file f: a file-like

        .. note::

            if using a string for the `f` parameter, the string itself is taken as the file content to upload

        :returns: information on the file uploaded to the folder, as a dict of:

                    * **path** : path of the file inside the folder
                    * **size** : size of the file in bytes
                    * **lastModified** : last modification time, in milliseconds since epoch

        :rtype: dict
        """
        return self.client._perform_json_upload(
                "POST", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)),
                "", f).json()

    def upload_folder(self, path, folder):
        """
        Upload the content of a folder to a managed folder.

        .. note::

            `upload_folder("/some/target", "./a/source/")` will result in "target" containing the contents of "source", 
            but not the "source" folder being a child of "target"

        :param str path: the destination path of the folder in the managed folder
        :param str folder: local path (absolute or relative) of the source folder to upload
        """
        for root, _, files in os.walk(folder):
            for file in files:
                filename = os.path.join(root, file)
                with open(filename, "rb") as f:
                    rel_posix_path = "/".join(os.path.relpath(filename, folder).split(os.sep))
                    self.put_file("{}/{}".format(path, rel_posix_path), f)

    ########################################################
    # Managed folder actions
    ########################################################

    def compute_metrics(self, metric_ids=None, probes=None):
        """
        Compute metrics on this managed folder.

        Usage example:

        .. code-block:: python

            future_resp = folder.compute_metrics()
            future = DSSFuture(client, future_resp.get("jobId", None), future_resp)
            metrics = future.wait_for_result()
            print("Computed in %s ms" % (metrics["endTime"] - metrics["startTime"]))
            for computed in metrics["computed"]:
                print("Metric %s = %s" % (computed["metricId"], computed["value"]))

        :param metric_ids: (optional) identifiers of metrics to compute, among the metrics defined
                           on the folder
        :type metric_ids: list[string]

        :param probes: (optional) definition of metrics probes to use, in place of the ones defined
                       on the folder. The current set of probes on the folder is the `probes` field
                       in the dict returned by :meth:`get_definition`
        :type probes: dict

        :returns: a future as dict representing the task of computing the probes
        :rtype: dict
        """
        url = "/projects/%s/managedfolders/%s/actions" % (self.project_key, self.odb_id)
        if metric_ids is not None:
            return self.client._perform_json(
                    "POST" , "%s/computeMetricsFromIds" % url,
                     body={"metricIds" : metric_ids})
        elif probes is not None:
            return self.client._perform_json(
                    "POST" , "%s/computeMetrics" % url,
                     body=probes)
        else:
            return self.client._perform_json(
                    "POST" , "%s/computeMetrics" % url)

	                
    ########################################################
    # Metrics
    ########################################################

    def get_last_metric_values(self):
        """
        Get the last values of the metrics on this managed folder.
        
        :returns: a handle on the values of the metrics
        :rtype: :class:`dataikuapi.dss.metrics.ComputedMetrics`
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/metrics/last" % (self.project_key, self.odb_id)))


    def get_metric_history(self, metric):
        """
        Get the history of the values of a metric on this managed folder.

        Usage example:

        .. code-block:: python

            history = folder.get_metric_history("basic:COUNT_FILES")
            for value in history["values"]:
                time_str = datetime.fromtimestamp(value["time"] / 1000).strftime("%Y-%m-%d %H:%m:%S")
                print("%s : %s" % (time_str, value["value"]))

        :param string metric: identifier of the metric to get values of
        
        :returns: an object containing the values of the metric, cast to the appropriate type (double, 
                  boolean,...). The identifier of the metric is in a **metricId** field.

        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/metrics/history" % (self.project_key, self.odb_id),
                params={'metricLookup' : metric if isinstance(metric, str) or isinstance(metric, unicode) else json.dumps(metric)})


                
    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Get the flow zone of this managed folder.

        :returns: a flow zone
        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Move this object to a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object, or its identifier
        """
        if isinstance(zone, basestring):
           zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Share this object to a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to share the object, or its identifier
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshare this object from a flow zone.

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` from where to unshare the object, or its identifier
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Get the recipes referencing this folder.

        Usage example:

        .. code-block:: python

            for usage in folder.get_usages():
                if usage["type"] == 'RECIPE_INPUT':
                    print("Used as input of %s" % usage["objectId"])

        :returns: a list of usages, each one a dict of:

                     * **type** : the type of usage, either "RECIPE_INPUT" or "RECIPE_OUTPUT"
                     * **objectId** : name of the recipe
                     * **objectProjectKey** : project of the recipe

        :rtype: list[dict]
        """
        return self.client._perform_json("GET", "/projects/%s/managedfolders/%s/usages" % (self.project_key, self.odb_id))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the managed folder.

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MANAGED_FOLDER", self.odb_id)

    ########################################################
    # utilities
    ########################################################
    def copy_to(self, target, write_mode="OVERWRITE"):
        """
        Copy the data of this folder to another folder.

        :param object target: a :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` representing the target location of this copy

        :returns: a DSSFuture representing the operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        dqr = {
             "targetProjectKey" : target.project_key,
             "targetFolderId": target.odb_id,
             "writeMode" : write_mode
        }
        future_resp = self.client._perform_json("POST", "/projects/%s/managedfolders/%s/actions/copyTo" % (self.project_key, self.odb_id), body=dqr)
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)

    def create_dataset_from_files(self, dataset_name):
        """
        Create a new dataset of type 'FilesInFolder', taking its files from this managed folder, and 
        return a handle to interact with it.

        The created dataset does not have its format and schema initialized, it is recommended to use
        :meth:`~dataikuapi.dss.dataset.DSSDataset.autodetect_settings` on the returned object

        :param str dataset_name: the name of the dataset to create. Must not already exist

        :returns: A dataset handle
        :rtype: :class:`dataikuapi.dss.dataset.DSSDataset`
        """
        obj = {
            "name": dataset_name,
            "projectKey": self.project_key,
            "type": "FilesInFolder",
            "params": {
                "folderSmartId": self.odb_id
            }
        }
        self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key, body=obj)
        return DSSDataset(self.client, self.project_key, dataset_name)



class DSSManagedFolderSettings(DSSTaggableObjectSettings):
    """
    Base settings class for a DSS managed folder.
    Do not instantiate this class directly, use :meth:`DSSManagedFolder.get_settings`

    Use :meth:`save` to save your changes
    """

    def __init__(self, folder, settings):
        super(DSSManagedFolderSettings, self).__init__(settings)
        self.folder = folder
        self.settings = settings

    def get_raw(self):
        """
        Get the managed folder settings.

        :returns: the settings, as a dict. The definition of the actual location of the files in the 
                  managed folder is a **params** sub-dict.

        :rtype: dict
        """
        return self.settings

    def get_raw_params(self):
        """
        Get the type-specific (S3/ filesystem/ HDFS/ ...) params as a dict.

        :returns: the type-specific patams. Each type defines a set of fields; commonly found fields are :

                    * **connection** : name of the connection used by the managed folder
                    * **path** : root of the managed folder within the connection
                    * **bucket** or **container** : the bucket/container name on cloud storages

        :rtype: dict
        """
        return self.settings["params"]

    @property
    def type(self):
        """
        Get the type of filesystem that the managed folder uses.

        :rtype: string
        """
        return self.settings["type"]


    def save(self):
        """
        Save the changes to the settings on the managed folder.

        Usage example:

        .. code-block:: python

            folder = project.get_managed_folder("my_folder_id")
            settings = folder.get_settings()
            settings.set_connection_and_path("some_S3_connection", None)
            settings.get_raw_params()["bucket"] = "some_S3_bucket"
            settings.save()

        """
        self.folder.client._perform_empty(
                "PUT", "/projects/%s/managedfolders/%s" % (self.folder.project_key, self.folder.odb_id),
                body=self.settings)

    ########################################################
    # Partitioning
    ########################################################    
    def remove_partitioning(self):
        """
        Make the managed folder non-partitioned.
        """
        self.settings["partitioning"] = {"dimensions" : []}

    def add_discrete_partitioning_dimension(self, dim_name):
        """
        Add a discrete partitioning dimension.

        :param string dim_name: name of the partitioning dimension
        """
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "value"})

    def add_time_partitioning_dimension(self, dim_name, period="DAY"):
        """
        Add a time partitioning dimension.

        :param string dim_name: name of the partitioning dimension
        :param string period: granularity of the partitioning dimension (YEAR, MONTH, DAY (default), HOUR)
        """
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "time", "params":{"period": period}})

    def set_partitioning_file_pattern(self, pattern):
        """
        Set the partitioning pattern of the folder. The pattern indicates which paths inside the folder belong to
        which partition. Partition dimensions are written with:

          * `%{dim_name}` for discrete dimensions
          * `%Y` (=year), `%M` (=month), `%D` (=day) and `%H` (=hour) for time dimensions

        Besides the `%...` variables for injecting the partition dimensions, the pattern is a regular expression.

        Usage example:

        .. code-block:: python

            # partition a managed folder by month
            folder = project.get_managed_folder("my_folder_id")
            settings = folder.get_settings()
            settings.add_time_partitioning_dimension("my_date", "MONTH")
            settings.set_partitioning_file_pattern("/year=%Y/month=%M/.*")
            settings.save()


        :param string pattern: the partitioning pattern
        """
        self.settings["partitioning"]["filePathPattern"] = pattern

    ########################################################
    # Basic
    ########################################################
    def set_connection_and_path(self, connection, path):
        """
        Change the managed folder connection and/or path. 

        .. note::
        
            When changing the connection or path, the folder's files aren't moved or copied to the new location

        .. attention::

            When changing the connection for a connection with a different type, for example going from a S3 connection
            to an Azure Blob Storage connection, only the managed folder type is changed. Type-specific fields are not
            converted. In the example of a S3 to Azure conversion, the S3 bucket isn't converted to a storage account
            container.

        :param string connection: the name of a file-based connection. If `None`, the connection of the managed folder is
                                  left unchanged
        :param string path: a path relative to the connection root. If `None`, the path of the managed folder is left 
                            unchanged
        """
        if connection is not None:
            if connection != self.settings["params"]["connection"]:
                # get the actual connection type (and check that it exists)
                connection_info = self.folder.client.get_connection(connection).get_info(self.folder.project_key)
                connection_type = connection_info["type"]
                if connection_type == 'EC2':
                    self.settings["type"] = 'S3' # the fsprovider type is different
                elif connection_type == 'SSH':
                    # can be SCP or SFTP, default to SCP if connection type changed
                    if self.settings["type"] not in ['SCP', 'SFTP']:
                        self.settings["type"] = 'SCP'
                else:
                    self.settings["type"] = connection_type
                self.settings["params"]["connection"] = connection
        if path is not None:
            self.settings["params"]["path"] = path

