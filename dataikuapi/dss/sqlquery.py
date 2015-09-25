from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader

class DSSSQLQuery(object):

    def __init__(self, client, query, connection, database, dataset_full_name, pre_queries, post_queries, type):
        self.client = client
        self.query = query
        self.connection = connection
        self.database = database
        self.dataset_full_name = dataset_full_name
        self.pre_queries = pre_queries
        self.post_queries = post_queries
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
                    "type" : self.type
                })
        self.queryId = self.streaming_session['queryId']

    def get_schema(self):
        """
        Get the query's result set's schema
        """
        return self.streaming_session['schema']

    def iter_rows(self):
        """
        Iterator over the query's result set
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
        """
        resp = self.client._perform_empty(
                "GET", "/sql/queries/%s/finish-streaming" % (self.queryId))
        # exception raising is done in _perform_empty()