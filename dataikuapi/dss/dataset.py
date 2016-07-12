from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
from .metrics import ComputedMetrics

class DSSDataset(object):
    """
    A dataset on the DSS instance
    """
    def __init__(self, client, project_key, dataset_name):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name

    ########################################################
    # Dataset deletion
    ########################################################
    
    def delete(self):
        """
        Delete the dataset
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name))



    ########################################################
    # Dataset definition
    ########################################################
    
    def get_definition(self):
        """
        Get the definition of the dataset
        
        Returns:
            the definition, as a JSON object
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name))

    def set_definition(self, definition):
        """
        Set the definition of the dataset
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name),
                body=definition)

    ########################################################
    # Dataset metadata
    ########################################################

    def get_schema(self):
        """
        Get the schema of the dataset
        
        Returns:
            a JSON object of the schema, with the list of columns
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        """
        Set the schema of the dataset
        
        Args:
            schema: the desired schema for the dataset, as a JSON object. All columns have to provide their
            name and type
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_metadata(self):
        """
        Get the metadata attached to this dataset. The metadata contains label, description
        checklists, tags and custom metadata of the dataset
        
        Returns:
            a dict object. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/latest
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this dataset.
        
        Args:
            metadata: the new state of the metadata for the dataset. You should only set a metadata object 
            that has been retrieved using the get_metadata call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name),
                body=metadata)


    ########################################################
    # Dataset data
    ########################################################

    def iter_rows(self, partitions=None):
        """
        Get the dataset's data
        
        Return:
            an iterator over the rows, each row being a tuple of values. The order of values
            in the tuples is the same as the order of columns in the schema returned by get_schema
        """
        csv_stream = self.client._perform_raw(
                "GET" , "/projects/%s/datasets/%s/data/" %(self.project_key, self.dataset_name),
                params = {
                    "format" : "tsv-excel-noheader",
                    "partitions" : partitions
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema()["columns"], csv_stream).iter_rows()


    def list_partitions(self):
        """
        Get the list of all partitions of this dataset
        
        Returns:
            the list of partitions, as a list of strings
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/partitions" % (self.project_key, self.dataset_name))


    def clear(self, partitions=None):
        """
        Clear all data in this dataset
        
        Args:
            partitions: (optional) a list of partitions to clear. When not provided, the entire dataset
            is cleared
        """
        return self.client._perform_json(
                "DELETE", "/projects/%s/datasets/%s/data" % (self.project_key, self.dataset_name),
                params={"partitions" : partitions})

    ########################################################
    # Dataset actions
    ########################################################

    def synchronize_hive_metastore(self):
        """
        Synchronize this dataset with the Hive metastore
        """
        self.client._perform_empty(
                "POST" , "/projects/%s/datasets/%s/actions/synchronizeHiveMetastore" %(self.project_key, self.dataset_name))

    def compute_metrics(self, partition='', metric_ids=None, probes=None):
        """
        Compute metrics on a partition of this dataset.
        If neither metric ids nor custom probes set are specified, the metrics
        setup on the dataset are used.
        """
        url = "/projects/%s/datasets/%s/actions" % (self.project_key, self.dataset_name)
        if metric_ids is not None:
            return self.client._perform_json(
                    "POST" , "%s/computeMetricsFromIds" % url,
                    params={'partition':partition}, body={"metricIds" : metric_ids})
        elif probes is not None:
            return self.client._perform_json(
                    "POST" , "%s/computeMetrics" % url,
                    params={'partition':partition}, body=probes)
        else:
            return self.client._perform_empty(
                    "POST" , "%s/computeMetrics" % url,
                    params={'partition':partition})

    def run_checks(self, partition='', checks=None):
        """
        Run checks on a partition of this dataset. If the checks are not specified, the checks
        setup on the dataset are used.
        """
        if checks is None:
            return self.client._perform_empty(
                    "POST" , "/projects/%s/datasets/%s/actions/runChecks" %(self.project_key, self.dataset_name, partition))
        else:
            return self.client._perform_json(
                    "POST" , "/projects/%s/datasets/%s/actions/runChecks" %(self.project_key, self.dataset_name, partition),
                    params=checks)

    ########################################################
    # Metrics
    ########################################################

    def get_last_metric_values(self, partition=''):
        """
        Get the last values of the metrics on this dataset

        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metrics/last/%s" % (self.project_key, self.dataset_name, 'NP' if len(partition) == 0 else partition)))


    def get_metric_history(self, metric, partition=''):
        """
        Get the history of the values of the metric on this dataset

        Returns:
            an object containing the values of the metric, cast to the appropriate type (double, boolean,...)
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metrics/history/%s" % (self.project_key, self.dataset_name, 'NP' if len(partition) == 0 else partition),
                params={'metricLookup' : metric if isinstance(metric, str) or isinstance(metric, unicode) else json.dumps(metric)})

    ########################################################
    # Usages
    ########################################################

    def get_usages(self):
        """
        Get the recipes or analyses referencing this dataset

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/datasets/%s/usages" % (self.project_key, self.dataset_name))
