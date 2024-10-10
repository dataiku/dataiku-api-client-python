import datetime

from ..utils import DataikuException, DataikuValueCaster
from ..utils import DataikuStreamedHttpUTF8CSVReader
from ..utils import _timestamp_ms_to_zoned_datetime
import json, warnings
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings
from .future import DSSFuture
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions
from .statistics import DSSStatisticsWorksheet
from .data_quality import DSSDataQualityRuleSet
from . import recipe
import uuid
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
        Get the dataset schema as a dict.
        
        :returns: a dict object of the schema, with the list of columns. See :meth:`DSSDataset.get_schema()`
        :rtype: dict
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
        Get a given column in the dataset schema by its name.
        
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
        """
        Get the dataset identifier.
        
        :rtype: string
        """
        return self.dataset_name

    @property
    def name(self):
        """
        Get the dataset name.
        
        :rtype: string
        """
        return self.dataset_name

    ########################################################
    # Dataset deletion
    ########################################################

    def delete(self, drop_data=False):
        """
        Delete the dataset.

        :param bool drop_data: Should the data of the dataset be dropped, defaults to False
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name), params = {
                "dropData" : drop_data
            })

    ########################################################
    # Dataset renaming
    ########################################################

    def rename(self, new_name):
        """
        Rename the dataset with the new specified name

        :param str new_name: the new name of the dataset
        """
        if self.dataset_name == new_name:
            raise ValueError("Dataset name is already " + new_name)
        obj = {
            "oldName": self.dataset_name,
            "newName": new_name
        }
        self.client._perform_empty("POST", "/projects/%s/actions/renameDataset" % self.project_key, body=obj)
        self.dataset_name = new_name

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
        Get the raw settings of the dataset as a dict.

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
        
        :param dict definition: the definition, as a dict. You should only set a definition object 
                            that has been retrieved using the :meth:`get_definition` call.
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
        Get the dataset schema.
        
        :returns: a dict object of the schema, with the list of columns.
        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        """
        Set the dataset schema.
        
        :param dict schema: the desired schema for the dataset, as a dict. 
                       All columns have to provide their name and type.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_metadata(self):
        """
        Get the metadata attached to this dataset. The metadata contains label, description
        checklists, tags and custom metadata of the dataset
        
        :returns: a dict object. For more information on available metadata, please see
                  https://doc.dataiku.com/dss/api/latest/rest/
        :rtype: dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this dataset.
        
        :param dict metadata: the new state of the metadata for the dataset. You should only set a metadata object 
                         that has been retrieved using the :meth:`get_metadata` call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name),
                body=metadata)


    ########################################################
    # Dataset data
    ########################################################

    def iter_rows(self, partitions=None):
        """
        Get the dataset data as a row-by-row iterator.

        :param partitions: (optional) partition identifier, or list of partitions to include, if applicable.
        :type partitions: Union[string, list[string]]
        :returns: an iterator over the rows, each row being a list of values. The order of values
                  in the list is the same as the order of columns in the schema returned by :meth:`get_schema`
        :rtype: generator[list]
        """
        read_session_id = str(uuid.uuid4())
        csv_stream = self.client._perform_raw(
                "GET" , "/projects/%s/datasets/%s/data/" %(self.project_key, self.dataset_name),
                params = {
                    "format" : "tsv-excel-noheader",
                    "partitions" : partitions,
                    "readSessionId": read_session_id
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema()["columns"], csv_stream, read_session_id=read_session_id,
                                                client=self.client, project_key=self.project_key,
                                                dataset_name=self.dataset_name).iter_rows()


    def list_partitions(self):
        """
        Get the list of all partitions of this dataset.
        
        :returns: the list of partitions, as a list of strings.
        :rtype: list[string]
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/partitions" % (self.project_key, self.dataset_name))


    def clear(self, partitions=None):
        """
        Clear data in this dataset.
        
        :param partitions: (optional) partition identifier, or list of partitions to clear. When not provided, the entire dataset
                           is cleared.
        :type partitions: Union[string, list[string]]

        :returns: a dict containing the method call status.
        :rtype: dict
        """
        return self.client._perform_json(
                "DELETE", "/projects/%s/datasets/%s/data" % (self.project_key, self.dataset_name),
                params={"partitions" : partitions})

    def copy_to(self, target, sync_schema=True, write_mode="OVERWRITE"):
        """
        Copy the data of this dataset to another dataset.

        :param target: an object representing the target of this copy.
        :type target: :class:`dataikuapi.dss.dataset.DSSDataset`
        :param bool sync_schema: (optional) update the target dataset schema to make it match the sourece dataset schema.
        :param string write_mode: (optional) OVERWRITE (default) or APPEND. If OVERWRITE, the output dataset is cleared prior to writing the data.
        :returns: a DSSFuture representing the operation.
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        dqr = {
             "targetProjectKey" : target.project_key,
             "targetDatasetName": target.dataset_name,
             "syncSchema": sync_schema,
             "writeMode" : write_mode
        }
        future_resp = self.client._perform_json("POST", "/projects/%s/datasets/%s/actions/copyTo" % (self.project_key, self.dataset_name), body=dqr)
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)

    def search_data_elastic(self, query_string, start=0, size=128, sort_columns=None, partitions=None):
        """
        .. caution::
            Only for datasets on Elasticsearch connections

        Query the service with a search string to directly fetch data
        
        :param str query_string: Elasticsearch compatible query string
        :param int start: row to start fetching the data
        :param int size: number of results to return
        :param list sort_columns: list of {"column", "order"} dict, which is the order to fetch data. "order" is "asc" for ascending, "desc" for descending
        :param list partitions: if the dataset is partitioned, a list of partition ids to search

        :return: a dict containing "columns", "rows", "warnings", "found" (when start == 0)
        :rtype: dict
        """
        params = {
            "queryString": query_string,
            "start": start,
            "size": size,
            "sortColumns": json.dumps(sort_columns),
            "partitions": json.dumps(partitions),
        }
        future_resp = self.client._perform_json("GET", "/projects/%s/datasets/%s/search-data-elastic" % (self.project_key, self.dataset_name), params=params)
        result = DSSFuture(self.client, future_resp.get("jobId", None), future_resp).wait_for_result()
        value_caster = DataikuValueCaster(result["columns"])
        result["rows"] = [value_caster.cast_values(row) for row in result["rows"]]
        return result

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

        :param job_type: the job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param partitions: if the dataset is partitioned, a list of partition ids to build
        :param bool wait: whether to wait for the job completion before returning the job handle, defaults to True
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

        :param partition: (optional) partition identifier, use ALL to compute metrics on all data.
        :type partition: string
        :param list[string] metric_ids: (optional) ids of the metrics to build

        :returns: a metric computation report, as a dict
        :rtype: dict
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

        .. caution::

            Deprecated. Use :meth:`dataikuapi.dss.data_quality.DSSDataQualityRuleSet.compute_rules` instead

        :param str partition: (optional) partition identifier, use ALL to run checks on all data.
        :param list[string] checks: (optional) ids of the checks to run.

        :returns: a checks computation report, as a dict.
        :rtype: dict
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
        List the files in an "uploaded files" dataset.

        :returns: uploaded files metadata as a list of dicts, with one dict per file.
        :rtype: list[dict]
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

        """Creates a new prediction task in a new visual analysis lab
        for a dataset.

        :param str target_variable: the variable to predict
        :param str ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O (defaults to **PY_MEMORY**)
        :param str guess_policy: Policy to use for setting the default parameters.  Valid values are: DEFAULT,
            SIMPLE_FORMULA, DECISION_TREE, EXPLANATORY and PERFORMANCE (defaults to **DEFAULT**)
        :param str prediction_type: The type of prediction problem this is. If not provided the prediction type will be
            guessed. Valid values are: BINARY_CLASSIFICATION, REGRESSION, MULTICLASS (defaults to **None**)
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing
            the input dataset to determine feature handling and algorithms (defaults to **True**). You should wait for
            the guessing to be completed by calling **wait_guess_complete** on the returned object before doing anything
            else (in particular calling **train** or **get_settings**)

        :returns: A ML task handle of type 'PREDICTION'
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTask`
        """
        return self.project.create_prediction_ml_task(self.dataset_name,
             target_variable = target_variable, ml_backend_type = ml_backend_type,
             guess_policy = guess_policy, prediction_type = prediction_type, wait_guess_complete = wait_guess_complete)

    def create_clustering_ml_task(self, input_dataset,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="KMEANS",
                                  wait_guess_complete=True):
        """Creates a new clustering task in a new visual analysis lab for a dataset.

        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        **wait_guess_complete** on the returned object before doing anything
        else (in particular calling **train** or **get_settings**)

        :param string input_dataset: The dataset to use for training/testing the model
        :param str ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O (defaults to **PY_MEMORY**)
        :param str guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and
            ANOMALY_DETECTION (defaults to **KMEANS**)
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing
            the input dataset to determine feature handling and algorithms (defaults to **True**). You should wait for
            the guessing to be completed by calling **wait_guess_complete** on the returned object before doing anything
            else (in particular calling **train** or **get_settings**)

        :returns: A ML task handle of type 'CLUSTERING'
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTask`
        """
        return self.project.create_clustering_ml_task(self.dataset_name, ml_backend_type=ml_backend_type, guess_policy=guess_policy,
                                                      wait_guess_complete=wait_guess_complete)

    def create_timeseries_forecasting_ml_task(self, target_variable,
                                              time_variable,
                                              timeseries_identifiers=None,
                                              guess_policy="TIMESERIES_DEFAULT",
                                              wait_guess_complete=True):
        """Creates a new time series forecasting task in a new visual analysis lab for a dataset.

        :param string target_variable: The variable to forecast
        :param string time_variable:  Column to be used as time variable. Should be a Date (parsed) column.
        :param list timeseries_identifiers:  List of columns to be used as time series identifiers (when the dataset has multiple series)
        :param string guess_policy: Policy to use for setting the default parameters.
                                    Valid values are: TIMESERIES_DEFAULT, TIMESERIES_STATISTICAL, and TIMESERIES_DEEP_LEARNING
        :param boolean wait_guess_complete: If False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        :returns: A ML task handle of type 'PREDICTION'
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTask`
        """
        return self.project.create_timeseries_forecasting_ml_task(self.dataset_name, target_variable=target_variable,
                                                                  time_variable=time_variable, timeseries_identifiers=timeseries_identifiers,
                                                                  guess_policy=guess_policy, wait_guess_complete=wait_guess_complete)

    def create_causal_prediction_ml_task(self, outcome_variable,
                                         treatment_variable,
                                         prediction_type=None,
                                         wait_guess_complete=True):
        """Creates a new causal prediction task in a new visual analysis lab for a dataset.

        :param string outcome_variable: The outcome variable to predict.
        :param string treatment_variable: The treatment variable.
        :param string or None prediction_type: Valid values are: "CAUSAL_BINARY_CLASSIFICATION", "CAUSAL_REGRESSION" or None (in this case prediction_type will be set by the Guesser)
        :param boolean wait_guess_complete: If False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        :returns: A ML task handle of type 'PREDICTION'
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTask`
        """
        return self.project.create_causal_prediction_ml_task(self.dataset_name, outcome_variable=outcome_variable,
                                                             treatment_variable=treatment_variable, prediction_type=prediction_type,
                                                             wait_guess_complete=wait_guess_complete)

    def create_analysis(self):
        """
        Create a new visual analysis lab for the dataset.

        :returns: A visual analysis handle
        :rtype: :class:`dataikuapi.dss.analysis.DSSAnalysis`
        """
        return self.project.create_analysis(self.dataset_name)

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

        :param bool as_objects: if true, returns the statistics worksheets as :class:`dataikuapi.dss.statistics.DSSStatisticsWorksheet`, else as a list of dicts

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

        :param string name: name of the worksheet

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

        :param partition: (optional) partition identifier, use ALL to retrieve metric values on all data.
        :type partition: string

        :returns: a list of metric objects and their value
        :rtype: :class:`dataikuapi.dss.metrics.ComputedMetrics`
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metrics/last/%s" % (self.project_key, self.dataset_name, 'NP' if len(partition) == 0 else partition)))

    def get_metric_history(self, metric, partition=''):
        """
        Get the history of the values of the metric on this dataset

        :param string metric: id of the metric to get
        :param partition: (optional) partition identifier, use ALL to retrieve metric history on all data.
        :type partition: string

        :returns: a dict containing the values of the metric, cast to the appropriate type (double, boolean,...)
        :rtype: dict
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
        :rtype: list[dict]
        """
        return self.client._perform_json("GET", "/projects/%s/datasets/%s/usages" % (self.project_key, self.dataset_name))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the dataset

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
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
        """Used internally by :meth:`autodetect_settings` It is not usually required to call this method
        
        :param bool infer_storage_types: whether to infer storage types
        """
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

        :param bool infer_storage_types: whether to infer storage types

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

        :rtype: :class:`dataiku.Dataset`
        """
        import dataiku
        return dataiku.Dataset("%s.%s" % (self.project_key, self.dataset_name))

    ########################################################
    # Creation of recipes
    ########################################################

    def new_code_recipe(self, type, code=None, recipe_name=None):
        """
        Start the creation of a new code recipe taking this dataset as input.
        
        :param str type: type of the recipe ('python', 'r', 'pyspark', 'sparkr', 'sql', 'sparksql', 'hive', ...).
        :param str code: the code of the recipe.
        :param str recipe_name: (optional) base name for the new recipe.

        :returns: a handle to the new recipe's creator object.
        :rtype: Union[:class:`dataikuapi.dss.recipe.CodeRecipeCreator`, :class:`dataikuapi.dss.recipe.PythonRecipeCreator`]
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

        :param str type: type of the recipe ('python', 'r', 'pyspark', 'sparkr', 'sql', 'sparksql', 'hive', ...).
        :param str recipe_name: (optional) base name for the new recipe.
        """
        builder = self.project.new_recipe(type=type, name=recipe_name)
        builder.with_input(self.dataset_name)
        return builder

    ########################################################
    # Data Quality
    ########################################################

    def get_data_quality_rules(self):
        """
        Get a handle to interact with the data quality rules of the dataset.

        :returns: A handle to the data quality rules of the dataset.
        :rtype: :class:`dataikuapi.dss.data_quality.DSSDataQualityRuleSet`
        """
        return DSSDataQualityRuleSet(self.project_key, self.dataset_name, self.client)

    ########################################################
    # Column Lineage
    ########################################################

    def get_column_lineage(self, column, max_dataset_count=None):
        """
        Get the full lineage (auto-computed and manual) information of a column in this dataset.
        Column relations with datasets from both local and foreign projects will be included in the result.
 
        :param str column: name of the column to retrieve the lineage on.
        :param integer max_dataset_count: (optional) the maximum number of datasets to query for. If none, then the max hard limit is used. 

        :returns: the full column lineage (auto-computed and manual) as a list of relations.
        :rtype: list of dict
        """
        
        if max_dataset_count is not None and max_dataset_count <= 0:
            raise ValueError("Invalid value, max_dataset_count must be a positive integer.")

        return self.client._perform_json(
            "GET", "/projects/%s/datasets/%s/column-lineage" % (self.project_key, self.dataset_name),
            params={
                "columnName": column,
                "maxDatasetCount": max_dataset_count,
            }
        )

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
        """Get the raw dataset settings as a dict.
        
        :rtype: dict
        """
        return self.settings

    def get_raw_params(self):
        """Get the type-specific params, as a raw dict.
        
        :rtype: dict
        """
        return self.settings["params"]

    @property
    def type(self):
        """Returns the settings type as a string.

        :rtype: string
        """
        return self.settings["type"]

    @property
    def schema_columns(self):
        """
        Get the schema columns settings.
        
        :returns: a list of dicts with column settings.
        :rtype: list[dict]
        """
        return self.settings["schema"]["columns"]

    def remove_partitioning(self):
        """
        Reset partitioning settings to those of a non-partitioned dataset.
        """
        self.settings["partitioning"] = {"dimensions" : []}

    def add_discrete_partitioning_dimension(self, dim_name):
        """
        Add a discrete partitioning dimension to settings.

        :param string dim_name: name of the partition to add.
        """
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "value"})

    def add_time_partitioning_dimension(self, dim_name, period="DAY"):
        """
        Add a time partitioning dimension to settings.

        :param string dim_name: name of the partition to add.
        :param string period: (optional) time granularity of the created partition. Can be YEAR, MONTH, DAY, HOUR.
        """
        self.settings["partitioning"]["dimensions"].append({"name": dim_name, "type": "time", "params":{"period": period}})

    def add_raw_schema_column(self, column):
        """
        Add a column to the schema settings.

        :param dict column: column settings to add.
        """
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
        """
        Save settings.
        """
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
        """
        Set connection and path parameters.

        :param string connection: connection to use.
        :param string path: path to use.
        """
        self.settings["params"]["connection"] = connection
        self.settings["params"]["path"] = path

    def get_raw_format_params(self):
        """
        Get the raw format parameters as a dict.
        
        :rtype: dict
        """
        return self.settings["formatParams"]

    def set_format(self, format_type, format_params = None):
        """
        Set format parameters.

        :param string format_type: format type to use.
        :param dict format_params: dict of parameters to assign to the formatParams settings section.
        """
        if format_params is None:
            format_params = {}
        self.settings["formatType"] = format_type
        self.settings["formatParams"] = format_params

    def set_csv_format(self, separator=",", style="excel", skip_rows_before=0, header_row=True, skip_rows_after=0):
        """
        Set format parameters for a csv-based dataset.

        :param string separator: (optional) separator to use, default is ','".
        :param string style: (optional) style to use, default is 'excel'.
        :param int skip_rows_before: (optional) number of rows to skip before header, default is 0.
        :param bool header_row: (optional) wheter or not the header row is parsed, default is true.
        :param int skip_rows_after: (optional) number of rows to skip before header, default is 0.
        """
        format_params = {
            "style" : style,
            "separator":  separator,
            "skipRowsBeforeHeader":  skip_rows_before,
            "parseHeaderRow":  header_row,
            "skipRowsAfterHeader":  skip_rows_after
        }
        self.set_format("csv", format_params)

    def set_partitioning_file_pattern(self, pattern):
        """
        Set the dataset partitionning file pattern.

        :param str pattern: pattern to set.
        """
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
    
    .. caution:: Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_managed_dataset`
    """


    def __init__(self, project, dataset_name):
        self.project = project
        self.dataset_name = dataset_name
        self.creation_settings = { "specificSettings" : {} }

    def get_creation_settings(self):
        """
        Get the dataset creation settings as a dict.

        :rtype: dict
        """
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
        Sets the new managed dataset to use the same partitioning as an existing dataset

        :param str dataset_ref: Name of the dataset to copy partitioning from
        :param str object_type: Type of the object to copy partitioning from, values can be DATASET or FOLDER

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
        Check if dataset already exists.

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
        return _timestamp_ms_to_zoned_datetime(timestamp)

    @property
    def last_build_end_time(self):
        """
        The last build end time of the dataset as a :class:`datetime.datetime` or None if there is no last build information.

        :returns: the last build end time
        :rtype: :class:`datetime.datetime` or None
        """
        last_build_info = self.info.get("lastBuild", dict())
        timestamp = last_build_info.get("buildEndTime", None)
        return _timestamp_ms_to_zoned_datetime(timestamp)

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
