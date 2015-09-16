from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader


class DSSDataset(object):

    def __init__(self, client, project_key, dataset_name):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name

    ########################################################
    # Dataset deletion
    ########################################################
    
    def delete(self):
        """
        Delete the dataset
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s" % (self.project_key, self.dataset_name))



    ########################################################
    # Dataset definition
    ########################################################
    
    def get_definition(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name))

    def set_definition(self, definition):
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name),
                body=definition)

    ########################################################
    # Dataset metadata
    ########################################################

    def get_schema(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_metadata(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name))

    def set_metadata(self, metadata):
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name),
                body=metadata)


    ########################################################
    # Dataset data
    ########################################################

    def iter_rows(self):
        csv_stream = self.client._perform_raw(
                "GET" , "/projects/%s/datasets/%s/data/" %(self.project_key, self.dataset_name),
                params = {
                    "format" : "tsv-excel-noheader"
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema()["columns"], csv_stream).iter_rows()


    def list_partitions(self):
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/partitions" % (self.project_key, self.dataset_name))


    def clear(self, partitions=None):
        return self.client._perform_json(
                "DELETE", "/projects/%s/datasets/%s/data" % (self.project_key, self.dataset_name),
                params={"partitions" : partitions})

    ########################################################
    # Dataset actions
    ########################################################

    def synchronize_hive_metastore(self):
        self.client._perform_empty(
                "POST" , "/projects/%s/datasets/%s/actions/synchronizeHiveMetastore" %(self.project_key, self.dataset_name))
        