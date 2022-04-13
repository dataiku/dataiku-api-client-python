from .discussion import DSSObjectDiscussions
import re


class DSSModelComparison(object):
    """
    A handle to interact with a model comparison on the DSS instance

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_model_comparison`
    """
    def __init__(self, client, project_key, mec_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.mec_id = mec_id

    @property
    def id(self):
        return self.mec_id

    def get_settings(self):
        """
        Returns the settings of this model comparison

        :rtype: :class:`dataikuapi.dss.modelcomparison.DSSModelComparisonSettings`
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/modelcomparisons/%s" % (self.project_key, self.mec_id))
        return DSSModelComparisonSettings(self, data)

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the model comparison

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MODEL_COMPARISON", self.mec_id)

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

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the model comparison

        """
        return self.client._perform_empty("DELETE", "/projects/%s/modelcomparisons/%s" % (self.project_key, self.mec_id))


class DSSModelComparisonSettings(object):
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
        self.model_comparison = model_comparison
        self.settings = settings

    def get_raw(self):
        """
        Get raw settings of a model comparison

        :return: the raw settings of comparison, as a dict. Modifications made to the returned object
        are reflected when saving
        :rtype: dict
        """
        return self.settings

    def add_compared_item(self, full_id):
        """
        Add an item to the list of compared items

        :param full_id: full id of the item (lab model, saved model version, model evaluation) to add
        """
        if "comparedModels" not in self.settings:
            self.settings["comparedModels"] = []
        self.settings["comparedModels"].append({
            "refId": full_id
        })

    def remove_compared_item(self, full_id):
        """
        Remove an item from the list of compared items

        :param full_id: full id of the item (lab model, saved model version, model evaluation) to remove
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
    def prediction_type(self):
        """
        Get the prediction type of this comparison

        :return: str
        """
        return self.settings["predictionType"]

    @prediction_type.setter
    def prediction_type(self, prediction_type):
        """
        Set the prediction type of this comparison. Must be consistent
        with the prediction types of compared items.

        :param prediction_type:
        """
        self.settings["predictionType"] = prediction_type

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
        self.model_comparison.client._perform_empty(
            "PUT", "/projects/%s/modelcomparisons/%s" % (self.model_comparison.project_key, self.model_comparison.mec_id),
            body=self.settings)

