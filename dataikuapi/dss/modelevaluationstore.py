# Unused imports are needed for backwards compatibility
from .drift import (
    DataDriftParams,
    DriftParams,
    PerColumnDriftParamBuilder,
    DataDriftResult,
    DriftResult,
    DriftModelResult,
    UnivariateDriftResult,
    PredictionDriftResult,
    ColumnSettings,
    DriftModelAccuracy,
)
from .evaluationstore import (
    DSSEvaluationStore,
    DSSEvaluationStoreSettings,
    DSSEvaluation,
    DSSEvaluationFullInfo,
    DSSTimeSeriesModelEvaluationFullInfo,
)

try:
    basestring
except NameError:
    basestring = str


class DSSModelEvaluationStore(DSSEvaluationStore):
    """
    A handle to interact with a model evaluation store on the DSS instance.

    .. warning::
        Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_model_evaluation_store`
    """
    def __init__(self, client, project_key, mes_id):
        super(DSSModelEvaluationStore, self).__init__(client, project_key, mes_id)

    @property
    def mes_id(self):
        return self.id

    def get_settings(self):
        """
        Returns the settings of this model evaluation store.

        :rtype: DSSModelEvaluationStoreSettings
        """
        data = self._fetch_settings()
        return DSSModelEvaluationStoreSettings(self, data)

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
        items = self._fetch_evaluations()
        return [DSSModelEvaluation(self, item["ref"]["evaluationId"]) for item in items]

    def get_model_evaluation(self, evaluation_id):
        """
        Get a handle to interact with a specific model evaluation

        :param string evaluation_id: the id of the desired model evaluation

        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
        """
        return DSSModelEvaluation(self, evaluation_id)

    def get_latest_model_evaluation(self):
        """
        Get a handle to interact with the latest model evaluation computed

        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
            if the store is not empty, else None
        """
        latest_evaluation_id = self._fetch_latest_evaluation_id()
        if not latest_evaluation_id:
            return None
        return DSSModelEvaluation(self, latest_evaluation_id)

    def delete_model_evaluations(self, evaluations):
        self.delete_evaluations(evaluations)

    ########################################################
    # Metrics
    ########################################################

    # Here for backwards compatibility
    MetricDefinition = DSSEvaluationStore.MetricDefinition
    LabelDefinition = DSSEvaluationStore.LabelDefinition

    def add_custom_model_evaluation(self, metrics, evaluation_id=None, name=None, labels=None, model=None):
        """
        Adds a model evaluation with custom metrics to the model evaluation store.

        :param list[DSSModelEvaluationStore.MetricDefinition] metrics: the metrics to add.
        :param str evaluation_id: the id of the evaluation (optional)
        :param str name: the human-readable name of the evaluation (optional)
        :param list[DSSModelEvaluationStore.LabelDefinition] labels: labels to set on the model evaluation (optionam). See below.
        :param model: saved model version (full ID or DSSTrainedPredictionModelDetails) of the evaluated model (optional)
        :type model: Union[str,  DSSTrainedPredictionModelDetails]

        Code sample:

        .. code-block:: python

            import dataiku
            from dataikuapi.dss.modelevaluationstore import DSSModelEvaluationStore

            client=dataiku.api_client()
            project=client.get_default_project()
            mes=project.get_model_evaluation_store("7vFZWNck")

            accuracy = DSSModelEvaluationStore.MetricDefinition("accuracy", 0.95, "Accuracy")
            other = DSSModelEvaluationStore.MetricDefinition("other", 42, "Other", "Other metric desc")
            label = DSSModelEvaluationStore.LabelDefinition("custom:myLabel", "myValue")

            mes.add_custom_model_evaluation([accuracy, other], labels=[label])
            mes.run_checks()
        """
        super(DSSModelEvaluationStore, self).add_custom_evaluation(metrics, evaluation_id, name, labels, model)


class DSSModelEvaluationStoreSettings(DSSEvaluationStoreSettings):
    """
    A handle on the settings of a model evaluation store

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationStore.get_settings`
    """

    @property
    def model_evaluation_store(self):
        return self.evaluation_store

    def __init__(self, model_evaluation_store, settings):
        super(DSSModelEvaluationStoreSettings, self).__init__(model_evaluation_store, settings)


class DSSModelEvaluation(DSSEvaluation):
    """
    A handle on a model evaluation

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluationStore.get_model_evaluation`
    """

    def __init__(self, model_evaluation_store, evaluation_id):
        super(DSSModelEvaluation, self).__init__(model_evaluation_store, evaluation_id)

    @property
    def mes_id(self):
        return self.evaluation_store.id

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
            return DSSModelEvaluationFullInfo(self, data)


class DSSModelEvaluationFullInfo(DSSEvaluationFullInfo):
    """
    A handle on the full information on a model evaluation.

    Includes information such as the full id of the evaluated model, the evaluation params,
    the performance and drift metrics, if any, etc.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation.get_full_info`
    """
    def __init__(self, model_evaluation, full_info):
        super(DSSModelEvaluationFullInfo, self).__init__(model_evaluation, full_info)

    @property
    def model_evaluation(self):
        return self.evaluation
