import os

class PluginDSSHeaderProvider:

    def in_context(self):
        env_variables = {"DSS_MLFLOW_HEADER", "DSS_MLFLOW_TOKEN", "DSS_MLFLOW_PROJECTKEY"}
        if len(env_variables.difference(set(os.environ))) == 0:
            return True

    def request_headers(self):
        headers = {
            os.environ.get("DSS_MLFLOW_HEADER"): os.environ.get("DSS_MLFLOW_TOKEN"),
            "x-dku-mlflow-project-key": os.environ.get("DSS_MLFLOW_PROJECTKEY"),
            "x-dku-mlflow-managed-folder-id": os.environ.get("DSS_MLFLOW_MANAGED_FOLDER_ID"),
        }
        return headers
