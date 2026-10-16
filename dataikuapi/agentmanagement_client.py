import json
import warnings
from datetime import datetime, timedelta, timezone

from requests import Session
from requests.auth import HTTPBasicAuth
from .utils import handle_http_exception
from .agentmanagement.metrics import BucketedMetricsFetchResults
from .agentmanagement._utils import dku_quote_fn, _to_timestamp_ms, _format_list
from .agentmanagement.agent import AgentFilter, Agent, AgentListItem
from .agentmanagement.risk import EstateRiskExposure, RiskTaxonomySettings
from .agentmanagement.operations import OperationSearchResult, Operation
from .agentmanagement.platform import Platform, PlatformListItem
from .agentmanagement.alerting import AlertConfiguration, AlertConfigurationListItem, MetricAlertConfigurationBuilder, TriggeredAlertSearchResult, Alert
from .agentmanagement.settings import Settings
from .agentmanagement.topic_family import TopicFamily, TopicFamilyListItem
from .agentmanagement.cobuild import CobuildConversation


def _consolidate_metric_chunks(chunks):
    series = []
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    for index, chunk in enumerate(chunks):
        time_columns = [i for i, column in enumerate(chunk["columns"]) if column in ("timestamp", "start", "end")]
        for row in chunk.get("rows", []):
            for i in time_columns:
                if row[i] is not None:
                    row[i] = epoch + timedelta(milliseconds=row[i])
        chunks[index] = None
        if (series
                and series[-1].get("infrastructureName") == chunk.get("infrastructureName")
                and series[-1].get("agentId") == chunk.get("agentId")
                and series[-1].get("columns") == chunk.get("columns")):
            rows = chunk.get("rows", [])
            series[-1]["rows"].extend(rows)
            del rows[:]
            chunk.clear()
        else:
            series.append(chunk)
    del chunks[:]
    return series


