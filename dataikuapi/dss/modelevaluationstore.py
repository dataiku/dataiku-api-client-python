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
    # Runs
    ########################################################

    def list_model_evaluations(self, as_type=None):
        """
        List the model evaluations in this model evaluation store.

        :returns: The list of the model evaluations
        :rtype: list
        """
        items = self.client._perform_json("GET", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id))
        if as_type == "objects" or as_type == "object":
            return [DSSModelEvaluation(self, item["ref"]["runId"]) for item in items]
        else:
            return items

    def get_model_evaluation(self, run_id):
        """
        Get a handle to interact with a specific model evaluations
       
        :param string run_id: the id of the desired model evaluation
        
        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
        """
        return DSSModelEvaluation(self, run_id)

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
        self.model_evaluation_store.client._perform_json(
                "DELETE", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id, self.run_id), body=obj)


    def create_model_evaluation(self, labels=None, prediction_type=None, model_type=None, model_params=None, data_type=None, data_params=None, metric_params=None, active_classifier_threshold=None):
        """
        Create a new model evaluation in the model evaluation store, and return a handle to interact with it.
        
        :returns: A :class:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation` model evaluation handle
        """
        obj = {
            "labels": labels,
            "modelType": model_type,
            "modelParams": model_params if model_params is not None else {},
            "dataType": data_type,
            "dataParams": data_params if data_params is not None else {},
            "predictionType": prediction_type,
            "activeClassifierThreshold": active_classifier_threshold,
            "metricParams": metric_params if metric_params is not None else {}
        }
        res = self.client._perform_json("POST", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id), 
                                            body = obj)
        run_id = res['id']
        return DSSModelEvaluation(self, run_id)


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
        return self.client._perform_json(
                "GET", "/projects/%s/modelevaluationstores/%s/runs/%s" % (self.project_key, self.mes_id, self.run_id))

    def get_settings(self):
        """
        Set the definition of this model evaluation
        """
        data = self.client._perform_json(
                "GET", "/projects/%s/modelevaluationstores/%s/runs/%s/settings" % (self.project_key, self.mes_id, self.run_id))
        return DSSModelEvaluationSettings(self, data)

    def delete(self):
        """
        Remove this model evaluation
        """
        obj = [self.run_id]
        self.client._perform_json(
                "DELETE", "/projects/%s/modelevaluationstores/%s/runs/" % (self.project_key, self.mes_id), body=obj)

    ########################################################
    # Model evaluation contents
    ########################################################
    
    def list_contents(self):
        """
        Get the list of files in the model evaluation
        
        Returns:
            the list of files, as a JSON object
        """
        return self.client._perform_json(
                "GET", "/projects/%s/modelevaluationstores/%s/runs/%s/contents" % (self.project_key, self.mes_id, self.run_id))

    def get_file(self, path):
        """
        Get a file from the model evaluation
        
        Returns:
            the file's content, as a stream
        """
        return self.client._perform_raw(
                "GET", "/projects/%s/modelevaluationstores/%s/runs/%s/contents/%s" % (self.project_key, self.mes_id, self.run_id, utils.quote(path)))

    def delete_file(self, path):
        """
        Delete a file from the model evaluation
        """
        return self.client._perform_empty(
                "DELETE", "/projects/%s/modelevaluationstores/%s/runs/%s/contents/%s" % (self.project_key, self.mes_id, self.run_id, utils.quote(path)))

    def put_file(self, path, f):
        """
        Upload the file to the model evaluation
        
        Args:
            f: the file contents, as a stream
            path: the path of the file
        """
        return self.client._perform_json_upload(
                "POST", "/projects/%s/modelevaluationstores/%s/runs/%s/contents/%s" % (self.project_key, self.mes_id, self.run_id, utils.quote(path)),
                "", f)

class DSSModelEvaluationSettings:
    """
    A handle on the settings of a model evaluation

    Do not create this class directly, instead use :meth:`dataikuapi.dss.DSSModelEvaluation.get_settings`
    """

    def __init__(self, model_evaluation, settings):
        self.model_evaluation = model_evaluation
        self.settings = settings
        # unpack some fields
        self.client = model_evaluation.client
        self.run_id = model_evaluation.run_id
        self.project_key = model_evaluation.project_key
        self.mes_id = model_evaluation.mes_id

    def get_raw(self):
        return self.settings

    def save(self):
        return self.client._perform_json(
                "PUT", "/projects/%s/modelevaluationstores/%s/runs/%s/settings" % (self.project_key, self.mes_id, self.run_id),
                        body=self.settings)


