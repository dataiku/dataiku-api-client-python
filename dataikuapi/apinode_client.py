from .utils import DataikuException
from .base_client import DSSBaseClient

class APINodeClient(DSSBaseClient):
    """Entry point for the DSS API Node client
    This is an API client for the user-facing API of DSS API Node server (user facing API)
    """

    def __init__(self, uri, service_id, api_key=None):
        """
        Instantiate a new DSS API client on the given base URI with the given API key.

        :param str uri: Base URI of the DSS API node server (http://host:port/ or https://host:port/)
        :param str service_id: Identifier of the service to query
        :param str api_key: Optional, API key for the service. Only required if the service has authentication
        """
        DSSBaseClient.__init__(self, "%s/%s" % (uri, "public/api/v1/%s" % service_id), api_key)

    def predict_record(self, endpoint_id, features, forced_generation=None, dispatch_key=None, context=None):
        """
        Predicts a single record on a DSS API node endpoint (standard or custom prediction)

        :param str endpoint_id: Identifier of the endpoint to query
        :param features: Python dictionary of features of the record
        :param forced_generation: See documentation about multi-version prediction
        :param dispatch_key: See documentation about multi-version prediction
        :param context: Optional, Python dictionary of additional context information. The context information is logged, but not directly used.

        :return: a Python dict of the API answer. The answer contains a "result" key (itself a dict)
        """
        obj =  {
            "features" :features
        }
        if context is not None:
            obj["context"] = context
        if forced_generation is not None:
            obj["dispatch"] = {"forcedGeneration" : forced_generation }
        elif dispatch_key is not None:
            obj["dispatch"] = {"dispatchKey" : dispatch_key }

        return self._perform_json("POST", "%s/predict" % endpoint_id, body = obj)

    def predict_records(self, endpoint_id, records, forced_generation=None, dispatch_key=None):
        """
        Predicts a batch of records on a DSS API node endpoint (standard or custom prediction)

        :param str endpoint_id: Identifier of the endpoint to query
        :param records: Python list of records. Each record must be a Python dict. Each record must contain a "features" dict (see predict_record) and optionally a "context" dict.
        :param forced_generation: See documentation about multi-version prediction
        :param dispatch_key: See documentation about multi-version prediction

        :return: a Python dict of the API answer. The answer contains a "results" key (which is an array of result objects)
        """

        for record in records:
            if not "features" in record:
                raise ValueError("Each record must contain a 'features' dict")

        obj = {
            "items" : records
        }

        if forced_generation is not None:
            obj["dispatch"] = {"forcedGeneration" : forced_generation }
        elif dispatch_key is not None:
            obj["dispatch"] = {"dispatchKey" : dispatch_key }

        return self._perform_json("POST", "%s/predict-multi" % endpoint_id, body = obj)