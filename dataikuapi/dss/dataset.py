import datetime

from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
from .future import DSSFuture
import json, warnings
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings
from .future import DSSFuture
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions
from .statistics import DSSStatisticsWorksheet
from . import recipe
try:
    basestring
except NameError:
    basestring = str

class DSSDatasetListItem(DSSTaggableObjectListItem):
    """
    An item in a list of datasets. 
    
    .. caution::
    
        Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_datasets`
    """
    def __init__(self, client, data):
        super(DSSDatasetListItem, self).__init__(data)
        self.client = client

    def to_dataset(self):
        """
        Gets a handle on the corresponding dataset.
        
        :returns: a handle on a dataset
        :rtype: :class:`DSSDataset`
        """
        return DSSDataset(self.client, self._data["projectKey"], self._data["name"])

    @property
    def name(self):
        """
        Get the name of the dataset.
        
        :rtype: string
        """
        return self._data["name"]
    @property
    def id(self):
        """
        Get the identifier of the dataset.
        
        :rtype: string
        """
        return self._data["name"]
    @property
    def type(self):
        """
        Get the type of the dataset.
        
        :rtype: string
        """
        return self._data["type"]
    @property
    def schema(self):
        """
        Get the schema of the dataset.
        
        :returns: a list of column definitions. See :meth:`DSSDataset.get_schema()`
        :rtype: list[dict]
        """
        return self._data["schema"]

    @property
    def connection(self):
        """
        Get the name of the connection on which this dataset is attached, or None if there is no connection for this dataset.
        
        :rtype: string
        """
        if not "params" in self._data:
            return None
        return self._data["params"].get("connection", None)

    def get_column(self, column):
        """
        Get the a given column in the schema of the dataset, by its name.
        
        :param str column: name of the column to find
        
        :returns: the column settings or None if column does not exist
        :rtype: dict
        """
        matched = [col for col in self.schema["columns"] if col["name"] == column]
        return None if len(matched) == 0 else matched[0]

