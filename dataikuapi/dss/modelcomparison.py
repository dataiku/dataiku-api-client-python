import json

from dataikuapi.dss.discussion import DSSObjectDiscussions


class DSSModelComparison(object):
    """
    A handle to interact with a model comparison on the DSS instance.

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
        Returns the settings of this model comparison.

        :rtype: DSSModelComparisonSettings
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

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the model comparison

        """
        return self.client._perform_empty("DELETE", "/projects/%s/modelcomparisons/%s" % (self.project_key, self.mec_id))


class DSSModelComparisonSettings:
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
        Gets raw settings of a model comparison

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
        self.settings["comparedModels"] = filter(lambda x: x["refId"] != full_id, self.settings["comparedModels"])

    def get_compared_items(self):
        """
        Gets the full ids of items compared in this comparison

        :return: the list of the full ids of compared items
        :rtype: list[str]
        """
        if not self.settings["comparedModels"]:
            return []
        return map(lambda x: x["refId"], self.settings["comparedModels"])

    def get_prediction_type(self):
        """
        Gets the prediction type of this comparison

        :return: str
        """
        return self.settings["predictionType"]

    def set_prediction_type(self, prediction_type):
        """
        Sets the prediction type of this comparison. Must be consistent
        with the prediction types of compared items.

        :param prediction_type:
        """
        self.settings["predictionType"] = prediction_type

    def get_display_name(self):
        """
        Human readable name of this comparison

        :return: str
        """
        return self.settings["displayName"]

    def set_display_name(self, display_name):
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

