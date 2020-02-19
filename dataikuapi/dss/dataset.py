from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions
from .statistics import DSSStatisticsWorksheet

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

    def delete(self, drop_data=False):
        """
        Delete the dataset

        :param bool drop_data: Should the data of the dataset be dropped
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name), params = {
                "dropData" : drop_data
            })


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
                "GET", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name))

    def set_definition(self, definition):
        """
        Set the definition of the dataset
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name),
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
            https://doc.dataiku.com/dss/api/5.0/rest/
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

    def update_from_hive(self):
        """
        Resynchronize this dataset from its Hive definition
        """
        self.client._perform_empty(
                "POST", "/projects/%s/datasets/%s/actions/updateFromHive" %(self.project_key, self.dataset_name))

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
            return self.client._perform_json(
                    "POST" , "%s/computeMetrics" % url,
                    params={'partition':partition})

    def run_checks(self, partition='', checks=None):
        """
        Run checks on a partition of this dataset. If the checks are not specified, the checks
        setup on the dataset are used.
        """
        if checks is None:
            return self.client._perform_json(
                    "POST" , "/projects/%s/datasets/%s/actions/runChecks" %(self.project_key, self.dataset_name),
                    params={'partition':partition})
        else:
            return self.client._perform_json(
                    "POST" , "/projects/%s/datasets/%s/actions/runChecks" %(self.project_key, self.dataset_name),
                    params={'partition':partition}, body=checks)

    ########################################################
    # Statistics worksheets
    ########################################################

    def list_statistics_worksheets(self, as_objects=True):
        """
        List the statistics worksheets associated to this dataset.

        :rtype: list of :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet`
        """
        worksheets = self.client._perform_json(
            "GET", "/projects/%s/datasets/%s/statistics/worksheets/" % (self.project_key, self.dataset_name))
        if as_objects:
            return [self.get_statistics_worksheet(worksheet['id']) for worksheet in worksheets]
        else:
            return worksheets

    def create_statistics_worksheet(self, name="My worksheet"):
        """
        Create a new worksheet in the dataset, and return a handle to interact with it.

        :param string input_dataset: input dataset of the worksheet
        :param string worksheet_name: name of the worksheet

        Returns:
            A :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet` dataset handle
        """

        worksheet_definition = {
            "projectKey": self.project_key,
            "name": name,
            "dataSpec": {
                "inputDatasetSmartName": self.dataset_name,
                "datasetSelection": {
                    "partitionSelectionMethod": "ALL",
                    "maxRecords": 30000,
                    "samplingMethod": "FULL"
                }
            }
        }
        created_worksheet = self.client._perform_json(
            "POST", "/projects/%s/datasets/%s/statistics/worksheets/" % (self.project_key, self.dataset_name),
            body=worksheet_definition
        )
        return self.get_statistics_worksheet(created_worksheet['id'])

    def get_statistics_worksheet(self, worksheet_id):
        """
        Get a handle to interact with a statistics worksheet

        :param string worksheet_id: the ID of the desired worksheet

        :returns: A :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet` worksheet handle
        """
        return DSSStatisticsWorksheet(self.client, self.project_key, self.dataset_name, worksheet_id)

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

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the dataset

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "DATASET", self.dataset_name)

class DSSManagedDatasetCreationHelper(object):

    def __init__(self, project, dataset_name):
        self.project = project
        self.dataset_name = dataset_name
        self.creation_settings = { "specificSettings" : {} }

    def get_creation_settings(self):
        return self.creation_settings

    def with_store_into(self, connection, type_option_id = None, format_option_id = None):
        """
        Sets the connection into which to store the new managed dataset
        :param str connection: Name of the connection to store into
        :param str type_option_id: If the connection accepts several types of datasets, the type
        :param str format_option_id: Optional identifier of a file format option
        :return: self
        """
        self.creation_settings["connectionId"] = connection
        if type_option_id is not None:
            self.creation_settings["typeOptionId"] = type_option_id
        if format_option_id is not None:
            self.creation_settings["specificSettings"]["formatOptionId"] = format_option_id 
        return self

    def with_copy_partitioning_from(self, dataset_ref, object_type='DATASET'):
        """
        Sets the new managed dataset to use the same partitioning as an existing dataset_name

        :param str dataset_ref: Name of the dataset to copy partitioning from
        :return: self
        """
        code = 'dataset' if object_type == 'DATASET' else 'folder'
        self.creation_settings["partitioningOptionId"] = "copy:%s:%s" % (code, dataset_ref)
        return self

    def create(self):
        """
        Executes the creation of the managed dataset according to the selected options

        :return: The :class:`DSSDataset` corresponding to the newly created dataset
        """
        self.project.client._perform_json("POST", "/projects/%s/datasets/managed" % self.project.project_key,
            body = {
                "name": self.dataset_name,
                "creationSettings":  self.creation_settings
        })
        return DSSDataset(self.project.client, self.project.project_key, self.dataset_name)