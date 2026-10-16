from .metrics import AgentBucketedMetricsFetchResults
from ._utils import dku_quote_fn, _format_list
from .risk import RiskAssessment
from .operations import Operation
from .alerting import AlertConfiguration, AlertConfigurationListItem, MetricAlertConfigurationBuilder, AgentReviewAlertConfigurationBuilder


class AgentFilter(object):
    """
    Agent filter accepted by search, metric retrieval and bulk action methods.

    Values within each list criterion, including scopes, are combined with OR.
    Different criteria are combined with AND.
    """

    NO_TAGS = "__NO_TAGS__"

    DISCOVERY_FOUND = "FOUND"
    DISCOVERY_NOT_FOUND = "NOT_FOUND"
    DISCOVERY_MANUALLY_ADDED = "MANUALLY_ADDED"

    RISK_SIGNED_OFF = "SIGNED_OFF"
    RISK_NOT_SIGNED_OFF = "NOT_SIGNED_OFF"

    STATE_DISCOVERED = "DISCOVERED"
    STATE_MANAGED = "MANAGED"
    STATE_IGNORED = "IGNORED"
    STATE_ARCHIVED = "ARCHIVED"

    def __init__(self):
        self.text_filter = None
        self.agent_ids = None
        self.scope_ids = None
        self.platform_types = None
        self.platform_ids = None
        self.discovery_statuses = None
        self.risk_sign_offs = None
        self.tags = None
        self.states = None
        self.favorites = None

    def with_text_filter(self, text_filter):
        self.text_filter = text_filter
        return self

    def with_agent_ids(self, *agent_ids):
        self.agent_ids = list(agent_ids)
        return self

    def with_scope_ids(self, *scope_ids):
        self.scope_ids = list(scope_ids)
        return self

    def with_platform_types(self, *platform_types):
        self.platform_types = list(platform_types)
        return self

    def with_platform_ids(self, *platform_ids):
        self.platform_ids = list(platform_ids)
        return self

    def with_discovery_statuses(self, *discovery_statuses):
        self.discovery_statuses = list(discovery_statuses)
        return self

    def with_risk_sign_offs(self, *risk_sign_offs):
        self.risk_sign_offs = list(risk_sign_offs)
        return self

    def with_tags(self, *tags):
        self.tags = list(tags)
        return self

    def with_states(self, *states):
        self.states = list(states)
        return self

    def with_favorites(self, favorites=True):
        """
        Filters on the authenticated user's favorite agents.

        Use a personal API key to access the same favorites as in DSS. A non-personal
        API key does not use the favorites of its creator or impersonated user.

        :param bool favorites: True for favorites, False for non-favorites, None to remove this criterion
        :rtype: AgentFilter
        """
        self.favorites = favorites
        return self

    def _as_dict(self):
        return {
            name: value for name, value in (
                ("textFilter", self.text_filter),
                ("agentId", self.agent_ids),
                ("scopeId", self.scope_ids),
                ("platformType", self.platform_types),
                ("platformName", self.platform_ids),
                ("discoveryStatus", self.discovery_statuses),
                ("riskSignOff", self.risk_sign_offs),
                ("tags", self.tags),
                ("state", self.states),
                ("favorites", self.favorites),
            ) if value is not None
        }


