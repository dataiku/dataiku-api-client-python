import csv, sys
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

class DSSExtensibleDict(dict):
    """
    Utility to define dict-like objects that can be sub-classed.
    
    Behaves like dict for most common operations. In particular, 
    it is possible to update an instance of `:class:`dataikuapi.dss.ml.DSSExtensibleDict` 
    with either a dict or another instance of `:class:`dataikuapi.dss.ml.DSSExtensibleDict`.
    
    Provides an `internal_dict` dict field that is the actual holder of the data.
    """
    
    def __init__(self, orig_dict=None):
        if orig_dict is None:
            self.internal_dict = dict()
        else:
            self.internal_dict = orig_dict

    def __getitem__(self, key):
        return self.internal_dict[key]

    def __iter__(self):
        return self.internal_dict.__iter__()

    def __setitem__(self, key, value):
        self.internal_dict[key] = value

    def __str__(self):
        return self.internal_dict.__str__()
    
    def __len__(self):
        return self.internal_dict.__len__()

    def clear(self):
        self.internal_dict.clear()
    
    def __contains__(self, key):
        return self.internal_dict.__contains__(key)

    def copy(self):
        return self.internal_dict.copy()

    def fromkeys(self, sequence, value=None):
        return self.internal_dict.fromkeys(sequence, value)

    def get(self, key, value=None):
        return self.internal_dict.get(key, value)

    def items(self):
        return self.internal_dict.items()

    def keys(self):
        return self.internal_dict.keys()

    def popitem(self):
        return self.internal_dict.popitem()

    def pop(self, key, *argv):
        return self.internal_dict.pop(key, *argv)

    def setdefault(self, key, default_value=None):
        return self.internal_dict.setdefault(key, default_value)

    def update(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], DSSExtensibleDict):
            self.internal_dict.update(args[0].internal_dict, **kwargs)
        else:
            self.internal_dict.update(*args, **kwargs)

    def values(self):
        return self.internal_dict.values()