class AgentManagementClient(object):
    """
    Entry point for the Dataiku Agent Management API client.

    Usage example:

    .. code-block:: python

        import dataikuapi

        client = dataikuapi.AgentManagementClient("https://agent-management.example", api_key="your-api-key")
        agent = client.get_agent("my-platform", "my-agent")
        status = agent.get_status()
    """

    def __init__(self, host, api_key=None, internal_ticket=None, extra_headers=None, no_check_certificate=False, client_certificate=None,
                 jwt_bearer_token=None, **kwargs):
        """Initialize a new Agent Management API client.

        Args:
            host (str): The host URL of the Agent Management instance (e.g., "http://localhost:11200")
            api_key (str, optional): API key for authentication
            no_check_certificate (bool, optional): If True, disables SSL certificate verification. Defaults to False.
            extra_headers (dict, optional): Additional HTTP headers to include in requests.
            client_certificate (str or tuple, optional): Path to client certificate file or tuple of (cert, key) paths.
            jwt_bearer_token (str, optional): JWT bearer token for authentication.
        """
        self.api_key = api_key
        self.internal_ticket = internal_ticket
        self.jwt_bearer_token = jwt_bearer_token
        self.host = host
        self._session = Session()
        if no_check_certificate:
            self._session.verify = False
        if client_certificate:
            self._session.cert = client_certificate

        if self.api_key is not None:
            self._session.auth = HTTPBasicAuth(self.api_key, "")
        elif self.internal_ticket is not None:
            self._session.headers.update({"X-DKU-APITicket" : self.internal_ticket})
        elif jwt_bearer_token is not None:
            self._session.headers.update({"Authorization": "Bearer " + jwt_bearer_token})
        else:
            raise ValueError("Authentication is required. You must provide either api_key, internal_ticket or jwt_bearer_token.")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    def new_cobuild_conversation(self):
        """
        Start a new empty Cobuild conversation in Agent Management.

        Example::

            conversation = client.new_cobuild_conversation()
            response = conversation.send_message("List the agents in my estate")
            print(response.message)

        Pass ``allow_edit=True`` to ``send_message`` or ``approve_plan`` to allow changes
        for that turn. Assistant responses can request a confirmation or an explicit
        answer; continue with ``answer_confirmation`` or ``answer_question`` respectively.

        :rtype: :class:`dataikuapi.agentmanagement.cobuild.CobuildConversation`
        """
        raw = self._perform_json("POST", "/agent-management/cobuild/conversations", body={})
        return CobuildConversation(self, raw["conversationId"])

    def get_settings(self):
        """
        Returns the global Agent Management settings.

        :rtype: :class:`dataikuapi.agentmanagement.settings.Settings`
        """
        settings = self._perform_json("GET", "/agent-management/settings")
        return Settings(self, settings)

    def list_alert_configurations(self, as_type="listitems"):
        """
        Lists alert configurations owned globally, not configurations from other levels.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        path = "/agent-management/alert-configurations"
        configurations = self._perform_json("GET", path)
        return _format_list([AlertConfigurationListItem(self, configuration, path) for configuration in configurations], as_type)

    def new_alert_configuration(self, type="metric", name=None):
        """
        Initializes a new alert configuration builder owned by this client.

        Configure the returned builder, then call its ``create()`` method to submit it.

        :param str type: ``metric``; agent review configurations can only be created on an agent
        :param str name: optional display name
        :rtype: MetricAlertConfigurationBuilder
        """
        if type == "metric":
            return MetricAlertConfigurationBuilder(self, "/agent-management/alert-configurations", name)
        raise ValueError("Unsupported alert configuration type: %r" % (type,))

    def get_alert_configuration(self, configuration_id):
        """
        Returns a handle to an alert configuration owned globally.

        :param str configuration_id: configuration ID
        :rtype: :class:`dataikuapi.agentmanagement.alerting.AlertConfiguration`
        """
        return AlertConfiguration(self, "/agent-management/alert-configurations", configuration_id)

    def list_platforms(self, as_type="listitems"):
        """
        Lists Agent Management platforms.

        :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.platform.Platform`
        :returns: a list - see ``as_type`` for more information
        :rtype: list
        """
        platforms = self._perform_json("GET", "/agent-management/platforms")
        return _format_list([PlatformListItem(self, platform) for platform in platforms], as_type)

    def create_platform(self, platform_id, platform_type, display_name, connection_name=None, default_project_key=None,
                     permissions=None, default_agent_permissions=None):
        """
        Creates an Agent Management platform with default settings and returns a handle to it.

        :param str platform_id: unique identifier of the platform
        :param str platform_type: type of platform
        :param str display_name: display name of the platform
        :param str connection_name: platform connection used by the platform (except OpenTelemetryReceiver)
        :param str default_project_key: default DSS project used by the platform
        :param list permissions: platform permissions; the creator is also made an administrator
        :param list default_agent_permissions: default permissions for agents in the platform
        :rtype: :class:`dataikuapi.agentmanagement.platform.Platform`
        """
        body = {
            "id": platform_id,
            "displayName": display_name,
            "defaultProjectKey": default_project_key,
            "type": platform_type,
            "connectionName": connection_name,
            "permissions": permissions or [],
            "defaultAgentPermissions": default_agent_permissions or []
        }
        created = self._perform_json("POST", "/agent-management/platforms", body=body)
        return Platform(self, created["id"])

    def get_platform(self, platform_id):
        """
        Returns a handle to an Agent Management platform.

        :param str platform_id: identifier of the platform
        :rtype: :class:`dataikuapi.agentmanagement.platform.Platform`
        """
        return Platform(self, platform_id)

    def get_agent(self, platform_id, agent_id):
        """
        Returns a handle to an agent.

        :param str platform_id: identifier of the platform
        :param str agent_id: identifier of the agent
        :rtype: :class:`dataikuapi.agentmanagement.agent.Agent`
        """
        return Agent(self, platform_id, agent_id)

    def list_agents(self, as_type="listitems", agent_filter=None):
        """
        Lists readable agents matching an optional filter.

        :param str as_type: "listitems"/"listitem" returns AgentListItem entries; "objects"/"object" returns Agent handles
        :param AgentFilter agent_filter: optional agent selection
        :rtype: list
        """
        agents = self.search_agents(agent_filter=agent_filter)["agents"]
        return _format_list([AgentListItem(self, agent) for agent in agents], as_type)

    def search_agents(self, agent_filter=None):
        """
        Lists the readable agents matching a filter.

        Values of a facet are combined with OR, while different facets are combined with AND.

        :param AgentFilter agent_filter: agent filter
        :returns: a dictionary containing ``agents`` and contextual ``facets`` counts
        :rtype: dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = agent_filter._as_dict() if agent_filter is not None else {}
        return self._perform_json("POST", "/agent-management/agents/search", body=body)

    def evaluate_alerts(self, agent_filter=None, mode="DUE"):
        """
        Queues alert evaluation through the scheduler for editable agents matching a filter,
        whether or not periodic evaluation is enabled. Evaluation errors are logged asynchronously.

        Agents that the caller cannot edit are ignored.

        :param AgentFilter agent_filter: optional agent selection
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
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        response = self._perform_json("POST", "/agent-management/agents/actions/evaluate-alerts", params={"mode": mode},
                                             body=agent_filter._as_dict() if agent_filter is not None else {})
        return response["queuedAgentCount"]

    def get_available_metric_ids(self, agent_filter=None):
        """
        Lists the metric identifiers supported by readable agents matching the filter.

        Returns the union across selected agents, sorted by identifier. Each dictionary contains
        ``id``, ``supportsBuckets`` and ``supportsTimeSeries``. The flags indicate compatibility with
        :meth:`get_metric_buckets` and :meth:`get_metric_time_series`; they do not guarantee stored data.
        Configured business KPIs use the ``business-kpi.`` prefix and support both query methods.
        An empty agent selection returns an empty list.

        :param AgentFilter agent_filter: optional agent filter; omitted selects all readable agents
        :returns: metric identifiers and their query compatibility
        :rtype: list of dict

        Example::

            available = dam.get_available_metric_ids()
            bucket_metric_ids = [metric["id"] for metric in available if metric["supportsBuckets"]]
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        return self._perform_json("POST", "/agent-management/agents/metrics/available",
                                  body=agent_filter._as_dict() if agent_filter is not None else {})

    def get_metric_time_series(self, metrics, agent_filter=None, from_time=None, to_time=None, latest_only=False):
        """
        Returns stored, non-aggregated metric values for the selected agents.

        This method can only return metrics for which individual values are stored. Metrics which
        exist only as aggregates cannot be reconstructed as time-series values and must be queried
        with :meth:`get_metric_buckets` instead.

        ``metrics`` is a list of qualified metric identifiers. Each identifier includes its family,
        for example ``reliability.uptime_test_status``. The accepted identifiers are ``reliability.uptime_test_status``,
        ``performance.uptime_test_response_time_ms`` and ``business-kpi.<id>``, where ``<id>`` is the identifier of a
        business KPI assigned to the agent. Uptime and business KPI metrics can be requested in the
        same call. Examples of metrics which only exist as buckets include ``reliability.uptime_successful_tests_count``,
        ``reliability.uptime_tests_count``, ``reliability.uptime_pct`` and all activity, consumption, behavior and bucketed performance metrics. This list is not
        exhaustive; any requested metric which is not stored as individual values is rejected.

        The response is a list of series. Each series has ``infrastructureName``, ``agentId``,
        ``columns`` and ``rows``. The first column is ``timestamp`` as a UTC-aware datetime; remaining
        columns are the qualified metrics. Rows are chronological lists aligned with
        ``columns``. Metrics sharing the same stored timeline are grouped; each business KPI has its
        own series. A selected agent with no value has an empty ``rows`` list.

        If ``latest_only`` is True, each series contains at most its latest available row. Metrics
        which share a timeline still share one row: this mode does not look for the latest non-null
        value of each metric separately. Both timestamps must be omitted in this mode. Otherwise
        ``from_time`` is required and ``to_time`` defaults to the current time.

        To get the latest available values, omit both timestamps and set ``latest_only=True``:

        .. code-block:: python

            latest_time_series = dam.get_metric_time_series(
                metrics=["reliability.uptime_test_status", "performance.uptime_test_response_time_ms"],
                latest_only=True
            )

        This example requests one metric from each family available as stored time-series values.
        The business KPI points are deliberately shifted by five minutes from the uptime points:

        .. code-block:: python

            from datetime import datetime, timezone

            time_series = dam.get_metric_time_series(
                metrics=["reliability.uptime_test_status", "business-kpi.customer-satisfaction"],
                from_time=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                to_time=datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
                agent_filter=AgentFilter().with_agent_ids("support-agent")
            )

            # time_series == [
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "reliability.uptime_test_status"],
            #         "rows": [[datetime(2026, 1, 1, 1, 0, tzinfo=timezone.utc), "OK"], [datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc), "ERROR"]]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "business-kpi.customer-satisfaction"],
            #         "rows": [[datetime(2026, 1, 1, 1, 5, tzinfo=timezone.utc), 4.6], [datetime(2026, 1, 1, 2, 5, tzinfo=timezone.utc), 4.8]]
            #     }
            # ]

        :param list metrics: qualified metric identifiers, for example
            ``["reliability.uptime_test_status", "performance.uptime_test_response_time_ms", "business-kpi.revenue"]``
        :param AgentFilter agent_filter: optional agent selection
        :param int or datetime from_time: optional inclusive lower bound, as epoch milliseconds or a timezone-aware datetime;
            required when ``latest_only`` is False and forbidden when it is True
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime;
            defaults to the current time when ``from_time`` is set and is forbidden when ``latest_only`` is True
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        if latest_only and (from_time is not None or to_time is not None):
            raise ValueError("from_time and to_time must be omitted when latest_only is True")
        if not latest_only and from_time is None:
            raise ValueError("from_time is required when latest_only is False")
        chunks = self._perform_json("POST", "/agent-management/agents/metrics/time-series", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": _to_timestamp_ms(from_time, "from_time"),
            "toTimestamp": _to_timestamp_ms(to_time, "to_time"),
            "metrics": list(metrics),
            "latestOnly": latest_only
        })
        return _consolidate_metric_chunks(chunks)

    def get_metric_buckets(self, metrics, bucket, agent_filter=None, from_time=None, to_time=None):
        """
        Returns bucketed metrics for the selected agents.

        ``metrics`` is a list of qualified metric identifiers. Each identifier has the form
        ``<family>.<metric>`` and a single request may mix families. The accepted identifiers are:

        - reliability: ``reliability.uptime_pct``, ``reliability.uptime_tests_count``,
          ``reliability.uptime_successful_tests_count``, ``reliability.uptime_failed_tests_count``,
          ``reliability.interaction_errors``, ``reliability.interaction_error_rate_pct``,
          ``reliability.platform_side.interaction_errors``,
          ``reliability.platform_side.interaction_error_rate_pct``, ``reliability.platform_side.throttles``;
        - activity: ``activity.distinct_users_count``, ``activity.interactions``, ``activity.conversations``,
          ``activity.platform_side.interactions`` and ``activity.interactions_per_conversation`` statistics;
        - performance: ``performance.interaction_latency_ms`` and ``performance.conversation_total_latency_ms`` statistics,
          plus ``performance.platform_side.interaction_latency_ms_avg`` and ``performance.platform_side.interaction_latency_ms_p95``;
        - consumption: ``consumption.tokens.input``, ``consumption.tokens.output``, ``consumption.tokens.total``,
          ``consumption.tokens.input_cache_read``, ``consumption.tokens.input_cache_write``,
          ``consumption.cost.total``, plus ``consumption.tokens.input_per_interaction``,
          ``consumption.tokens.output_per_interaction``, ``consumption.tokens.total_per_interaction``,
          ``consumption.cost.per_interaction`` and ``consumption.cost.per_conversation`` statistics;
        - behavior: ``behavior.tool_calls``, plus ``behavior.tool_calls_per_interaction``
          and ``behavior.tool_calls_per_conversation`` statistics;
        - business KPI: ``business-kpi.<id>``.

        Request statistics with an explicit ``.avg`` or ``.percentile.95`` suffix, for example
        ``performance.conversation_total_latency_ms.percentile.95``. Platform-side latency values
        are supplied by the platform and do not support custom aggregation suffixes.
        Percentages, including uptime and error rates, range from 0 to 100; rates without samples are missing.

        Supported buckets are ``HOUR``, ``DAY``, ``WEEK`` and ``MONTH`` for all metric families.
        Business KPI buckets use the latest dataset value within each bucket.
        Activity counts distinct users and conversations within each bucket, not sums of smaller buckets.
        Conversation statistics use only interactions within the bucket and exclude missing conversation IDs.
        Conversation total latency is the sum of interaction durations, excluding time spent waiting for the user.
        Tool-call metrics describe recorded calls and include interactions with zero recorded calls in their population;
        missing trace data cannot be distinguished from no calls. Cost is an estimate: partially priced samples
        contribute known charges, while entirely unpriced samples are excluded from cost distributions.

        Bucket boundaries always use the global metrics timezone configured in Agent Management.
        Weekly boundaries also use the globally configured first day of the week. ``start`` and
        ``end`` are nevertheless absolute instants returned as UTC-aware datetimes.

        Returns :class:`dataikuapi.agentmanagement.metrics.BucketedMetricsFetchResults`.
        Its ``agents()`` lists represented agents as platform/agent tuples. Use
        ``agent_series(platform_name, agent_id)`` for a unified ``{columns, rows}`` table:
        columns are ``start``, ``end`` and the requested metrics in request order, and rows are
        joined on exact bucket boundaries and sorted chronologically. Missing values are ``None``.
        ``raw_agent_data(platform_name, agent_id)`` preserves the original grouped series and metadata.
        ``agent_single_series(platform_name, agent_id, metric_id)`` returns ``(start, end, value)`` tuples.
        ``agent_values_at_time(platform_name, agent_id, time)`` returns metric values in the bucket
        containing the instant, accepting epoch milliseconds or an aware datetime.

        Example::

            results = dam.get_metric_buckets(
                ["activity.interactions", "performance.conversation_total_latency_ms.avg"],
                "DAY", from_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
            for platform_name, agent_id in results.agents():
                table = results.agent_series(platform_name, agent_id)

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param AgentFilter agent_filter: optional agent selection
        :param int or datetime from_time: inclusive lower bound, as epoch milliseconds or a timezone-aware datetime
        :param int or datetime to_time: optional exclusive upper bound, as epoch milliseconds or a timezone-aware datetime;
            defaults to the current time
        :rtype: dataikuapi.agentmanagement.metrics.BucketedMetricsFetchResults
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        if from_time is None:
            raise ValueError("from_time is required")
        metrics = list(metrics)
        chunks = self._perform_json("POST", "/agent-management/agents/metrics/buckets", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": _to_timestamp_ms(from_time, "from_time"),
            "toTimestamp": _to_timestamp_ms(to_time, "to_time"),
            "metrics": metrics,
            "bucket": bucket
        })
        return BucketedMetricsFetchResults(_consolidate_metric_chunks(chunks), metrics)

    def list_operations(self, agent_filter=None, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None, current_only=False, as_type="listitems"):
        """
        Lists readable Agent Management operations matching the supplied filters.

        The result contains ``operations`` and ``has_more``, which indicates whether additional operations matched.

        :param AgentFilter agent_filter: filter selecting operations attached to matching agents
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: maximum number of returned operations, defaults to 1000, up to 10000
        :param boolean current_only: whether to return only queued or running operations
        :param str as_type: "listitems"/"listitem" returns OperationListItem entries; "objects"/"object" returns Operation handles
        :rtype: :class:`dataikuapi.agentmanagement.operations.OperationSearchResult`
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = {"agentFilter": agent_filter._as_dict() if agent_filter is not None else {}}
        body.update({
            name: value for name, value in (
                ("type", operation_types),
                ("status", statuses),
                ("trigger", triggers),
                ("fromTimestamp", from_timestamp),
                ("toTimestamp", to_timestamp),
                ("limit", limit),
                ("currentOnly", current_only),
            ) if value is not None
        })
        response = self._perform_json("POST", "/agent-management/operations/search", body=body)
        return OperationSearchResult(self, response, as_type)

    def search_triggered_alerts(self, agent_filter=None, states=None, severities=None, configuration_ids=None,
                                origins=None, from_timestamp=None, to_timestamp=None, limit=None, as_objects=True):
        """
        Searches readable Agent Management triggered alerts matching the supplied filters.

        If ``states`` is omitted or empty, only active, unacknowledged alerts are returned. Explicitly requesting ``OPEN`` also
        includes acknowledged alerts that remain open pending recovery.

        :param AgentFilter agent_filter: filter selecting triggered alerts attached to matching agents
        :param list states: triggered alert states, either ``OPEN`` or ``CLOSED``
        :param list severities: triggered alert severities, either ``WARNING`` or ``CRITICAL``
        :param list configuration_ids: alert configuration IDs, without an origin prefix
        :param list origins: configuration origins: ``GLOBAL``, ``INFRA``, ``AGENT``, or ``SCOPE``;
            combined with ``configuration_ids`` when both filters are supplied
        :param int from_timestamp: optional inclusive lower opening timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper opening timestamp bound, in milliseconds since the Unix epoch
        :param int limit: optional maximum number of returned alerts; defaults to 100 and is capped at 1000
        :param boolean as_objects: if True, the result contains :class:`dataikuapi.agentmanagement.alerting.Alert` handles, otherwise dictionaries
        :rtype: :class:`dataikuapi.agentmanagement.alerting.TriggeredAlertSearchResult`
        """
        if agent_filter is not None and not isinstance(agent_filter, AgentFilter):
            raise TypeError("agent_filter must be a AgentFilter")
        body = {"agentFilter": agent_filter._as_dict() if agent_filter is not None else {}}
        body.update({
            name: value for name, value in (
                ("state", states),
                ("severity", severities),
                ("configurationId", configuration_ids),
                ("origin", origins),
                ("fromTimestamp", from_timestamp),
                ("toTimestamp", to_timestamp),
                ("limit", limit),
            ) if value is not None
        })
        response = self._perform_json("POST", "/agent-management/alerts/search", body=body)
        return TriggeredAlertSearchResult(self, response, as_objects)

    def get_triggered_alert(self, alert_id):
        """
        Returns a handle to an Agent Management triggered alert.

        :param str alert_id: identifier of the alert
        :rtype: :class:`dataikuapi.agentmanagement.alerting.Alert`
        """
        return Alert(self, alert_id)

    # def list_topic_families(self, as_type="listitems"):
    #     """
    #     Lists the Agent Management topic families.
    #
    #     :param str as_type: "listitems"/"listitem" returns list items; "objects"/"object" returns handles of :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     :returns: a list - see ``as_type`` for more information
    #     :rtype: list
    #     """
    #     families = self._perform_json("GET", "/agent-management/settings/topic-families")
    #     return _format_list([TopicFamilyListItem(self, family) for family in families], as_type)
    #
    # def create_topic_family(self, definition):
    #     """
    #     Creates a topic family.
    #
    #     :param dict definition: topic family definition, including its ``id``
    #     :rtype: :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     """
    #     created = self._perform_json("POST", "/agent-management/settings/topic-families", body=definition)
    #     return TopicFamily(self, created["id"])
    #
    # def get_topic_family(self, family_id):
    #     """
    #     Returns a handle to a topic family.
    #
    #     :param str family_id: identifier of the topic family
    #     :rtype: :class:`dataikuapi.agentmanagement.topic_family.TopicFamily`
    #     """
    #     return TopicFamily(self, family_id)

    def get_risk_exposure(self):
        """
        Returns the aggregated Agent Management risk exposure.

        :rtype: :class:`dataikuapi.agentmanagement.risk.EstateRiskExposure`
        """
        exposure = self._perform_json("GET", "/agent-management/risk-exposure")["exposure"]
        return EstateRiskExposure(exposure)

    def get_risk_taxonomy(self):
        """
        Returns the Agent Management risk taxonomy settings.

        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskTaxonomySettings`
        """
        taxonomy = self._perform_json("GET", "/agent-management/risk-taxonomy")
        return RiskTaxonomySettings(self, taxonomy)

    def get_default_risk_taxonomy(self):
        """
        Returns the default Agent Management risk taxonomy settings.

        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskTaxonomySettings`
        """
        taxonomy = self._perform_json("GET", "/agent-management/risk-taxonomy/default")
        return RiskTaxonomySettings(self, taxonomy)

    def list_tags(self):
        """
        Lists tags used by Agent Management agents.

        :rtype: :class:`dataikuapi.agentmanagement_client.AgentManagementTags`
        """
        return AgentManagementTags(self, self._perform_json("GET", "/agent-management/tags"))



    def get_dssclient(self):
        """
        Creates a DSSClient to access the capabilities of the underlying DSS instance.

        :return: a DSSClient client
        :rtype: :class:`dataikuapi.DSSClient`
        """
        from .dssclient import DSSClient

        amc = DSSClient(self.host, api_key=self.api_key, internal_ticket=self.internal_ticket,
                                    extra_headers=self._session.headers, client_certificate=self._session.cert, jwt_bearer_token=self.jwt_bearer_token)

        # When the client was created from a ticket with encrypted RPC, verify is not just a boolean
        if self._session.verify is not None:
            amc._session.verify = self._session.verify

        return amc

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None, headers=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        http_res = self._session.request(
                method, "%s/dip/publicapi%s" % (self.host, path),
                params=params, data=body,
                files=files,
                stream=stream,
                headers=headers,
                verify=self._session.verify)
        handle_http_exception(http_res)
        return http_res

    def _perform_empty(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers)

    def _perform_text(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).text

    def _perform_json(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body, headers=headers).json()

    def _perform_raw(self, method, path, params=None, body=None, files=None, raw_body=None, headers=None):
        return self._perform_http(method, path, params=params, body=body, files=files, stream=True, raw_body=raw_body, headers=headers)


class AgentManagementTags(object):
    """
    A snapshot of tags used by Agent Management agents, iterable as tag objects.

    Do not create this directly, use :meth:`AgentManagementClient.list_tags`.
    """
    def __init__(self, client, tags):
        self._tags = [AgentManagementTag(client, tag) for tag in tags]

    def __iter__(self):
        return iter(self._tags)

    def __len__(self):
        return len(self._tags)

    def tag(self, name):
        """
        Returns a tag by its name.

        :param str name: tag name
        :rtype: :class:`AgentManagementTag`
        :raises KeyError: if the tag is not in this collection
        """
        for tag in self._tags:
            if tag.name == name:
                return tag
        raise KeyError(name)


class AgentManagementTag(object):
    """
    An Agent Management tag.

    Do not create this directly, use :meth:`AgentManagementTags.tag`.
    """
    def __init__(self, client, tag):
        self.client = client
        self._tag = dict(tag)

    def __repr__(self):
        return "<AgentManagementTag name=%r>" % self.name

    @property
    def name(self):
        """The tag name (read-only). Use :meth:`rename` to change it."""
        return self._tag["name"]

    @property
    def color(self):
        """The tag color. Changes are persisted by :meth:`save`."""
        return self._tag["color"]

    @color.setter
    def color(self, color):
        self._tag["color"] = color

    def save(self):
        """
        Saves the tag color.

        :returns: this tag with its saved definition
        :rtype: :class:`AgentManagementTag`
        """
        self._tag = self.client._perform_json("PUT", "/agent-management/tags/%s" % dku_quote_fn(self.name, safe=""),
                                              body={"color": self.color})
        return self

    def rename(self, new_name):
        """
        Renames the tag everywhere it is used and updates this object's definition.

        :param str new_name: new tag name
        :returns: this tag with its renamed definition
        :rtype: :class:`AgentManagementTag`
        """
        self._tag = self.client._perform_json("POST", "/agent-management/tags/%s/actions/rename" % dku_quote_fn(self.name, safe=""),
                                              body={"newName": new_name})
        return self

    def delete(self):
        """Deletes the tag everywhere it is used."""
        self.client._perform_empty("DELETE", "/agent-management/tags/%s" % dku_quote_fn(self.name, safe=""))
