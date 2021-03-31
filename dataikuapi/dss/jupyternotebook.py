from .discussion import DSSObjectDiscussions
from .utils import DSSTaggableObjectListItem

class DSSJupyterNotebookListItem(DSSTaggableObjectListItem):
    """An item in a list of Jupyter notebooks. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_jupyter_notebooks`"""
    def __init__(self, client, data):
        super(DSSJupyterNotebookListItem, self).__init__(data)
        self.client = client

    def to_notebook(self):
        """Gets the :class:`DSSJupyterNotebook` corresponding to this notebook"""
        return DSSJupyterNotebook(self.client, self._data["projectKey"], self._data["name"])

    @property
    def name(self):
        return self._data["name"]
    @property
    def language(self):
        return self._data["language"]
    @property
    def kernel_spec(self):
        return self._data["kernelSpec"]

class DSSJupyterNotebook(object):
    def __init__(self, client, project_key, notebook_name):
       self.client = client
       self.project_key = project_key
       self.notebook_name = notebook_name

    def unload(self, session_id=None):
        """
        Stop this Jupyter notebook and release its resources
        """
        sessions = self.get_sessions()
        if sessions is None:
            raise Exception("Notebook isn't running")
        if len(sessions) == 0:
            raise Exception("Notebook isn't running")
        if session_id is None:
            if len(sessions) > 1:
                raise Exception("Several sessions of the notebook are running, choose one")
            else:
                session_id = sessions[0].get('sessionId', None)
        return self.client._perform_json("DELETE",
                                         "/projects/%s/jupyter-notebooks/%s/sessions/%s" % (self.project_key, self.notebook_name, session_id))

    def get_sessions(self, as_objects=False):
        """
        Get the list of running sessions of this Jupyter notebook

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.notebook.DSSNotebookSession`
        :rtype: list of :class:`dataikuapi.dss.notebook.DSSNotebookSession` or list of dict
        """
        sessions = self.client._perform_json("GET",
                                             "/projects/%s/jupyter-notebooks/%s/sessions" % (self.project_key, self.notebook_name))

        if as_objects:
            return [DSSNotebookSession(self.client, session) for session in sessions]
        else:
            return sessions

    def get_content(self):
        """
        Get the content of this Jupyter notebook (metadata, cells, nbformat)
        """
        raw_content = self.client._perform_json("GET", "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name))
        return DSSNotebookContent(self.client, self.project_key, self.notebook_name, raw_content)

    def delete(self):
        """
        Delete this Jupyter notebook and stop all of its active sessions.
        """
        return self.client._perform_json("DELETE",
                                         "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the notebook

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "JUPYTER_NOTEBOOK", self.notebook_name)

class DSSNotebookContent(object):
    """
    Content of a Jupyter Notebook. Do not create this directly, use :meth:`DSSJupyterNotebook.get_content`
    """

    """
    A Python/R/Scala notebook on the DSS instance
    """
    def __init__(self, client, project_key, notebook_name, content):
        self.client = client
        self.project_key = project_key
        self.notebook_name = notebook_name
        self.content = content

    def get_raw(self):
        """
        Get the content of this Jupyter notebook (metadata, cells, nbformat)
        :rtype: a dict containing the full content of a notebook
        """
        return self.content

    def get_metadata(self):
        """
        Get the metadata associated to this Jupyter notebook
        :rtype: dict with metadata
        """
        return self.content["metadata"]

    def get_cells(self):
        """
        Get the cells associated to this Jupyter notebook
        :rtype: list of cells
        """
        return self.content["cells"]

    def save(self):
        """
        Save the content of this Jupyter notebook
        """
        return self.client._perform_json("PUT",
                                         "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name),
                                         body=self.content)

class DSSNotebookSession(object):
    """
    Metadata associated to the session of a Jupyter Notebook. Do not create this directly, use :meth:`DSSJupyterNotebook.get_sessions()`
    """

    def __init__(self, client, session):
        self.client = client
        self.project_key = session.get("projectKey")
        self.notebook_name = session.get("notebookName")
        self.session_creator = session.get("sessionCreator")
        self.session_creator_display_name = session.get("sessionCreatorDisplayName")
        self.session_unix_owner = session.get("sessionUnixOwner")
        self.session_id = session.get("sessionId")
        self.kernel_id = session.get("kernelId")
        self.kernel_pid = session.get("kernelPid")
        self.kernel_connections = session.get("kernelConnections")
        self.kernel_last_activity_time = session.get("kernelLastActivityTime")
        self.kernel_execution_state = session.get("kernelExecutionState")
        self.session_start_time = session.get("sessionStartTime")


    def unload(self):
        """
        Stop this Jupyter notebook and release its resources
        """
        return self.client._perform_json("DELETE",
                                         "/projects/%s/jupyter-notebooks/%s/sessions/%s" % (self.project_key, self.notebook_name, self.session_id))
