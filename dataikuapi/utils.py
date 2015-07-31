import csv

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