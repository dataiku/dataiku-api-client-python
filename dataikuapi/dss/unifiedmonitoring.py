MANAGED_API_ENDPOINT_MONITORING_TYPE = "MANAGED_API_ENDPOINT"
EXTERNAL_API_ENDPOINT_MONITORING_TYPE = "EXTERNAL_API_ENDPOINT"


class DSSUnifiedMonitoring(object):
    """
    Handle to interact with Unified Monitoring

    .. warning::
        Do not create this class directly, use :meth:`dataikuapi.dssclient.DSSClient.get_unified_monitoring`
    """

    def __init__(self, client):
        self.client = client

    def list_monitored_project_deployments(self):
        """
        Lists the monitored project deployments

        :return: The list of monitored projects
        :rtype: list of :class:`dataikuapi.dss.unifiedmonitoring.MonitoredProjectDeployment`
        """
        items = self.client._perform_json("GET", "/unified-monitoring/deployer/projects")
        return [MonitoredProjectDeployment(monitoring) for monitoring in items]

    def list_monitored_api_endpoints(self, remove_duplicated_external_endpoints=True):
        """
        Lists the monitored API endpoints

        :param boolean remove_duplicated_external_endpoints: if True, an endpoint that is both in a Deploy Anywhere Infrastructure and in an External endpoint scope will be listed only once, under the Deploy Anywhere Infrastructure. Optional
        :return: The list of monitored API endpoints
        :rtype: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.MonitoredManagedApiEndpoint`, :class:`dataikuapi.dss.unifiedmonitoring.MonitoredExternalApiEndpoint`]
        """
        params = {
            'removeDuplicatedExternalEndpoints': remove_duplicated_external_endpoints
        }

        items = self.client._perform_json("GET", "/unified-monitoring/deployer/api-endpoints", params=params)

        monitorings = []

        for monitoring in items:
            if MANAGED_API_ENDPOINT_MONITORING_TYPE == monitoring.get("type"):
                monitorings.append(MonitoredManagedApiEndpoint(self.client, monitoring))
            elif EXTERNAL_API_ENDPOINT_MONITORING_TYPE == monitoring.get("type"):
                monitorings.append(MonitoredExternalApiEndpoint(self.client, monitoring))
        return monitorings

    def list_monitored_api_endpoint_with_activity_metrics(self, endpoints_to_filter_on=None, remove_duplicated_external_endpoints=True):
        """
        Lists the monitored API endpoints with their activity metrics

        :param endpoints_to_filter_on: endpoints for which monitoring and activity metrics should be retrieved. If None or empty, all endpoints are considered
        :type endpoints_to_filter_on: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.DSSApiEndpointMonitoring`, :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointMonitoring`]. Optional
        :param boolean remove_duplicated_external_endpoints: if True, an endpoint that is both in a Deploy Anywhere Infrastructure and in an External Endpoint Scope will be listed only once, under the Deploy Anywhere Infrastructure. Optional
        :return: The list of API endpoint monitorings with their activity metrics
        :rtype: list of Union[:class:`dataikuapi.dss.unifiedmonitoring.DSSApiEndpointMonitoringWithActivityMetrics`, :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointMonitoringWithActivityMetrics`]
        """

        formatted_endpoint_params = []
        if endpoints_to_filter_on:
            for endpoint_monitoring in endpoints_to_filter_on:
                if isinstance(endpoint_monitoring, MonitoredManagedApiEndpoint):
                    formatted_endpoint_params.append({'endpointId': endpoint_monitoring.endpoint_id, 'deploymentId': endpoint_monitoring.deployment_id})
                elif isinstance(endpoint_monitoring, MonitoredExternalApiEndpoint):
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
            if monitoring_with_activity_metrics.get("type") == MANAGED_API_ENDPOINT_MONITORING_TYPE:
                monitorings.append(MonitoredManagedApiEndpointWithActivityMetrics(self.client, monitoring_with_activity_metrics))
            elif monitoring_with_activity_metrics.get("type") == EXTERNAL_API_ENDPOINT_MONITORING_TYPE:
                monitorings.append(MonitoredExternalApiEndpointWithActivityMetrics(self.client, monitoring_with_activity_metrics))
        return monitorings


class AbstractMonitoredThing(object):
    def __init__(self, data):
        self.deployment_id = data.get("deploymentId")
        self.infrastructure_id = data.get("infrastructureId")
        self.stage = data.get("stage")
        self.snapshot_timestamp = data.get("snapshotTimestamp")
        self.data = data


