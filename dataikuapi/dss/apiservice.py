import json

class DSSAPIServiceListItem(dict):
    """
    An item in a list of API services. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_api_services()`
    """
    def __init__(self, client, data):
        super(DSSAPIServiceListItem, self).__init__(data)
        self.client = client

    def to_api_service(self):
        """
        Get a handle corresponding to this API service.

        :rtype: :class:`DSSAPIService`
        """
        return DSSAPIService(self.client, self["projectKey"], self["id"])

    @property
    def name(self):
        """
        Get the name of the API service.

        :rtype: string
        """
        return self["name"]

    @property
    def id(self):
        """
        Get the identifier of the API service.

        :rtype: string
        """
        return self["id"]

    @property
    def auth_method(self):
        """
        Get the method used to authenticate on the API service.

        Usage example:

        .. code-block:: python

            # list all public API services
            for service in project.list_api_services(as_type="list_item"):
                if service.auth_method == 'PUBLIC':
                    print("Service {} isn't authenticating requests".format(service.id))

        :return: an authentication method. Possible values: PUBLIC (no authentication), API_KEYS, OAUTH2
        :rtype: string
        """
        return self["authMethod"]

    @property
    def endpoints(self):
        """
        Get the endpoints in this API service.

        :return: a list of endpoints, each one a dict with fields:

                    * **id** : identifier of the endpoint
                    * **type** : type of endpoint. Possible values: STD_PREDICTION, STD_CLUSTERING, STD_FORECAST, STD_CAUSAL_PREDICTION, CUSTOM_PREDICTION, CUSTOM_R_PREDICTION, R_FUNCTION, PY_FUNCTION, DATASETS_LOOKUP, SQL_QUERY

        :rtype: list[dict]
        """
        return self["endpoints"]


