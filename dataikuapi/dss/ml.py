from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import time
from .metrics import ComputedMetrics

class DSSMLTaskSettings(object):
    def __init__(self, client, project_key, analysis_id, mltask_id, mltask_settings):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id
        self.mltask_id = mltask_id
        self.mltask_settings = mltask_settings

    def get_raw(self):
        """Gets the raw settings.
        This returns a reference to the raw settings, not a copy.
        """
        return self.mltask_settings

    def get_feature_preprocessing(self, feature_name):
        return self.mltask_settings["preprocessing"]["per_feature"][feature_name]

    def reject_feature(self, feature_name):
        self.get_feature_preprocessing(feature_name)["role"] = "REJECT"

    def use_feature(self, feature_name):
        self.get_feature_preprocessing(feature_name)["role"] = "INPUT"

    def get_algorithm_settings(self, algorithm_name):
        algorithm_remap = {
            "SVC_CLASSIFICATION" : "svc_classifier",
            "SGD_CLASSIFICATION" : "sgd_classifier",
            "SPARKLING_DEEP_LEARNING" : "deep_learning_sparkling",
            "SPARKLING_GBM" : "gbm_sparkling",
            "SPARKLING_RF" : "rf_sparkling",
            "SPARKLING_GLM" : "glm_sparkling",
            "SPARKLING_NB" : "nb_sparkling",
            "XGBOOST_CLASSIFICATION" : "xgboost",
            "XGBOOST_REGRESSION" : "xgboost",
            "MLLIB_LOGISTIC_REGRESSION" : "mllib_logit",
            "MLLIB_LINEAR_REGRESSION" : "mllib_linreg",
            "MLLIB_RANDOM_FOREST" : "mllib_rf"
        }
        if algorithm_name in algorithm_remap:
            algorithm_name = algorithm_remap[algorithm_name]

        return self.mltask_settings["modeling"][algorithm_name.lower()]

    def set_algorithm_enabled(self, algorithm_name, enabled):
        self.get_algorithm_settings(algorithm_name)["enabled"] = enabled

    def save(self):
        """Saves back these settings to the ML Task"""

        print("WILL SAVE: %s" % json.dumps(self.mltask_settings, indent=2))

        self.client._perform_empty(
                "POST", "/projects/%s/models/lab/%s/%s/settings" % (self.project_key, self.analysis_id, self.mltask_id),
                body = self.mltask_settings)

class DSSMLTask(object):
    def __init__(self, client, project_key, analysis_id, mltask_id):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id
        self.mltask_id = mltask_id

    def wait_guess_complete(self):
        """
        Waits for guess to be complete. This should be called immediately after the creation of a new ML Task,
        before calling ``get_settings`` or ``train``
        """
        while True:
            status = self.get_status()
            if status.get("guessing", "???") == False:
                break
            time.sleep(0.2)

    def wait_train_complete(self):
        """
        Waits for train to be complete.
        """
        while True:
            status = self.get_status()
            if status.get("training", "???") == False:
                break
            time.sleep(2)

    def get_status(self):
        """
        Gets the status of this ML Task

        :return: a dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/status" % (self.project_key, self.analysis_id, self.mltask_id))
                

    def get_settings(self):
        """
        Gets the settings of this ML Tasks

        :return: a DSSMLTaskSettings object to interact with the settings
        """
        settings =  self.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/settings" % (self.project_key, self.analysis_id, self.mltask_id))

        return DSSMLTaskSettings(self.client, self.project_key, self.analysis_id, self.mltask_id, settings)

    def start_train(self):
        """Starts asynchronously a new train session for this ML Task.

        This returns immediately, before train is complete. To wait for train to complete, 
        poll on ``get_status`` until ``training`` is False"""
        self.client._perform_empty(
                "POST", "/projects/%s/models/lab/%s/%s/train" % (self.project_key, self.analysis_id, self.mltask_id))


    def get_trained_models_ids(self):
        status = self.get_status()
        return [x["id"] for x in status["fullModelIds"]]


    def get_trained_model_summary(self, id):
        obj = {
            "modelsIds" : [id]
        }
        return self.client._perform_json(
            "POST", "/projects/%s/models/lab/%s/%s/models-summaries" % (self.project_key, self.analysis_id, self.mltask_id),
            body = obj)[id]

    def deploy_to_flow(self, model_id, model_name, train_dataset, test_dataset=None, redo_optimization=True):
        obj = {
            "trainDatasetRef" : train_dataset,
            "testDatasetRef" : test_dataset,
            "modelName" : model_name,
            "redoOptimization":  redo_optimization
        }
        return self.client._perform_json(
            "POST", "/projects/%s/models/lab/%s/%s/models/%s/actions/deployToFlow" % (self.project_key, self.analysis_id, self.mltask_id, model_id),
            body = obj)

