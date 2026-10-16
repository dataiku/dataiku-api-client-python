import copy

from ._utils import dku_quote_fn, _format_list
from .agent import AgentFilter, Agent, AgentListItem
from .operations import Operation
from .alerting import AlertConfiguration, AlertConfigurationListItem, MetricAlertConfigurationBuilder

class Platform(object):
    """
    An Agent Management platform.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_platform`.
    """

    def __init__(self, client, platform_id):
        self.client = client
        self.platform_id = platform_id

    @property
    def id(self):
        return self.platform_id

    def __repr__(self):
        return "<Platform id=%r>" % self.platform_id

    def get_status(self):
        """
        Returns status information about this platform.

        :rtype: :class:`dataikuapi.agentmanagement.platform.PlatformStatus`
        """
        status = self.client._perform_json("GET", self._path())
        return PlatformStatus(self.client, self.platform_id, status)

    def get_settings(self):
        """
        Returns the settings of this platform.

        :rtype: :class:`dataikuapi.agentmanagement.platform.PlatformSettings`
        """
        settings = self.client._perform_json("GET", self._path("settings"))
        return PlatformSettings(self.client, self.platform_id, settings)

    def list_alert_configurations(self, as_type="listitems"):
        """
        Lists alert configurations owned on this platform, not configurations from other levels.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        path = self._path("alert-configurations")
        configurations = self.client._perform_json("GET", path)
        return _format_list([AlertConfigurationListItem(self.client, configuration, path) for configuration in configurations], as_type)

    def new_alert_configuration(self, type="metric", name=None):
        """
        Initializes a new alert configuration builder owned by this platform.

        Configure the returned builder, then call its ``create()`` method to submit it.

        :param str type: ``metric``; agent review configurations can only be created on an agent
        :param str name: optional display name
        :rtype: MetricAlertConfigurationBuilder
        """
        if type == "metric":
            return MetricAlertConfigurationBuilder(self.client, self._path("alert-configurations"), name)
        raise ValueError("Unsupported alert configuration type: %r" % (type,))

    def get_alert_configuration(self, configuration_id):
        """
        Returns a handle to an alert configuration owned on this platform.

        :param str configuration_id: configuration ID
        :rtype: :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        """
        return AlertConfiguration(self.client, self._path("alert-configurations"), configuration_id)

    def delete(self, allow_deletion_if_platform_contains_agents=False):
        """
        Deletes the platform and all its Agent Management agent records.

        :param boolean allow_deletion_if_platform_contains_agents: allow deletion even if the platform
            contains discovered or managed agents (default: False). Otherwise, these agents prevent deletion.
            Ignored and archived agents do not prevent deletion and are deleted with the platform.
        """
        self.client._perform_empty("DELETE", self._path(),
                                   params={"force": allow_deletion_if_platform_contains_agents})

    def list_agents(self, as_type="listitems", agent_filter=None):
        """
        Lists agents on this platform.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.agent.Agent`
        :param AgentFilter agent_filter: optional additional agent selection
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else AgentFilter()
        scoped_filter.with_platform_ids(self.platform_id)
        agents = self.client.search_agents(agent_filter=scoped_filter)["agents"]
        return _format_list([AgentListItem(self.client, agent) for agent in agents], as_type)

    def start_disable_agents(self, agent_filter, allow_destructive=False):
        """
        Starts disabling the agents matching a filter on their remote platform.

        Only agents on this platform are selected, regardless of any platform IDs
        in the filter. The server validates the complete selection before starting the operation.

        :param AgentFilter agent_filter: agents to disable
        :param bool allow_destructive: accept irreversible disable operations, including permanent deletion of
            remote resources (default: False). Without this consent, the server rejects the entire selection
            if any affected agent requires a destructive operation.
        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the activation change
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        if not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        response = self.client._perform_json("POST", self._path("agents/actions/disable"),
                                             params={"allowDestructive": allow_destructive}, body=agent_filter._as_dict())
        return Operation(self.client, self.platform_id, response["operation"]["id"], response["operation"]["agentId"])

    def start_enable_agents(self, agent_filter):
        """
        Starts enabling the agents matching a filter on their remote platform.

        Only agents on this platform are selected, regardless of any platform IDs
        in the filter. The server validates the complete selection before starting the operation.

        :param AgentFilter agent_filter: agents to enable
        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the activation change
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        if not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        response = self.client._perform_json("POST", self._path("agents/actions/enable"), body=agent_filter._as_dict())
        return Operation(self.client, self.platform_id, response["operation"]["id"], response["operation"]["agentId"])

    def setup_monitoring(self, agents, run_first_fetch=True, include_in_uptime_tests=True, **kwargs):
        """
        Enables monitoring for one or several agents on this platform in one pass.

        Provisions monitoring resources and enables supported monitoring capabilities.
        Administration rights are required on each agent.

        :param iterable agents: agent IDs (strings), :class:`dataikuapi.agentmanagement.agent.AgentListItem` entries,
            or :class:`dataikuapi.agentmanagement.agent.Agent` handles
        :param boolean run_first_fetch: whether to launch the initial data fetch (default: True)
        :param boolean include_in_uptime_tests: whether to include agents in supported uptime tests (default: True)
        :param str project_key: optional project in which to provision monitoring resources
        :param str connection_name: optional connection for managed monitoring datasets
        :param str partitioning: optional time partitioning, ``NONE`` or ``DAY``
        :returns: setup results containing ``configuredAgentIds`` and ``warnings``; check warnings for agents that could not be configured
        :rtype: dict
        """
        if isinstance(agents, (str, dict, Agent)):
            raise TypeError("agents must be an iterable of agent IDs, AgentListItem entries or Agent handles")
        agent_ids = []
        for agent in agents:
            if isinstance(agent, str):
                agent_id = agent
            elif isinstance(agent, (AgentListItem, Agent)):
                if agent.platform_id != self.platform_id:
                    raise ValueError("All agents must belong to this platform")
                agent_id = agent.id
            else:
                raise TypeError("Each agent must be an ID, AgentListItem entry or Agent handle")
            if not isinstance(agent_id, str) or not agent_id.strip():
                raise ValueError("Agent IDs must be non-empty strings")
            agent_ids.append(agent_id)
        if not agent_ids or len(set(agent_ids)) != len(agent_ids):
            raise ValueError("Agent IDs must be unique and non-empty")
        unsupported = set(kwargs) - {"project_key", "connection_name", "partitioning"}
        if unsupported:
            raise TypeError("Unsupported monitoring setup options: %s" % ", ".join(sorted(unsupported)))
        if "partitioning" in kwargs and kwargs["partitioning"] not in ("NONE", "DAY"):
            raise ValueError("partitioning must be NONE or DAY")
        body = {"agentIds": agent_ids, "runFirstFetch": run_first_fetch, "includeInUptimeTests": include_in_uptime_tests}
        body.update({key: kwargs[name] for name, key in (("project_key", "projectKey"), ("connection_name", "connectionName"),
                                                      ("partitioning", "partitioning")) if name in kwargs})
        return self.client._perform_json("POST", self._path("agents/actions/setup-monitoring"), body=body)

    def get_available_metric_ids(self, agent_filter=None):
        """
        Lists the union of metric identifiers supported by readable agents in this platform.

        Returns the dictionaries documented by :meth:`dataikuapi.AgentManagementClient.get_available_metric_ids`.
        The platform scope is added to a copy of the optional filter.

        :param AgentFilter agent_filter: optional additional agent filter
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else AgentFilter()
        scoped_filter.with_platform_ids(self.platform_id)
        return self.client.get_available_metric_ids(agent_filter=scoped_filter)

    def get_metric_time_series(self, metrics, agent_filter=None, from_time=None, to_time=None, latest_only=False):
        """
        Returns stored time-series values for agents on this platform.

        ``metrics`` uses the qualified identifiers and the response uses the compact tabular format
        documented by :meth:`dataikuapi.AgentManagementClient.get_metric_time_series`. The platform scope is added to the
        optional ``agent_filter`` and the same global REST endpoint is used.
        Set ``latest_only=True`` and omit both timestamps to get the latest available values.

        :param list metrics: qualified metric identifiers
        :param AgentFilter agent_filter: optional additional agent selection
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else AgentFilter()
        scoped_filter.with_platform_ids(self.platform_id)
        return self.client.get_metric_time_series(metrics, agent_filter=scoped_filter,
                                                       from_time=from_time, to_time=to_time,
                                                       latest_only=latest_only)

    def get_metric_buckets(self, metrics, bucket, agent_filter=None, from_time=None, to_time=None):
        """
        Returns bucketed metrics for agents on this platform.

        ``metrics`` uses the qualified identifiers, bucket compatibility rules and compact tabular
        response documented by :meth:`dataikuapi.AgentManagementClient.get_metric_buckets`. The platform scope is added to
        the optional ``agent_filter`` and the same global REST endpoint is used.

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param AgentFilter agent_filter: optional additional agent selection
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime
        :rtype: dataikuapi.agentmanagement.metrics.BucketedMetricsFetchResults
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else AgentFilter()
        scoped_filter.with_platform_ids(self.platform_id)
        return self.client.get_metric_buckets(metrics, bucket, agent_filter=scoped_filter,
                                                   from_time=from_time, to_time=to_time)

    def create_agent(self, agent_id, display_name=None, description=None, tags=None, configuration=None, permissions=None,
                     agent_owner=None):
        """
        Creates an agent manually and returns a handle to it. It is not usually necessary to create agents manually,
        as they are almost always discovered automatically by the platform scan.

        :param str agent_id: unique identifier of the agent
        :param str display_name: display name of the agent
        :param str description: agent description
        :param list tags: tags assigned to the agent
        :param dict configuration: provider-specific configuration
        :param list permissions: agent permissions
        :param dict agent_owner: owner, as ``{"user": "login"}`` or ``{"group": "name"}``. Omit to use the platform default
        :rtype: :class:`dataikuapi.agentmanagement.agent.Agent`
        """
        body = {
            "id": agent_id,
            "displayName": display_name,
            "description": description,
            "tags": tags or [],
            "configuration": configuration or {},
            "permissions": permissions or []
        }
        if agent_owner is not None:
            body["agentOwner"] = agent_owner
        created = self.client._perform_json("POST", self._path("agents"), body=body)
        return Agent(self.client, self.platform_id, created["id"])

    def get_agent(self, agent_id):
        """
        Returns a handle to an agent on this platform.

        :param str agent_id: identifier of the agent
        :rtype: :class:`dataikuapi.agentmanagement.agent.Agent`
        """
        return Agent(self.client, self.platform_id, agent_id)

    def start_scan(self):
        """
        Starts an platform scan.

        Usage example:

        .. code-block:: python

            platform = client.get_platform("my-platform")
            operation = platform.start_scan()
            scan_result = operation.wait_for_result()

        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the scan
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        response = self.client._perform_json("POST", self._path("actions/scan"))
        return Operation(self.client, self.platform_id, response["operation"]["id"])

    def start_run_uptime_tests(self, agent_ids=None):
        """
        Starts uptime tests for this platform.

        Usage example:

        .. code-block:: python

            platform = client.get_platform("my-platform")
            operation = platform.start_run_uptime_tests(["my-agent"])
            uptime_test_results = operation.wait_for_result()

        :param list agent_ids: agents to test, or None to test all eligible agents
        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the uptime tests
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        body = None if agent_ids is None else {"agentIds": agent_ids}
        response = self.client._perform_json("POST", self._path("actions/run-uptime-tests"), body=body)
        return Operation(self.client, self.platform_id, response["operation"]["id"])

    def list_operations(self, as_type="listitems", current_only=False, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None):
        """
        Lists operations launched for this platform.

        :param str as_type: "listitems"/"listitem" returns OperationListItem entries; "objects"/"object" returns Operation handles
        :param boolean current_only: whether to return only queued or running operations
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: maximum number of returned operations, defaults to 1000, up to 10000
        :returns: operations and a ``has_more`` flag indicating whether additional operations matched
        :rtype: :class:`dataikuapi.agentmanagement.operations.OperationSearchResult`
        """
        return self.client.list_operations(
            agent_filter=AgentFilter().with_platform_ids(self.platform_id),
            operation_types=operation_types,
            statuses=statuses,
            triggers=triggers,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            current_only=current_only,
            as_type=as_type)

    def get_operation(self, operation_id):
        """
        Returns a handle to an platform operation.

        :param str operation_id: identifier of the operation
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        return Operation(self.client, self.platform_id, operation_id)

    def _path(self, suffix=None):
        path = "/agent-management/platforms/%s" % dku_quote_fn(self.platform_id, safe="")
        if suffix is not None:
            path += "/" + suffix
        return path


class PlatformStatus(object):
    """
    The status of an Agent Management platform.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.platform.Platform.get_status`.
    """
    def __init__(self, client, platform_id, status):
        self.client = client
        self.platform_id = platform_id
        self.status = status

    def get_raw(self):
        """
        Returns the raw status of this platform.

        :rtype: dict
        """
        return self.status


class PlatformSettings(object):
    """
    The settings of an Agent Management platform.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.platform.Platform.get_settings`.
    """
    def __init__(self, client, platform_id, settings):
        self.client = client
        self.platform_id = platform_id
        self.settings = settings

    @property
    def raw(self):
        """
        The raw settings of this platform.

        An platform administrator can change ``raw["defaultAgentOwner"]``
        to ``{"user": "login"}``, ``{"group": "name"}``, or ``None``, then call :meth:`save`.
        Changing this default does not reassign existing agents.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Saves the settings of this platform, using ``fetchedRevision`` to detect concurrent changes.

        Remove ``fetchedRevision`` from :attr:`raw` or set it to ``None`` to save without a revision check.

        :returns: the saved settings
        :rtype: :class:`dataikuapi.agentmanagement.platform.PlatformSettings`
        """
        body = dict(self.settings)
        path = "/agent-management/platforms/%s/settings" % dku_quote_fn(self.platform_id, safe="")
        self.settings = self.client._perform_json("PUT", path, body=body)
        return self


class PlatformListItem(dict):
    """A Platform listing entry with local accessors and conversion to a resource handle."""

    def __init__(self, client, data):
        super(PlatformListItem, self).__init__(data)
        self.client = client

    @property
    def id(self):
        """The listing entry's id."""
        return self["id"]

    @property
    def name(self):
        """The listing entry's name."""
        return self.get("displayName")

    @property
    def display_name(self):
        """The listing entry's display name."""
        return self.get("displayName")

    @property
    def type(self):
        """The listing entry's type."""
        return self.get("type")

    def to_platform(self):
        """Return a :class:`Platform` handle without making an API call."""
        return Platform(self.client, self.id)

    def _to_object(self):
        return self.to_platform()