class DSSAPIServiceSettings(object):
    """
    The settings of an API Service in the API Designer.

    .. important::

        Do not instantiate directly, use :meth:`DSSAPIService.get_settings`.
    """
    def __init__(self, client, project_key, service_id, settings):
        self.client = client
        self.project_key = project_key
        self.service_id = service_id
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of this API Service. 

        This returns a reference to the raw settings, not a copy, so changes made 
        to the returned object will be reflected when saving.

        :return: the settings of the API service, as a dict. Notable fields are:

                    * **projectKey** and **id** : identifier of the API service
                    * **name** : name of API service in UI
                    * **tags** : list of tags (each a string)
                    * **authMethod** : method used to authenticate calls on the service. Possible values: PUBLIC, API_KEYS, OAUTH2
                    * **authRealm** : dict of API keys settings, used when **authMethod** is API_KEYS. This dict has a sub-field:

                        * **queryKeys** : list of API keys allowed on queries, each key being a string

                    * **oauth2Config** : dict of OAuth2 settings, used when **authMethod** is OAUTH2
                    * **endpoints** : list of endpoints, each one a dict. Endpoint have different fields depending on their type, but always have at least:

                        * **id** : identifier of the endpoint
                        * **type** : type of endpoint. Possible values: STD_PREDICTION, STD_CLUSTERING, STD_FORECAST, STD_CAUSAL_PREDICTION, CUSTOM_PREDICTION, CUSTOM_R_PREDICTION, R_FUNCTION, PY_FUNCTION, DATASETS_LOOKUP, SQL_QUERY

        :rtype: dict
        """
        return self.settings

    @property
    def auth_method(self):
        """
        Get the method used to authenticate on the API service

        :return: an authentication method. Possible values: PUBLIC (no authentication), API_KEYS, OAUTH2
        :rtype: string
        """
        return self.settings["authMethod"]     

    @property
    def endpoints(self):
        """
        Get the list of endpoints of this API service

        :return: ist of endpoints, each one a dict. Endpoint have different fields depending on their type, but always have at least:

                        * **id** : identifier of the endpoint
                        * **type** : type of endpoint. Possible values: STD_PREDICTION, STD_CLUSTERING, STD_FORECAST, STD_CAUSAL_PREDICTION, CUSTOM_PREDICTION, CUSTOM_R_PREDICTION, R_FUNCTION, PY_FUNCTION, DATASETS_LOOKUP, SQL_QUERY

        :rtype: list[dict]
        """
        return self.settings["endpoints"]
    

    def add_prediction_endpoint(self, endpoint_id, saved_model_id):
        """
        Add a new "visual prediction" endpoint to this API service.

        :param string endpoint_id: identifier of the new endpoint to create
        :param string saved_model_id: identifier of the saved model (that is currently deployed to the Flow) to use
        """
        self.settings["endpoints"].append({
            "id" : endpoint_id,
            "type" : "STD_PREDICTION",
            "modelRef": saved_model_id
        })

    def add_clustering_endpoint(self, endpoint_id, saved_model_id):
        """
        Add a new "visual clustering" endpoint to this API service.

        :param string endpoint_id: identifier of the new endpoint to create
        :param string saved_model_id: identifier of the saved model (that is currently deployed to the Flow) to use
        """
        self.settings["endpoints"].append({
            "id" : endpoint_id,
            "type" : "STD_CLUSTERING",
            "modelRef": saved_model_id
        })

    def add_forecasting_endpoint(self, endpoint_id, saved_model_id):
        """
        Add a new "visual time series forecasting" endpoint to this API service.

        :param string endpoint_id: identifier of the new endpoint to create
        :param string saved_model_id: identifier of the saved model (that is currently deployed to the Flow) to use
        """
        self.settings["endpoints"].append({
            "id" : endpoint_id,
            "type" : "STD_FORECAST",
            "modelRef": saved_model_id
        })

    def save(self):
        """
        Save back these settings to the API Service.
        """
        self.client._perform_empty(
                "PUT", "/projects/%s/apiservices/%s/settings" % (self.project_key, self.service_id),
                body = self.settings)


class DSSAPIService(object):
    """
    An API Service from the API Designer on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_api_service`
    """
    def __init__(self, client, project_key, service_id):
        self.client = client
        self.project_key = project_key
        self.service_id = service_id

    @property
    def id(self):
        """
        Get the API service's identifier
        
        :rtype: string
        """
        return self.service_id

    def get_settings(self):
        """
        Get the settings of this API Service.

        Usage example:

        .. code-block:: python

            # list all API services using a given model
            model_lookup = "my_saved_model_id"
            model = project.get_saved_model(model_lookup)
            model_name = model.get_settings().get_raw()["name"]
            for service in project.list_api_services(as_type='object'):
                settings = service.get_settings()
                endpoints_on_model = [e for e in settings.endpoints if e.get("modelRef", '') == model_lookup]
                if len(endpoints_on_model) > 0:
                    print("Service {} uses model {}".format(service.id, model_name))

        :return: a handle on the settings
        :rtype: :class:`DSSAPIServiceSettings`
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/apiservices/%s/settings" % (self.project_key, self.service_id))

        return DSSAPIServiceSettings(self.client, self.project_key, self.service_id, settings)

    def list_packages(self):
        """
        List the versions of this API service.
        
        :return: a list of pacakges, each one as a dict. Each dict has fields:

                    * **id** : version (identifier) of the package
                    * **createdOn** : timestamp in milliseconds of when the package was created

        :rtype: list[dict]
        """
        return self.client._perform_json(
            "GET", "/projects/%s/apiservices/%s/packages" % (self.project_key, self.service_id))

    def create_package(self, package_id):
        """
        Create a new version of this API service.

        :param string package_id: version (identifier) of the package to create
        """
        self.client._perform_empty(
            "POST", "/projects/%s/apiservices/%s/packages/%s" % (self.project_key, self.service_id, package_id))

    def delete_package(self, package_id):
        """
        Delete a version of this API service.

        :param string package_id: version (identifier) of the package to delete
        """
        self.client._perform_empty(
            "DELETE", "/projects/%s/apiservices/%s/packages/%s" % (self.project_key, self.service_id, package_id))

    def download_package_stream(self, package_id):
        """
        Download an archive of a package as a stream.

        The archive can then be deployed in a DSS API Node.
        
        .. warning::

            This call will monopolize the DSSClient until the stream it returns is closed.

        :param string package_id: version (identifier) of the package to download

        :return: the package archive, as a HTTP stream
        :rtype: file-like
        """
        return self.client._perform_raw(
            "GET", "/projects/%s/apiservices/%s/packages/%s/archive" % (self.project_key, self.service_id, package_id)).raw

    def download_package_to_file(self, package_id, path):
        """
        Download an archive of a package to a local file.

        The archive can then be deployed in a DSS API Node.
        
        :param string package_id: version (identifier) of the package to download
        :param string path: absolute or relative path to a file in which the package is downloaded
        """
        package_stream = self.client._perform_raw(
            "GET", "/projects/%s/apiservices/%s/packages/%s/archive" % (self.project_key, self.service_id, package_id))
        with open(path, 'wb') as f:
            for chunk in package_stream.iter_content(chunk_size=10000):
                if chunk:
                    f.write(chunk)
                    f.flush()

    def publish_package(self, package_id, published_service_id=None):
        """
        Publish a package on the API Deployer.

        :param string package_id: version (identifier) of the package to publish
        :param string published_service_id: identifier of the API service on the API Deployer in which the package will be published.
            A new published API service will be created if none matches the identifier.
            If the parameter is not set, the identifier from the current :class:`DSSAPIService` is used.
        """
        params = None
        if published_service_id is not None:
            params = {"publishedServiceId": published_service_id}
        self.client._perform_empty("POST", "/projects/%s/apiservices/%s/packages/%s/publish" % (self.project_key, self.service_id, package_id), params=params)
