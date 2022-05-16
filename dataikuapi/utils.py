import csv, sys
from dateutil import parser as date_iso_parser
from contextlib import closing
import os
import zipfile
import itertools

if sys.version_info > (3,0):
    import codecs

    dku_basestring_type = str
    dku_zip_longest = itertools.zip_longest
else:
    dku_basestring_type = basestring
    dku_zip_longest = itertools.izip_longest



class DataikuException(Exception):
    """Exception launched by the Dataiku API clients when an error occurs"""

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


class DataikuStreamedHttpUTF8CSVReader(object):
    """
    A CSV reader with a schema
    """
    def __init__(self, schema, csv_stream):
        self.schema = schema
        self.csv_stream = csv_stream

    def iter_rows(self):
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
            "boolean": str_to_bool,
        }
        schema = self.schema
        casters = [
            CASTERS.get(col["type"], decode) for col in schema
        ]
        with closing(self.csv_stream) as r:
            if sys.version_info > (3,0):
                raw_generator = codecs.iterdecode(r.raw, 'utf-8')
            else:
                raw_generator = r.raw
            for uncasted_tuple in csv.reader(raw_generator,
                                                delimiter='\t',
                                                quotechar='"',
                                                doublequote=True):
                yield [none_if_throws(caster)(val)
                        for (caster, val) in dku_zip_longest(casters, uncasted_tuple)]

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
