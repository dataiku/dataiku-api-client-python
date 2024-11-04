from ..utils import DataikuException
from ..dss.managedfolder import DSSManagedFolder
import logging
import os
import sys
import tempfile
import shutil
from base64 import b64encode


class MLflowHandle:
    def __init__(self, client, project, managed_folder, host=None):
        """ Add the MLflow-plugin parts of dataikuapi to MLflow local setup.

        This method deals with
        1. importing dynamically the DSS MLflow plugin:
        MLflow uses entrypoints==0.3 to load entrypoints from plugins at import time.
        We add dss-mlflow-plugin entrypoints dynamically by adding them in sys.path
        at call time.

        2. Setup the correct environment variables to setup the plugin to work
        with DSS backend as the tracking backend and enable using DSS managed folder
        as artifact location.
        """
        self.project = project
        self.project_key = project.project_key
        self.client = client
        self.mlflow_env = {}
        self.env_save = {}

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

        if sys.version_info > (3, 4):
            from importlib import reload
        import mlflow
        import mlflow.store.artifact.artifact_repository_registry
        import mlflow.tracking.request_header.registry
        reload(mlflow.tracking.request_header.registry) # Reload the request_header registry in case MLflow was imported beforehand
        reload(mlflow.store.artifact.artifact_repository_registry) # Reload the artifact_repository_registry in case MLflow was imported beforehand
        mlflow.set_tracking_uri(None)  # if user has changed tracking backend manually before
        mlflow.end_run()  # if user already created a run with another tracking backend
        self.remove_dataiku_duplicates_in_request_header_registry()

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

        if client._session.verify == False:
            self.mlflow_env.update({"MLFLOW_TRACKING_INSECURE_TLS": "true"})
            self.mlflow_env.update({"MLFLOW_TRACKING_SERVER_CERT_PATH": None})
        else:
            self.mlflow_env.update({"MLFLOW_TRACKING_INSECURE_TLS": "false"})
            if isinstance(client._session.verify, str):
                # when in a notebook with encrypted RPC, client._session.verify will have the RPC server cert
                # so we have to store it and restore it when creating again the api client (such as in the
                # artifact repository plugin)
                self.mlflow_env.update({"MLFLOW_TRACKING_SERVER_CERT_PATH": client._session.verify})
                self.mlflow_env.update({"DSS_MLFLOW_VERIFY_CERT": client._session.verify})
        mf_full_id = None
        if isinstance(managed_folder, DSSManagedFolder):
            mf_full_id = managed_folder.project.project_key + "." + managed_folder.id
        elif isinstance(managed_folder, str):
            mf_full_id = managed_folder
        else:
            try:
                from dataiku import Folder
                if isinstance(managed_folder, Folder):
                    mf_full_id = managed_folder.name
            except ImportError:
                pass

        if not mf_full_id:
            raise TypeError('Type of managed_folder must be "str", "DSSManagedFolder" or "dataiku.Folder".')

        if "." not in mf_full_id:
            mf_full_id = self.project_key + "." + mf_full_id

        mf_project = mf_full_id.split(".")[0]
        mf_id = mf_full_id.split(".")[1]

        try:
            client.get_project(mf_project).get_managed_folder(mf_id).get_definition()
        except DataikuException as e:
            if "NotFoundException" in str(e):
                logging.error('The managed folder "%s" does not exist, please create it in your project flow before running this command.' % (mf_full_id))
            raise

        # Set host, tracking URI, project key and managed_folder_id
        self.mlflow_env.update({
            "DSS_MLFLOW_PROJECTKEY": self.project_key,
            "MLFLOW_TRACKING_URI": self.client.host + "/dip/publicapi" if host is None else host,
            "DSS_MLFLOW_HOST": self.client.host,
            "DSS_MLFLOW_MANAGED_FOLDER_ID": mf_full_id
        })
        self.override_env(self.mlflow_env)


    def remove_dataiku_duplicates_in_request_header_registry(self):
        try:
            # Try to make sure we are not loading our MLflow plugin twice
            # see https://app.shortcut.com/dataiku/story/210232
            from mlflow.tracking.request_header.registry import _request_header_provider_registry
            registry = _request_header_provider_registry._registry
            seen = set()
            i = 0
            while i < len(registry):
                entrypoint = registry[i]
                entrypoint_name = "{}.{}".format(entrypoint.__class__.__module__, entrypoint.__class__.__name__)
                if entrypoint_name in seen and 'dataikuapi' in entrypoint_name:
                    registry.pop(i)
                else:
                    seen.add(entrypoint_name)
                    i += 1
        except Exception as e:
            logging.warning(str(e), exc_info=True)


    def clear(self):
        shutil.rmtree(self.tempdir)
        self.restore_env(self.mlflow_env)

    def override_env(self, overrides):
        assert len(self.env_save) == 0, "Environment variables already overriden, override_env called twice?"
        for key, value in overrides.items():
            try:
                current_value = os.environ.pop(key)
                self.env_save[key] = current_value
                if value is None:
                    # allow to unset env variables by using 'None' as a value in overrides
                    del os.environ[key]
            except KeyError:
                # Means that overriden var does not exist, safe to ignore.
                pass
            if value is not None:
                os.environ[key] = value

    def restore_env(self, overrides):
        for variable in overrides:
            os.environ.pop(variable, None)
        os.environ.update(self.env_save)

    def import_mlflow(self):
        import mlflow
        return mlflow

    def __enter__(self):
        return self.import_mlflow()

    def __exit__(self, exc_type, exc_value, traceback):
        self.clear()
