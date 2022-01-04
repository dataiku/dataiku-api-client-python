class DSSMLflowExtension(object):
    """
    A handle to interact with specific endpoints of the DSS MLflow integration.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_mlflow_extension`
    """
    ROOT_URL = ""

    def __init__(self, client, project_key):
        self.client = client
        self.project = client.get_project(project_key)
        self.project_key = project_key

    def list_models(self, run_id):
        response = self.client._perform_http(
            "GET", "/api/2.0/mlflow/extension/models/{}".format(run_id),
            headers={"x-dku-mlflow-project-key": self.project_key}
        )
        return response.json()
