import warnings

from .discussion import DSSObjectDiscussions
from .evaluationcomparison import DSSEvaluationComparisonSettings, DSSEvaluationComparison
import re


class DSSModelComparison(DSSEvaluationComparison):
    """
    A handle to interact with a model comparison on the DSS instance

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_model_comparison`
    """
    def __init__(self, client, project_key, mec_id):
        super(DSSModelComparison, self).__init__(client, project_key, mec_id)

    @property
    def id(self):
        return self.comparison_id

    @property
    def mec_id(self):
        return self.comparison_id

    def get_settings(self):
        """
        Returns the settings of this model comparison

        :rtype: :class:`dataikuapi.dss.modelcomparison.DSSModelComparisonSettings`
        """
        data = self._fetch_settings()
        return DSSModelComparisonSettings(self, data)

    def get_evaluation_like_from_full_id(self, full_id):
        """
        Retrieves a Saved Model from the flow, a Lab Model from an Analysis or a Model Evaluation from a Model Evaluation Store) using its full id.

        :param string full_id: the full id of the item to retrieve

        :returns: A handle on the Saved Model, the Model Evaluation or the Lab Model
        :rtype: :class:`dataikuapi.dss.savedmodel.DSSSavedModel`
        :rtype: :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation`
        :rtype: :class:`dataikuapi.dss.ml.DSSTrainedPredictionModelDetails`
        """

        saved_model_pattern = re.compile("^S-(\\w+)-(\\w+)-(\\w+)(?:-part-(\\w+)-(v?\\d+))?$\\Z")
        analysis_model_pattern = re.compile("^A-(\\w+)-(\\w+)-(\\w+)-(s[0-9]+)-(pp[0-9]+(?:-part-(\\w+)|-base)?)-(m[0-9]+)$\\Z")
        model_evaluation_pattern = re.compile("^ME-(\\w+)-(\\w+)-(\\w+)$\\Z")

        if saved_model_pattern.match(full_id):
            return self.project.get_saved_model(full_id)
        elif model_evaluation_pattern.match(full_id):
            mes_id = full_id.split('-')[2]
            evaluation_id = full_id.split('-')[3]
            mes = self.project.get_model_evaluation_store(mes_id)
            return mes.get_model_evaluation(evaluation_id)
        elif analysis_model_pattern.match(full_id):
            analysis_id = full_id.split('-')[2]
            task_id = full_id.split('-')[3]
            return self.project.get_ml_task(analysis_id, task_id).get_trained_model_details(full_id)

        raise ValueError("{} is not a valid full model id or full model evaluation id.".format(full_id))


class DSSModelComparisonSettings(DSSEvaluationComparisonSettings):
    """
    A handle on the settings of a model comparison

    A model comparison has:
    - a display name ;
    - a prediction type ;
    - a list of full ids of items to compare

    The prediction type can be:
    - BINARY_CLASSIFICATION,
    - REGRESSION,
    - MULTICLASS

    The full ids are:
    - the model id of a Lab Model,
    - the model id of a saved model version,
    - the model evaluation id of a model evaluation.

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelComparison.get_settings`
    """
    def __init__(self, model_comparison, settings):
        super(DSSModelComparisonSettings, self).__init__(model_comparison, settings)

    def model_comparison(self):
        return self.evaluation_comparison

    @property
    def prediction_type(self):
        """
        Get the prediction type of this comparison

        :return: str
        """
        warnings.warn("prediction_type field is deprecated. Use model_task_type instead", DeprecationWarning)
        return self.settings.get("modelTaskType", self.settings.get("predictionType"))

    @prediction_type.setter
    def prediction_type(self, prediction_type):
        """
        Set the prediction type of this comparison. Must be consistent
        with the prediction types of compared items.

        :param prediction_type:
        """
        warnings.warn("prediction_type field is deprecated. Use model_task_type instead", DeprecationWarning)
        self.model_task_type = prediction_type
