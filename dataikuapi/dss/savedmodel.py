from .metrics import ComputedMetrics
from .ml import DSSMLTask
from .ml import DSSTrainedClusteringModelDetails
from .ml import DSSTrainedPredictionModelDetails

try:
    basestring
except NameError:
    basestring = str

class DSSSavedModel(object):
    """
    A handle to interact with a saved model on the DSS instance.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_saved_model`
    """
    def __init__(self, client, project_key, sm_id):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key
        self.sm_id = sm_id
  
    @property
    def id(self):
        return self.sm_id

    def get_settings(self):
        """
        Returns the settings of this saved model.

        :rtype: DSSSavedModelSettings
        """
        data = self.client._perform_json(
            "GET", "/projects/%s/savedmodels/%s" % (self.project_key, self.sm_id))
        return DSSSavedModelSettings(self, data)

        
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

    def delete_versions(self, versions, remove_intermediate=True):
        """
        Delete version(s) of the saved model

        :param versions: list of versions to delete
        :type versions: list[str]
        :param remove_intermediate: also remove intermediate versions (default: True). In the case of a partitioned
        model, an intermediate version is created every time a partition has finished training.
        :type remove_intermediate: bool
        """
        if not isinstance(versions, list):
            versions = [versions]
        body = {
            "versions": versions,
            "removeIntermediate": remove_intermediate
        }
        self.client._perform_empty(
            "POST", "/projects/%s/savedmodels/%s/actions/delete-versions" % (self.project_key, self.sm_id),
            body=body)

    def get_origin_ml_task(self):
        """
        Fetch the last ML task that has been exported to this saved model. Returns None if the saved model
        does not have an origin ml task.

        :rtype: DSSMLTask | None
        """
        fmi = self.get_settings().get_raw().get("lastExportedFrom")
        if fmi is not None:
            return DSSMLTask.from_full_model_id(self.client, fmi, project_key=self.project_key)


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
    # Misc
    ########################################################

    def get_zone(self):
        """
        Gets the flow zone of this saved model

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
        Get the recipes referencing this model

        Returns:
            a list of usages
        """
        return self.client._perform_json("GET", "/projects/%s/savedmodels/%s/usages" % (self.project_key, self.sm_id))

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


class DSSSavedModelSettings:
    """
    A handle on the settings of a saved model

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSSavedModel.get_settings`
    """

    def __init__(self, saved_model, settings):
        self.saved_model = saved_model
        self.settings = settings

    def get_raw(self):
        return self.settings
