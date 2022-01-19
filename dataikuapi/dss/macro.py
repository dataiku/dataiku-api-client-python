import time
import sys, json
from ..utils import DataikuException

class DSSMacro(object):
    """
    A macro on the DSS instance

    :param client: an api client to connect to the DSS backend
    :param project_key: identifier of the project to access the macro from
    :param runnable_type: identifier of the macro
    :param definition: if available, the macro's definition
    """
    def __init__(self, client, project_key, runnable_type, definition=None):
        self.client = client
        self.runnable_type = runnable_type
        self.project_key = project_key
        self.definition = definition

    def get_definition(self):
        """
        Get the macro definition. The result contains :

            * identification of the macro
            * display info like label
            * what kind of result the macro returns (html, file, url, ...)
            * the list of parameters to pass in order to start a run (adminParams is 
              empty unless the authentication of the api client covers admin rights)
        """
        if self.definition is None:
            self.definition = self.client._perform_json(
            "GET", "/projects/%s/runnables/%s" % (self.project_key, self.runnable_type))
        return self.definition


    def run(self, params=None, admin_params=None, wait=True):
        """
        Run the macro from the project

        :param dict params: parameters to the macro run (defaults to `{}`)
        :param dict admin_params: admin parameters to the macro run (if the authentication of
                             the api client does not cover admin rights, they are ignored, defaults to `{}`)
        :param wait: if True, the call blocks until the run is finished
        :returns: a run identifier to use to abort or retrieve results
        """
        if params is None:
            params = {}
        if admin_params is None:
            admin_params = {}
        return self.client._perform_json(
            "POST", "/projects/%s/runnables/%s" % (self.project_key, self.runnable_type), 
            params={'wait':wait}, body={'params':params, 'adminParams':admin_params})['runId']

    def abort(self, run_id):
        """
        Aborts a run of the macro

        :param run_id: a run identifier, as return from the run() method
        """
        self.client._perform_empty(
            "POST", "/projects/%s/runnables/%s/abort/%s" % (self.project_key, self.runnable_type, run_id))

    def get_status(self, run_id):
        """
        Polls the status of a run of the macro
        
        :param run_id: a run identifier, as return from the run() method
        :returns: a dict holding information about whether the run exists, is still running,
                  errors that might have happened during the run, and result type if it finished.
        """
        return self.client._perform_json(
            "GET", "/projects/%s/runnables/%s/state/%s" % (self.project_key, self.runnable_type, run_id))

    def get_result(self, run_id, as_type=None):
        """
        Retrieve the result of a run of the macro
        
        :param run_id: a run identifier, as return from the run() method
        :param as_type: if not None, one of 'string' or 'json'
        :returns: the result of the macro run, as a file-like is as_type is None; as a str if
                  as_type is "string"; as an object if as_type is "json". If the macro is still 
                  running, an Exception is raised
        """
        resp = self.client._perform_raw(
                "GET", "/projects/%s/runnables/%s/result/%s" % (self.project_key, self.runnable_type, run_id))
        if as_type == 'string':
            with resp.raw as s:
                return s.read()
        elif as_type == 'json':
            with resp.raw as s:
                return json.load(s)
        else:
            return resp.raw

