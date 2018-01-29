import json

class DSSAPIServiceSettings(object):
    def __init__(self, client, project_key, service_id, settings):
        self.client = client
        self.project_key = project_key
        self.service_id = service_id
        self.settings = settings

    def add_prediction_endpoint(self, endpoint_id, saved_model_id):
        self.settings["endpoints"].append({
            "id" : endpoint_id,
            "type" : "STD_PREDICTION",
            "modelRef": saved_model_id
        })

    def save(self):
        """Saves back these settings to the API Service"""
        print("SAVING: %s" % json.dumps(self.settings, indent=2))
        self.client._perform_empty(
                "PUT", "/projects/%s/apiservices/%s/settings" % (self.project_key, self.service_id),
                body = self.settings)


class DSSAPIService(object):
    """
    An API Service on the DSS instance
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
        List the packages of this API services
        
        Returns:
            the list of API service packages, each one as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/apiservices/%s/packages" % (self.project_key, self.service_id))

    def create_package(self, package_id):
        """
        Prepare a package of this API service
        """
        return self.client._perform_empty(
            "POST", "/projects/%s/apiservices/%s/packages/%s" % (self.project_key, self.service_id, package_id))

    def delete_package(self, package_id):
        """
        Delete a package of this API service
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

