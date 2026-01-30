import json
import warnings
from io import BytesIO

from .discussion import DSSObjectDiscussions
from .drift import DataDriftResult, DriftResult
from .future import DSSFuture
from .metrics import ComputedMetrics

try:
    basestring
except NameError:
    basestring = str


class DSSEvaluationStore(object):
    """
    A handle to interact with an evaluation store on the DSS instance.

    .. warning::
        Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_evaluation_store`
    """

    def __init__(self, client, project_key, evaluation_store_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.evaluation_store_id = evaluation_store_id

    @property
    def id(self):
        return self.evaluation_store_id

    def _fetch_settings(self):
        url = "/projects/%s/evaluationstores/%s" % (self.project_key, self.id)
        return self.client._perform_json("GET", url)

    def get_settings(self):
        """
        Returns the settings of this evaluation store.

        :rtype: DSSEvaluationStoreSettings
        """
        data = self._fetch_settings()
        return DSSEvaluationStoreSettings(self, data)

    ########################################################
    # Evaluations
    ########################################################

    def _fetch_evaluations(self):
        url = "/projects/%s/evaluationstores/%s/evaluations/" % (self.project_key, self.id)
        return self.client._perform_json("GET", url)

    def _fetch_latest_evaluation_id(self):
        url = "/projects/%s/evaluationstores/%s/latestEvaluationId" % (self.project_key, self.id)
        return self.client._perform_text("GET", url)

    def list_evaluations(self):
        """
        List the evaluations in this evaluation store. The list is sorted by creation date.

        :returns: The list of the evaluations
        :rtype: list of :class:`dataikuapi.dss.evaluationstore.DSSEvaluation`
        """
        items = self._fetch_evaluations()
        return [DSSEvaluation(self, item["ref"]["evaluationId"]) for item in items]

    def get_evaluation(self, evaluation_id):
        """
        Get a handle to interact with a specific evaluation

        :param string evaluation_id: the id of the desired evaluation

        :returns: A :class:`dataikuapi.dss.evaluation.DSSEvaluation` evaluation handle
        """
        return DSSEvaluation(self, evaluation_id)

    def get_latest_evaluation(self):
        """
        Get a handle to interact with the latest evaluation computed

        :returns: A :class:`dataikuapi.dss.evaluation.DSSEvaluation` evaluation handle if the store is not empty, else None
        """
        latest_evaluation_id = self._fetch_latest_evaluation_id()
        if not latest_evaluation_id:
            return None
        return DSSEvaluation(self, latest_evaluation_id)

    def delete_evaluations(self, evaluations):
        """
        Remove evaluations from this store
        """
        obj = []
        for evaluation in evaluations:
            if isinstance(evaluation, DSSEvaluation):
                obj.append(evaluation.evaluation_id)
            elif isinstance(evaluation, dict):
                obj.append(evaluation["evaluation_id"])
            else:
                obj.append(evaluation)
        url = "/projects/%s/evaluationstores/%s/evaluations/" % (self.project_key, self.id)
        self.client._perform_json("DELETE", url, body=obj)

    def build(self, job_type="NON_RECURSIVE_FORCED_BUILD", wait=True, no_fail=False):
        """
        Starts a new job to build this evaluation store and wait for it to complete.
        Raises if the job failed.

        .. code-block:: python

            job = mes.build()
            print("Job %s done" % job.id)

        :param job_type: The job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param wait: wait for the build to finish before returning
        :param no_fail: if True, does not raise if the job failed. Valid only when wait is True
        :return: the :class:`dataikuapi.dss.job.DSSJob` job handle corresponding to the built job
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        jd = self.project.new_job(job_type)
        jd.with_output(self.id, object_type="MODEL_EVALUATION_STORE")
        if wait:
            return jd.start_and_wait(no_fail)
        else:
            return jd.start(allowFail=not no_fail)

    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this evaluation store

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
        Get the recipes referencing evaluation store

        :return: a list of usages
        """
        return self.client._perform_json(
            "GET", "/projects/%s/evaluationstores/%s/usages" % (self.project_key, self.id)
        )

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the evaluation store

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MODEL_EVALUATION_STORE", self.id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the evaluation store
        """
        url = "/projects/%s/evaluationstores/%s" % (self.project_key, self.id)
        return self.client._perform_empty("DELETE", url)

    ########################################################
    # Metrics
    ########################################################

    class MetricDefinition(dict):
        def __init__(self, code, value, name=None, description=None):
            dict.__init__(self, {"metricCode": code, "value": value, "name": name, "description": description})

    class LabelDefinition(dict):
        def __init__(self, key, value):
            dict.__init__(self, {"key": key, "value": value})

    def get_last_metric_values(self):
        """
        Get the metrics of the latest evaluation built

        :returns:
            a list of metric objects and their value
        """
        url = "/projects/%s/evaluationstores/%s/metrics/last" % (self.project_key, self.id)
        return ComputedMetrics(self.client._perform_json("GET", url))

    def get_metric_history(self, metric):
        """
        Get the history of the values of the metric on this evaluation store

        :returns:
            an object containing the values of the metric, cast to the appropriate type (double, boolean,...)
        """
        url = "/projects/%s/evaluationstores/%s/metrics/history" % (self.project_key, self.id)
        metric_lookup = metric if isinstance(metric, str) or isinstance(metric, unicode) else json.dumps(metric)
        return self.client._perform_json("GET", url, params={"metricLookup": metric_lookup})

    def compute_metrics(self, metric_ids=None, probes=None):
        """
        Compute metrics on this evaluation store. If the metrics are not specified, the metrics setup on the evaluation
        store are used.
        """
        url = "/projects/%s/evaluationstores/%s/actions" % (self.project_key, self.evaluation_store_id)
        if metric_ids is not None:
            return self.client._perform_json("POST", "%s/computeMetricsFromIds" % url, body={"metricIds": metric_ids})
        elif probes is not None:
            return self.client._perform_json("POST", "%s/computeMetrics" % url, body=probes)
        else:
            return self.client._perform_json("POST", "%s/computeMetrics" % url)

    def run_checks(self, evaluation_id="", checks=None):
        """
        Run checks on a partition of this evaluation store.

        If the checks are not specified, the checks setup on the evaluation store are used.

        :param str evaluation_id: (optional) id of evaluation on which checks should be run. Last evaluation is used if not specified.
        :param list[str] | dict checks: (optional) The checks to run. This can be:

                       - A **list of strings**: The labels of the checks to run.
                       - A **dictionary**: The full definition of the checks (e.g., ``{"checks": [...]}``).

        :returns: a checks computation report, as a dict.
        :rtype: dict
        """
        if checks is None:
            return self.client._perform_json(
                "POST",
                "/projects/%s/evaluationstores/%s/actions/runChecks" % (self.project_key, self.id),
                params={"evaluationId": evaluation_id},
            )
        else:
            return self.client._perform_json(
                "POST",
                "/projects/%s/evaluationstores/%s/actions/runChecks" % (self.project_key, self.id),
                params={"evaluationId": evaluation_id},
                body=checks,
            )

    def add_custom_evaluation(self, metrics, evaluation_id=None, name=None, labels=None, model=None):
        """
        Adds an evaluation with custom metrics to the evaluation store.

        :param list[DSSEvaluationStore.MetricDefinition] metrics: the metrics to add.
        :param str evaluation_id: the id of the evaluation (optional)
        :param str name: the human-readable name of the evaluation (optional)
        :param list[DSSEvaluationStore.LabelDefinition] labels: labels to set on the evaluation (optional). See below.
        :param model: saved model version (full ID or DSSTrainedPredictionModelDetails) of the evaluated model
            (optional). Should only be used with *model* evaluation stores
        :type model: Union[str,  DSSTrainedPredictionModelDetails]

        Code sample:

        .. code-block:: python

            import dataiku
            from dataikuapi.dss.evaluationstore import DSSEvaluationStore

            client = dataiku.api_client()
            project = client.get_default_project()
            mes = project.get_evaluation_store("7vFZWNck")

            accuracy = DSSEvaluationStore.MetricDefinition("accuracy", 0.95, "Accuracy")
            other = DSSEvaluationStore.MetricDefinition("other", 42, "Other", "Other metric desc")
            label = DSSEvaluationStore.LabelDefinition("custom:myLabel", "myValue")

            evaluation_store.add_custom_evaluation([accuracy, other], labels=[label])
            mes.run_checks()
        """
        if hasattr(model, "full_id"):
            model = model.full_id

        url = "/projects/%s/evaluationstores/%s/evaluations" % (self.project_key, self.id)
        return self.client._perform_json(
            "POST",
            url,
            body={
                "evaluationId": evaluation_id,
                "name": name,
                "metrics": metrics,
                "labels": labels,
                "fullModelId": model,
            },
        )


class DSSEvaluationStoreSettings(object):
    """
    A handle on the settings of an evaluation store

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.evaluationstore.DSSEvaluationStore.get_settings`
    """

    def __init__(self, evaluation_store, settings):
        self.evaluation_store = evaluation_store
        self.settings = settings

    def get_raw(self):
        return self.settings

    def save(self):
        url = "/projects/%s/evaluationstores/%s" % (self.evaluation_store.project_key, self.evaluation_store.id)
        self.evaluation_store.client._perform_empty("PUT", url, body=self.settings)


class DSSEvaluation(object):
    """
    A handle on an evaluation

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.evaluationstore.DSSEvaluationStore.get_evaluation`
    """

    def __init__(self, evaluation_store, evaluation_id):
        self.evaluation_store = evaluation_store
        self.client = evaluation_store.client
        # unpack some fields
        self.evaluation_id = evaluation_id
        self.project_key = evaluation_store.project_key
        self.evaluation_store_id = evaluation_store.id

    def get_full_id(self):
        return self.full_id

    @property
    def full_id(self):
        return "ME-{}-{}-{}".format(self.project_key, self.evaluation_store_id, self.evaluation_id)

    def delete(self):
        """
        Remove this evaluation
        """
        obj = [self.evaluation_id]
        url = "/projects/%s/evaluationstores/%s/evaluations/" % (self.project_key, self.evaluation_store_id)
        self.client._perform_json("DELETE", url, body=obj)

    def get_metrics(self):
        """
        Get the metrics for this evaluation. Metrics must be understood here as Metrics in DSS Metrics & Checks

        :return: the metrics, as a JSON object
        """
        url = "/projects/%s/evaluationstores/%s/evaluations/%s/metrics" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )
        return self.client._perform_json("GET", url)

    def _fetch_evaluation(self):
        url = "/projects/%s/evaluationstores/%s/evaluations/%s" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )
        return self.client._perform_json("GET", url)

    def get_full_info(self):
        """
        Retrieve the model evaluation with its performance data

        :return: the model evaluation full info, as a :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationFullInfo`
        """
        data = self._fetch_evaluation()
        prediction_type = data["evaluation"].get("predictionType")
        if prediction_type == "TIMESERIES_FORECAST":
            return DSSTimeSeriesModelEvaluationFullInfo(self, data)
        else:
            return DSSEvaluationFullInfo(self, data)

    def compute_data_drift(self, reference=None, data_drift_params=None, wait=True):
        """
        Compute data drift against a reference model or model evaluation. The reference is determined automatically unless specified.

        Note that this method is only available for model evaluations stores.

        .. attention::
            Deprecated. Use :meth:`dataikuapi.dss.evaluationstore.DSSEvaluationStore.compute_drift` instead

        :param reference: saved model version (full ID or DSSTrainedPredictionModelDetails)
            or model evaluation (full ID or DSSEvaluation) to use as reference (optional)
        :type reference: Union[str, DSSEvaluation, DSSTrainedPredictionDetails]
        :param data_drift_params: data drift computation settings as a :class:`dataikuapi.dss.drift.DataDriftParams` (optional)
        :type data_drift_params: DataDriftParams
        :param wait: data drift computation settings (optional)
        :returns: a :class:`dataikuapi.dss.drift.DataDriftResult` containing data drift analysis results if `wait` is `True`, or a :class:`~dataikuapi.dss.future.DSSFuture` handle otherwise
        """

        warnings.warn("This method is deprecated. Use DSSEvaluationStore.compute_drift instead", DeprecationWarning)

        if hasattr(reference, "full_id"):
            reference = reference.full_id

        if data_drift_params:
            data_drift_params = data_drift_params.data

        url = "/projects/%s/evaluationstores/%s/evaluations/%s/computeDataDrift" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )
        future_response = self.client._perform_json(
            "POST", url, body={"referenceId": reference, "dataDriftParams": data_drift_params}
        )
        future = DSSFuture(
            self.client, future_response.get("jobId", None), future_response, result_wrapper=DataDriftResult
        )
        return future.wait_for_result() if wait else future

    def compute_drift(self, reference=None, drift_params=None, wait=True):
        """
        Compute drift against a reference model or model evaluation. The reference is determined automatically unless specified.

        Note that this method is only available for model evaluations stores.

        :param reference: saved model version (full ID or DSSTrainedPredictionModelDetails)
                or model evaluation (full ID or DSSEvaluation) to use as reference (optional)
        :type reference: Union[str, DSSEvaluation, DSSTrainedPredictionModelDetails]
        :param drift_params: drift computation settings as a :class:`dataikuapi.dss.drift.DriftParams` (optional)
        :type drift_params: DriftParams
        :param wait: data drift computation settings (optional)
        :returns: a :class:`dataikuapi.dss.drift.DriftResult` containing data drift analysis results if `wait` is `True`, or a :class:`~dataikuapi.dss.future.DSSFuture` handle otherwise
        """

        if hasattr(reference, "full_id"):
            reference = reference.full_id

        if drift_params:
            drift_params = drift_params.data

        url = "/projects/%s/evaluationstores/%s/evaluations/%s/computeDrift" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )

        future_response = self.client._perform_json(
            "POST", url, body={"referenceId": reference, "driftParams": drift_params}
        )
        future = DSSFuture(self.client, future_response.get("jobId", None), future_response, result_wrapper=DriftResult)
        return future.wait_for_result() if wait else future

    def get_sample_df(self):
        """
        Get the sample of the evaluation dataset on which the evaluation was performed.

        Note that this method is only available for model evaluations stores.

        :return:
            the sample content, as a :class:`pandas.DataFrame`
        """
        buf = BytesIO()
        sample_url = "/projects/%s/evaluationstores/%s/evaluations/%s/sample" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )
        with self.client._perform_raw("GET", sample_url).raw as f:
            buf.write(f.read())

        schema_url = "/projects/%s/evaluationstores/%s/evaluations/%s/schema" % (
            self.project_key,
            self.evaluation_store_id,
            self.evaluation_id,
        )
        schema_txt = self.client._perform_raw("GET", schema_url).text
        schema = json.loads(schema_txt)

        import pandas as pd

        return pd.read_csv(
            BytesIO(buf.getvalue()),
            compression="gzip",
            sep="\t",
            header=None,
            names=[c["name"] for c in schema["columns"]],
        )


class DSSEvaluationFullInfo:
    """
    A handle on the full information on an evaluation.

    Includes information such as the full id of the evaluated model/LLM/Agent, the evaluation params, the performance
    and drift metrics (if any), etc.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.evaluationstore.DSSEvaluation.get_full_info`
    """

    def __init__(self, evaluation, full_info):
        self.evaluation = evaluation
        self.full_info = full_info
        # The performance and data drift metric, if any
        self.metrics = self.full_info["metrics"]  # type: dict
        # The date and time of the creation of the evaluation, as an epoch
        self.creation_date = self.full_info["evaluation"]["created"]  # type: int
        self.full_id = self.full_info["evaluation"]["ref"]["fullId"]  # type: str
        if "modelRef" in self.full_info["evaluation"]:
            self.model_full_id = self.full_info["evaluation"]["modelRef"]["fullId"]  # type: str
        else:
            self.model_full_id = None
        self.prediction_type = self.full_info["evaluation"].get("predictionType")  # type: str
        self.prediction_variable = self.full_info["evaluation"].get("predictionVariable")  # type: str
        self.target_variable = self.full_info["evaluation"].get("targetVariable")  # type: str

        self.has_model = self.full_info["evaluation"].get("hasModel")
        # The user-accessible metadata (name, labels). Returns the original object, not a copy. Changes to the returned
        # object are persisted to DSS by calling :meth:`save_user_meta`."""
        self.user_meta = self.full_info["evaluation"]["userMeta"]  # type: dict

    def get_raw(self):
        return self.full_info

    def save_user_meta(self):
        url = "/projects/%s/evaluationstores/%s/evaluations/%s/user-meta" % (
            self.evaluation.project_key,
            self.evaluation.mes_id,
            self.evaluation.evaluation_id,
        )
        return self.evaluation.client._perform_text("PUT", url, body=self.user_meta)


class DSSTimeSeriesModelEvaluationFullInfo(DSSEvaluationFullInfo):
    """
    A handle on the full information on a time series model evaluation.

    Includes information such as the full id of the evaluated model, the evaluation params,
    the performance metrics, if any, etc.

    Also provides methods for retrieving per-timeseries performance metrics.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.evaluationstore.DSSEvaluation.get_full_info`
    """

    def __init__(self, model_evaluation, full_info):
        super(DSSTimeSeriesModelEvaluationFullInfo, self).__init__(model_evaluation, full_info)

    @property
    def model_evaluation(self):
        return self.evaluation

    def get_per_timeseries_metrics(self):
        """
        Returns per timeseries performance metrics for this model evaluation.

        :returns: a dict of performance metrics values
        :rtype: dict
        """
        url = "/projects/%s/evaluationstores/%s/evaluations/%s/per-timeseries-metrics" % (
            self.evaluation.project_key,
            self.evaluation.evaluation_store_id,
            self.evaluation.evaluation_id,
        )
        return self.evaluation.client._perform_json("GET", url)
