from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader


class DSSDataset(object):
    """
    A dataset on the DSS instance
    """
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
        """
        Get the definition of the dataset
        
        Returns:
            the definition, as a JSON object
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name))

    def set_definition(self, definition):
        """
        Set the definition of the dataset
        
        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/" % (self.project_key, self.dataset_name),
                body=definition)

    ########################################################
    # Dataset metadata
    ########################################################

    def get_schema(self):
        """
        Get the schema of the dataset
        
        Returns:
            a JSON object of the schema, with the list of columns
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name))

    def set_schema(self, schema):
        """
        Set the schema of the dataset
        
        Args:
            schema: the desired schema for the dataset, as a JSON object. All columns have to provide their
            name and type
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/schema" % (self.project_key, self.dataset_name),
                body=schema)

    def get_metadata(self):
        """
        Get the metadata attached to this dataset. The metadata contains label, description
        checklists, tags and custom metadata of the dataset
        
        Returns:
            a dict object. For more information on available metadata, please see
            https://doc.dataiku.com/dss/api/latest
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name))

    def set_metadata(self, metadata):
        """
        Set the metadata on this dataset.
        
        Args:
            metadata: the new state of the metadata for the dataset. You should only set a metadata object 
            that has been retrieved using the get_metadata call.
        """
        return self.client._perform_json(
                "PUT", "/projects/%s/datasets/%s/metadata" % (self.project_key, self.dataset_name),
                body=metadata)


    ########################################################
    # Dataset data
    ########################################################

    def iter_rows(self, partitions=None):
        """
        Get the dataset's data
        
        Return:
            an iterator over the rows, each row being a tuple of values. The order of values
            in the tuples is the same as the order of columns in the schema returned by get_schema
        """
        csv_stream = self.client._perform_raw(
                "GET" , "/projects/%s/datasets/%s/data/" %(self.project_key, self.dataset_name),
                params = {
                    "format" : "tsv-excel-noheader",
                    "partitions" : partitions
                })

        return DataikuStreamedHttpUTF8CSVReader(self.get_schema()["columns"], csv_stream).iter_rows()


    def list_partitions(self):
        """
        Get the list of all partitions of this dataset
        
        Returns:
            the list of partitions, as a list of strings
        """
        return self.client._perform_json(
                "GET", "/projects/%s/datasets/%s/partitions" % (self.project_key, self.dataset_name))


    def clear(self, partitions=None):
        """
        Clear all data in this dataset
        
        Args:
            partitions: (optional) a list of partitions to clear. When not provided, the entire dataset
            is cleared
        """
        return self.client._perform_json(
                "DELETE", "/projects/%s/datasets/%s/data" % (self.project_key, self.dataset_name),
                params={"partitions" : partitions})

    ########################################################
    # Dataset actions
    ########################################################

    def synchronize_hive_metastore(self):
        """
        Synchronize this dataset with the Hive metastore
        """
        self.client._perform_empty(
                "POST" , "/projects/%s/datasets/%s/actions/synchronizeHiveMetastore" %(self.project_key, self.dataset_name))
        