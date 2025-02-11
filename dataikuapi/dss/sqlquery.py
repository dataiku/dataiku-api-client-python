from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json


class DSSSQLQuery(object):
    """
    A connection to a database or database-like on which queries can be run through DSS.

    .. important::
    
        Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.sql_query`

    Usage example:

    .. code-block:: python

        # run some query on a connection
        query = client.sql_query('select * from "public"."SOME_TABLE"', connection='some_postgres_connection')
        n = 0
        for row in query.iter_rows():
            n += 1
            if n < 10:
                print("row %s : %s" % (n, row))
        query.verify()
        print("Returned %s rows" % n)

    """
    def __init__(self, client, query, connection, database, dataset_full_name, pre_queries, post_queries, type, extra_conf, script_steps, script_input_schema, script_output_schema, script_report_location, read_timestamp_without_timezone_as_string, read_date_as_string, datetimenotz_read_mode, dateonly_read_mode, project_key):
        self.client = client

        self.streaming_session = self.client._perform_json(
                "POST", "/sql/queries/",
                body = {
                    "query" : query,
                    "preQueries" : pre_queries,
                    "postQueries" : post_queries,
                    "connection" : connection,
                    "database" : database,
                    "datasetFullName" : dataset_full_name,
                    "projectKey" : project_key,
                    "type" : type,
                    "extraConf" : extra_conf,
                    "scriptSteps" : script_steps,
                    "scriptInputSchema" : script_input_schema,
                    "scriptOutputSchema" : script_output_schema,
                    "scriptReportLocation" : script_report_location,
                    "datetimenotzReadMode" : datetimenotz_read_mode,
                    "dateonlyReadMode" : dateonly_read_mode,
                    "readTimestampWithoutTimezoneAsString" : read_timestamp_without_timezone_as_string,
                    "readDateAsString" : read_date_as_string
                })
        self.queryId = self.streaming_session['queryId']

    def get_schema(self):
        """
        Get the query's result set's schema.

        The schema made of DSS column types, and built from mapping database types to DSS types. The actual
        type in the database can be found in the `originalType` field (`originalSQLType` in BigQuery)
        
        :return: a schema, as a dict with a `columns` array, in which each element is a column, itself as a dict of

                     * **name** : the column name
                     * **type** : the column type (smallint, int, bigint, float, double, boolean, date, string)
                     * **length** : the string length
                     * **comment** : the column name
                     * **originalType** : type of the column in the database

        :rtype: dict
        """
        return self.streaming_session['schema']

    def iter_rows(self):
        """
        Get an iterator on the query's results.
        
        :return: an iterator over the rows, each row being a tuple of values. The order of values
                 in the tuples is the same as the order of columns in the schema returned by :meth:`~get_schema()`.
                 The values are cast to python types according to the types in :meth:`~get_schema()`
        :rtype: iterator[list]
        """
        csv_stream = self.client._perform_raw(
                "GET", "/sql/queries/%s/stream" % (self.queryId),
                params = {
                    "format" : "tsv-excel-noheader"
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema(), csv_stream).iter_rows()

    def verify(self):
        """
        Verify that reading results completed successfully.

        When using the :meth:`~iter_rows()` method, and the iterator stops returning rows, there is
        no way to tell whether there are no more rows because the query didn't return more rows, or
        because an error in the query, or in the fetching of its results, happened. You should thus
        call :meth:`~verify()` after the iterator is done, because it will raise an Exception if
        an error happened.
        
        :raises: Exception
            
        """
        resp = self.client._perform_empty(
                "GET", "/sql/queries/%s/finish-streaming" % (self.queryId))
        # exception raising is done in _perform_empty()