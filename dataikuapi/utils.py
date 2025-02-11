import csv, sys
from dateutil import parser as date_iso_parser
from contextlib import closing
import os
import zipfile
import itertools
import sys
import time
from datetime import datetime

if sys.version_info > (3,0):
    import codecs

    dku_basestring_type = str
    dku_zip_longest = itertools.zip_longest
else:
    dku_basestring_type = basestring
    dku_zip_longest = itertools.izip_longest



class DataikuException(Exception):
    """Exception launched by the Dataiku API clients when an error occurs"""

def handle_http_exception(http_res):
    if http_res.status_code >= 400:
        try:
            ex = http_res.json()
        except ValueError:
            ex = {"message": http_res.text}
        raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("detailedMessage", ex.get("message", "No message"))))


class DataikuUTF8CSVReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in UTF-8.
    """

    def __init__(self, f, **kwds):
        self.reader = csv.reader(f, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

def none_if_throws(f):
    def aux(*args, **kargs):
        try:
            return f(*args, **kargs)
        except:
            return None
    return aux


class DataikuValueCaster(object):
    def __init__(self, schema):
        self.casters = self._get_value_casters(schema)
        
    def _get_value_casters(self, schema):
        def decode(x):
            if sys.version_info > (3,0):
                return x
            else:
                return unicode(x, "utf8")
    
        def parse_iso_date(s):
            if s == "":
                return None
            else:
                return date_iso_parser.parse(s)
    
        def str_to_bool(s):
            if s is None:
                return False
            return s.lower() == "true"
    
        CASTERS = {
            "tinyint" : int,
            "smallint" : int,
            "int": int,
            "bigint": int,
            "float": float,
            "double": float,
            "date": parse_iso_date,
            "dateonly": parse_iso_date,
            "datetimenotz": parse_iso_date,
            "boolean": str_to_bool,
        }
        return [CASTERS.get(col["type"], decode) for col in schema]
    
    def cast_values(self, values):
        return [none_if_throws(caster)(val)
                for (caster, val) in dku_zip_longest(self.casters, values)]


class DataikuStreamedHttpUTF8CSVReader(object):
    """
    A CSV reader with a schema

    To verify the stream after all rows have been yielded, you must pass **ALL** the optional arguments:
    read_session_id, client, project_key, dataset_name
    """
    def __init__(self, schema, csv_stream, read_session_id=None, client=None, project_key=None, dataset_name=None):
        self.schema = schema
        self.csv_stream = csv_stream
        # To verify a dataset streaming session
        self.read_session_id = read_session_id
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.client = client

    def iter_rows(self):
        schema = self.schema
        value_caster = DataikuValueCaster(schema)
        with closing(self.csv_stream) as r:
            if sys.version_info > (3,0):
                raw_generator = codecs.iterdecode(r.raw, 'utf-8')
            else:
                raw_generator = r.raw
            for uncasted_tuple in csv.reader(raw_generator,
                                                delimiter='\t',
                                                quotechar='"',
                                                doublequote=True):
                yield value_caster.cast_values(uncasted_tuple)

        if self.read_session_id:
            # exception will be raised if there's an error while streaming
            self.client._perform_empty(
                "GET", "/projects/%s/datasets/%s/finish-streaming/" % (self.project_key, self.dataset_name),
                params = {
                    "readSessionId" : self.read_session_id
                })


class CallableStr(str):
    def __init__(self, val):
        self.val = val

    def __call__(self):
        return self.val


def _make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipfp:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename):
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zipfp.write(filename, arcname)
    return output_filename


def _write_response_content_to_file(response, path):
    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=10000):
            if chunk:
                f.write(chunk)
                f.flush()

if sys.version_info >= (3,3):
    _local_timezone = datetime.now().astimezone().tzinfo
else:
    _local_timezone = None
def _timestamp_ms_to_zoned_datetime(timestamp_ms):
    if timestamp_ms and timestamp_ms > 0:
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=_local_timezone)
    else:
        return None


class _ExponentialBackoff(object):
    # These values lead to:
    #  - 25 calls in the first 20 seconds
    #  - Overhead overall remains below 10%
    #  - After 1 minute, the interval is 5 seconds

    def __init__(self, initial_time_ms=200, max_time_ms=15000, factor=1.1):
        self.initial_time_ms = initial_time_ms
        self.last_time = None
        self.max_time_ms = max_time_ms
        self.factor = factor

    def next_sleep_time(self):
        if self.last_time is None:
            next_time = self.initial_time_ms
        else:
            next_time = self.last_time * self.factor
        if next_time > self.max_time_ms:
            next_time = self.max_time_ms

        self.last_time = next_time

        return next_time

    def sleep_next(self):
        sleep_time = float(self.next_sleep_time()) / 1000.0
        #print("Sleeping %.3f" % sleep_time)
        time.sleep(sleep_time)