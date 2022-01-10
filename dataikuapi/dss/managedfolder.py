from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import os
from requests import utils
from .metrics import ComputedMetrics
from .future import DSSFuture
from .discussion import DSSObjectDiscussions

try:
    basestring
except NameError:
    basestring = str
class DSSManagedFolder(object):
    """
    A managed folder on the DSS instance
    """
    def __init__(self, client, project_key, odb_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.odb_id = odb_id

    @property
    def id(self):
        return self.odb_id
    
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
                "GET", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id))

    def set_definition(self, definition):
        """
        Set the definition of the managed folder
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/managedfolders/%s" % (self.project_key, self.odb_id),
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
                "GET", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)))

    def delete_file(self, path):
        """
        Delete a file from the managed folder
        """
        return self.client._perform_empty(
                "DELETE", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)))

    def put_file(self, path, f):
        """
        Upload the file to the managed folder

        Args:
            f: the file contents, as a stream
            path: the path of the file
        """
        return self.client._perform_json_upload(
                "POST", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, utils.quote(path)),
                "", f)

    def upload_folder(self, path, folder):
        """
        Upload the content of a folder at path in the managed folder.

        Note: upload_folder("target", "source") will result in "target" containing the content
        of "source", not in "target" containing "source".

        :param str path: the destination path of the folder in the managed folder
        :param str folder: path  (absolute or relative) of the source folder to upload
        """
        for root, _, files in os.walk(folder):
            for file in files:
                filename = os.path.join(root, file)
                with open(filename, "rb") as f:
                    self.put_file(os.path.join(path, os.path.relpath(filename, folder)), f)

    ########################################################
    # Managed folder actions
    ########################################################

    def compute_metrics(self, metric_ids=None, probes=None):
        """
        Compute metrics on this managed folder. If the metrics are not specified, the metrics
        setup on the managed folder are used.
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
        Get the last values of the metrics on this managed folder
        
        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/metrics/last" % (self.project_key, self.odb_id)))


    def get_metric_history(self, metric):
        """
        Get the history of the values of the metric on this dataset
        
        Returns:
            an object containing the values of the metric, cast to the appropriate type (double, boolean,...)
        """
        return self.client._perform_json(
                "GET", "/projects/%s/managedfolders/%s/metrics/history" % (self.project_key, self.odb_id),
                params={'metricLookup' : metric if isinstance(metric, str) or isinstance(metric, unicode) else json.dumps(metric)})


                
    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this managed folder

        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Moves this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to move the object
        """
        if isinstance(zone, basestring):
           zone = self.project.get_flow().get_zone(zone)
        zone.add_item(self)

    def share_to_zone(self, zone):
        """
        Share this object to a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` where to share the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.add_shared(self)

    def unshare_from_zone(self, zone):
        """
        Unshare this object from a flow zone

        :param object zone: a :class:`dataikuapi.dss.flow.DSSFlowZone` from where to unshare the object
        """
        if isinstance(zone, basestring):
            zone = self.project.get_flow().get_zone(zone)
        zone.remove_shared(self)

    def get_usages(self):
        """
        Get the recipes referencing this folder

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/managedfolders/%s/usages" % (self.project_key, self.odb_id))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the managed folder

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MANAGED_FOLDER", self.odb_id)

    ########################################################
    # utilities
    ########################################################
    def copy_to(self, target, write_mode="OVERWRITE"):
        """
        Copies the data of this folder to another folder

        :param target Folder: a :class:`dataikuapi.dss.managedfolder.DSSManagedFolder` representing the target of this copy
        :returns: a DSSFuture representing the operation
        """
        dqr = {
             "targetProjectKey" : target.project_key,
             "targetFolderId": target.odb_id,
             "writeMode" : write_mode
        }
        future_resp = self.client._perform_json("POST", "/projects/%s/managedfolders/%s/actions/copyTo" % (self.project_key, self.odb_id), body=dqr)
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)

