import json

from dataikuapi.dss.discussion import DSSObjectDiscussions


class DSSModelComparator(object):
    """
    A handle to interact with a model comparator on the DSS instance.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_model_comparator`
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
        Returns the settings of this model comparator.

        :rtype: DSSModelComparatorSettings
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/modelcomparisons/%s" % (self.project_key, self.mec_id))
        return DSSModelComparatorSettings(self, data)

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the model comparator

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "MODEL_COMPARISON", self.mec_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the model evaluation store

        """
        return self.client._perform_empty("DELETE", "/projects/%s/modelcomparisons/%s" % (self.project_key, self.mec_id))


class DSSModelComparatorSettings:
    """
    A handle on the settings of a model comparator

    A model comparator has:
    - a display name ;
    - a prediction type ;
    - a list of full ids of items to compare

    The prediction type can be:
    - BINARY_CLASSIFICATION,
    - REGRESSION,
    - MULTICLASS

    The full ids are:
    - the model id of a Lab Model, such as A-PROJECTKEY-LABID-MODELID-s1-pp1-m1 (visible on the summary tab of the model) ;
    - the model id of a saved model version, such as S-PROJECTKEY-SMID-1234567891234 (visible on the summary tab of the model) ;
    - the model evaluation id of a model evaluation, such as ME-PROJECTKEY-STOREID-MEID (visible on the summary tab of the model evaluation).


    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelComparator.get_settings`
    """

    def __init__(self, model_comparator, settings):
        self.model_comparator = model_comparator
        self.settings = settings

    def get_raw(self):
        """
        Gets raw settings of a model comparator

        :return: the raw settings of comparator, as a dict. Modifications made to the returned object
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
        Gets the full ids of items compared in this comparator instance

        :return: the list of the full ids of compared items
        :rtype: list[str]
        """
        if not self.settings["comparedModels"]:
            return []
        return map(lambda x: x["refId"], self.settings["comparedModels"])

    def get_prediction_type(self):
        """
        Gets the prediction type of this comparator instance

        :return: str
        """
        return self.settings["predictionType"]

    def set_prediction_type(self, prediction_type):
        """
        Sets the prediction type of this comparator instance. Must be consistent
        with the prediction types of compared items.

        :param prediction_type:
        """
        self.settings["predictionType"] = prediction_type

    def get_display_name(self):
        """
        Human readable name of this comparator instance

        :return: str
        """
        return self.settings["displayName"]

    def set_display_name(self, display_name):
        """
        Set the human readable name of this comparator instance

        :param display_name:
        """
        self.settings["displayName"] = display_name

    def save(self):
        """
        Save settings modifications
        """
        self.model_comparator.client._perform_empty(
            "PUT", "/projects/%s/modelcomparisons/%s" % (self.model_comparator.project_key, self.model_comparator.mec_id),
            body=self.settings)

