import os
import posixpath
import tempfile
import urllib
import re
from dataikuapi import DSSClient


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
        self.base_artifact_path = os.path.normpath(parsed_uri.path)

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
        path = (
            os.path.join(self.base_artifact_path, artifact_path) if artifact_path else self.base_artifact_path
        )
        self.managed_folder.put_file(os.path.join(path, os.path.basename(local_file)), open(local_file, "rb"))

    def log_artifacts(self, local_dir, artifact_path=None):
        """
        Log the files in the specified local directory as artifacts, optionally taking
        an ``artifact_path`` to place them in within the run's artifacts.

        :param local_dir: Directory of local artifacts to log
        :param artifact_path: Directory within the run's artifact directory in which to log the
                              artifacts
        """
        path = (
            os.path.join(self.base_artifact_path, artifact_path) if artifact_path else self.base_artifact_path
        )
        self.managed_folder.upload_folder(path, local_dir)

    def list_artifacts(self, path):
        """
        Return all the artifacts for this run_id directly under path. If path is a file, returns
        an empty list. Will error if path is neither a file nor directory.

        :param path: Relative source path that contains desired artifacts

        :return: List of artifacts as FileInfo listed directly under path.
        """
        from pathlib import Path
        path = Path(os.path.join(self.base_artifact_path, path))
        files = [x["path"] for x in self.managed_folder.list_contents().get("items", []) if path in Path(x["path"]).parents]
        return files

    def _is_directory(self, artifact_path):
        listing = self.list_artifacts(artifact_path)
        return len(listing) > 0

    def _create_download_destination(self, src_artifact_path, dst_local_dir_path=None):
        """
        Creates a local filesystem location to be used as a destination for downloading the artifact
        specified by `src_artifact_path`. The destination location is a subdirectory of the
        specified `dst_local_dir_path`, which is determined according to the structure of
        `src_artifact_path`. For example, if `src_artifact_path` is `dir1/file1.txt`, then the
        resulting destination path is `<dst_local_dir_path>/dir1/file1.txt`. Local directories are
        created for the resulting destination location if they do not exist.

        :param src_artifact_path: A relative, POSIX-style path referring to an artifact stored
                                  within the repository's artifact root location.
                                  `src_artifact_path` should be specified relative to the
                                  repository's artifact root location.
        :param dst_local_dir_path: The absolute path to a local filesystem directory in which the
                                   local destination path will be contained. The local destination
                                   path may be contained in a subdirectory of `dst_root_dir` if
                                   `src_artifact_path` contains subdirectories.
        :return: The absolute path to a local filesystem location to be used as a destination
                 for downloading the artifact specified by `src_artifact_path`.
        """
        src_artifact_path = src_artifact_path.rstrip("/")  # Ensure correct dirname for trailing '/'
        dirpath = posixpath.dirname(src_artifact_path)
        local_dir_path = os.path.join(dst_local_dir_path, dirpath)
        local_file_path = os.path.join(dst_local_dir_path, src_artifact_path)
        if not os.path.exists(local_dir_path):
            os.makedirs(local_dir_path, exist_ok=True)
        return local_file_path

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

        # TODO: Probably need to add a more efficient method to stream just a single artifact
        #       without downloading it, or to get a pre-signed URL for cloud storage.
        def download_artifact(src_artifact_path, dst_local_dir_path):
            """
            Download the file artifact specified by `src_artifact_path` to the local filesystem
            directory specified by `dst_local_dir_path`.

            :param src_artifact_path: A relative, POSIX-style path referring to a file artifact
                                      stored within the repository's artifact root location.
                                      `src_artifact_path` should be specified relative to the
                                      repository's artifact root location.
            :param dst_local_dir_path: Absolute path of the local filesystem destination directory
                                       to which to download the specified artifact. The downloaded
                                       artifact may be written to a subdirectory of
                                       `dst_local_dir_path` if `src_artifact_path` contains
                                       subdirectories.
            :return: A local filesystem path referring to the downloaded file.
            """
            local_destination_file_path = self._create_download_destination(
                src_artifact_path=src_artifact_path, dst_local_dir_path=dst_local_dir_path
            )
            self._download_file(
                remote_file_path=src_artifact_path, local_path=local_destination_file_path
            )
            return local_destination_file_path

        def download_artifact_dir(src_artifact_dir_path, dst_local_dir_path):
            local_dir = os.path.join(dst_local_dir_path, src_artifact_dir_path)
            dir_content = [  # prevent infinite loop, sometimes the dir is recursively included
                file_info
                for file_info in self.list_artifacts(src_artifact_dir_path)
                if file_info.path != "." and file_info.path != src_artifact_dir_path
            ]
            if not dir_content:  # empty dir
                if not os.path.exists(local_dir):
                    os.makedirs(local_dir, exist_ok=True)
            else:
                for file_info in dir_content:
                    if file_info.is_dir:
                        download_artifact_dir(
                            src_artifact_dir_path=file_info.path,
                            dst_local_dir_path=dst_local_dir_path,
                        )
                    else:
                        download_artifact(
                            src_artifact_path=file_info.path, dst_local_dir_path=dst_local_dir_path
                        )
            return local_dir

        if dst_path is None:
            dst_path = tempfile.mkdtemp()
        dst_path = os.path.abspath(dst_path)

        if not os.path.exists(dst_path):
            raise MlflowException(
                message=(
                    "The destination path for downloaded artifacts does not"
                    " exist! Destination path: {dst_path}".format(dst_path=dst_path)
                ),
                error_code=RESOURCE_DOES_NOT_EXIST,
            )
        elif not os.path.isdir(dst_path):
            raise MlflowException(
                message=(
                    "The destination path for downloaded artifacts must be a directory!"
                    " Destination path: {dst_path}".format(dst_path=dst_path)
                ),
                error_code=INVALID_PARAMETER_VALUE,
            )

        # Check if the artifacts points to a directory
        if self._is_directory(artifact_path):
            return download_artifact_dir(
                src_artifact_dir_path=artifact_path, dst_local_dir_path=dst_path
            )
        else:
            return download_artifact(src_artifact_path=artifact_path, dst_local_dir_path=dst_path)

    def _download_file(self, remote_file_path, local_path):
        """
        Download the file at the specified relative remote path and saves
        it at the specified local path.

        :param remote_file_path: Source path to the remote file, relative to the root
                                 directory of the artifact repository.
        :param local_path: The path to which to save the downloaded file.
        """
        with self.managed_folder.get_file(remote_file_path) as remote_file:
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
            os.path.join(self.base_artifact_path, artifact_path) if artifact_path else self.base_artifact_path
        )
        self.managed_folder.delete_file(path)


def verify_artifact_path(artifact_path):
    from mlflow.exceptions import MlflowException
    from mlflow.utils.validation import path_not_unique, bad_path_message
    if artifact_path and path_not_unique(artifact_path):
        raise MlflowException(
            "Invalid artifact path: '%s'. %s" % (artifact_path, bad_path_message(artifact_path))
        )