class Agent(object):
    """
    A monitored Agent Management agent.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.platform.Platform.get_agent`.
    """

    def __init__(self, client, platform_id, agent_id):
        self.client = client
        self.platform_id = platform_id
        self.agent_id = agent_id

    @property
    def id(self):
        return self.agent_id

    def __repr__(self):
        return "<Agent platform_id=%r id=%r>" % (self.platform_id, self.agent_id)

    def get_status(self):
        """
        Returns status information about this agent.

        :rtype: :class:`dataikuapi.agentmanagement.agent.AgentStatus`
        """
        light = self.client._perform_json("GET", self._path())
        heavy = self.client._perform_json("GET", self._path("status"))
        return AgentStatus(self.client, self.platform_id, self.agent_id, light, heavy)

    def get_settings(self):
        """
        Returns the settings of this agent.

        :rtype: :class:`dataikuapi.agentmanagement.agent.AgentSettings`
        """
        settings = self.client._perform_json("GET", self._path("settings"))
        return AgentSettings(self.client, self.platform_id, self.agent_id, settings)

    def list_alert_configurations(self, as_type="listitems"):
        """
        Lists alert configurations owned on this agent, not configurations from other levels.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        path = self._path("alert-configurations")
        configurations = self.client._perform_json("GET", path)
        return _format_list([AlertConfigurationListItem(self.client, configuration, path) for configuration in configurations], as_type)

    def new_alert_configuration(self, type="metric", name=None):
        """
        Initializes a new alert configuration builder owned by this agent.

        Configure the returned builder, then call its ``create()`` method to submit it.

        :param str type: ``metric`` or ``agent_review``
        :param str name: optional display name
        :rtype: MetricAlertConfigurationBuilder or AgentReviewAlertConfigurationBuilder
        """
        if type == "metric":
            return MetricAlertConfigurationBuilder(self.client, self._path("alert-configurations"), name)
        if type == "agent_review":
            return AgentReviewAlertConfigurationBuilder(self.client, self._path("alert-configurations"), name)
        raise ValueError("Unsupported alert configuration type: %r" % (type,))

    def get_alert_configuration(self, configuration_id):
        """
        Returns a handle to an alert configuration owned on this agent.

        :param str configuration_id: configuration ID
        :rtype: :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        """
        return AlertConfiguration(self.client, self._path("alert-configurations"), configuration_id)

    def list_applicable_alert_configurations(self):
        """
        Lists global, platform, matching scope, and agent alert configurations applicable to this agent.

        Configurations apply independently, without overriding one another. Disabled and incomplete configurations
        are included; edit each configuration where it was defined.

        Each result contains ``configuration``, its resolved ``loc``, and ``latestEvaluation`` when available,
        even if no alert has opened. Unavailable evaluations do not imply recovery.
        Evaluation results may include shared ``breachProgress`` and policy-specific ``diagnostics``, identified by ``type``.
        Timestamps are in milliseconds since the Unix epoch.

        :rtype: list of :class:`dataikuapi.agentmanagement.alerting.AlertConfigurationListItem`
        """
        configurations = self.client._perform_json("GET", self._path("applicable-alert-configurations"))
        return [AlertConfigurationListItem(self.client, configuration) for configuration in configurations]

    def evaluate_alerts(self, mode="DUE"):
        """
        Queues alert evaluation through the scheduler for this agent, whether or not periodic
        evaluation is enabled. Evaluation errors are logged asynchronously.

        :param str mode: ``DUE`` processes pending metric buckets within the catch-up limit.
                         ``FORCE_LATEST`` recomputes the latest completed eligible bucket and
                         corrects its alerts. ``FORCE_CATCH_UP`` does the same for the last N
                         buckets, where N is the configured catch-up depth. Both read additional
                         supporting history when consecutive breaches require it. Affected alerts
                         remain in history as invalidated. Replacements have new IDs, even when
                         recomputed values are unchanged, and do not inherit acknowledgements;
                         these remain on the original alerts. Missing target observations prevent
                         correction of the requested range. Missing older supporting observations
                         also prevent correction when too few consecutive breaches remain to establish the observed severity.
                         Agent-review alerts evaluate the latest eligible review run in every mode.
        :returns: number of agents included in the queued request
        :rtype: int
        """
        response = self.client._perform_json("POST", self._path("actions/evaluate-alerts"), params={"mode": mode})
        return response["queuedAgentCount"]

    def delete(self):
        """Deletes the agent."""
        self.client._perform_empty("DELETE", self._path())

    def start_disable(self, allow_destructive=False):
        """
        Starts disabling this agent on its remote platform.

        :param bool allow_destructive: accept an irreversible disable operation, including permanent deletion of
            remote resources (default: False). Without this consent, the server rejects destructive operations.
        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the activation change
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        response = self.client._perform_json("POST", self._path("actions/disable"), params={"allowDestructive": allow_destructive})
        return Operation(self.client, self.platform_id, response["operation"]["id"], self.agent_id)

    def start_enable(self):
        """
        Starts enabling this agent on its remote platform.

        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the activation change
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        response = self.client._perform_json("POST", self._path("actions/enable"))
        return Operation(self.client, self.platform_id, response["operation"]["id"], self.agent_id)

    def setup_monitoring(self, run_first_fetch=True, include_in_uptime_tests=True, **kwargs):
        """
        Enables monitoring for this agent and provisions its monitoring resources.

        For multiple agents, prefer a single call to :meth:`dataikuapi.agentmanagement.platform.Platform.setup_monitoring`
        to set them up in one pass. Administration rights are required on this agent.

        :param boolean run_first_fetch: whether to launch the initial data fetch (default: True)
        :param boolean include_in_uptime_tests: whether to include this agent in supported uptime tests (default: True)
        :param str project_key: optional project in which to provision monitoring resources
        :param str connection_name: optional connection for managed monitoring datasets
        :param str partitioning: optional time partitioning, ``NONE`` or ``DAY``
        :returns: setup results containing ``configuredAgentIds`` and ``warnings``; check warnings if the agent could not be configured
        :rtype: dict
        """
        return self.client.get_platform(self.platform_id).setup_monitoring([self], run_first_fetch=run_first_fetch,
                                                                 include_in_uptime_tests=include_in_uptime_tests, **kwargs)

    # def get_history(self, from_timestamp=None, to_timestamp=None, field_query=None, event_types=None, triggers=None):
    #     """
    #     Returns the agent change history.
    #
    #     The server streams matching events and this method returns them as a single list.
    #
    #     :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
    #     :param int to_timestamp: optional inclusive upper timestamp bound, in milliseconds since the Unix epoch
    #     :param str field_query: optional case-insensitive search in the labels of changed fields,
    #         for example ``permissions`` or ``scheduled log fetch``. This does not search field
    #         values. Events without a matching changed field are omitted and only matching changes
    #         are included in returned events.
    #     :param list event_types: optional event types among ``CREATED``, ``UPDATED`` and ``DELETED``
    #     :param list triggers: optional triggers among ``EXPLICIT_REQUEST`` and ``SCAN``
    #     :rtype: list of dict
    #     """
    #     return self.client._perform_json("POST", self._path("history/search"), body={
    #         "fromTimestamp": from_timestamp,
    #         "toTimestamp": to_timestamp,
    #         "eventTypes": list(event_types) if event_types is not None else [],
    #         "triggers": list(triggers) if triggers is not None else [],
    #         "fieldQuery": field_query
    #     })

    def get_available_metric_ids(self):
        """
        Lists metric identifiers supported by this agent and their query compatibility.

        Each dictionary contains ``id``, ``supportsBuckets`` and ``supportsTimeSeries``, as documented by
        :meth:`dataikuapi.AgentManagementClient.get_available_metric_ids`. Includes configured business KPIs.
        Supported metrics may have no stored data yet.

        :rtype: list of dict
        """
        agent_filter = AgentFilter().with_platform_ids(self.platform_id).with_agent_ids(self.agent_id)
        return self.client.get_available_metric_ids(agent_filter=agent_filter)

    def get_metric_time_series(self, metrics, from_time=None, to_time=None, latest_only=False):
        """
        Returns stored time-series values for this agent.

        ``metrics`` uses the qualified identifiers and compact tabular response documented by
        :meth:`dataikuapi.AgentManagementClient.get_metric_time_series`. The agent is selected through the global endpoint.
        Set ``latest_only=True`` and omit both timestamps to get the latest available values.

        :param list metrics: qualified metric identifiers
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        agent_filter = AgentFilter().with_platform_ids(self.platform_id).with_agent_ids(self.agent_id)
        return self.client.get_metric_time_series(metrics, agent_filter=agent_filter,
                                                       from_time=from_time, to_time=to_time,
                                                       latest_only=latest_only)

    def get_metric_buckets(self, metrics, bucket, from_time=None, to_time=None):
        """
        Returns bucketed metrics for this agent.

        ``metrics`` uses the qualified identifiers, bucket compatibility rules and compact tabular
        response documented by :meth:`dataikuapi.AgentManagementClient.get_metric_buckets`. The agent is selected through the
        global endpoint. Use ``series()`` for the unified table, ``raw_data()`` for the grouped
        response, ``single_series(metric_id)`` for bucket tuples, and ``values_at_time(time)``
        for values in the bucket containing an epoch millisecond timestamp or aware datetime.

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime
        :rtype: dataikuapi.agentmanagement.metrics.AgentBucketedMetricsFetchResults
        """
        agent_filter = AgentFilter().with_platform_ids(self.platform_id).with_agent_ids(self.agent_id)
        results = self.client.get_metric_buckets(metrics, bucket, agent_filter=agent_filter,
                                                   from_time=from_time, to_time=to_time)
        return AgentBucketedMetricsFetchResults(results, self.platform_id, self.agent_id)

    def get_uptime_results(self, from_time=None, to_time=None):
        """
        Returns the agent uptime test results.

        :param str from_time: optional lower time bound
        :param str to_time: optional upper time bound
        :rtype: list of dict
        """
        return self.client._perform_json("GET", self._path("uptime-results"), params={"from": from_time, "to": to_time})

    # def get_topic_modeling(self, periodicity="QUARTER"):
    #     """
    #     Returns topic-modeling results for the agent.
    #
    #     :param str periodicity: aggregation periodicity
    #     :rtype: dict
    #     """
    #     response = self.client._perform_json("GET", self._path("topic-modeling"), params={"periodicity": periodicity})
    #     return response.get("result")
    #
    # def validate_log_fetch(self, configuration=None):
    #     """
    #     Validates the persisted log-fetch configuration, or the supplied agent configuration, without saving it.
    #
    #     :param dict configuration: optional agent configuration to validate
    #     :returns: True when the configuration is valid
    #     :rtype: boolean
    #     """
    #     body = None if configuration is None else {"configuration": configuration}
    #     response = self.client._perform_json("POST", self._path("log-fetch/actions/validate"), body=body)
    #     return response.get("valid", False)

    def start_fetch_logs(self):
        """
        Starts fetching execution logs for the agent.

        Usage example:

        .. code-block:: python

            agent = client.get_agent("my-platform", "my-agent")
            operation = agent.start_fetch_logs()
            log_fetch_result = operation.wait_for_result()

        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the log fetch
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        response = self.client._perform_json("POST", self._path("actions/fetch-logs"))
        return Operation(self.client, self.platform_id, response["operation"]["id"], self.agent_id)

    def start_fetch_platform_operational_metrics(self):
        """
        Starts fetching platform operational metrics for the agent.

        Usage example:

        .. code-block:: python

            agent = client.get_agent("my-platform", "my-agent")
            operation = agent.start_fetch_platform_operational_metrics()
            metrics_fetch_result = operation.wait_for_result()

        This method returns before the operation completes. Call ``wait_for_result()`` on the returned operation to wait.

        :returns: the Agent Management operation tracking the platform operational metrics fetch
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        response = self.client._perform_json("POST", self._path("actions/fetch-platform-operational-metrics"))
        return Operation(self.client, self.platform_id, response["operation"]["id"], self.agent_id)

    def create_external_agent(self, project_key, name):
        """
        Creates a DSS external agent backed by this monitored agent.

        :param str project_key: project in which to create the external agent
        :param str name: name of the external agent
        :returns: a reference to the created DSS object
        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("actions/create-external-agent"), body={"projectKey": project_key, "name": name})

    def list_operations(self, as_type="listitems", current_only=False, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None):
        """
        Lists operations launched for this agent.

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
            agent_filter=AgentFilter().with_platform_ids(self.platform_id).with_agent_ids(self.agent_id),
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
        Returns a handle to an operation for this agent.

        :param str operation_id: identifier of the operation
        :rtype: :class:`dataikuapi.agentmanagement.operations.Operation`
        """
        return Operation(self.client, self.platform_id, operation_id, self.agent_id)

    def get_risk_assessment(self):
        """
        Returns the risk assessment of this agent.

        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskAssessment`
        """
        assessment = self.client._perform_json("GET", self._path("risk-assessment"))
        return RiskAssessment(self.client, self.platform_id, self.agent_id, assessment)

    def set_risk_assessment_signed_off(self, signed_off):
        """
        Sets whether the current risk assessment is validated.

        :param boolean signed_off: True to validate the assessment, False to remove its validation
        :returns: the updated risk assessment
        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskAssessment`
        """
        if not isinstance(signed_off, bool):
            raise TypeError("signed_off must be a boolean")
        assessment = self.client._perform_json("POST" if signed_off else "DELETE", self._path("risk-assessment/sign-off"))
        return RiskAssessment(self.client, self.platform_id, self.agent_id, assessment)

    def _path(self, suffix=None):
        path = "/agent-management/platforms/%s/agents/%s" % (
            dku_quote_fn(self.platform_id, safe=""),
            dku_quote_fn(self.agent_id, safe=""))
        if suffix is not None:
            path += "/" + suffix
        return path


class AgentStatus(object):
    """
    The status of a monitored agent.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.agent.Agent.get_status`.
    """
    def __init__(self, client, platform_id, agent_id, light, heavy):
        self.client = client
        self.platform_id = platform_id
        self.agent_id = agent_id
        self.light = light
        self.heavy = heavy

    def get_light(self):
        """
        Gets the 'light' (summary) status of this agent.

        :rtype: dict
        """
        return self.light

    def get_heavy(self):
        """
        Gets the 'heavy' (full) status of this agent.

        :rtype: dict
        """
        return self.heavy

    @property
    def platform_activation_state(self):
        """
        Returns ``UNKNOWN``, ``ENABLED`` or ``DISABLED`` according to the last known state on the
        remote platform.

        :rtype: str
        """
        return self.light.get("platformActivationState", "UNKNOWN")


class AgentSettings(object):
    """
    The settings of a monitored agent.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.agent.Agent.get_settings`.
    """
    def __init__(self, client, platform_id, agent_id, settings):
        self.client = client
        self.platform_id = platform_id
        self.agent_id = agent_id
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw settings of this agent.

        Only an agent administrator can change ``configuration["agentOwner"]``.
        Use ``{"user": "login"}``, ``{"group": "name"}``, or ``None`` to remove
        the owner, then call :meth:`save`. Ownership grants implicit administration
        rights without changing explicit permissions.

        .. code-block:: python

            settings = agent.get_settings()
            settings.get_raw()["configuration"]["agentOwner"] = {"group": "agent-operators"}
            settings.save()

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Saves the settings of this agent, checking ``fetchedRevision`` read by ``get_settings``.

        Remove ``fetchedRevision`` from :meth:`get_raw` or set it to ``None`` to save without a revision check.

        After transferring ownership, the caller retains only their remaining permissions.
        If they lose read access, saving succeeds and ``get_raw()`` contains only the
        server's confirmation message.

        :returns: the saved settings
        :rtype: :class:`dataikuapi.agentmanagement.agent.AgentSettings`
        """
        body = dict(self.settings)
        body["fetchedRevision"] = self.settings.get("fetchedRevision")
        path = "/agent-management/platforms/%s/agents/%s/settings" % (dku_quote_fn(self.platform_id, safe=""), dku_quote_fn(self.agent_id, safe=""))
        self.settings = self.client._perform_json("PUT", path, body=body)
        return self


class AgentListItem(dict):
    """An agent listing entry returned by the client's or platform's ``list_agents`` method."""

    def __init__(self, client, data):
        super(AgentListItem, self).__init__(data)
        self.client = client

    @property
    def id(self):
        """The listing entry's id."""
        return self["id"]

    @property
    def platform_id(self):
        """The listing entry's platform id."""
        return self.get("infraId")

    @property
    def name(self):
        """The listing entry's name."""
        return self.get("displayName")

    @property
    def display_name(self):
        """The listing entry's display name."""
        return self.get("displayName")

    @property
    def tags(self):
        """The listing entry's tags."""
        return self.get("tags")

    @property
    def type(self):
        """The agent type."""
        return self.get("type")

    @property
    def state(self):
        """The agent state."""
        return self.get("state")

    @property
    def description(self):
        """The agent description."""
        return self.get("description")

    def to_agent(self):
        """Return a :class:`Agent` handle without making an API call."""
        return Agent(self.client, self.platform_id, self.id)

    def _to_object(self):
        return self.to_agent()