class DSSDataset(object):
    """
    A dataset on the DSS instance. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.get_dataset`
    """
    def __init__(self, client, project_key, dataset_name):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.dataset_name = dataset_name

    @property
    def id(self):
        return self.dataset_name

    @property
    def name(self):
        return self.dataset_name
    
    ########################################################
    # Dataset deletion
    ########################################################

    def delete(self, drop_data=False):
        """
        Delete the dataset

        :param bool drop_data: Should the data of the dataset be dropped, defaults to False
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name), params = {
                "dropData" : drop_data
            })


    ########################################################
    # Dataset definition
    ########################################################

    def get_settings(self):
        """
        Get the settings of this dataset as a :class:`DSSDatasetSettings`, or one of its subclasses.

        Know subclasses of :class:`DSSDatasetSettings` include :class:`FSLikeDatasetSettings` 
        and :class:`SQLDatasetSettings`

        You must use :meth:`~DSSDatasetSettings.save()` on the returned object to make your changes effective
        on the dataset.

        .. code-block:: python

            # Example: activating discrete partitioning on a SQL dataset
            dataset = project.get_dataset("my_database_table")
            settings = dataset.get_settings()
            settings.add_discrete_partitioning_dimension("country")
            settings.save()

        :rtype: :class:`DSSDatasetSettings`
        """
        data = self.client._perform_json("GET", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name))

        if data["type"] in self.__class__._FS_TYPES:
            return FSLikeDatasetSettings(self, data)
        elif data["type"] in self.__class__._SQL_TYPES:
            return SQLDatasetSettings(self, data)
        else:
            return DSSDatasetSettings(self, data)


    def get_definition(self):
        """
        Get the raw settings of the dataset as a dict

        .. caution:: Deprecated. Use :meth:`get_settings`
        
        :rtype: dict
        """
        warnings.warn("Dataset.get_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name))

    def set_definition(self, definition):
        """
        Set the definition of the dataset
        
        .. caution:: Deprecated. Use :meth:`get_settings` and :meth:`DSSDatasetSettings.save`
        
        :param definition: the definition, as a dict. You should only set a definition object 
                            that has been retrieved using the get_definition call.
        """
        warnings.warn("Dataset.set_definition is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name),
                body=definition)

    def exists(self):
        """
        Test if the dataset exists.
        
        :returns: whether this dataset exists
        :rtype: bool
        """
        try:
            self.get_metadata()
            return True
        except Exception as e:
            return False

    ########################################################
    # Dataset metadata
    ########################################################

    def get_schema(self):
        """
        Get the schema of the dataset
        
        :returns: a JSON object of the schema, with the list of columns
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        """
        Set the schema of the dataset
        
        :param schema: the desired schema for the dataset, as a JSON object. 
                       All columns have to provide their name and type
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_metadata(self):
        """
        Get the metadata attached to this dataset. The metadata contains label, description
        checklists, tags and custom metadata of the dataset
        
        :returns: a dict object. For more information on available metadata, please see
                  https://doc.dataiku.com/dss/api/11.0/rest/
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this dataset.
        
        :param metadata: the new state of the metadata for the dataset. You should only set a metadata object 
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
        
        :returns: an iterator over the rows, each row being a tuple of values. The order of values
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
        
        :returns: the list of partitions, as a list of strings
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/partitions" % (self.project_key, self.dataset_name))


    def clear(self, partitions=None):
        """
        Clear all data in this dataset
        
        :param partitions: (optional) a list of partitions to clear. When not provided, the entire dataset
                           is cleared
        """
        return self.client._perform_json(
                "DELETE", "/projects/%s/datasets/%s/data" % (self.project_key, self.dataset_name),
                params={"partitions" : partitions})

    def copy_to(self, target, sync_schema=True, write_mode="OVERWRITE"):
        """
        Copy the data of this dataset to another dataset

        :param target Dataset: a :class:`dataikuapi.dss.dataset.DSSDataset` representing the target of this copy
        :returns: a DSSFuture representing the operation
        """
        dqr = {
             "targetProjectKey" : target.project_key,
             "targetDatasetName": target.dataset_name,
             "syncSchema": sync_schema,
             "writeMode" : write_mode
        }
        future_resp = self.client._perform_json("POST", "/projects/%s/datasets/%s/actions/copyTo" % (self.project_key, self.dataset_name), body=dqr)
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)

    ########################################################
    # Dataset actions
    ########################################################

    def build(self, job_type="NON_RECURSIVE_FORCED_BUILD", partitions=None, wait=True, no_fail=False):
        """
        Start a new job to build this dataset and wait for it to complete.
        Raises if the job failed.

        .. code-block:: python

            job = dataset.build()
            print("Job %s done" % job.id)

        :param job_type: The job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param partitions: If the dataset is partitioned, a list of partition ids to build
        :param no_fail: if True, does not raise if the job failed.
        :returns: the :class:`dataikuapi.dss.job.DSSJob` job handle corresponding to the built job
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        jd = self.project.new_job(job_type)
        jd.with_output(self.dataset_name, partition=partitions)
        if wait:
            return jd.start_and_wait()
        else:
            return jd.start()


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
        Run checks on a partition of this dataset. 
        
        If the checks are not specified, the checks
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

    def uploaded_add_file(self, fp, filename):
        """
        Add a file to an "uploaded files" dataset

        :param file fp: A file-like object that represents the file to upload
        :param str filename: The filename for the file to upload 
        """
        self.client._perform_empty("POST", "/projects/%s/datasets/%s/uploaded/files" % (self.project_key, self.dataset_name),
         files={"file":(filename, fp)})

    def uploaded_list_files(self):
        """
        List the files in an "uploaded files" dataset
        """
        return self.client._perform_json("GET", "/projects/%s/datasets/%s/uploaded/files" % (self.project_key, self.dataset_name))

    ########################################################
    # Lab and ML
    # Don't forget to synchronize with DSSProject.*
    ########################################################

    def create_prediction_ml_task(self, target_variable,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="DEFAULT",
                                  prediction_type=None,
                                  wait_guess_complete=True):

        """
        Create a new prediction task in a new visual analysis lab
        for a dataset.

        :param string input_dataset: the dataset to use for training/testing the model
        :param string target_variable: the variable to predict
        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: DEFAULT, SIMPLE_FORMULA, DECISION_TREE, EXPLANATORY and PERFORMANCE
        :param string prediction_type: The type of prediction problem this is. If not provided the prediction type will be guessed. Valid values are: BINARY_CLASSIFICATION, REGRESSION, MULTICLASS
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """
        return self.project.create_prediction_ml_task(self.dataset_name, 
             target_variable = target_variable, ml_backend_type = ml_backend_type,
             guess_policy = guess_policy, prediction_type = prediction_type, wait_guess_complete = wait_guess_complete)

    def create_clustering_ml_task(self, input_dataset,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="KMEANS",
                                  wait_guess_complete=True):
        """
        Create a new clustering task in a new visual analysis lab
        for a dataset.


        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and ANOMALY_DETECTION
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """
        return self.project.create_clustering_ml_task(self.dataset_name, ml_backend_type=ml_backend_type, guess_policy=guess_policy,
                                                      wait_guess_complete=wait_guess_complete)

    def create_timeseries_forecasting_ml_task(self, target_variable,
                                              time_variable,
                                              timeseries_identifiers=None,
                                              guess_policy="TIMESERIES_DEFAULT",
                                              wait_guess_complete=True):
        """
        Create a new time series forecasting task in a new visual analysis lab for a dataset.

        :param string target_variable: The variable to forecast
        :param string time_variable:  Column to be used as time variable. Should be a Date (parsed) column.
        :param list timeseries_identifiers:  List of columns to be used as time series identifiers (when the dataset has multiple series)
        :param string guess_policy: Policy to use for setting the default parameters.
                                    Valid values are: TIMESERIES_DEFAULT, TIMESERIES_STATISTICAL, and TIMESERIES_DEEP_LEARNING
        :param boolean wait_guess_complete: If False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """
        return self.project.create_timeseries_forecasting_ml_task(self.dataset_name, target_variable=target_variable,
                                                                  time_variable=time_variable, timeseries_identifiers=timeseries_identifiers,
                                                                  guess_policy=guess_policy, wait_guess_complete=wait_guess_complete)

    def create_analysis(self):
        """
        Create a new visual analysis lab
        """
        return self.project_create_analysis(self.dataset_name)
 
    def list_analyses(self, as_type="listitems"):
        """
        List the visual analyses on this dataset

        :param str as_type: How to return the list. Supported values are "listitems" and "objects", defaults to "listitems"
        
        :returns: The list of the analyses. If "as_type" is "listitems", each one as a dict,
                  If "as_type" is "objects", each one as a :class:`dataikuapi.dss.analysis.DSSAnalysis` 
        :rtype: list
        """
        analysis_list = [al for al in self.project.list_analyses() if self.dataset_name == al.get('inputDataset')]

        if as_type == "listitems" or as_type == "listitem":
            return analysis_list
        elif as_type == "objects" or as_type == "object":
            return [self.project.get_analysis(item["analysisId"])for item in analysis_list]
        else:
            raise ValueError("Unknown as_type")

    def delete_analyses(self, drop_data=False):
        """
        Delete all analyses that have this dataset as input dataset. Also deletes
        ML tasks that are part of the analysis

        :param bool drop_data: whether to drop data for all ML tasks in the analysis, defaults to False
        """
        [analysis.delete(drop_data=drop_data) for analysis in self.list_analyses(as_type="objects")]

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

        :returns: a statistic worksheet handle
        :rtype: :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet`
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

        :returns: a statistic worksheet handle
        :rtype: :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet`
        """
        return DSSStatisticsWorksheet(self.client, self.project_key, self.dataset_name, worksheet_id)

    ########################################################
    # Metrics
    ########################################################

    def get_last_metric_values(self, partition=''):
        """
        Get the last values of the metrics on this dataset

        :returns: a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metrics/last/%s" % (self.project_key, self.dataset_name, 'NP' if len(partition) == 0 else partition)))

    def get_metric_history(self, metric, partition=''):
        """
        Get the history of the values of the metric on this dataset

        :returns: an object containing the values of the metric, cast to the appropriate type (double, boolean,...)
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metrics/history/%s" % (self.project_key, self.dataset_name, 'NP' if len(partition) == 0 else partition),
                params={'metricLookup' : metric if isinstance(metric, str) or isinstance(metric, unicode) else json.dumps(metric)})

    def get_info(self):
        """
        Retrieve all the information about a dataset

        :returns: a :class:`DSSDatasetInfo` containing all the information about a dataset.
        :rtype: :class:`DSSDatasetInfo`
        """
        data = self.client._perform_json("GET", "/projects/%s/datasets/%s/info" % (self.project_key, self.dataset_name))
        return DSSDatasetInfo(self, data)

    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Get the flow zone of this dataset

        :rtype: :class:`dataikuapi.dss.flow.DSSFlowZone`
        """
        return self.project.get_flow().get_zone_of_object(self)

    def move_to_zone(self, zone):
        """
        Move this object to a flow zone

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
        Get the recipes or analyses referencing this dataset

        :returns: a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/datasets/%s/usages" % (self.project_key, self.dataset_name))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the dataset

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "DATASET", self.dataset_name)

    ########################################################
    # Test / Autofill
    ########################################################

    _FS_TYPES = ["Filesystem", "UploadedFiles", "FilesInFolder",
                "HDFS", "S3", "Azure", "GCS", "FTP", "SCP", "SFTP"]
    # HTTP is FSLike but not FS                

    _SQL_TYPES = ["JDBC", "PostgreSQL", "MySQL", "Vertica", "Snowflake", "Redshift",
                "Greenplum", "Teradata", "Oracle", "SQLServer", "SAPHANA", "Netezza",
                "BigQuery", "Athena", "hiveserver2", "Synapse", "Databricks"]

    def test_and_detect(self, infer_storage_types=False):
        """Used internally by autodetect_settings. It is not usually required to call this method"""
        settings = self.get_settings()

        if settings.type in self.__class__._FS_TYPES:
            future_resp = self.client._perform_json("POST",
                "/projects/%s/datasets/%s/actions/testAndDetectSettings/fsLike"% (self.project_key, self.dataset_name),
                body = {"detectPossibleFormats" : True, "inferStorageTypes" : infer_storage_types })

            return DSSFuture(self.client, future_resp.get('jobId', None), future_resp)
        elif settings.type in self.__class__._SQL_TYPES:
            return self.client._perform_json("POST",
                "/projects/%s/datasets/%s/actions/testAndDetectSettings/externalSQL"% (self.project_key, self.dataset_name))
        
        elif settings.type == "ElasticSearch":
            return self.client._perform_json("POST",
                "/projects/%s/datasets/%s/actions/testAndDetectSettings/elasticsearch"% (self.project_key, self.dataset_name))

        else:
            raise ValueError("don't know how to test/detect on dataset type:%s" % settings.type)

    def autodetect_settings(self, infer_storage_types=False):
        """
        Detect appropriate settings for this dataset using Dataiku detection engine

        :returns: new suggested settings that you can :meth:`DSSDatasetSettings.save`
        :rtype: :class:`DSSDatasetSettings` or a subclass
        """
        settings = self.get_settings()

        if settings.type in self.__class__._FS_TYPES:
            future = self.test_and_detect(infer_storage_types)
            result = future.wait_for_result()

            if not "format" in result or not result["format"]["ok"]:
                raise DataikuException("Format detection failed, complete response is " + json.dumps(result))

            settings.get_raw()["formatType"] = result["format"]["type"]
            settings.get_raw()["formatParams"] = result["format"]["params"]
            settings.get_raw()["schema"] = result["format"]["schemaDetection"]["newSchema"]

            return settings

        elif settings.type in self.__class__._SQL_TYPES:
            result = self.test_and_detect()

            if not "schemaDetection" in result:
                raise DataikuException("Format detection failed, complete response is " + json.dumps(result))

            settings.get_raw()["schema"] = result["schemaDetection"]["newSchema"]
            return settings
        
        elif settings.type == "ElasticSearch":
            result = self.test_and_detect()

            if not "schemaDetection" in result:
                raise DataikuException("Format detection failed, complete response is " + json.dumps(result))

            settings.get_raw()["schema"] = result["schemaDetection"]["newSchema"]
            return settings

        else:
            raise ValueError("don't know how to test/detect on dataset type:%s" % settings.type)

    def get_as_core_dataset(self):
        """
        Get the :class:`dataiku.Dataset` object corresponding to this dataset
        """
        import dataiku
        return dataiku.Dataset("%s.%s" % (self.project_key, self.dataset_name))

    ########################################################
    # Creation of recipes
    ########################################################

    def new_code_recipe(self, type, code=None, recipe_name=None):
        """
        Start the creation of a new code recipe taking this dataset as input
        
        :param str type: Type of the recipe ('python', 'r', 'pyspark', 'sparkr', 'sql', 'sparksql', 'hive', ...)
        :param str code: The code of the recipe
        """

        if type == "python":
            builder = recipe.PythonRecipeCreator(recipe_name, self.project)
        else:
            builder = recipe.CodeRecipeCreator(recipe_name, type, self.project)
        builder.with_input(self.dataset_name)
        if code is not None:
            builder.with_script(code)
        return builder

    def new_recipe(self, type, recipe_name=None):
        """
        Start the creation of a new recipe taking this dataset as input.
        For more details, please see :meth:`dataikuapi.dss.project.DSSProject.new_recipe`

        :param str type: Type of the recipe
        """
        builder = self.project.new_recipe(type=type, name=recipe_name)
        builder.with_input(self.dataset_name)
        return builder

