import json
from requests import Session, exceptions
from requests import exceptions
from requests.auth import HTTPBasicAuth
from .utils import DataikuException

class DSSBaseClient(object):
    def __init__(self, base_uri, api_key=None, internal_ticket=None, bearer_token=None):
        self.api_key = api_key
        self.bearer_token = bearer_token
        self.base_uri = base_uri
        self._session = Session()

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
            headers = {"Authorization": "Bearer " + self.bearer_token}

        try:
            http_res = self._session.request(
                    method, "%s/%s" % (self.base_uri, path),
                    params=params, data=body, headers=headers,
                    auth=auth, stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            ex = http_res.json()
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None):
        self._perform_http(method, path, params, body, False)

    def _perform_text(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).text

    def _perform_json(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, False).json()

    def _perform_raw(self, method, path, params=None, body=None):
        return self._perform_http(method, path, params, body, True)
