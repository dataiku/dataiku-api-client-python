import csv
from dateutil import parser as date_iso_parser
from itertools import izip_longest
from contextlib import closing


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
            for uncasted_tuple in csv.reader(r.raw,
                                         delimiter='\t',
                                         quotechar='"',
                                         doublequote=True):
                yield [none_if_throws(caster)(val)
                       for (caster, val) in izip_longest(casters, uncasted_tuple)]
