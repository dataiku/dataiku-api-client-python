DSS_API_ENDPOINT_MONITORING_TYPE = "DSS_API_ENDPOINT"
EXTERNAL_API_ENDPOINT_MONITORING_TYPE = "EXTERNAL_API_ENDPOINT"

class DSSUnifiedMonitoring(object):
    """
    Handle to interact with Unified Monitoring

    .. warning::
        Do not create this class directly, use :meth:`dataikuapi.dssclient.DSSClient.get_unified_monitoring`
    """

    def __init__(self, client):
        self.client = client

    def list_project_monitorings(self):
        """
        Lists the deployed projects monitorings

        :return: The list of project monitorings
        :rtype: list of :class:`dataikuapi.dss.unifiedmonitoring.DSSProjectMonitoring`
        """
        items = self.client._perform_json("GET", "/unified-monitoring/deployer/projects")
        return [DSSProjectMonitoring(monitoring) for monitoring in items]

    def list_api_endpoint_monitorings(self, remove_duplicated_external_endpoints=True):
        """
        Lists the API endpoints monitorings

        :param boolean remove_duplicated_external_endpoints: if True, an endpoint that is both in a Deploy Anywhere Infrastructure and in an External Endpoints Scope will be listed only once, under the Deploy Anywhere Infrastructure. Optional
        :return: The list of API endpoint monitorings
        :rtype: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.DSSApiEndpointMonitoring`, :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointMonitoring`]
        """
        params = {
            'removeDuplicatedExternalEndpoints': remove_duplicated_external_endpoints
        }

        items = self.client._perform_json("GET", "/unified-monitoring/deployer/api-endpoints", params=params)

        monitorings = []

        for monitoring in items:
            if DSS_API_ENDPOINT_MONITORING_TYPE == monitoring.get("type"):
                monitorings.append(DSSApiEndpointMonitoring(monitoring))
            elif EXTERNAL_API_ENDPOINT_MONITORING_TYPE == monitoring.get("type"):
                monitorings.append(ExternalApiEndpointMonitoring(monitoring))
        return monitorings

    def list_api_endpoint_monitorings_with_activity_metrics(self, endpoints_to_filter_on=None, remove_duplicated_external_endpoints=True):
        """
        Lists the API endpoints monitorings with their activity metrics

        :param endpoints_to_filter_on: endpoints for which monitoring and activity metrics should be retrieved. If None or empty, all endpoints are considered
        :type endpoints_to_filter_on: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.DSSApiEndpointMonitoring`, :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointMonitoring`]. Optional
        :param boolean remove_duplicated_external_endpoints: if True, an endpoint that is both in a Deploy Anywhere Infrastructure and in an External Endpoint Scope will be listed only once, under the Deploy Anywhere Infrastructure. Optional
        :return: The list of API endpoint monitorings with their activity metrics
        :rtype: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.DSSApiEndpointMonitoringWithActivityMetrics`, :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointMonitoringWithActivityMetrics`]
        """

        formatted_endpoint_params = []
        if endpoints_to_filter_on:
            for endpoint_monitoring in endpoints_to_filter_on:
                if isinstance(endpoint_monitoring, DSSApiEndpointMonitoring):
                    formatted_endpoint_params.append({'endpointId': endpoint_monitoring.endpoint_id, 'deploymentId': endpoint_monitoring.deployment_id})
                elif isinstance(endpoint_monitoring, ExternalApiEndpointMonitoring):
                    formatted_endpoint_params.append({'endpointName': endpoint_monitoring.endpoint_name,
                                                      'externalEndpointsScopeName': endpoint_monitoring.external_endpoints_scope.get("name")})
                else:
                    raise TypeError("Unsupported type: " + endpoint_monitoring.__class__.__name__)
        params = {
            'removeDuplicatedExternalEndpoints': remove_duplicated_external_endpoints,
        }

        items = self.client._perform_json("POST", "/unified-monitoring/deployer/api-endpoints-with-activity-metrics", params=params,
                                          body=formatted_endpoint_params)

        monitorings = []
        for monitoring_with_activity_metrics in items:
            if monitoring_with_activity_metrics.get("type") == DSS_API_ENDPOINT_MONITORING_TYPE:
                monitorings.append(DSSApiEndpointMonitoringWithActivityMetrics(monitoring_with_activity_metrics))
            elif monitoring_with_activity_metrics.get("type") == EXTERNAL_API_ENDPOINT_MONITORING_TYPE:
                monitorings.append(ExternalApiEndpointMonitoringWithActivityMetrics(monitoring_with_activity_metrics))
        return monitorings


class AbstractDeploymentMonitoring(object):
    def __init__(self, data):
        self.deployment_id = data.get("deploymentId")
        self.infrastructure_id = data.get("infrastructureId")
        self.stage = data.get("stage")
        self.snapshot_timestamp = data.get("snapshotTimestamp")
        self.data = data


class DSSProjectMonitoring(AbstractDeploymentMonitoring):
    """
    A handle on a project monitoring

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_project_monitorings`
    """

    def __init__(self, data):
        super(DSSProjectMonitoring, self).__init__(data)
        self.deployment_id = data.get("deploymentId")
        """The deployment id"""
        self.infrastructure_id = data.get("infrastructureId")
        """The infrastructure id"""
        self.stage = data.get("stage")
        """The stage of the deployment"""
        self.snapshot_timestamp = data.get("snapshotTimestamp")
        """The timestamp of the snapshot"""
        self.bundle_name = data.get("bundleName")
        """The bundle name"""
        self.deployed_project_key = data.get("deployedProjectKey")
        """The deployed project key"""
        self.published_project_key = data.get("publishedProjectKey")
        """The published project key"""
        self.data = data

    def get_raw(self):
        """
        Get the raw project monitoring

        :rtype: dict
        """
        return self.data

