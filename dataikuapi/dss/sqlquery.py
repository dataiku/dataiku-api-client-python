from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader

class DSSSQLQuery(object):
    """
    A connection to a database or database-like on which queries can be run through DSS
    """
    def __init__(self, client, query, connection, database, dataset_full_name, pre_queries, post_queries, type, extra_conf):
        self.client = client
        self.query = query
        self.connection = connection
        self.database = database
        self.dataset_full_name = dataset_full_name
        self.pre_queries = pre_queries
        self.post_queries = post_queries
        self.extra_conf = extra_conf
        self.type = type

        self.streaming_session = self.client._perform_json(
                "POST", "/sql/queries/",
                body = {
                    "query" : self.query,
                    "preQueries" : self.pre_queries,
                    "postQueries" : self.post_queries,
                    "connection" : self.connection,
                    "database" : self.database,
                    "datasetFullName" : self.dataset_full_name,
                    "type" : self.type,
                    "extraConf" : extra_conf
                })
        self.queryId = self.streaming_session['queryId']

    def get_schema(self):
        """
        Get the query's result set's schema
        
        Returns:
            the schema as a JSON array of columns
        """
        return self.streaming_session['schema']

    def iter_rows(self):
        """
        Get the query's results
        
        Returns:
            an iterator over the rows, each row being a tuple of values. The order of values
            in the tuples is the same as the order of columns in the schema returned by get_schema
        """
        csv_stream = self.client._perform_raw(
                "GET", "/sql/queries/%s/stream" % (self.queryId),
                params = {
                    "format" : "tsv-excel-noheader"
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema(), csv_stream).iter_rows()

    def verify(self):
        """
        Verify that the result set streaming completed successfully and was not truncated
        
        Raises:
            if the query failed at some point while streaming the results, an exception will be raised.
            If the call completes without exception, then the query was successfully streamed
        """
        resp = self.client._perform_empty(
                "GET", "/sql/queries/%s/finish-streaming" % (self.queryId))
        # exception raising is done in _perform_empty()