class DSSDatasetSettings(DSSTaggableObjectSettings):
    """
    Base settings class for a DSS dataset.
    
    .. caution:: Do not instantiate this class directly, use :meth:`DSSDataset.get_settings`

    Use :meth:`save` to save your changes
    """

    def __init__(self, dataset, settings):
        super(DSSDatasetSettings, self).__init__(settings)
        self.dataset = dataset
        self.settings = settings

    def get_raw(self):
        """Get the raw dataset settings as a dict"""
        return self.settings

    def get_raw_params(self):
        """Get the type-specific params, as a raw dict"""
        return self.settings["params"]

    @property
    def type(self):
        return self.settings["type"]

    @property
    def schema_columns(self):
        return self.settings["schema"]["columns"]

    def remove_partitioning(self):
        self.settings["partitioning"] = {"dimensions" : []}

    def add_discrete_partitioning_dimension(self, dim_name):
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "value"})

    def add_time_partitioning_dimension(self, dim_name, period="DAY"):
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "time", "params":{"period": period}})

    def add_raw_schema_column(self, column):
        self.settings["schema"]["columns"].append(column)

    @property
    def is_feature_group(self):
        """
        Indicates whether the Dataset is defined as a Feature Group, available in the Feature Store.

        :rtype: bool
        """
        return self.settings["featureGroup"]

    def set_feature_group(self, status):
        """
        (Un)sets the dataset as a Feature Group, available in the Feature Store.
        Changes of this property will be applied when calling :meth:`save` and require the "Manage Feature Store" permission.

        :param status: whether the dataset should be defined as a feature group
        :type status: bool
        """
        self.settings["featureGroup"] = status

    def save(self):
        self.dataset.client._perform_empty(
                "PUT", "/projects/%s/datasets/%s" % (self.dataset.project_key, self.dataset.dataset_name),
                body=self.settings)