class DSSApiEndpointMonitoring(AbstractDeploymentMonitoring):
    """
    A handle on a DSS API endpoint monitoring

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings`
    """

    def __init__(self, data):
        super(DSSApiEndpointMonitoring, self).__init__(data)
        self.deployment_id = data.get("deploymentId")
        """The deployment id"""
        self.infrastructure_id = data.get("infrastructureId")
        """The infrastructure id"""
        self.stage = data.get("stage")
        """The stage of the deployment"""
        self.snapshot_timestamp = data.get("snapshotTimestamp")
        """The timestamp of the snapshot"""
        self.endpoint_id = data.get("endpointId")
        """The endpoint id"""
        self.type = data.get("type")
        """'DSS_API_ENDPOINT'"""

    def get_raw(self):
        """
        Get the raw DSS API endpoint monitoring

        :rtype: dict
        """
        return self.data

class ExternalApiEndpointMonitoring(AbstractDeploymentMonitoring):
    """
    A handle on an external endpoint monitoring

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings`
    """

    def __init__(self, data):
        super(ExternalApiEndpointMonitoring, self).__init__(data)
        self.external_endpoints_scope = data.get("externalEndpointsScope")
        """The external endpoint scope configuration"""
        self.stage = data.get("stage")
        """The stage of the deployment"""
        self.snapshot_timestamp = data.get("snapshotTimestamp")
        """The timestamp of the snapshot"""
        self.endpoint_name = data.get("endpointName")
        """The endpoint name"""
        self.type = data.get("type")
        """'EXTERNAL_API_ENDPOINT'"""

    def get_raw(self):
        """
        Get the raw external endpoint monitoring

        :rtype: dict
        """
        return self.data

class DSSApiEndpointActivityMetrics(object):
    """
    A handle on the activity metrics of a DSS API endpoint

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings_with_activity_metrics`
    """

    def __init__(self, data):
        self.deployment_id = data.get("deploymentId")
        """The deployment id"""
        self.endpoint_id = data.get("endpointId")
        """The endpoint id"""
        self.period = data.get("period")
        """The time period spanned by this :class:`DSSApiEndpointActivityMetrics`"""
        self.period_all_requests_count = data.get("periodAllRequestsCount")
        """The count of all requests in the period"""
        self.period_error_rate = data.get("periodErrorRate")
        """The request error rate in the period"""
        self.period_response_time_ms = data.get("periodResponseTimeMs")
        """The average response time in the period"""
        self.counts = data.get("counts")
        """Detailed number of requests per timestamp"""
        self.data = data

    def get_raw(self):
        """
        Get the raw activity metrics of a DSS API endpoint

        :rtype: dict
        """
        return self.data

class ExternalApiEndpointActivityMetrics(object):
    """
    A handle on the activity metrics of an external API endpoint

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings_with_activity_metrics`
    """

    def __init__(self, data):
        self.external_endpoint_scope_name = data.get("externalEndpointScopeName")
        """The name of the external endpoint scope"""
        self.endpoint_name = data.get("endpointName")
        """The endpoint name"""
        self.period = data.get("period")
        """The time period spanned by this :class:`ExternalApiEndpointActivityMetrics`"""
        self.period_all_requests_count = data.get("periodAllRequestsCount")
        """The count of all requests in the period"""
        self.period_error_rate = data.get("periodErrorRate")
        """The request error rate in the period"""
        self.period_response_time_ms = data.get("periodResponseTimeMs")
        """The average response time in the period"""
        self.counts = data.get("counts")
        """Detailed number of requests per timestamp"""
        self.data = data

    def get_raw(self):
        """
        Get the raw activity metrics of an external API endpoint

        :rtype: dict
        """
        return self.data

class DSSApiEndpointMonitoringWithActivityMetrics(object):
    """
    A handle on a DSS API endpoint monitoring and its activity metrics

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings_with_activity_metrics`
    """

    def __init__(self, data):
        self.endpoint_monitoring = DSSApiEndpointMonitoring(data.get("endpointMonitoring"))
        """The DSS API endpoint monitoring"""
        raw_activity_metrics = data.get("activityMetrics")
        self.activity_metrics = DSSApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None
        """The DSS API endpoint activity metrics"""
        self.type = data.get("type")
        """'DSS_API_ENDPOINT'"""
        self.data = data

    def get_raw(self):
        """
        Get the raw DSS API endpoint monitoring with its activity metrics

        :rtype: dict
        """
        return self.data

class ExternalApiEndpointMonitoringWithActivityMetrics(object):
    """
    A handle on an external API endpoint monitoring and its activity metrics

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_api_endpoint_monitorings_with_activity_metrics`
    """

    def __init__(self, data):
        self.endpoint_monitoring = ExternalApiEndpointMonitoring(data.get("endpointMonitoring"))
        """The external API endpoint monitoring"""
        raw_activity_metrics = data.get("activityMetrics")
        self.activity_metrics = ExternalApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None
        """The external API endpoint activity metrics"""
        self.type = data.get("type")
        """'EXTERNAL_API_ENDPOINT'"""
        self.data = data

    def get_raw(self):
        """
        Get the raw external API endpoint monitoring with its activity metrics

        :rtype: dict
        """
        return self.data
