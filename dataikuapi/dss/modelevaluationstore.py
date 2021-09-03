import json

from dataikuapi.dss.metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions

from requests import utils

try:
    basestring
except NameError:
    basestring = str

class DSSModelEvaluationStore(object):
    """
    A handle to interact with a model evaluation store on the DSS instance.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_model_evaluation_store`
    """
    def __init__(self, client, project_key, mes_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.mes_id = mes_id

    @property
    def id(self):
        return self.mes_id

    def get_settings(self):
        """
        Returns the settings of this model evaluation store.

        :rtype: DSSModelEvaluationStoreSettings
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/modelevaluationstores/%s" % (self.project_key, self.mes_id))
        return DSSModelEvaluationStoreSettings(self, data)


    ########################################################
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this model evaluation store

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
        Get the recipes referencing this model evaluation store

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/modelevaluationstores/%s/usages" % (self.project_key, self.mes_id))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the model evaluation store

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MODEL_EVALUATION_STORE", self.mes_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the model evaluation store

        """
        return self.client._perform_empty("DELETE", "/projects/%s/modelevaluationstores/%s" % (self.project_key, self.mes_id))


    ########################################################
    # Model evaluations
    ########################################################

    def list_model_evaluations(self):
        """
        List the model evaluations in this model evaluation store. The list is sorted
        by ME creation date.

        :returns: The list of the model evaluations
        :rtype: list of :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation`
        """
        items = self.client._perform_json("GET", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id))
        return [DSSModelEvaluation(self, item["ref"]["runId"]) for item in items]

    def get_model_evaluation(self, run_id):
        """
        Get a handle to interact with a specific model evaluation
       
        :param string run_id: the id of the desired model evaluation
        
        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
        """
        return DSSModelEvaluation(self, run_id)

    def get_latest_model_evaluation(self):
        """
        Get a handle to interact with the latest model evaluation computed


        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
        """

        latest_run_id = self.client._perform_text(
            "GET", "/projects/%s/modelevaluationstores/%s/latestRunId" % (self.project_key, self.mes_id))
        return DSSModelEvaluation(self, latest_run_id)

    def delete_model_evaluations(self, evaluations):
        """
        Remove model evaluations from this store
        """
        obj = []
        for evaluation in evaluations:
            if isinstance(evaluation, DSSModelEvaluation):
                obj.append(evaluation.run_id)
            elif isinstance(evaluation, dict):
                obj.append(evaluation['run_id'])
            else:
                obj.append(evaluation)
        self.client._perform_json(
                "DELETE", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id, self.run_id), body=obj)

    def build(self, job_type="NON_RECURSIVE_FORCED_BUILD", wait=True, no_fail=False):
        """
        Starts a new job to build this Model Evaluation Store and wait for it to complete.
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
        jd.with_output(self.mes_id, object_type="MODEL_EVALUATION_STORE")
        if wait:
            return jd.start_and_wait(no_fail)
        else:
            return jd.start(allowFail=not no_fail)


    ########################################################
    # Metrics
    ########################################################

    def get_last_metric_values(self):
        """
        Get the metrics of the latest model evaluation built

        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
            "GET", "/projects/%s/modelevaluationstores/%s/metrics/last" % (self.project_key, self.mes_id)))


    def get_metric_history(self, metric):
        """
        Get the history of the values of the metric on this model evaluation store

        Returns:
            an object containing the values of the metric, cast to the appropriate type (double, boolean,...)
        """
        return self.client._perform_json(
            "GET", "/projects/%s/modelevaluationstores/%s/metrics/history" % (self.project_key, self.mes_id),
            params={'metricLookup': metric if isinstance(metric, str)or isinstance(metric, unicode)
                                           else json.dumps(metric)})

    def compute_metrics(self, metric_ids=None, probes=None):
        """
        Compute metrics on this model evaluation store. If the metrics are not specified, the metrics
        setup on the model evaluation store are used.
        """
        url = "/projects/%s/modelevaluationstores/%s/actions" % (self.project_key, self.mes_id)
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



class DSSModelEvaluationStoreSettings:
    """
    A handle on the settings of a model evaluation store

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelEvaluationStore.get_settings`
    """

    def __init__(self, model_evaluation_store, settings):
        self.model_evaluation_store = model_evaluation_store
        self.settings = settings

    def get_raw(self):
        return self.settings

    def save(self):
        self.model_evaluation_store.client._perform_empty(
                "PUT", "/projects/%s/modelevaluationstores/%s" % (self.model_evaluation_store.project_key, self.model_evaluation_store.mes_id),
                body=self.settings)


class DSSModelEvaluation:
    """
    A handle on a model evaluation

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelEvaluationStore.get_model_evaluation`
    """

    def __init__(self, model_evaluation_store, run_id):
        self.model_evaluation_store = model_evaluation_store
        self.client = model_evaluation_store.client
        # unpack some fields
        self.run_id = run_id
        self.project_key = model_evaluation_store.project_key
        self.mes_id = model_evaluation_store.mes_id

    def get_full_info(self):
        """
        Retrieve the model evaluation with its performance data
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/modelevaluationstores/%s/runs/%s" % (self.project_key, self.mes_id, self.run_id))
        return DSSModelEvaluationFullInfo(self, data)

    def delete(self):
        """
        Remove this model evaluation
        """
        obj = [self.run_id]
        self.client._perform_json(
                "DELETE", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id), body=obj)

    def get_metrics(self):
        """
        Get the metrics for this model evaluation. Metrics must be understood here as Metrics in DSS Metrics & Checks

        :return: the metrics, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/modelevaluationstores/%s/runs/%s/metrics" % (self.project_key, self.mes_id, self.run_id))


class DSSModelEvaluationFullInfo:
    """
    A handle on the full information on a model evaluation.

    Includes information such as the full id of the evaluated model, the evaluation params,
    the performance and drift metrics, if any, etc.

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelEvaluation.get_full_info`
    """
    def __init__(self, model_evaluation, full_info):
        self.model_evaluation = model_evaluation
        self.full_info = full_info

    def get_raw(self):
        return self.full_info

    def get_metrics(self):
        """
        Get the metrics evaluated, if any.

        :return: a dict containing the performance and data drift metric, if any
        """
        return self.full_info["metrics"]

    def get_labels(self):
        """
        Get the labels of the Model Evaluation

        :return: a dict containing the labels
        """
        return self.full_info["evaluation"]["labels"]

    def get_evaluation_parameters(self):
        """
        Get info on the evaluation parameters, most noticeably the evaluation metric (evaluationMetric field
        of the returned dict)

        :return: a dict
        """
        return self.full_info["evaluation"]["metricParams"]

    def get_creation_date(self):
        """
        Return the date and time of the creation of the Model Evaluation

        :return: the date and time, as an epoch
        """
        return self.full_info["evaluation"]["created"]