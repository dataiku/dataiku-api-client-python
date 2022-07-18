import json

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
        when deploying using the GUI an MLflow model as a version of a DSS Saved Model.

        :param prediction_type: prediction type (see doc)
        :type prediction_type: str
        :param run_id: run_id for which to set the classes
        :type run_id: str
        :param classes: ordered list of classes (not for all prediction types, see doc)
        :type classes: list(str)
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
                    raise ValueError('class can not be None')
                if not isinstance(cur_class, str):
                    raise ValueError('Wrong type for class {}: {}'.format(cur_class, type(cur_class)))

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
