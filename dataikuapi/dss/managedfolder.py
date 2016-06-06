from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
from .metrics import ComputedMetrics

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

    def delete_file(self, path):
        """
        Delete a file from the managed folder
        """
        return self.client._perform_empty(
                "DELETE", "/projects/%s/managedfolders/%s/contents/%s" % (self.project_key, self.odb_id, path))

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
            return self.client._perform_empty(
                    "POST" , "%s/computeMetrics" % url)

        if metrics is None:
	        self.client._perform_empty(
	                "POST" , "/projects/%s/managedfolders/%s/actions/computeMetrics" %(self.project_key, self.odb_id))
        else:
	        self.client._perform_json(
	                "POST" , "/projects/%s/managedfolders/%s/actions/computeMetrics" %(self.project_key, self.odb_id),
	                params=metrics)
	                
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
    # Usages
    ########################################################

    def get_usages(self):
        """
        Get the recipes referencing this folder

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/managedfolders/%s/usages" % (self.project_key, self.odb_id))


