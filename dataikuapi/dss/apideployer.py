import json
from .future import DSSFuture
from ..utils import CallableStr

class DSSAPIDeployer(object):
    """
    Handle to interact with the API Deployer.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSClient.get_apideployer`
    """
    def __init__(self, client):
        self.client = client

    def list_deployments(self, as_objects=True):
        """
        Lists deployments on the API Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSAPIDeployerDeployment`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this deployment

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/api-deployer/deployments")
        if as_objects:
            return [DSSAPIDeployerDeployment(self.client, x["deploymentBasicInfo"]["id"]) for x in l]
        else:
            return l

    def get_deployment(self, deployment_id):
        """
        Returns a handle to interact with a single deployment, as a :class:`DSSAPIDeployerDeployment` 

        :param str deployment_id: Identifier of the deployment to get
        :rtype: :class:`DSSAPIDeployerDeployment`
        """
        return DSSAPIDeployerDeployment(self.client, deployment_id)

    def create_deployment(self, deployment_id, service_id, infra_id, version, endpoint_id=None, ignore_warnings=False):
        """
        Creates a deployment and returns the handle to interact with it. The returned deployment
        is not yet started and you need to call :meth:`~DSSAPIDeployerDeployment.start_update`

        :param str deployment_id: Identifier of the deployment to create
        :param str service_id: Identifier of the API Service to target
        :param str infra_id: Identifier of the deployment infrastructure to use
        :param str version: Identifier of the API Service version to deploy
        :param str endpoint_id: Identifier of the endpoint to deploy if you use a Deploy Anywhere infra. Ignored otherwise
        :param boolean ignore_warnings: ignore warnings concerning the governance status of the model version(s) to deploy
        :rtype: :class:`DSSAPIDeployerDeployment`
        """
        settings = {
            "deploymentId": deployment_id,
            "publishedServiceId": service_id,
            "infraId": infra_id,
            "version": version,
            "endpointId": endpoint_id
        }
        self.client._perform_json("POST", "/api-deployer/deployments", params={"ignoreWarnings": ignore_warnings}, body=settings)
        return self.get_deployment(deployment_id)

    def list_stages(self):
        """
        Lists infrastructure stages of the API Deployer

        :rtype: list of dict. Each dict contains a field "id" for the stage identifier and "desc" for its description.
        :rtype: list
        """
        return self.client._perform_json("GET", "/api-deployer/stages")

    def list_infras(self, as_objects=True):
        """
        Lists deployment infrastructures on the API Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSAPIDeployerInfra`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this infra

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/api-deployer/infras")
        if as_objects:
            return [DSSAPIDeployerInfra(self.client, x["infraBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_infra(self, infra_id, stage, type, govern_check_policy="NO_CHECK"):
        """
        Creates a new infrastructure on the API Deployer and returns the handle to interact with it.

        :param str infra_id: Unique Identifier of the infra to create
        :param str stage: Infrastructure stage. Stages are configurable on each API Deployer
        :param str type: STATIC, K8S, AZURE_ML, SAGEMAKER, SNOWPARK or VERTEX_AI
        :param str govern_check_policy: PREVENT, WARN, or NO_CHECK depending if the deployer will check whether the saved model versions deployed on this infrastructure has to be managed and approved in Dataiku Govern
        :rtype: :class:`DSSAPIDeployerInfra`
        """
        settings = {
            "id": infra_id,
            "stage": stage,
            "type": type,
            "governCheckPolicy": govern_check_policy,
        }
        self.client._perform_json("POST", "/api-deployer/infras", body=settings)
        return self.get_infra(infra_id)

    def get_infra(self, infra_id):
        """
        Returns a handle to interact with a single deployment infra, as a :class:`DSSAPIDeployerInfra` 

        :param str infra_id: Identifier of the infra to get
        :rtype: :class:`DSSAPIDeployerInfra`
        """
        return DSSAPIDeployerInfra(self.client, infra_id)

    def list_services(self, as_objects=True):
        """
        Lists API services on the API Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSAPIDeployerService`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this Service

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/api-deployer/services")
        if as_objects:
            return [DSSAPIDeployerService(self.client, x["serviceBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_service(self, service_id):
        """
        Creates a new API Service on the API Deployer and returns the handle to interact with it.

        :param str service_id: Identifier of the API Service to create
        :rtype: :class:`DSSAPIDeployerService`
        """
        settings = {
            "publishedServiceId" : service_id
        }
        self.client._perform_json("POST", "/api-deployer/services", body=settings)
        return self.get_service(service_id)

    def get_service(self, service_id):
        """
        Returns a handle to interact with a single service, as a :class:`DSSAPIDeployerService` 

        :param str service_id: Identifier of the API service to get
        :rtype: :class:`DSSAPIDeployerService`
        """
        return DSSAPIDeployerService(self.client, service_id)




###############################################
# Infrastructures
###############################################


class DSSAPIDeployerInfra(object):
    """
    An API Deployer infrastructure.

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployer.get_infra`
    """
    def __init__(self, client, infra_id):
        self.client = client
        self.infra_id = infra_id

    @property
    def id(self):
        return CallableStr(self.infra_id)

    def get_status(self):
        """
        Returns status information about this infrastructure

        :rtype: :class:`dataikuapi.dss.apideployer.DSSAPIDeployerInfraStatus`
        """
        light = self.client._perform_json("GET", "/api-deployer/infras/%s" % (self.infra_id))

        return DSSAPIDeployerInfraStatus(self.client, self.infra_id, light)

    def get_settings(self):
        """
        Gets the settings of this infra. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerInfraSettings.save` on the returned 
        object

        :returns: a :class:`dataikuapi.dss.apideployer.DSSAPIDeployerInfraSettings`
        """
        settings = self.client._perform_json(
            "GET", "/api-deployer/infras/%s/settings" % (self.infra_id))

        return DSSAPIDeployerInfraSettings(self.client, self.infra_id, settings)

    def delete(self):
        """
        Deletes this infra
        You may only delete an infra if it has no deployments on it anymore.
        """
        self.client._perform_empty(
            "DELETE", "/api-deployer/infras/%s" % (self.infra_id))


class DSSAPIDeployerInfraSettings(object):
    """
    The settings of an API Deployer infrastructure

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerInfra.get_settings`
    """
    def __init__(self, client, infra_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.settings = settings

    def get_type(self):
        """
        Gets the type of this infra

        :returns: the type of this infra
        :rtype: string
        """
        return self.settings["type"]

    def add_apinode(self, url, api_key, graphite_prefix=None):
        """
        Adds an API node to the list of nodes of this infra.

        Only applicable to STATIC infrastructures

        :param str url: url of the API node that will be added to this infra
        :param str api_key: api key secret to connect to the API node
        :param str graphite_prefix: graphite prefix for metric reports if graphite is configured
        """
        new_node = {
            "url": url,
            "adminAPIKey" : api_key,
            "graphitePrefix" : graphite_prefix
        }
        self.settings["apiNodes"].append(new_node)

    def remove_apinode(self, node_url):
        """
        Removes a node from the list of nodes of this infra.
        Only applicable to STATIC infrastructures

        :param str node_url: URL of the node to remove
        """
        api_nodes = list(self.settings["apiNodes"])
        for node in api_nodes:
            if node.get("url") == node_url:
                self.settings["apiNodes"].remove(node)

    def get_raw(self):
        """
        Gets the raw settings of this infra. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """Saves back these settings to the infra"""
        self.client._perform_empty(
                "PUT", "/api-deployer/infras/%s/settings" % (self.infra_id),
                body = self.settings)


class DSSAPIDeployerInfraStatus(object):
    """
    The status of an API Deployer infrastructure.

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerInfra.get_status`
    """
    def __init__(self, client, infra_id, light_status):
        self.client = client
        self.infra_id = infra_id
        self.light_status = light_status

    def get_deployments(self):
        """
        Returns the deployments that are deployed on this infrastructure

        :returns: a list of deployments
        :rtype: list of :class:`dataikuapi.dss.apideployer.DSSAPIDeployerDeployment`
        """
        return [DSSAPIDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]

    def get_raw(self):
        """
        Gets the raw status information. This returns a dictionary with various information about the infrastructure

        :rtype: dict
        """
        return self.light_status


###############################################
# Deployments
###############################################

class DSSAPIDeployerDeployment(object):
    """
    A Deployment on the API Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployer.get_deployment`
    """
    def __init__(self, client, deployment_id):
        self.client = client
        self.deployment_id = deployment_id

    @property
    def id(self):
        return CallableStr(self.deployment_id)

    def get_status(self):
        """
        Returns status information about this deployment

        :rtype: dataikuapi.dss.apideployer.DSSAPIDeployerDeploymentStatus
        """
        light = self.client._perform_json("GET", "/api-deployer/deployments/%s" % (self.deployment_id))
        heavy = self.client._perform_json("GET", "/api-deployer/deployments/%s/status" % (self.deployment_id))

        return DSSAPIDeployerDeploymentStatus(self.client, self.deployment_id, light, heavy)

    def get_governance_status(self, version=""):
        """
        Returns the governance status about this deployment if applicable
        It covers all the embedded model versions

        :param str version: (Optional) The specific package version of the published service to get status from. If empty, consider all the versions used in the deployment generation mapping.
        :rtype: dict InforMessages containing the governance status
        """
        return self.client._perform_json("GET", "/api-deployer/deployments/%s/governance-status" % (self.deployment_id), params={ "version": version })

    def get_settings(self):
        """
        Gets the settings of this deployment. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerDeploymentSettings.save` on the returned 
        object

        :returns: a :class:`dataikuapi.dss.apideployer.DSSAPIDeployerDeploymentSettings`
        """
        settings = self.client._perform_json(
            "GET", "/api-deployer/deployments/%s/settings" % (self.deployment_id))

        return DSSAPIDeployerDeploymentSettings(self.client, self.deployment_id, settings)

    def start_update(self):
        """
        Starts an asynchronous update of this deployment to try to match the actual state to the current settings

        :returns: a :class:`dataikuapi.dss.future.DSSFuture` tracking the progress of the update. Call 
                   :meth:`~dataikuapi.dss.future.DSSFuture.wait_for_result` on the returned object
                   to wait for completion (or failure)
        """
        future_response = self.client._perform_json(
            "POST", "/api-deployer/deployments/%s/actions/update" % (self.deployment_id))

        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

    def delete(self, disable_first=False, ignore_pre_delete_errors=False):
        """
        Deletes this deployment. The disable_first flag automatically disables the deployment
        before its deletion.

        :param boolean disable_first: If True, automatically disables this deployment before deleting it.
            If False, will raise an Exception if this deployment is enabled.

        :param boolean ignore_pre_delete_errors: If True, any error occurred during the actions performed previously to
            delete the deployment will be ignored and the delete action will be performed anyway.

        """

        # Check if the deployment is disabled
        is_enabled = self.get_status().light_status["deploymentBasicInfo"].get("enabled")
        if is_enabled and not disable_first:
            raise Exception("Deployment {} deletion failed: deployment must be disabled first.".format(self.deployment_id))
        if is_enabled:
            settings = self.get_settings()
            settings.set_enabled(enabled=False)
            settings.save()
        self.client._perform_empty(
                "DELETE", "/api-deployer/deployments/%s" % (self.deployment_id),
            params = { "ignorePreDeleteErrors" : ignore_pre_delete_errors }
        )

    def get_open_api(self):
        """
        Gets the OpenAPI document of this deployment if it's available or raise a 404 error.

        :returns: a :class:`dataikuapi.dss.apideployer.DSSAPIDeployerDeploymentOpenApi`
        """
        open_api = self.client._perform_text("GET", "/api-deployer/deployments/%s/get-open-api" % (self.deployment_id))

        return DSSAPIDeployerDeploymentOpenApi(open_api)


    def run_test_queries(self, endpoint_id=None, test_queries=None):
        """
        Runs test queries on a deployment and returns results as a dict

        :param str endpoint_id: Mandatory if the deployment has multiple endpoints
        :param list test_queries: Queries as str, formatted as [{"q": {"features": {"feat_1": "value", ...}}, {...}, ... ].
            If left to None, the test queries of the current version of the service will be used.
        :rtype: dict

        Usage example

        .. code-block:: python

            import dataiku

            client = dataiku.api_client()
            deployer = client.get_apideployer()
            deployment = deployer.get_deployment('service14');

            test_queries = [{'q': {'features': {
                'Pclass': '200',
                'Sex': 'male',
                'Age': '22',
                'Embarked': 'S'
            }}}]

            # run existing test queries on deployement endpoint (if unique, else error)
            test_queries_result = deployment.run_test_queries()

            # run specified test queries on deployement "survived" endpoint
            test_queries_result = deployment.run_test_queries(endpoint_id="survived", test_queries=test_queries)

            # run existing test queries on deployement  "survived" endpoint
            test_queries_result = deployment.run_test_queries(endpoint_id="survived")

            # run specified test queries on deployement endpoint (if unique, else error)
            test_queries_result = deployment.run_test_queries(test_queries=test_queries)

        """
        settings = {}
        if endpoint_id is not None:
            settings["endpointIdParam"] = endpoint_id
        if test_queries is not None:
            settings["testQueriesParam"] = json.dumps(test_queries)

        return self.client._perform_json("POST", "/api-deployer/deployments/%s/actions/run-test-queries" % self.deployment_id, params=settings)


class DSSAPIDeployerDeploymentSettings(object):
    """
    The settings of an API Deployer deployment. 

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerDeployment.get_settings`
    """
    def __init__(self, client, deployment_id, settings):
        self.client = client
        self.deployment_id = deployment_id
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this deployment. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def set_enabled(self, enabled):
        """
        Enables or disables this deployment

        :param bool enabled: True/False to Enable/Disable this deployment
        """
        self.settings["enabled"] = enabled

    def set_single_version(self, version):
        """
        Sets this deployment to target a single version of the API service

        :param str version: Identifier of the version to set
        """
        self.settings["generationsMapping"] = {
            "mode": "SINGLE_GENERATION",
            "generation": version
        }

    def save(self, ignore_warnings=False):
        """
        Saves back these settings to the deployment

        :param boolean ignore_warnings: ignore warnings concerning the governance status of the model version(s) to deploy
        """
        self.client._perform_empty(
                "PUT", "/api-deployer/deployments/%s/settings" % (self.deployment_id),
                params = { "ignoreWarnings" : ignore_warnings },
                body = self.settings)


class DSSAPIDeployerDeploymentStatus(object):
    """
    The status of an API Deployer deployment. 

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerDeployment.get_status`
    """
    def __init__(self, client, deployment_id, light_status, heavy_status):
        self.client = client
        self.deployment_id = deployment_id
        self.light_status = light_status
        self.heavy_status = heavy_status

    def get_light(self):
        """
        Gets the 'light' (summary) status. This returns a dictionary with various information about the deployment,
        but not the actual health of the deployment

        :rtype: dict
        """
        return self.light_status

    def get_heavy(self):
        """
        Gets the 'heavy' (full) status. This returns a dictionary with various information about the deployment

        :rtype: dict
        """
        return self.heavy_status

    def get_service_urls(self):
        """
        Returns service-level URLs for this deployment (ie without the enpdoint-specific suffix)

        :returns: a list of service-level URLs for this deployment
        :rtype: list
        """

        if "deployedServiceId" in self.light_status["deploymentBasicInfo"]:
            service_id = self.light_status["deploymentBasicInfo"]["deployedServiceId"]
        else:
            service_id =  self.light_status["deploymentBasicInfo"]["publishedServiceId"]

        if "apiNodes" in self.heavy_status:
            return ["%s/public/api/v1/%s" % (x["url"], service_id) for x in self.heavy_status["apiNodes"]]
        elif "publicURL" in self.heavy_status:
            return ["%s/public/api/v1/%s" % (self.heavy_status["publicURL"], service_id)]
        else:
            raise ValueError("PublicURL not available for this deployment. It might still be initializing")

    def get_health(self):
        """
        Returns the health of this deployment as a string

        :returns: HEALTHY if the deployment is working properly, various other status otherwise
        :rtype: string
        """
        return self.heavy_status["health"]

    def get_health_messages(self):
        """Returns messages about the health of this deployment"""
        return self.heavy_status["healthMessages"]


class DSSAPIDeployerDeploymentOpenApi(object):
    """
    The OpenAPI document of an API Deployer deployment.

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerDeployment.get_open_api`
    """
    def __init__(self, open_api_doc_json):
        self.open_api_doc_json = open_api_doc_json

    def get(self):
        """
        Gets the OpenAPI document as dict.

        :rtype: dict
        """
        return json.loads(self.open_api_doc_json)

    def get_raw(self):
        """
        Gets the OpenAPI document raw.

        :rtype: string
        """
        return self.open_api_doc_json


###############################################
# Published Service
###############################################

class DSSAPIDeployerService(object):
    """
    An API service on the API Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployer.get_service`
    """
    def __init__(self, client, service_id):
        self.client = client
        self.service_id = service_id

    @property
    def id(self):
        return CallableStr(self.service_id)

    def get_status(self):
        """
        Returns status information about this service. This is used mostly to get information about
        which versions are available and which deployments are exposing this service

        :rtype: dataikuapi.dss.apideployer.DSSAPIDeployerServiceStatus
        """
        light = self.client._perform_json("GET", "/api-deployer/services/%s" % (self.service_id))
        return DSSAPIDeployerServiceStatus(self.client, self.service_id, light)

    def import_version(self, fp):
        """
        Imports a new version for an API service from a file-like object pointing 
        to a version package Zip file

        :param string fp: A file-like object pointing to a version package Zip file
        """
        return self.client._perform_empty("POST",
                "/api-deployer/services/%s/versions" % (self.service_id), files={"file":fp})

    def get_settings(self):
        """
        Gets the settings of this service. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerServiceSettings.save` on the returned 
        object.

        The main things that can be modified in a service settings are permissions

        :returns: a :class:`dataikuapi.dss.apideployer.DSSAPIDeployerServiceSettings`
        """
        settings = self.client._perform_json(
            "GET", "/api-deployer/services/%s/settings" % (self.service_id))

        return DSSAPIDeployerServiceSettings(self.client, self.service_id, settings)

    def delete_version(self, version):
        """
        Deletes a version from this service

        :param string version: The version to delete
        """
        self.client._perform_empty(
            "DELETE", "/api-deployer/services/%s/versions/%s" % (self.service_id, version))

    def get_version_stream(self, version_id):
        """
        Download a version of a service as a stream.

        The archive of this version can then be deployed in a DSS API Node.

        .. warning::

            This call will monopolize the DSSClient until the stream it returns is closed.

        .. code-block:: python

                with api_deployer_service.get_version_stream('v1') as fp:
                    # use fp

                # or explicitly close the stream after use
                fp = api_deployer_service.get_version_stream('v1')
                # use fp, then close
                fp.close()

        :param string version_id: version (identifier) of the package to download

        :return: the package archive, as an HTTP stream
        :rtype: file-like
        """
        return self.client._perform_raw(
            "GET", "/api-deployer/services/%s/versions/%s" % (self.service_id, version_id))

    def download_version_to_file(self, version_id, path):
        """
        Download an archive of a version to a local file.

        The archive can then be deployed in a DSS API Node.

        :param string version_id: version (identifier) of the package to download
        :param string path: absolute or relative path to a file in which the package is downloaded
        """
        with self.get_version_stream(version_id) as version_stream:
            with open(path, 'wb') as f:
                for chunk in version_stream.iter_content(chunk_size=10000):
                    if chunk:
                        f.write(chunk)
                        f.flush()

    def delete(self):
        """
        Deletes this service

        You may only delete a service if it has no deployments on it anymore.
        """
        self.client._perform_empty(
            "DELETE", "/api-deployer/services/%s" % (self.service_id))


class DSSAPIDeployerServiceSettings(object):
    """
    The settings of an API Deployer Service. 

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerService.get_settings`
    """
    def __init__(self, client, service_id, settings):
        self.client = client
        self.service_id = service_id
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this deployment. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Saves back these settings to the API service
        """
        self.client._perform_empty(
                "PUT", "/api-deployer/services/%s/settings" % (self.service_id),
                body = self.settings)


class DSSAPIDeployerServiceStatus(object):
    """
    The status of an API Deployer Service. 

    Do not create this directly, use :meth:`~dataikuapi.dss.apideployer.DSSAPIDeployerService.get_status`
    """
    def __init__(self, client, service_id, light_status):
        self.client = client
        self.service_id = service_id
        self.light_status = light_status

    def get_deployments(self, infra_id=None):
        """
        Returns the deployments that have been created from this published project

        :param str infra_id: Identifier of an infra, allows to only keep in the returned list the deployments on this infra.
            If not set, the list contains all the deployments using this published project, across every infra of the Project Deployer.

        :returns: a list of deployments
        :rtype: list of :class:`dataikuapi.dss.apideployer.DSSAPIDeployerDeployment`
        """
        if infra_id is None:
            return [DSSAPIDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]
        return [DSSAPIDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"] if infra_id == deployment["infraId"]]

    def get_versions(self):
        """
        Returns the versions of this service that have been published on the API Service

        Each version is a dict that contains at least a "id" field, which is the version identifier

        :returns: a list of versions, each as a dict containing a "id" field
        :rtype: list of dicts
        """
        return self.light_status["packages"]

    def get_raw(self):
        """
        Gets the raw status information. This returns a dictionary with various information about the service,

        :rtype: dict
        """
        return self.light_status
