import csv
from dateutil import parser as date_iso_parser
from itertools import izip_longest

from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader

from contextlib import closing

def none_if_throws(f):
    def aux(*args, **kargs):
        try:
            return f(*args, **kargs)
        except:
            return None
    return aux

class DSSDataset(object):

    def __init__(self, client, project_key, dataset_name):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name

    def get_schema(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_config(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name))

    def set_config(self, config):
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name),
                body=config)

    def iter_rows(self):

        csv_stream = self.client._perform_raw(
                "GET" , "/projects/%s/datasets/%s/data/" %(self.project_key, self.dataset_name),
                params = {
                    "format" : "tsv-excel-noheader"
                })

        def decode(x):
            return unicode(x, "utf8")

        def parse_iso_date(s):
            if s == "":
                return None
            else:
                return date_iso_parser.parse(s)
        CASTERS = {
            "int": int,
            "bigint": int,
            "float": float,
            "double": float,
            "date": parse_iso_date,
            "boolean": bool,
        }
        schema = self.get_schema()
        casters = [
            CASTERS.get(col["type"], decode) for col in schema["columns"]
        ]
        with closing(csv_stream) as r:
            for uncasted_tuple in csv.reader(r.raw,
                                         delimiter='\t',
                                         quotechar='"',
                                         doublequote=True):
                yield [none_if_throws(caster)(val)
                       for (caster, val) in izip_longest(casters, uncasted_tuple)]
