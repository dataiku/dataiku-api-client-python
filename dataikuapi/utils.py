import csv, sys, threading
from dateutil import parser as date_iso_parser
from contextlib import closing

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

impersonate_tickets = threading.local()

def _get_current_impersonate_tickets():
    global impersonate_tickets
    if hasattr(impersonate_tickets, 'x'):
        return impersonate_tickets.x
    else:
        return None

class DkuProxyingContext(object):
    """
    Use in a `with DkuProxyingContext(True):` to make all calls attempt to exchange the current
    ticket for one impersonating the current browser identity. Conversely, use `with DkuProxyingContext(False):`
    to make calls use the default ticket (in case impersonation has been set as default)
    """
    def __init__(self, impersonate):
        self.impersonate = impersonate
        self.previous = None

    def __enter__(self):
        global impersonate_tickets
        self.previous = _get_current_impersonate_tickets()
        impersonate_tickets.x = self.impersonate
        
    def __exit__(self, exception_type, exception_value, traceback):
        global impersonate_tickets
        impersonate_tickets.x = self.previous
        
