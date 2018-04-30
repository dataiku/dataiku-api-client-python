import json

class DSSAPIServiceSettings(object):
    """
    The settings of an API Service in the API Designer

    Do not create this directly, use :meth:`DSSAPIService.get_settings`
    """
    def __init__(self, client, project_key, service_id, settings):
        self.client = client
        self.project_key = project_key
        self.service_id = service_id
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this API Service. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def add_prediction_endpoint(self, endpoint_id, saved_model_id):
        """Adds a new "visual prediction" endpoint to this API service

        :param str endpoint_id: Identifier of the new endpoint to create
        :param str saved_model_id: Identifier of the saved model (deployed to Flow) to use
        """
        self.settings["endpoints"].append({
            "id" : endpoint_id,
            "type" : "STD_PREDICTION",
            "modelRef": saved_model_id
        })

    def save(self):
        """Saves back these settings to the API Service"""
        self.client._perform_empty(
                "PUT", "/projects/%s/apiservices/%s/settings" % (self.project_key, self.service_id),
                body = self.settings)


class DSSAPIService(object):
    """
    An API Service from the API Designer on the DSS instance

    Do not create this directly, use :meth:`dataikuapi.dss.project.DSSProject.get_api_service`
    """
    def __init__(self, client, project_key, service_id):
        self.client = client
        self.project_key = project_key
        self.service_id = service_id

    def get_settings(self):
        """Gets the settings of this API Service"""
        settings = self.client._perform_json(
            "GET", "/projects/%s/apiservices/%s/settings" % (self.project_key, self.service_id))

        return DSSAPIServiceSettings(self.client, self.project_key, self.service_id, settings)

    def list_packages(self):
        """
        List the versions of this API service
        
        :returns: a list of dictionaries, with one item per version.
                  Each dictionary contains at least a 'id' field which is the version identifier
        :rtype: list of dict
        """
        return self.client._perform_json(
            "GET", "/projects/%s/apiservices/%s/packages" % (self.project_key, self.service_id))

    def create_package(self, package_id):
        """
        Create a new version of this API service

        :param str package_id: Identifier of the new version to create
        """
        return self.client._perform_empty(
            "POST", "/projects/%s/apiservices/%s/packages/%s" % (self.project_key, self.service_id, package_id))

    def delete_package(self, package_id):
        """
        Delete a version of this API service
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/apiservices/%s/packages/%s" % (self.project_key, self.service_id, package_id))

    def download_package_stream(self, package_id):
        """
        Download a package archive that can be deployed in a DSS API Node, as a binary stream.
        
        Warning: this stream will monopolize the DSSClient until closed.
        """
        return self.client._perform_raw(
            "GET", "/projects/%s/apiservices/%s/packages/%s/archive" % (self.project_key, self.service_id, package_id)).raw

    def download_package_to_file(self, package_id, path):
        """
        Download a package archive that can be deployed in a DSS API Node, into the given output file.
        """
        package_stream = self.client._perform_raw(
            "GET", "/projects/%s/apiservices/%s/packages/%s/archive" % (self.project_key, self.service_id, package_id))
        with open(path, 'wb') as f:
            for chunk in package_stream.iter_content(chunk_size=10000):
                if chunk:
                    f.write(chunk)
                    f.flush()

