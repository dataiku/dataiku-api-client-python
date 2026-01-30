import re
import warnings

from dataikuapi.dss.discussion import DSSObjectDiscussions


class DSSEvaluationComparison(object):
    """
    A handle to interact with an evaluation comparison on the DSS instance

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_evaluation_comparison`
    """

    def __init__(self, client, project_key, comparison_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.comparison_id = comparison_id

    @property
    def mec_id(self):
        warnings.warn("mec_id field is deprecated. Use comparison_id instead", DeprecationWarning)
        return self.comparison_id

    def _fetch_settings(self):
        url = "/projects/%s/evaluationcomparisons/%s" % (self.project_key, self.comparison_id)
        return self.client._perform_json("GET", url)

    def get_settings(self):
        """
        Returns the settings of this evaluationcomparison comparison

        :rtype: :class:`dataikuapi.dss.evaluationcomparison.DSSEvaluationComparisonSettings`
        """
        data = self._fetch_settings()
        return DSSEvaluationComparisonSettings(self, data)

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the model comparison

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MODEL_COMPARISON", self.comparison_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the evaluation comparison

        """
        url = "/projects/%s/evaluationcomparisons/%s" % (self.project_key, self.comparison_id)
        return self.client._perform_empty("DELETE", url)

    def get_evaluation_like_from_full_id(self, full_id):
        """
        Retrieves a Saved Model from the flow, a Lab Model from an Analysis or a Model Evaluation from a Model Evaluation Store) using its full id.

        Note that this method is not available for LLM or AGENT comparisons

        :param string full_id: the full id of the item to retrieve

        :returns: A handle on the Saved Model, the Model Evaluation or the Lab Model
        :rtype: :class:`dataikuapi.dss.savedmodel.DSSSavedModel`
        :rtype: :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation`
        :rtype: :class:`dataikuapi.dss.ml.DSSTrainedPredictionModelDetails`
        """
        saved_model_pattern = re.compile("^S-(\\w+)-(\\w+)-(\\w+)(?:-part-(\\w+)-(v?\\d+))?$\\Z")
        analysis_model_pattern = re.compile(
            "^A-(\\w+)-(\\w+)-(\\w+)-(s[0-9]+)-(pp[0-9]+(?:-part-(\\w+)|-base)?)-(m[0-9]+)$\\Z"
        )
        model_evaluation_pattern = re.compile("^ME-(\\w+)-(\\w+)-(\\w+)$\\Z")

        if saved_model_pattern.match(full_id):
            return self.project.get_saved_model(full_id)
        elif model_evaluation_pattern.match(full_id):
            evaluation_store_id = full_id.split("-")[2]
            evaluation_id = full_id.split("-")[3]
            evaluation_store = self.project.get_evaluation_store(evaluation_store_id)
            return evaluation_store.get_evaluation(evaluation_id)
        elif analysis_model_pattern.match(full_id):
            analysis_id = full_id.split("-")[2]
            task_id = full_id.split("-")[3]
            return self.project.get_ml_task(analysis_id, task_id).get_trained_model_details(full_id)

        raise ValueError("{} is not a valid full model id or full model evaluation id.".format(full_id))


class DSSEvaluationComparisonSettings(object):
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
    - AGENT
    - LLM

    The full ids are:
    - the model id of a Lab Model,
    - the model id of a saved model version,
    - the evaluation id of an evaluation.

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSEvaluationComparison.get_settings`
    """

    def __init__(self, evaluation_comparison, settings):
        self.evaluation_comparison = evaluation_comparison
        self.settings = settings

    def get_raw(self):
        """
        Get raw settings of an evaluation comparison

        :return: the raw settings of comparison, as a dict. Modifications made to the returned object
        are reflected when saving
        :rtype: dict
        """
        return self.settings

    def add_compared_item(self, full_id):
        """
        Add an item to the list of compared items

        :param full_id: full id of the item (lab model, saved model version, LLM, agent, model evaluation) to add
        """
        if "comparedModels" not in self.settings:
            self.settings["comparedModels"] = []
        self.settings["comparedModels"].append({"refId": full_id})

    def remove_compared_item(self, full_id):
        """
        Remove an item from the list of compared items

        :param full_id: full id of the item (lab model, saved model version, LLM, agent, model evaluation) to remove
        """
        if not self.settings["comparedModels"]:
            return
        self.settings["comparedModels"] = list(filter(lambda x: x["refId"] != full_id, self.settings["comparedModels"]))

    def get_compared_items(self):
        """
        Get the full ids of items compared in this comparison

        :return: the list of the full ids of compared items
        :rtype: list[str]
        """
        if not self.settings["comparedModels"]:
            return []
        return [x["refId"] for x in self.settings["comparedModels"]]

    @property
    def model_task_type(self):
        """
        Get the prediction type of this comparison

        :return: str
        """
        return self.settings.get("modelTaskType")

    @model_task_type.setter
    def model_task_type(self, model_task_type):
        """
        Set the initial model task type of this comparison. Must be consistent
        with the model task types of compared items.

        :param model_task_type:
        """
        self.settings["modelTaskType"] = model_task_type

    @property
    def display_name(self):
        """
        Human readable name of this comparison

        :return: str
        """
        return self.settings["displayName"]

    @display_name.setter
    def display_name(self, display_name):
        """
        Set the human readable name of this comparison

        :param display_name:
        """
        self.settings["displayName"] = display_name

    def save(self):
        """
        Save settings modifications
        """
        url = "/projects/%s/evaluationcomparisons/%s" % (
            self.evaluation_comparison.project_key,
            self.evaluation_comparison.comparison_id,
        )
        self.evaluation_comparison.client._perform_empty("PUT", url, body=self.settings)
