from .discussion import DSSObjectDiscussions

class DSSNotebook(object):
    """
    A Python/R/Scala notebook on the DSS instance
    """
    def __init__(self, client, project_key, notebook_name, state=None):
       self.client = client
       self.project_key = project_key
       self.notebook_name = notebook_name
       self.state = state
       self.state_is_peek = True

    def unload(self, session_id=None):
        """
        Stop the notebook and release its resources
        """
        state = self.get_state()
        if state is None:
            raise Exception("Notebook isn't running")
        if state.get('activeSessions', None) is None:
            raise Exception("Notebook isn't running")
        if len(state['activeSessions']) == 0:
            raise Exception("Notebook isn't running")
        if session_id is None:
            if len(state['activeSessions']) > 1:
                raise Exception("Several sessions of the notebook are running, choose one")
            else:
                session_id = state['activeSessions'][0].get('sessionId', None)
        return self.client._perform_json("DELETE", "/projects/%s/notebooks/" % self.project_key, params={'notebookName' : self.notebook_name, 'sessionId' : session_id})

    def get_state(self):
        """
        Get the status of the notebook
        """
        if self.state is None:
            self.state = self.client._perform_json("GET", "/projects/%s/notebooks/" % self.project_key, params={'notebookName' : self.notebook_name})
        return self.state

    def get_sessions(self):
        """
        Get the list of the running sessions of this notebook
        """
        state = self.get_state()
        if state is None:
            raise Exception("Notebook isn't running")
        if state.get('activeSessions', None) is None:
            raise Exception("Notebook isn't running")
        return state['activeSessions']

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
