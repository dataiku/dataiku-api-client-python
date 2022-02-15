class DSSMLflowExtension(object):
    """
    A handle to interact with specific endpoints of the DSS MLflow integration.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_mlflow_extension`
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
        Permanently deletes the experiments and runs marked as "Deleted
        """
        self.client._perform_http(
            "GET", "/api/2.0/mlflow/extension/garbage-collect",
            headers={"x-dku-mlflow-project-key": self.project_key}
        )
