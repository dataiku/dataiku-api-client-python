from dataset import DSSDataset
from job import DSSJob


class DSSProject(object):

    def __init__(self, client, project_key):
       self.client = client
       self.project_key = project_key
       
    ########################################################
    # Project deletion
    ########################################################
    
    def delete(self):
       """
       Delete the project
       """
       return self.client._perform_empty(
          "DELETE", "/projects/%s" % self.project_key)

    ########################################################
    # Project export
    ########################################################
    
    def get_export_stream(self):
       """
       Return a stream of the exported project
       """
       return self.client._perform_raw(
          "GET", "/projects/%s/export" % self.project_key).raw

    def export_to_file(self, path):
       """
       Return a stream of the exported project
       """
       with open(path, 'w') as f:
          export_stream = self.client._perform_raw(
             "GET", "/projects/%s/export" % self.project_key)
          for chunk in export_stream.iter_content(chunk_size=10000):
             if chunk:
                f.write(chunk)
                f.flush()

    ########################################################
    # Project infos
    ########################################################

    def get_metadata(self):
       """
       Get the metadata attached to this project.
       Metadata is retrieved as a dict object. For more information on available metadata, please see
       https://doc.dataiku.com/dss/api/latest
       """
       return self.client._perform_json(
          "GET", "/projects/%s/metadata" % self.project_key)

    def set_metadata(self, metadata):
       """
       Set the metadata on this project.

       You should only set a metadata object that has been retrieved using the get_metadata call.
       """
       return self.client._perform_empty(
          "PUT", "/projects/%s/metadata" % self.project_key, body = metadata)

    def get_permissions(self):
       """
       Get the permissions attached to this project
       """
       return self.client._perform_json(
          "GET", "/projects/%s/permissions" % self.project_key)

    def set_permissions(self, permissions):
       """
       Set the permissions on this project
       """
       return self.client._perform_empty(
          "PUT", "/projects/%s/permissions" % self.project_key, body = permissions)

    ########################################################
    # Datasets
    ########################################################

    def list_datasets(self):
       """
       List the datasets in this project
       """
       return self.client._perform_json(
          "GET", "/projects/%s/datasets/" % self.project_key)

    def get_dataset(self, dataset_name):
       """
       Get a handler to interact with a specific dataset
       """
       return DSSDataset(self.client, self.project_key, dataset_name)

    def create_dataset(self, dataset_name, type,
                params={}, formatType=None, formatParams={}):

       obj = {
          "name" : dataset_name,
          "projectKey" : self.project_key,
          "type" : type,
          "params" : params,
          "formatType" : formatType,
          "formatParams" : formatParams
       }
       self.client._perform_json("POST", "/projects/%s/datasets/" % self.project_key,
                       body = obj)
       return DSSDataset(self.client, self.project_key, dataset_name)


    ########################################################
    # Jobs
    ########################################################

    def list_jobs(self):
       """
       List the jobs in this project
       """
       return self.client._perform_json(
          "GET", "/projects/%s/jobs/" % self.project_key)

    def get_job(self, id):
       """
       Get a handler to interact with a specific job
       """
       return DSSJob(self.client, self.project_key, id)

    def start_job(self, definition):

        job_def = self.client._perform_json("POST", "/projects/%s/jobs/" % self.project_key, body = definition)
        return DSSJob(self.client, self.project_key, job_def['id'])
