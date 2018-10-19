from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
from .ml import DSSTrainedPredictionModelDetails, DSSTrainedClusteringModelDetails
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions

class DSSSavedModel(object):
    """
    A handle to interact with a saved model on the DSS instance.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_saved_model`
    """
    def __init__(self, client, project_key, sm_id):
        self.client = client
        self.project_key = project_key
        self.sm_id = sm_id

        
    ########################################################
    # Versions
    ########################################################

    def list_versions(self):
        """
        Get the versions of this saved model
        
        :return: a list of the versions, as a dict of object. Each object contains at least a "id" parameter, which can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`
        :rtype: list
        """
        return self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions" % (self.project_key, self.sm_id))

    def get_active_version(self):
        """
        Gets the active version of this saved model
        
        :return: a dict representing the active version or None if no version is active. The dict contains at least a "id" parameter, which can be passed to :meth:`get_metric_values`, :meth:`get_version_details` and :meth:`set_active_version`
        :rtype: dict
        """
        filtered = [x for x in self.list_versions() if x["active"]]
        if len(filtered) == 0:
            return None
        else:
            return filtered[0]

    def get_version_details(self, version_id):
        """
        Gets details for a version of a saved model
        
        :param str version_id: Identifier of the version, as returned by :meth:`list_versions`

        :return: A :class:`DSSTrainedPredictionModelDetails` representing the details of this trained model id
        :rtype: :class:`DSSTrainedPredictionModelDetails`
        """
        details = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s/versions/%s/details" % (self.project_key, self.sm_id, version_id))
        snippet = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s/versions/%s/snippet" % (self.project_key, self.sm_id, version_id))

        if "facts" in details:
            return DSSTrainedClusteringModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)
        else:
            return DSSTrainedPredictionModelDetails(details, snippet, saved_model=self, saved_model_version=version_id)

    def set_active_version(self, version_id):
        """Sets a particular version of the saved model as the active one"""
        self.client._perform_empty(
            "POST", "/projects/%s/savedmodels/%s/versions/%s/actions/setActive" % (self.project_key, self.sm_id, version_id))

    ########################################################
    # Metrics
    ########################################################

    def get_metric_values(self, version_id):
        """
        Get the values of the metrics on the version of this saved model
        
        Returns:
            a list of metric objects and their value
        """
        return ComputedMetrics(self.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/metrics/%s" % (self.project_key, self.sm_id, version_id)))

                
    ########################################################
    # Usages
    ########################################################

    def get_usages(self):
        """
        Get the recipes referencing this model

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/savedmodels/%s/usages" % (self.project_key, self.sm_id))


    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the saved model

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SAVED_MODEL", self.sm_id)

    ########################################################
    # Deletion
    ########################################################

    def delete(self):
        """
        Delete the saved model

        """
        return self.client._perform_empty("DELETE", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))