class FSLikeDatasetSettings(DSSDatasetSettings):
    """
    Settings for a files-based dataset. This class inherits from :class:`DSSDatasetSettings`.
    
    .. caution:: Do not instantiate this class directly, use :meth:`DSSDataset.get_settings`

    Use :meth:`save` to save your changes
    """

    def __init__(self, dataset, settings):
        super(FSLikeDatasetSettings, self).__init__(dataset, settings)

    def set_connection_and_path(self, connection, path):
        self.settings["params"]["connection"] = connection
        self.settings["params"]["path"] = path

    def get_raw_format_params(self):
        """Get the raw format parameters as a dict""" 
        return self.settings["formatParams"]

    def set_format(self, format_type, format_params = None):
        if format_params is None:
            format_params = {}
        self.settings["formatType"] = format_type
        self.settings["formatParams"] = format_params

    def set_csv_format(self, separator=",", style="excel", skip_rows_before=0, header_row=True, skip_rows_after=0):
        format_params = {
            "style" : style,
            "separator":  separator,
            "skipRowsBeforeHeader":  skip_rows_before,
            "parseHeaderRow":  header_row,
            "skipRowsAfterHeader":  skip_rows_after
        }
        self.set_format("csv", format_params)

    def set_partitioning_file_pattern(self, pattern):
        self.settings["partitioning"]["filePathPattern"] = pattern

