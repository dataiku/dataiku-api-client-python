import json
import time
from datetime import datetime
from dataikuapi.dss.utils import DSSDatasetSelectionBuilder
from dataikuapi.dss.savedmodel import ExternalModelVersionHandler

class DSSMLflowExtension(object):
    """
    A handle to interact with specific endpoints of the DSS MLflow integration.

    Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_mlflow_extension`
    """

    def __init__(self, client, project_key):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key

    def list_models(self, run_id):
        """
        Returns the list of models of given run

        :param run_id: run_id for which to return a list of models
        :type run_id: str
        """
        response = self.client._perform_http(
            "GET", "/api/2.0/mlflow/extension/models/{}".format(run_id),
            headers={"x-dku-mlflow-project-key": self.project_key}
        )
        return response.json()

    def list_experiments(self, view_type="ACTIVE_ONLY", max_results=1000):
        """
        Returns the list of experiments in the DSS project for which MLflow integration
        is setup

        :param view_type: ACTIVE_ONLY, DELETED_ONLY or ALL
        :type view_type: str
        :param max_results: max results count
        :type max_results: int
        :rtype: dict
        """
        response = self.client._perform_http(
            "GET", "/api/2.0/mlflow/experiments/list?view_type={view_type}&max_results={max_results}".format(view_type=view_type, max_results=max_results),
            headers={"x-dku-mlflow-project-key": self.project_key}
        )
        return response.json()

    def rename_experiment(self, experiment_id, new_name):
        """
        Renames an experiment

        :param experiment_id: experiment id
        :type experiment_id: str
        :param new_name: new name
        :type new_name: str
        """
        response = self.client._perform_http(
            "POST", "/api/2.0/mlflow/experiments/update",
            headers={"x-dku-mlflow-project-key": self.project_key},
            body={"experiment_id": experiment_id, "new_name": new_name}
        )
        return response.json()

    def restore_experiment(self, experiment_id):
        """
        Restores a deleted experiment

        :param experiment_id: experiment id
        :type experiment_id: str
        """
        response = self.client._perform_http(
            "POST", "/api/2.0/mlflow/experiments/restore",
            headers={"x-dku-mlflow-project-key": self.project_key},
            body={"experiment_id": experiment_id}
        )
        return response.json()

    def restore_run(self, run_id):
        """
        Restores a deleted run

        :param run_id: run id
        :type run_id: str
        """
        response = self.client._perform_http(
            "POST", "/api/2.0/mlflow/runs/restore",
            headers={"x-dku-mlflow-project-key": self.project_key},
            body={"run_id": run_id}
        )
        return response.json()

    def garbage_collect(self):
        """
        Permanently deletes the experiments and runs marked as "Deleted"
        """
        self.client._perform_http(
            "POST", "/api/2.0/mlflow/extension/garbage-collect",
            headers={"x-dku-mlflow-project-key": self.project_key}
        )

    def create_experiment_tracking_dataset(self, dataset_name, experiment_ids=[], view_type="ACTIVE_ONLY", filter_expr="", order_by=[], format="LONG"):
        """

        Creates a virtual dataset exposing experiment tracking data.

        :param dataset_name: name of the dataset
        :type dataset_name: str
        :param experiment_ids: list of ids of experiments to filter on. No filtering if empty
        :type experiment_ids: list(str)
        :param view_type: one of ACTIVE_ONLY, DELETED_ONLY and ALL. Default is ACTIVE_ONLY
        :type view_type: str
        :param filter_expr: MLflow search expression
        :type filter_expr: str
        :param order_by: list of order by clauses. Default is ordered by start_time, then runId
        :type order_by: list(str)
        :param format: LONG or JSON. Default is LONG
        :type format: str
        """
        self.client._perform_http(
            "POST", "/api/2.0/mlflow/extension/create-project-experiments-dataset",
            headers={"x-dku-mlflow-project-key": self.project_key},
            body={
                "datasetName": dataset_name,
                "experimentIds": experiment_ids,
                "viewType": view_type,
                "filter": filter_expr,
                "orderBy": order_by,
                "format": format
            }
        )

    def clean_experiment_tracking_db(self):
        """
        Cleans the experiments, runs, params, metrics, tags, etc. for this project

        This call requires an API key with admin rights
        """
        self.client._perform_raw("DELETE", "/api/2.0/mlflow/extension/clean-db/%s" % self.project_key)

    def set_run_inference_info(self, run_id, prediction_type, classes=None, code_env_name=None, target=None):
        """
        Sets the type of the model, and optionally other information useful to deploy or evaluate it.

        prediction_type must be one of:
        - REGRESSION
        - BINARY_CLASSIFICATION
        - MULTICLASS
        - OTHER

        Classes must be specified if and only if the model is a BINARY_CLASSIFICATION or MULTICLASS model.

        This information is leveraged to filter saved models on their prediction type and prefill the classes
        when deploying (using the GUI or :meth:`deploy_run_model`) an MLflow model as a version of a DSS Saved Model.

        :param prediction_type: prediction type (see doc)
        :type prediction_type: str
        :param run_id: run_id for which to set the classes
        :type run_id: str
        :param classes: ordered list of classes (not for all prediction types, see doc). Every class will be converted by calling str().
            The classes must be specified in the same order as learned by the model.
            Some flavors such as scikit-learn may allow you to build this list from the model itself.
        :type classes: list
        :param code_env_name: name of an adequate DSS python code environment
        :type code_env_name: str
        :param target: name of the target
        :type target: str
        """
        if prediction_type not in {"REGRESSION", "BINARY_CLASSIFICATION", "MULTICLASS", "OTHER"}:
            raise ValueError('Invalid prediction type: {}'.format(prediction_type))

        if classes and prediction_type not in {"BINARY_CLASSIFICATION", "MULTICLASS"}:
            raise ValueError('Classes can be specified only for BINARY_CLASSIFICATION or MULTICLASS prediction types')
        if prediction_type in {"BINARY_CLASSIFICATION", "MULTICLASS"}:
            if not classes:
                raise ValueError('Classes must be specified for {} prediction type'.format(prediction_type))
            if not isinstance(classes, list):
                raise ValueError('Wrong type for classes: {}'.format(type(classes)))
            for cur_class in classes:
                if cur_class is None:
                    raise ValueError('class cannot be None')
            classes = [str(cur_class) for cur_class in classes]

        if code_env_name and not isinstance(code_env_name, str):
            raise ValueError('code_env_name must be a string')
        if target and not isinstance(target, str):
            raise ValueError('target must be a string')

        params = {
            "run_id": run_id,
            "prediction_type": prediction_type
        }

        if classes:
            params["classes"] = json.dumps(classes)
        if code_env_name:
            params["code_env_name"] = code_env_name
        if target:
            params["target"] = target

        self.client._perform_http(
            "POST", "/api/2.0/mlflow/extension/set-run-inference-info",
            headers={"x-dku-mlflow-project-key": self.project_key},
            body=params
        )

    def deploy_run_model(self, run_id, sm_id, version_id=None, use_inference_info=True, code_env_name=None, evaluation_dataset=None,
                         target_column_name=None, class_labels=None, model_sub_folder=None, selection=None, activate=True,
                         binary_classification_threshold=0.5, use_optimal_threshold=True):
        """
        Deploys a model from an experiment run, with lineage.

        Simple usage:

        .. code-block:: python

            mlflow_ext.set_run_inference_info(run_id, "BINARY_CLASSIFICATION", list_of_classes, code_env_name, target_column_name)
            sm_id = project.create_mlflow_pyfunc_model("model_name", "BINARY_CLASSIFICATION").id
            mlflow_extension.deploy_run_model(run_id, sm_id, evaluation_dataset)

        If the optional `evaluation_dataset` is not set, the model will be deployed but not evaluated: this makes `target_column_name` optional as well in :meth:`set_run_inference_info`

        :param run_id: The id of the run to deploy
        :type run_id: str
        :param sm_id: The id of the saved model to deploy the run to
        :type sm_id: str
        :param version_id: [optional] Unique identifier of a Saved Model Version. If id already exists, existing version is overwritten.
            Whitespaces or dashes are not allowed. If not set, a timestamp will be used as version_id.
        :type version_id: str
        :param use_inference_info: [optional] default to True. if set, uses the :meth:`set_inference_info` previously done
            on the run to retrieve the prediction type of the model, its code environment, classes and target.
        :type use_inference_info: bool
        :param evaluation_dataset: [optional] The evaluation dataset, if the deployment of the models can imply an evaluation.
        :type evaluation_dataset: str
        :param target_column_name: [optional] The target column of the evaluation dataset. Can be set by :meth:`set_inference_info`.
        :type target_column_name: str
        :param class_labels: [optional] The class labels of the target. Can be set by :meth:`set_inference_info`.
        :type class_labels: list(str)
        :param code_env_name: [optional] The code environment to be used. Must contain a supported version of the mlflow package and the ML libs used to train the model.
            Can be set by :meth:`set_inference_info`.
        :type code_env_name: str
        :param model_sub_folder: [optional] The name of the subfolder containing the model. Optional if it is unique.
            Existing values can be retrieved with `project.get_mlflow_extension().list_models(run_id)`
        :type model_sub_folder: str
        :param str selection: [optional] will default to HEAD_SEQUENTIAL with a maxRecords of 10_000.
        :type selection: :class:`DSSDatasetSelectionBuilder` optional sampling parameter for the evaluation or dict
                                e.g.
                                    DSSDatasetSelectionBuilder().with_head_sampling(100)
                                    {"samplingMethod": "HEAD_SEQUENTIAL", "maxRecords": 100}
        :param activate: [optional] True by default. Activate or not the version after deployment
        :type activate: bool
        :param binary_classification_threshold: [optional] Threshold (or cut-off) value to override if the model is a binary classification
        :type binary_classification_threshold: float
        :param use_optimal_threshold: [optional] Use or not the optimal threshold for the saved model metric computed at evaluation
        :type use_optimal_threshold: bool
        :return: a handler in order to interact with the new MLFlow model version
        :rtype: :class:`dataikuapi.dss.savedmodel.ExternalModelVersionHandler`
        """
        sampling_param = selection.build() if isinstance(
            selection, DSSDatasetSelectionBuilder) else selection

        if version_id is None:
            dt = datetime.fromtimestamp(time.time())
            version_id = dt.strftime("%Y_%m_%dT%H_%M_%S")

        prediction_type = self.project.get_saved_model(sm_id).get_settings().settings["miniTask"].get("predictionType")
        output_labels = []
        if class_labels:
            for label in class_labels:
                output_labels.append({'label': label})

        model_version_info_obj = {}
        if evaluation_dataset is not None:
            model_version_info_obj["gatherFeaturesFromDataset"] = evaluation_dataset
        if target_column_name is not None:
            model_version_info_obj["targetColumnName"] = target_column_name
        if output_labels is not None:
            model_version_info_obj["classLabels"] = output_labels
        if code_env_name is not None:
            model_version_info_obj["pythonCodeEnvName"] = code_env_name
        if prediction_type is not None:
            model_version_info_obj["predictionType"] = prediction_type

        self.client._perform_http("POST", "/api/2.0/mlflow/extension/deploy-run",
                                  headers={"x-dku-mlflow-project-key": self.project_key},
                                  params={"projectKey": self.project_key,
                                          "runId": run_id,
                                          "smId": sm_id,
                                          "modelSubfolder": model_sub_folder,
                                          "versionId": version_id,
                                          "modelVersionInfo": json.dumps(model_version_info_obj),
                                          "samplingParam": sampling_param,
                                          "activate": activate,
                                          "binaryClassificationThreshold": binary_classification_threshold,
                                          "useOptimalThreshold": use_optimal_threshold,
                                          "useInferenceInfo": use_inference_info
                                          }
                                      )
        return ExternalModelVersionHandler(sm_id, version_id)