class MonitoredProjectDeployment(AbstractMonitoredThing):
    """
    A handle on a monitored project deployment

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_project_deployments`
    """

    def __init__(self, data):
        super(MonitoredProjectDeployment, self).__init__(data)
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
        Get the raw monitored project

        :rtype: dict
        """
        return self.data


class MonitoredManagedApiEndpoint(AbstractMonitoredThing):
    """
    A handle on a monitored managed API endpoint

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoints`
    """

    def __init__(self, client, data):
        super(MonitoredManagedApiEndpoint, self).__init__(data)
        self.client = client
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
        """'MANAGED_API_ENDPOINT'"""

    def get_activity_metrics(self):
        """
        Get the activity metrics of the monitored managed API endpoint

        :return: The activity metrics
        :rtype: :class:`dataikuapi.dss.unifiedmonitoring.ManagedApiEndpointActivityMetrics`
        """
        endpoint_identifier = {
            'deploymentId': self.deployment_id,
            'endpointId': self.endpoint_id
        }

        raw_activity_metrics = self.client._perform_json("POST", "/unified-monitoring/deployer/activity-metrics", body=endpoint_identifier)
        return ManagedApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None

    def get_raw(self):
        """
        Get the raw monitored managed API endpoint

        :rtype: dict
        """
        return self.data


class MonitoredExternalApiEndpoint(AbstractMonitoredThing):
    """
    A handle on a monitored external API endpoint

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoints`
    """

    def __init__(self, client, data):
        super(MonitoredExternalApiEndpoint, self).__init__(data)
        self.client = client
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

    def get_activity_metrics(self):
        """
        Get the activity metrics of the monitored external API endpoint

        :return: The activity metrics
        :rtype: :class:`dataikuapi.dss.unifiedmonitoring.ExternalApiEndpointActivityMetrics`
        """
        endpoint_identifier = {
            'externalEndpointsScopeName': self.external_endpoints_scope.get("name"),
            'endpointName': self.endpoint_name
        }

        raw_activity_metrics = self.client._perform_json("POST", "/unified-monitoring/deployer/activity-metrics", body=endpoint_identifier)
        return ExternalApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None

    def get_raw(self):
        """
        Get the raw monitored external API endpoint

        :rtype: dict
        """
        return self.data


class ManagedApiEndpointActivityMetrics(object):
    """
    A handle on the activity metrics of a managed API endpoint

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoint_with_activity_metrics`
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
        Get the raw activity metrics of a managed API endpoint

        :rtype: dict
        """
        return self.data


class ExternalApiEndpointActivityMetrics(object):
    """
    A handle on the activity metrics of an external API endpoint

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoint_with_activity_metrics`
    """

    def __init__(self, data):
        self.external_endpoints_scope_name = data.get("externalEndpointsScopeName")
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


class MonitoredManagedApiEndpointWithActivityMetrics(object):
    """
    A handle on a monitored managed API endpoint and its activity metrics

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoint_with_activity_metrics`
    """

    def __init__(self, client, data):
        self.endpoint_monitoring = MonitoredManagedApiEndpoint(client, data.get("endpointMonitoring"))
        """The DSS API endpoint monitoring"""
        raw_activity_metrics = data.get("activityMetrics")
        self.activity_metrics = ManagedApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None
        """The DSS API endpoint activity metrics"""
        self.type = data.get("type")
        """'MANAGED_API_ENDPOINT'"""
        self.data = data

    def get_raw(self):
        """
        Get the raw monitored managed API endpoint with its activity metrics

        :rtype: dict
        """
        return self.data


class MonitoredExternalApiEndpointWithActivityMetrics(object):
    """
    A handle on a monitored external API endpoint and its activity metrics

    .. warning::
        Do not create this class directly, instead use
        :meth:`dataikuapi.dss.unifiedmonitoring.DSSUnifiedMonitoring.list_monitored_api_endpoint_with_activity_metrics`
    """

    def __init__(self, client, data):
        self.endpoint_monitoring = MonitoredExternalApiEndpoint(client, data.get("endpointMonitoring"))
        """The external API endpoint monitoring"""
        raw_activity_metrics = data.get("activityMetrics")
        self.activity_metrics = ExternalApiEndpointActivityMetrics(raw_activity_metrics) if raw_activity_metrics else None
        """The external API endpoint activity metrics"""
        self.type = data.get("type")
        """'EXTERNAL_API_ENDPOINT'"""
        self.data = data

    def get_raw(self):
        """
        Get the raw monitored external API endpoint with its activity metrics

        :rtype: dict
        """
        return self.data
