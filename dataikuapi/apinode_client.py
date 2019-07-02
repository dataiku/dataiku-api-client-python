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

    def predict_record(self, endpoint_id, features, forced_generation=None, dispatch_key=None, context=None, partition=None):
        """
        Predicts a single record on a DSS API node endpoint (standard or custom prediction)

        :param str endpoint_id: Identifier of the endpoint to query
        :param features: Python dictionary of features of the record
        :param forced_generation: See documentation about multi-version prediction
        :param dispatch_key: See documentation about multi-version prediction
        :param context: Optional, Python dictionary of additional context information. The context information is logged, but not directly used.
        :param partition: Optional, partition id of partitioned model to use. Guessed otherwise from record if needed.

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
        if partition is not None:
            obj["partition"] = partition

        return self._perform_json("POST", "%s/predict" % endpoint_id, body = obj)

    def predict_records(self, endpoint_id, records, forced_generation=None, dispatch_key=None, partition=None):
        """
        Predicts a batch of records on a DSS API node endpoint (standard or custom prediction)

        :param str endpoint_id: Identifier of the endpoint to query
        :param records: Python list of records. Each record must be a Python dict. Each record must contain a "features" dict (see predict_record) and optionally a "context" dict.
        :param forced_generation: See documentation about multi-version prediction
        :param dispatch_key: See documentation about multi-version prediction
        :param partition: Optional, partition id of partitioned model to use for all records. Guessed otherwise from each record if needed.

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
        if partition is not None:
            obj["partition"] = partition

        return self._perform_json("POST", "%s/predict-multi" % endpoint_id, body = obj)

    def sql_query(self, endpoint_id, parameters):
        """
        Queries a "SQL query" endpoint on a DSS API node

        :param str endpoint_id: Identifier of the endpoint to query
        :param parameters: Python dictionary of the named parameters for the SQL query endpoint

        :return: a Python dict of the API answer. The answer is the a dict with a columns field and a rows field (list of rows as list of strings)
        """
        return self._perform_json("POST", "%s/query" % endpoint_id, body = parameters)


    def lookup_record(self, endpoint_id, record, context=None):
        """
        Lookup a single record on a DSS API node endpoint of "dataset lookup" type

        :param str endpoint_id: Identifier of the endpoint to query
        :param record: Python dictionary of features of the record
        :param context: Optional, Python dictionary of additional context information. The context information is logged, but not directly used.

        :return: a Python dict of the API answer. The answer contains a "data" key (itself a dict)
        """
        obj =  {
            "data" :record
        }
        if context is not None:
            obj["context"] = context

        return self._perform_json("POST", "%s/lookup" % endpoint_id, body = obj).get("results", [])[0]

    def lookup_records(self, endpoint_id, records):
        """
        Lookups a batch of records on a DSS API node endpoint of "dataset lookup" type

        :param str endpoint_id: Identifier of the endpoint to query
        :param records: Python list of records. Each record must be a Python dict, containing at least one entry called "data": a dict containing the input columns

        :return: a Python dict of the API answer. The answer contains a "results" key, which is an array of result objects. Each result contains a "data" dict which is the output
        """

        for record in records:
            if not "data" in record:
                raise ValueError("Each record must contain a 'data' dict")

        obj = {
            "items" : records
        }

        return self._perform_json("POST", "%s/lookup-multi" % endpoint_id, body = obj)

    def run_function(self, endpoint_id, **kwargs):
        """
        Calls a "Run function" endpoint on a DSS API node

        :param str endpoint_id: Identifier of the endpoint to query
        :param kwargs: Arguments of the function

        :return: The function result
        """
        obj = {}
        for (k,v) in kwargs.items():
            obj[k] = v
        return self._perform_json("POST", "%s/run" % endpoint_id, body = obj)
