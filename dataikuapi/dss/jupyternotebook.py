from .discussion import DSSObjectDiscussions
from .utils import DSSTaggableObjectListItem

class DSSJupyterNotebookListItem(DSSTaggableObjectListItem):
    """
    An item in a list of Jupyter notebooks. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_jupyter_notebooks`
    """
    def __init__(self, client, data):
        super(DSSJupyterNotebookListItem, self).__init__(data)
        self.client = client

    def to_notebook(self):
        """
        Get a handle on the corresponding notebook

        :rtype: :class:`DSSJupyterNotebook`
        """
        return DSSJupyterNotebook(self.client, self._data["projectKey"], self._data["name"])

    @property
    def name(self):
        """
        Get the name of the notebook.

        Used as identifier.
        """
        return self._data["name"]

    @property
    def language(self):
        """
        Get the language of the notebook.

        Possible values are 'python', 'R', 'toree' (scala)

        :rtype: string
        """
        return self._data["language"]

    @property
    def kernel_spec(self):
        """
        Get the raw kernel spec of the notebook.

        The kernel spec is internal data for Jupyter, that identifies the kernel. 

        :return: the spec of a Jupyter kernel. Top-level fields are:

                    * **name** : identifier of the kernel in Jupyter, for example 'python2' or 'python3'
                    * **display_name** : name of the kernel as shown in the Jupyter UI
                    * **language** : language of the notebook (informative field)

        :rtype: dict
        """
        return self._data["kernelSpec"]

class DSSJupyterNotebook(object):
    """
    A handle on a Python/R/scala notebook.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_jupyter_notebook()` or
        :meth:`dataikuapi.dss.project.DSSProject.create_jupyter_notebook()`.
    """
    def __init__(self, client, project_key, notebook_name):
       self.client = client
       self.project_key = project_key
       self.notebook_name = notebook_name

    def unload(self, session_id=None):
        """
        Stop this Jupyter notebook and release its resources.
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
        Get the list of running sessions of this Jupyter notebook.

        Usage example:

        .. code-block:: python

            # list the running notebooks in a project
            for notebook in project.list_jupyter_notebooks(as_type="object"):
                if len(notebook.get_sessions()) > 0:
                    print("Notebook %s is running" % notebook.notebook_name)

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.jupyternotebook.DSSNotebookSession`

        :return: a list of :class:`dataikuapi.dss.jupyternotebook.DSSNotebookSession` if **as_objects** is True, a list of dict 
                 otherwise. The dict has fields:

                    * **sessionId** : identifier of the session in the Jupyter server
                    * **notebookName** : name of the notebook
                    * **projectKey** : key of the DSS project containing the notebookd
                    * **kernelId** : identifier of the running kernel in the Jupyter server (a session can change the kernel, for example if you restart it)
                    * **kernelConnections** : how many kernels are connected to this session
                    * **kernelExecutionState** : state of the notebook in Jupyter. Common states are 'idle' and 'busy'
                    * **kernelId** : identifier of the running kernel in the Jupyter server
                    * **kernelLastActivityTime** : timestamp in milliseconds of the last run of a cell in the notebook
                    * **kernelPid** : pid of the process running the kernel
                    * **sessionCreator** : name of user that started the session
                    * **sessionCreatorDisplayName** : display name of user that started the session
                    * **sessionStartTime** : timestamp in milliseconds of the session creation

        :rtype: list
        """
        sessions = self.client._perform_json("GET",
                                             "/projects/%s/jupyter-notebooks/%s/sessions" % (self.project_key, self.notebook_name))

        if as_objects:
            return [DSSNotebookSession(self.client, session) for session in sessions]
        else:
            return sessions

    def get_content(self):
        """
        Get the full contents of this Jupyter notebook. 

        The content comprises metadata, cells, notebook format info.

        Usage example:

        .. code-block:: python

            # collect all the source code of a notebook
            lines = []
            for cell in notebook.get_content().get_cells():
                if cell["cell_type"] != 'code':
                    continue
                lines = lines + cell["source"]
            print('\\n'.join(lines))

        :return: a list of :class:`dataikuapi.dss.jupyternotebook.DSSNotebookContent`
        :rtype: list
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
        Get a handle to manage discussions on the notebook.

        :return: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "JUPYTER_NOTEBOOK", self.notebook_name)

class DSSNotebookContent(object):
    """
    The content of a Jupyter Notebook. 

    This is the actual notebook data, see the `nbformat doc <https://nbformat.readthedocs.io/en/latest/>`_ .

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.jupyternotebook.DSSJupyterNotebook.get_content`
    """
    def __init__(self, client, project_key, notebook_name, content):
        self.client = client
        self.project_key = project_key
        self.notebook_name = notebook_name
        self.content = content

    def get_raw(self):
        """
        Get the raw content of this Jupyter notebook.

        The content comprises metadata, cells, notebook format info.

        :return: a dict containing the full content of a notebook. Notable fields are:

                    * **metadata** : the metadata of the notebook, as a dict (see :meth:`get_metadata()`)
                    * **nbformat** and **nbformat_minor** : the version of the notebook format
                    * **cells** : list of cells, each one a dict (see :meth:`get_cells()`)

        :rtype: dict
        """
        return self.content

    def get_metadata(self):
        """
        Get the metadata associated to this Jupyter notebook.

        :return: the Jupyter metadata of the notebook, with fields:

                        * **kernelspec** : identification of the kernel used to run the notebook
                        * **creator** : name of the user that created the notebook
                        * **createdOn** : timestamp of creation, in milliseconds
                        * **modifiedBy** : name of last modifier
                        * **language_info** : information on the language of the notebook

        :rtype: dict
        """
        return self.content["metadata"]

    def get_cells(self):
        """
        Get the cells of this Jupyter notebook.

        :return: a list of cells, as defined by Jupyter. Each cell is a dict, with notable fields:

                        * **cell_type** : type of cell, for example 'code'
                        * **metadata** : notebook metadata in the cell
                        * **executionCount** : index of the last run of this cell
                        * **source** : content of the cell, as a list of string
                        * **output** : list of outputs of the last run of the cell, as a list of dict with fields **output_type**, **name** and **text**. Exact contents and meaning depend on the cell type.

        :rtype: list[dict]
        """
        return self.content["cells"]

    def save(self):
        """
        Save the content of this Jupyter notebook.
        """
        return self.client._perform_json("PUT",
                                         "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name),
                                         body=self.content)

class DSSNotebookSession(object):
    """
    Metadata associated to the session of a Jupyter Notebook. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.jupyternotebook.DSSJupyterNotebook.get_sessions()`
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
        Stop this Jupyter notebook and release its resources.
        """
        return self.client._perform_json("DELETE",
                                         "/projects/%s/jupyter-notebooks/%s/sessions/%s" % (self.project_key, self.notebook_name, self.session_id))
