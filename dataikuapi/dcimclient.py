import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
from .dcim.instance import DCIMLogicalInstance
from .dss.future import DSSFuture
import os.path as osp
from .utils import DataikuException

class DCIMClient(object):
    """Entry point for the DCIM API client"""

    def __init__(self, host, tenant_id, api_key_id, api_key_secret):
        """
        Instantiate a new DCIM API client on the given host with the given API key.
        """
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.host = host
        self.tenant_id = tenant_id
        self._session = Session()
        self._session.auth = HTTPBasicAuth(self.api_key_id, self.api_key_secret)            
            
    ########################################################
    # Futures
    ########################################################
            
    def list_futures(self, as_objects=False):
        """
        List the currently-running long tasks (a.k.a futures)

        :param boolean as_objects: if True, each returned item will be a :class:`dataikuapi.dss.future.DSSFuture`
        :param boolean all_users: if True, returns futures for all users (requires admin privileges). Else, only returns futures for the user associated with the current authentication context (if any)

        :return: list of futures. if as_objects is True, each future in the list is a :class:`dataikuapi.dss.future.DSSFuture`. Else, each future in the list is a dict. Each dict contains at least a 'jobId' field
        :rtype: list of :class:`dataikuapi.dss.future.DSSFuture` or list of dict
        """
        list = self._perform_json("GET", "/futures")
        if as_objects:
            return [DSSFuture(self, state['jobId'], state) for state in list]
        else:
            return list

    def get_future(self, job_id):
        """
        Get a handle to interact with a specific long task (a.k.a future). This notably allows aborting this future.

        :param str job_id: the identifier of the desired future (which can be returned by :py:meth:`list_futures` or :py:meth:`list_running_scenarios`)
        :returns: A handle to interact the future
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        return DSSFuture(self, job_id)


    ########################################################
    # Instances
    ########################################################
            
    def create_instance(self, label, virtual_network_id):
        """
        Creates a new logical instance
        """
        list = self._perform_json("GET", "/admin/notebooks/")
        if as_objects:
            return [DSSNotebook(self, notebook['projectKey'], notebook['name'], notebook) for notebook in list]
        else:
            return list

    def get_instance(self, logical_instance_id):
        return DCIMLogicalInstance(self, logical_instance_id)


    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        try:
            http_res = self._session.request(
                    method, "%s/api/public/tenants/%s/%s" % (self.host, self.tenant_id, path),
                    params=params, data=body,
                    files = files,
                    stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body)

    def _perform_text(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body).text

    def _perform_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body).json()

    def _perform_raw(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body)

    def _perform_json_upload(self, method, path, name, f):
        try:
            http_res = self._session.request(
                    method, "%s/dip/publicapi%s" % (self.host, path),
                    files = {'file': (name, f, {'Expires': '0'})} )
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))
