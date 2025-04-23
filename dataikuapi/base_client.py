import json
import warnings
from requests import Session, exceptions
from requests import exceptions
from requests.auth import HTTPBasicAuth
from .auth import HTTPBearerAuth
from .utils import handle_http_exception

class DSSBaseClient(object):
    def __init__(self, base_uri, api_key=None, internal_ticket=None, bearer_token=None, no_check_certificate=False, client_certificate=None, **kwargs):
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate

        self.api_key = api_key
        self.bearer_token = bearer_token
        self.base_uri = base_uri
        self._session = Session()
        if no_check_certificate:
            self._session.verify = False
        if client_certificate:
            self._session.cert = client_certificate


    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False):
        if body:
            body = json.dumps(body)

        headers = None
        auth = None

        if self.api_key:
            auth = HTTPBasicAuth(self.api_key, "")
        elif self.bearer_token:
            auth = HTTPBearerAuth(self.bearer_token)

        http_res = self._session.request(
                    method, "%s/%s" % (self.base_uri, path),
                    params=params, data=body, headers=headers,
                    auth=auth, stream = stream)
        handle_http_exception(http_res)
        return http_res

    def _perform_empty(self, method, path, params=None, body=None):
        self._perform_http(method, path, params, body, False)

    def _perform_text(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).text

    def _perform_json(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).json()

    def _perform_raw(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, True)