class SQLDatasetSettings(DSSDatasetSettings):
    """
    Settings for a SQL dataset. This class inherits from :class:`DSSDatasetSettings`.
    
    .. caution:: Do not instantiate this class directly, use :meth:`DSSDataset.get_settings`

    Use :meth:`save` to save your changes
    """
    def __init__(self, dataset, settings):
        super(SQLDatasetSettings, self).__init__(dataset, settings)

    def set_table(self, connection, schema, table, catalog=None):
        """
        Sets this SQL dataset in 'table' mode, targeting a particular table of a connection
        Leave catalog to None to target the default database associated with the connection
        """
        self.settings["params"].update({
            "connection": connection,
            "mode": "table",
            "schema": schema,
            "table": table,
            "catalog": catalog
        })

class DSSManagedDatasetCreationHelper(object):
    """Provide an helper to create partitioned dataset

    .. code-block:: python
        
        import dataiku

        client = dataiku.api_client()
        project_key = dataiku.default_project_key()
        project = client.get_project(project_key)

        #create the dataset
        builder = project.new_managed_dataset("py_generated")
        builder.with_store_into("filesystem_folders")
        dataset = builder.create(overwrite=True)

        #setup format & schema  settings
        ds_settings = ds.get_settings()
        ds_settings.set_csv_format()
        ds_settings.add_raw_schema_column({'name':'id', 'type':'int'})
        ds_settings.add_raw_schema_column({'name':'name', 'type':'string'})
        ds_settings.save()

        #put some data
        data = ["foo", "bar"]
        with ds.get_as_core_dataset().get_writer() as writer:
            for idx, val in enumerate(data):
                writer.write_row_array((idx, val))
    
    .. caution:: do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_managed_dataset`
    """


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
        
        :returns: self
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
        :returns: self
        """
        code = 'dataset' if object_type == 'DATASET' else 'folder'
        self.creation_settings["partitioningOptionId"] = "copy:%s:%s" % (code, dataset_ref)
        return self

    def create(self, overwrite=False):
        """
        Executes the creation of the managed dataset according to the selected options
        
        :param overwrite: If the dataset being created already exists, delete it first (removing data), defaults to False
        :type overwrite: bool, optional

        :returns: the newly created dataset
        :rtype: :class:`DSSDataset`
        """
        if overwrite and self.already_exists():
            self.project.get_dataset(self.dataset_name).delete(drop_data = True)

        self.project.client._perform_json("POST", "/projects/%s/datasets/managed" % self.project.project_key,
            body = {
                "name": self.dataset_name,
                "creationSettings":  self.creation_settings
        })
        return DSSDataset(self.project.client, self.project.project_key, self.dataset_name)

    def already_exists(self):
        """
        :returns: whether this managed dataset already exists
        :rtype: bool
        """
        dataset = self.project.get_dataset(self.dataset_name)
        try:
            dataset.get_metadata()
            return True
        except Exception as e:
            return False


class DSSDatasetInfo(object):
    """
    Info class for a DSS dataset (Read-Only).
    
    .. caution:: Do not instantiate this class directly, use :meth:`DSSDataset.get_info`
    """

    def __init__(self, dataset, info):
        self.dataset = dataset
        self.info = info

    def get_raw(self):
        """
        Get the raw dataset full information as a dict

        :returns: the raw dataset full information
        :rtype: dict
        """
        return self.info

    @property
    def last_build_start_time(self):
        """
        The last build start time of the dataset as a :class:`datetime.datetime` or None if there is no last build information.

        :returns: the last build start time
        :rtype: :class:`datetime.datetime` or None
        """
        last_build_info = self.info.get("lastBuild", dict())
        timestamp = last_build_info.get("buildStartTime", None)
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp is not None else None

    @property
    def last_build_end_time(self):
        """
        The last build end time of the dataset as a :class:`datetime.datetime` or None if there is no last build information.

        :returns: the last build end time
        :rtype: :class:`datetime.datetime` or None
        """
        last_build_info = self.info.get("lastBuild", dict())
        timestamp = last_build_info.get("buildEndTime", None)
        return datetime.datetime.fromtimestamp(timestamp / 1000) if timestamp is not None else None

    @property
    def is_last_build_successful(self):
        """
        Get whether the last build of the dataset is successful.

        :returns: True if the last build is successful
        :rtype: bool
        """
        last_build_info = self.info.get("lastBuild", dict())
        success = last_build_info.get("buildSuccess", False)
        return success
