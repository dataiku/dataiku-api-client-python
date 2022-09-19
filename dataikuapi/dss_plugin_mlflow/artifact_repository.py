import os
import tempfile
import urllib
import re
import sys
from dataikuapi import DSSClient


if sys.version_info > (3, 0):  # MLflow only work for python3 (in > 1.18.0)
    from pathlib import PurePosixPath, Path


def parse_dss_managed_folder_uri(uri):
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != "dss-managed-folder":
        raise Exception("Not a DSS Managed Folder URI: %s" % uri)
    pattern = re.compile("^(\w+\.)?\w{8}")
    if not parsed.netloc or not pattern.match(parsed.netloc):
        raise Exception("Could not find a managed folder id in URI: %s" % uri)
    return parsed


class PluginDSSManagedFolderArtifactRepository:

    def __init__(self, artifact_uri):
        if os.environ.get("DSS_MLFLOW_APIKEY") is not None:
            self.client = DSSClient(
                os.environ.get("DSS_MLFLOW_HOST"),
                api_key=os.environ.get("DSS_MLFLOW_APIKEY")
            )
        else:
            self.client = DSSClient(
                os.environ.get("DSS_MLFLOW_HOST"),
                internal_ticket=os.environ.get("DSS_MLFLOW_INTERNAL_TICKET")
            )
        self.project = self.client.get_project(os.environ.get("DSS_MLFLOW_PROJECTKEY"))
        parsed_uri = parse_dss_managed_folder_uri(artifact_uri)
        self.managed_folder = self.__get_managed_folder(parsed_uri.netloc)
        self.base_artifact_path = PurePosixPath(parsed_uri.path)

    def __get_managed_folder(self, managed_folder_smart_id):
        chunks = managed_folder_smart_id.split('.')
        if len(chunks) == 1:
            return self.project.get_managed_folder(chunks[0])
        elif len(chunks) == 2:
            project = self.client.get_project(chunks[0])
            return project.get_managed_folder(chunks[1])
        else:
            raise Exception("Invalid managed folder id: %s" % managed_folder_smart_id)

    def log_artifact(self, local_file, artifact_path=None):
        """
        Log a local file as an artifact, optionally taking an ``artifact_path`` to place it in
        within the run's artifacts. Run artifacts can be organized into directories, so you can
        place the artifact in a directory this way.

        :param local_file: Path to artifact to log
        :param artifact_path: Directory within the run's artifact directory in which to log the
                              artifact.
        """
        path = self.base_artifact_path
        if artifact_path is not None:
            path /= artifact_path
        self.managed_folder.put_file(str(path / os.path.basename(local_file)), open(local_file, "rb"))

    def log_artifacts(self, local_dir, artifact_path=None):
        """
        Log the files in the specified local directory as artifacts, optionally taking
        an ``artifact_path`` to place them in within the run's artifacts.

        :param local_dir: Directory of local artifacts to log
        :param artifact_path: Directory within the run's artifact directory in which to log the
                              artifacts
        """
        path = self.base_artifact_path
        if artifact_path is not None:
            path /= artifact_path
        self.managed_folder.upload_folder(str(path), local_dir)

    def list_artifacts(self, path=""):
        """
        Return all the artifacts for this run_id directly under path. If path is a file, returns
        an empty list. Will error if path is neither a file nor directory.

        :param path: Relative source path that contains desired artifacts

        :return: List of artifacts as FileInfo listed directly under path.
        """
        path = self.base_artifact_path / path
        files = [PurePosixPath(x["path"]) for x in self.managed_folder.list_contents().get("items", [])]
        return [file.relative_to(path) for file in files if path in file.parents]

    def download_artifacts(self, artifact_path, dst_path=None):
        """
        Download an artifact file or directory to a local directory if applicable, and return a
        local path for it.
        The caller is responsible for managing the lifecycle of the downloaded artifacts.

        :param artifact_path: Relative source path to the desired artifacts.
        :param dst_path: Absolute path of the local filesystem destination directory to which to
                         download the specified artifacts. This directory must already exist.
                         If unspecified, the artifacts will either be downloaded to a new
                         uniquely-named directory on the local filesystem or will be returned
                         directly in the case of the LocalArtifactRepository.

        :return: Absolute path of the local filesystem location containing the desired artifacts.
        """
        from mlflow.exceptions import MlflowException
        from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE, RESOURCE_DOES_NOT_EXIST

        if dst_path is None:
            dst_path = tempfile.mkdtemp()
        dst_path = Path(dst_path).absolute()

        if not dst_path.exists():
            raise MlflowException(
                message=("The destination path for downloaded artifacts does not"
                         " exist! Destination path: {dst_path}".format(dst_path=dst_path)),
                error_code=RESOURCE_DOES_NOT_EXIST,
            )
        elif not dst_path.is_dir():
            raise MlflowException(
                message=("The destination path for downloaded artifacts must be a directory!"
                         " Destination path: {dst_path}".format(dst_path=dst_path)),
                error_code=INVALID_PARAMETER_VALUE,
            )

        for path in self.list_artifacts(artifact_path):
            local_path = dst_path / path
            local_path.parent.mkdir(exist_ok=True)
            self._download_file(artifact_path / path, local_path)

        return dst_path

    def _download_file(self, artifact_path, local_path):
        """
        Download the file at the specified relative remote path and saves
        it at the specified local path.

        :param artifact_path: Source path to the remote file, relative to the root
                                 directory of the artifact repository.
        :param local_path: The path to which to save the downloaded file.
        """
        full_path = self.base_artifact_path / artifact_path
        with self.managed_folder.get_file(str(full_path)) as remote_file:
            with open(local_path, "wb") as local_file:
                for line in remote_file:
                    local_file.write(line)

    def delete_artifacts(self, artifact_path=None):
        """
        Delete the artifacts at the specified location.
        Supports the deletion of a single file or of a directory. Deletion of a directory
        is recursive.
        :param artifact_path: Path of the artifact to delete
        """
        path = (
            self.base_artifact_path / artifact_path if artifact_path else self.base_artifact_path
        )
        self.managed_folder.delete_file(str(path))


def verify_artifact_path(artifact_path):
    from mlflow.exceptions import MlflowException
    from mlflow.utils.validation import path_not_unique, bad_path_message
    if artifact_path and path_not_unique(artifact_path):
        raise MlflowException(
            "Invalid artifact path: '%s'. %s" % (artifact_path, bad_path_message(artifact_path))
        )
