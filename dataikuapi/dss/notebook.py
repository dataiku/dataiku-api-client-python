from .discussion import DSSObjectDiscussions
from .notebookcontent import DSSNotebookContent

class DSSNotebook(object):
    """
    A Python/R/Scala notebook on the DSS instance
    """
    def __init__(self, client, project_key, notebook_name, state=None, content=None):
       self.client = client
       self.project_key = project_key
       self.notebook_name = notebook_name
       self.state = state
       if content:
           self.content = content
       else:
           self.content = DSSNotebookContent(self.client, self.project_key, self.notebook_name)

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

    def get_state(self):
        """
        Deprecated. Use self.get_content().get_metadata()
        Get the metadata associated to this Jupyter notebook
        """
        import warnings
        warnings.warn("Use self.get_content().get_metadata()", DeprecationWarning)
        self.state = self.client._perform_json("GET",
                                               "/projects/%s/jupyter-notebooks/%s/metadata" % (self.project_key, self.notebook_name))
        return self.state

    def get_sessions(self):
        """
        Get the list of running sessions of this Jupyter notebook
        """

        if self.state is None:
            self.state = {}
        sessions = self.client._perform_json("GET",
                                             "/projects/%s/jupyter-notebooks/%s/sessions" % (self.project_key, self.notebook_name))
        self.state["activeSessions"] = sessions
        return sessions

    def get_content(self):
        """
        Get the content of this Jupyter notebook (metadata, cells, nbformat)
        """
        return self.content

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
