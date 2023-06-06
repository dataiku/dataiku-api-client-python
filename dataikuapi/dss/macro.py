import time
import sys, json
from ..utils import DataikuException

class DSSMacro(object):
    """
    A macro on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_macro()`
    """
    def __init__(self, client, project_key, runnable_type, definition=None):
        self.client = client
        self.runnable_type = runnable_type
        self.project_key = project_key
        self.definition = definition

    def get_definition(self):
        """
        Get the macro definition. 

        .. note::

            The **adminParams** field is empty unless the authentication of the API client covers admin rights.

        :return: the definition (read-only), as a dict with fields:

                    * **runnableType** : identifier of the macro
                    * **ownerPluginId** : identifier of the plugin where the macro is defined
                    * **meta** : display information about the macro, as a dict of:

                        * **category** : (optional) name of a category, used to group macros in the list
                        * **label** : display name
                        * **description** : short description of the macro
                        * **icon** : icon used for the macro in the UI

                    * **longDescription** : (optional) longer description. Can use Markdown
                    * **resultType** : type of result produced by the macro. Possible values: NONE, RESULT_TABLE, FILE, FOLDER_FILE, HTML, JSON_OBJECT, URL
                    * **resultLabel** : name for the result
                    * **mimeType** : (optional) MIME type of the result
                    * **extension** : (optional) extension of the result, used when **resultType** is FILE or FOLDER_FILE
                    * **params** : the list of parameters to pass in order to start a run. Each parameter is a dict with at least **name** and **type** fields. See `the doc <https://doc.dataiku.com/dss/latest/plugins/reference/params.html>`_ for available parameter definitions.
                    * **adminParams** : parameters only visible (and usable) by admins 

        :rtype: dict
        """
        if self.definition is None:
            self.definition = self.client._perform_json(
            "GET", "/projects/%s/runnables/%s" % (self.project_key, self.runnable_type))
        return self.definition


    def run(self, params=None, admin_params=None, wait=True):
        """
        Run the macro from the project

        .. note::

            If the authentication of the api client does not have admin rights, admin
            params are ignored.

        Usage example:

        .. code-block:: python

            # list all datasets on a connection.            
            connection_name = 'filesystem_managed'
            macro = project.get_macro('pyrunnable_builtin-macros_list-datasets-using-connection')
            run_id = macro.run(params={'connection': connection_name}, wait=True)
            # the result of this builtin macro is of type RESULT_TABLE
            result = macro.get_result(run_id, as_type="json")
            for record in result["records"]:
                print("Used by %s" % record[0])

        :param dict params: parameters to the macro run (defaults to `{}`)
        :param dict admin_params: admin parameters to the macro run (defaults to `{}`)
        :param boolean wait: if True, the call blocks until the run is finished
        
        :return: a run identifier to use with :meth:`abort()`, :meth:`get_status()` and :meth:`get_result()`
        :rtype: string
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
        Abort a run of the macro.

        :param string run_id: a run identifier, as returned by :meth:`run()`
        """
        self.client._perform_empty(
            "POST", "/projects/%s/runnables/%s/abort/%s" % (self.project_key, self.runnable_type, run_id))

    def get_status(self, run_id):
        """
        Poll the status of a run of the macro.

        .. note::

            Once the run is done, when :meth:`get_result()` is called, the run ceases to exist.
            Afterwards :meth:`get_status()` will answer that the run doesn't exist.
        
        :param string run_id: a run identifier, as returned by :meth:`run()`

        :return: the status, as a dict of:

                    * **exists** : whether there is a run with this identifier
                    * **running** : whether the run is still ongoing
                    * **progress** : when **running** is True, a dict of the progress of the run
                    * **empty** : for runs that don't run anymore, whether there is no result 
                    * **type** : type of result, when there's one. Possible values: NONE, RESULT_TABLE, FILE, FOLDER_FILE, HTML, JSON_OBJECT, URL
                    * **storedError** : dict of the error, when some error failed the run

        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/projects/%s/runnables/%s/state/%s" % (self.project_key, self.runnable_type, run_id))

    def get_result(self, run_id, as_type=None):
        """
        Retrieve the result of a run of the macro.

        .. note::

            If the macro is still running, an Exception is raised.

        The type of the contents of the result to expect can be checked using :meth:`get_definition()`,
        in particular the "resultType" field. 
        
        :param string run_id: a run identifier, as returned by :meth:`run()` method
        :param string as_type: if not None, one of 'string' or 'json'. Use 'json' when the type of result
                               advertised by the macro is RESULT_TABLE or JSON_OBJECT.

        :return: the contents of the result of the macro run, as a file-like is **as_type** is None; as a str if
                 **as_type** is "string"; as an object if **as_type** is "json". 
        :rtype: file-like, or string
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

