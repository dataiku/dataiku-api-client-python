import os
import sys
import tempfile
import shutil
from base64 import b64encode


class MLflowHandle:
    def __init__(self, client, project_key, managed_folder="mlflow_artifacts", host=None):
        """ Add the MLflow-plugin parts of dataikuapi to MLflow local setup.

        This method deals with
        1. importing dynamically the DSS Mlflow plugin:
        MLflow uses entrypoints==0.3 to load entrypoints from plugins at import time.
        We add dss-mlflow-plugin entrypoints dynamically by adding them in sys.path
        at call time.

        2. Setup the correct environemnent variables to setup the plugin to work
        with DSS backend as the tracking backend and enable using DSS managed folder
        as artifact location.
        """
        self.project_key = project_key
        self.client = client
        self.mlflow_env = {}

        # Load DSS as the plugin
        self.tempdir = tempfile.mkdtemp()
        plugin_dir = os.path.join(self.tempdir, "dss-plugin-mlflow.egg-info")
        if not os.path.isdir(plugin_dir):
            os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "entry_points.txt"), "w") as f:
            f.write(
                "[mlflow.request_header_provider]\n"
                "unused=dataikuapi.dss_plugin_mlflow.header_provider:PluginDSSHeaderProvider\n"
                "[mlflow.artifact_repository]\n"
                "dss-managed-folder=dataikuapi.dss_plugin_mlflow.artifact_repository:PluginDSSManagedFolderArtifactRepository\n"
            )
        sys.path.insert(0, self.tempdir)

        # Setup authentication
        if client._session.auth is not None:
            self.mlflow_env.update({
                "DSS_MLFLOW_HEADER": "Authorization",
                "DSS_MLFLOW_TOKEN": "Basic {}".format(
                    b64encode("{}:".format(self.client._session.auth.username).encode("utf-8")).decode("utf-8")),
                "DSS_MLFLOW_APIKEY": self.client.api_key
            })
        elif client.internal_ticket:
            self.mlflow_env.update({
                "DSS_MLFLOW_HEADER": "X-DKU-APITicket",
                "DSS_MLFLOW_TOKEN": self.client.internal_ticket,
                "DSS_MLFLOW_INTERNAL_TICKET": self.client.internal_ticket
            })
        # Set host, tracking URI and project key
        self.mlflow_env.update({
            "DSS_MLFLOW_PROJECTKEY": project_key,
            "MLFLOW_TRACKING_URI": self.client.host + "/dip/publicapi" if host is None else host,
            "DSS_MLFLOW_HOST": self.client.host,
            "DSS_MLFLOW_MANAGED_FOLDER": managed_folder
        })
        os.environ.update(self.mlflow_env)

    def clear(self):
        shutil.rmtree(self.tempdir)
        for variable in self.mlflow_env:
            os.environ.pop(variable, None)

    def import_mlflow(self):
        import mlflow
        return mlflow

    def __enter__(self):
        return self.import_mlflow()

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear()
