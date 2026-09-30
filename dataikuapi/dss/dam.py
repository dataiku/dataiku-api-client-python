import copy
import json
import os
import sys

from .future import DSSFuture
from ..utils import CallableStr

if sys.version_info >= (3, 0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote


def _as_future(client, response):
    return DSSFuture(client, response.get("jobId"), response)


def _consolidate_metric_chunks(chunks):
    series = []
    for index, chunk in enumerate(chunks):
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


class DAMAgentFilter(object):
    """
    Agent filter accepted by agent search, operation search and metric retrieval methods.

    Values passed to the same ``with_*`` method are combined with OR.
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
        self.infra_types = None
        self.infra_ids = None
        self.discovery_statuses = None
        self.risk_sign_offs = None
        self.tags = None
        self.states = None

    def with_text_filter(self, text_filter):
        self.text_filter = text_filter
        return self

    def with_agent_ids(self, *agent_ids):
        self.agent_ids = list(agent_ids)
        return self

    def with_infra_types(self, *infra_types):
        self.infra_types = list(infra_types)
        return self

    def with_infra_ids(self, *infra_ids):
        self.infra_ids = list(infra_ids)
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

    def _as_dict(self):
        return {
            name: value for name, value in (
                ("textFilter", self.text_filter),
                ("agentId", self.agent_ids),
                ("infrastructureType", self.infra_types),
                ("infrastructureName", self.infra_ids),
                ("discoveryStatus", self.discovery_statuses),
                ("riskSignOff", self.risk_sign_offs),
                ("tags", self.tags),
                ("state", self.states),
            ) if value is not None
        }


class DAM(object):
    """
    Handle to interact with Dataiku Agent Management (DAM).

    Do not create this directly, use :meth:`dataikuapi.dss.DSSClient.get_dam`.
    """

    def __init__(self, client):
        self.client = client

    def get_settings(self):
        """
        Returns the global DAM settings.

        :rtype: :class:`DAMSettings`
        """
        settings = self.client._perform_json("GET", "/dam/settings")
        return DAMSettings(self.client, settings)

    def list_infras(self, as_objects=True):
        """
        Lists DAM infrastructures.

        :param boolean as_objects: if True, returns a list of :class:`DAMInfra`, else returns a list of dict
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        infras = self.client._perform_json("GET", "/dam/infras")
        if as_objects:
            return [DAMInfra(self.client, infra["id"]) for infra in infras]
        return infras

    def create_infra(self, infra_id, infra_type, display_name, configuration=None, default_project_key=None, create_data_storage_project=False,
                     permissions=None, default_agent_permissions=None):
        """
        Creates a DAM infrastructure and returns a handle to it.

        :param str infra_id: unique identifier of the infrastructure
        :param str infra_type: type of infrastructure
        :param str display_name: display name of the infrastructure
        :param dict configuration: provider-specific configuration
        :param str default_project_key: default DSS project used by the infrastructure
        :param boolean create_data_storage_project: whether DAM should create its data storage project
        :param list permissions: infrastructure permissions
        :param list default_agent_permissions: permissions initially assigned to detected agents
        :rtype: :class:`DAMInfra`
        """
        configuration = dict(configuration or {})
        configuration["type"] = infra_type
        body = {
            "id": infra_id,
            "displayName": display_name,
            "defaultProjectKey": default_project_key,
            "createDataStorageProject": create_data_storage_project,
            "configuration": configuration,
            "permissions": permissions or [],
            "defaultAgentPermissions": default_agent_permissions or []
        }
        created = self.client._perform_json("POST", "/dam/infras", body=body)
        return DAMInfra(self.client, created["id"])

    def get_infra(self, infra_id):
        """
        Returns a handle to a DAM infrastructure.

        :param str infra_id: identifier of the infrastructure
        :rtype: :class:`DAMInfra`
        """
        return DAMInfra(self.client, infra_id)

    def get_agent(self, infra_id, agent_id):
        """
        Returns a handle to a monitored agent.

        :param str infra_id: identifier of the infrastructure
        :param str agent_id: identifier of the agent
        :rtype: :class:`DAMAgent`
        """
        return DAMAgent(self.client, infra_id, agent_id)

    def search_agents(self, agent_filter=None):
        """
        Lists the readable agents matching a filter.

        Values of a facet are combined with OR, while different facets are combined with AND.

        :param DAMAgentFilter agent_filter: agent filter
        :returns: a dictionary containing ``agents`` and contextual ``facets`` counts
        :rtype: dict
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
        body = agent_filter._as_dict() if agent_filter is not None else {}
        return self.client._perform_json("POST", "/dam/agents/search", body=body)

    def get_metric_time_series(self, metrics, agent_filter=None, from_timestamp=None, to_timestamp=None, latest_only=False):
        """
        Returns stored, non-aggregated metric values for the selected agents.

        This method can only return metrics for which individual values are stored. Metrics which
        exist only as aggregates cannot be reconstructed as time-series values and must be queried
        with :meth:`get_metric_buckets` instead.

        ``metrics`` is a list of qualified metric identifiers. Each identifier includes its family,
        for example ``uptime.status``. The accepted identifiers are ``uptime.status``,
        ``uptime.responseTimeMs`` and ``business-kpi.<id>``, where ``<id>`` is the identifier of a
        business KPI assigned to the agent. Uptime and business KPI metrics can be requested in the
        same call. Examples of metrics which only exist as buckets include ``uptime.okCount``,
        ``uptime.totalCount``, ``uptime.uptime``, ``operational.*`` and ``usage.*``. This list is not
        exhaustive; any requested metric which is not stored as individual values is rejected.

        The response is a list of series. Each series has ``infrastructureName``, ``agentId``,
        ``columns`` and ``rows``. The first column is ``timestamp`` in epoch milliseconds; remaining
        columns are the qualified metrics. Rows are chronological compact JSON arrays aligned with
        ``columns``. Metrics sharing the same stored timeline are grouped; each business KPI has its
        own series. A selected agent with no value has an empty ``rows`` list.

        If ``latest_only`` is True, each series contains at most its latest available row. Metrics
        which share a timeline still share one row: this mode does not look for the latest non-null
        value of each metric separately. Both timestamps must be omitted in this mode. Otherwise
        ``from_timestamp`` is required and ``to_timestamp`` defaults to the current time.

        To get the latest available values, omit both timestamps and set ``latest_only=True``:

        .. code-block:: python

            latest_time_series = dam.get_metric_time_series(
                metrics=["uptime.status", "uptime.responseTimeMs"],
                latest_only=True
            )

        This example requests one metric from each family available as stored time-series values.
        The business KPI points are deliberately shifted by five minutes from the uptime points:

        .. code-block:: python

            time_series = dam.get_metric_time_series(
                metrics=["uptime.status", "business-kpi.customer-satisfaction"],
                from_timestamp=1767225600000,
                to_timestamp=1767312000000,
                agent_filter=DAMAgentFilter().with_agent_ids("support-agent")
            )

            # time_series == [
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "uptime.status"],
            #         "rows": [[1767229200000, "OK"], [1767232800000, "ERROR"]]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["timestamp", "business-kpi.customer-satisfaction"],
            #         "rows": [[1767229500000, 4.6], [1767233100000, 4.8]]
            #     }
            # ]

        :param list metrics: qualified metric identifiers, for example
            ``["uptime.status", "uptime.responseTimeMs", "business-kpi.revenue"]``
        :param DAMAgentFilter agent_filter: optional agent selection
        :param int from_timestamp: optional inclusive lower bound, in milliseconds since the Unix epoch;
            required when ``latest_only`` is False and forbidden when it is True
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch;
            defaults to the current time when ``from_timestamp`` is set and is forbidden when ``latest_only`` is True
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
        if latest_only and (from_timestamp is not None or to_timestamp is not None):
            raise ValueError("from_timestamp and to_timestamp must be omitted when latest_only is True")
        if not latest_only and from_timestamp is None:
            raise ValueError("from_timestamp is required when latest_only is False")
        chunks = self.client._perform_json("POST", "/dam/agents/metrics/time-series", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "metrics": list(metrics),
            "latestOnly": latest_only
        })
        return _consolidate_metric_chunks(chunks)

    def get_metric_buckets(self, metrics, bucket, agent_filter=None, from_timestamp=None, to_timestamp=None):
        """
        Returns bucketed metrics for the selected agents.

        ``metrics`` is a list of qualified metric identifiers. Each identifier has the form
        ``<family>.<metric>`` and a single request may mix families. The accepted identifiers are:

        - uptime: ``uptime.okCount``, ``uptime.totalCount``, ``uptime.uptime``;
        - operational: ``operational.interactionQueriesCount``,
          ``operational.interactionErrorsCount``, ``operational.platformQueriesCount``,
          ``operational.platformErrorsCount``, ``operational.throttlesCount``,
          ``operational.inputTokens``, ``operational.outputTokens``, ``operational.totalTokens``,
          ``operational.interactionAvgLatencyMs``, ``operational.interactionP95LatencyMs``,
          ``operational.platformAvgLatencyMs`` and ``operational.platformP95LatencyMs``;
        - usage: ``usage.activeUsers`` and ``usage.conversations``;
        - business KPI: ``business-kpi.<id>``.

        Supported buckets are ``HOUR``, ``DAY``, ``WEEK`` and ``MONTH``. Uptime supports up to
        ``WEEK``; usage starts at ``DAY``; business KPIs support ``HOUR`` and ``DAY``; operational
        metrics support all four. Every requested metric must support the selected bucket.
        For usage metrics, ``WEEK`` and ``MONTH`` are rolling 7-day and 30-day windows ending on
        each returned display day, so successive intervals overlap.

        Bucket boundaries always use the global metrics timezone configured in Agent Management.
        Weekly boundaries also use the globally configured first day of the week. ``start`` and
        ``end`` are nevertheless absolute instants expressed as Unix epoch milliseconds.

        The response is a list of series. Each series has ``infrastructureName``, ``agentId``,
        ``columns`` and ``rows``. The first columns are ``start`` and ``end`` in epoch milliseconds;
        remaining columns are the qualified metrics. Rows are chronological compact JSON arrays
        aligned with ``columns`` and describe half-open intervals ``[start, end)``. Compatible
        metrics share a series; different families may produce separate series and business KPIs
        use one series per KPI. Missing values are returned as ``None`` and a series without values
        has an empty ``rows`` list.

        This ``DAY`` example covers every bucketed metric family, with all three uptime metrics and
        both usage metrics. The families deliberately have values on slightly different days:

        .. code-block:: python

            buckets = dam.get_metric_buckets(
                metrics=[
                    "uptime.okCount",
                    "uptime.totalCount",
                    "uptime.uptime",
                    "operational.totalTokens",
                    "usage.activeUsers",
                    "usage.conversations",
                    "business-kpi.customer-satisfaction"
                ],
                bucket="DAY",
                from_timestamp=1767222000000,
                to_timestamp=1767481200000,
                agent_filter=DAMAgentFilter().with_agent_ids("support-agent")
            )

            # buckets == [
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": [
            #             "start", "end", "uptime.okCount", "uptime.totalCount", "uptime.uptime"
            #         ],
            #         "rows": [
            #             [1767222000000, 1767308400000, 287, 288, 0.9965277778],
            #             [1767308400000, 1767394800000, 288, 288, 1.0]
            #         ]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["start", "end", "operational.totalTokens"],
            #         "rows": [
            #             [1767222000000, 1767308400000, 12420],
            #             [1767394800000, 1767481200000, 13010]
            #         ]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["start", "end", "usage.activeUsers", "usage.conversations"],
            #         "rows": [
            #             [1767308400000, 1767394800000, 318, 942],
            #             [1767394800000, 1767481200000, 327, 980]
            #         ]
            #     },
            #     {
            #         "infrastructureName": "production",
            #         "agentId": "support-agent",
            #         "columns": ["start", "end", "business-kpi.customer-satisfaction"],
            #         "rows": [[1767308400000, 1767394800000, 4.7]]
            #     }
            # ]

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param DAMAgentFilter agent_filter: optional agent selection
        :param int from_timestamp: inclusive lower bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch;
            defaults to the current time
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
        if from_timestamp is None:
            raise ValueError("from_timestamp is required")
        chunks = self.client._perform_json("POST", "/dam/agents/metrics/buckets", body={
            "agentFilter": agent_filter._as_dict() if agent_filter is not None else {},
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "metrics": list(metrics),
            "bucket": bucket
        })
        return _consolidate_metric_chunks(chunks)

    def list_operations(self, agent_filter=None, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None, current_only=False, as_objects=True):
        """
        Lists readable DAM operations matching the supplied filters.

        :param DAMAgentFilter agent_filter: filter selecting operations attached to matching agents
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: optional maximum number of returned operations
        :param boolean current_only: whether to return only queued or running operations
        :param boolean as_objects: if True, returns a list of :class:`DAMOperation`, else returns a list of dict
        :rtype: list
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
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
        operations = self.client._perform_json("POST", "/dam/operations/search", body=body)
        if as_objects:
            return [DAMOperation(self.client, operation["infraId"], operation["id"], operation.get("agentId"))
                    for operation in operations]
        return operations

    def list_business_kpis(self, as_objects=True):
        """
        Lists the DAM business KPI definitions.

        :param boolean as_objects: if True, returns a list of :class:`DAMBusinessKPI`, else returns a list of dict
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        kpis = self.client._perform_json("GET", "/dam/settings/business-kpis")
        if as_objects:
            return [DAMBusinessKPI(self.client, kpi["id"]) for kpi in kpis]
        return kpis

    def create_business_kpi(self, definition):
        """
        Creates a business KPI definition.

        :param dict definition: business KPI definition, including its ``id``
        :rtype: :class:`DAMBusinessKPI`
        """
        created = self.client._perform_json("POST", "/dam/settings/business-kpis", body=definition)
        return DAMBusinessKPI(self.client, created["id"])

    def get_business_kpi(self, kpi_id):
        """
        Returns a handle to a business KPI definition.

        :param str kpi_id: identifier of the business KPI
        :rtype: :class:`DAMBusinessKPI`
        """
        return DAMBusinessKPI(self.client, kpi_id)

    def list_topic_families(self, as_objects=True):
        """
        Lists the DAM topic families.

        :param boolean as_objects: if True, returns a list of :class:`DAMTopicFamily`, else returns a list of dict
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        families = self.client._perform_json("GET", "/dam/settings/topic-families")
        if as_objects:
            return [DAMTopicFamily(self.client, family["id"]) for family in families]
        return families

    def create_topic_family(self, definition):
        """
        Creates a topic family.

        :param dict definition: topic family definition, including its ``id``
        :rtype: :class:`DAMTopicFamily`
        """
        created = self.client._perform_json("POST", "/dam/settings/topic-families", body=definition)
        return DAMTopicFamily(self.client, created["id"])

    def get_topic_family(self, family_id):
        """
        Returns a handle to a topic family.

        :param str family_id: identifier of the topic family
        :rtype: :class:`DAMTopicFamily`
        """
        return DAMTopicFamily(self.client, family_id)

    def get_risk_exposure(self):
        """
        Returns the aggregated DAM risk exposure.

        :rtype: dict
        """
        return self.client._perform_json("GET", "/dam/risk-exposure")["exposure"]

    def get_risk_taxonomy(self):
        """
        Returns the DAM risk taxonomy settings.

        :rtype: :class:`DAMRiskTaxonomySettings`
        """
        taxonomy = self.client._perform_json("GET", "/dam/risk-taxonomy")
        return DAMRiskTaxonomySettings(self.client, taxonomy)

    def get_default_risk_taxonomy(self):
        """
        Returns the default DAM risk taxonomy.

        :rtype: dict
        """
        return self.client._perform_json("GET", "/dam/risk-taxonomy/default")["taxonomy"]

    def list_tags(self):
        """
        Lists tags used by DAM agents.

        :rtype: list of dict
        """
        return self.client._perform_json("GET", "/dam/tags")

    def update_tag(self, name, color):
        """
        Updates the color of an existing DAM tag.

        :param str name: existing tag name
        :param str color: tag color
        :returns: the updated tag definition
        :rtype: dict
        """
        return self.client._perform_json("PUT", "/dam/tags/%s" % dku_quote_fn(name, safe=""), body={"color": color})

    def rename_tag(self, name, new_name):
        """
        Renames a tag everywhere it is used.

        :param str name: current tag name
        :param str new_name: new tag name
        :returns: the renamed tag definition
        :rtype: dict
        """
        return self.client._perform_json("POST", "/dam/tags/%s/actions/rename" % dku_quote_fn(name, safe=""),
                                         body={"newName": new_name})

    def delete_tag(self, name):
        """
        Deletes a tag everywhere it is used.

        :param str name: tag name
        """
        self.client._perform_empty("DELETE", "/dam/tags/%s" % dku_quote_fn(name, safe=""))


class DAMSettings(object):
    """
    The global DAM settings.

    Do not create this directly, use :meth:`DAM.get_settings`.
    """
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw DAM settings.

        :rtype: dict
        """
        return self.settings

    def save(self, confirm_metric_reset=False):
        """
        Saves the global DAM settings.

        :param boolean confirm_metric_reset: whether to confirm deletion of metrics made incompatible by the settings change
        :returns: the saved settings
        :rtype: :class:`DAMSettings`
        """
        body = dict(self.settings)
        body["expectedRevision"] = self.settings.get("revision")
        body["confirmMetricReset"] = confirm_metric_reset
        self.settings = self.client._perform_json("PUT", "/dam/settings", body=body,
                                                  headers={"If-Match": self.settings.get("revision", "")})
        return self


class DAMInfra(object):
    """
    A DAM infrastructure.

    Do not create this directly, use :meth:`DAM.get_infra`.
    """

    def __init__(self, client, infra_id):
        self.client = client
        self.infra_id = infra_id

    @property
    def id(self):
        return CallableStr(self.infra_id)

    def __str__(self):
        return CallableStr(self.infra_id)

    def get_status(self):
        """
        Returns status information about this infrastructure.

        :rtype: :class:`DAMInfraStatus`
        """
        status = self.client._perform_json("GET", self._path())
        return DAMInfraStatus(self.client, self.infra_id, status)

    def get_settings(self):
        """
        Returns the settings of this infrastructure.

        :rtype: :class:`DAMInfraSettings`
        """
        settings = self.client._perform_json("GET", self._path("settings"))
        return DAMInfraSettings(self.client, self.infra_id, settings)

    def delete(self, force=False):
        """
        Deletes the infrastructure.

        :param boolean force: also delete the agents still attached to the infrastructure
        """
        self.client._perform_empty("DELETE", self._path(), params={"force": force})

    def list_agents(self, as_objects=True):
        """
        Lists agents on this infrastructure.

        :param boolean as_objects: if True, returns a list of :class:`DAMAgent`, else returns a list of dict
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        agents = DAM(self.client).search_agents(agent_filter=DAMAgentFilter().with_infra_ids(self.infra_id))["agents"]
        if as_objects:
            return [DAMAgent(self.client, agent["infraId"], agent["id"]) for agent in agents]
        return agents

    def get_metric_time_series(self, metrics, agent_filter=None, from_timestamp=None, to_timestamp=None, latest_only=False):
        """
        Returns stored time-series values for agents on this infrastructure.

        ``metrics`` uses the qualified identifiers and the response uses the compact tabular format
        documented by :meth:`DAM.get_metric_time_series`. The infrastructure scope is added to the
        optional ``agent_filter`` and the same global REST endpoint is used.
        Set ``latest_only=True`` and omit both timestamps to get the latest available values.

        :param list metrics: qualified metric identifiers
        :param DAMAgentFilter agent_filter: optional additional agent selection
        :param int from_timestamp: optional inclusive lower bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else DAMAgentFilter()
        scoped_filter.with_infra_ids(self.infra_id)
        return DAM(self.client).get_metric_time_series(metrics, agent_filter=scoped_filter,
                                                       from_timestamp=from_timestamp, to_timestamp=to_timestamp,
                                                       latest_only=latest_only)

    def get_metric_buckets(self, metrics, bucket, agent_filter=None, from_timestamp=None, to_timestamp=None):
        """
        Returns bucketed metrics for agents on this infrastructure.

        ``metrics`` uses the qualified identifiers, bucket compatibility rules and compact tabular
        response documented by :meth:`DAM.get_metric_buckets`. The infrastructure scope is added to
        the optional ``agent_filter`` and the same global REST endpoint is used.

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param DAMAgentFilter agent_filter: optional additional agent selection
        :param int from_timestamp: optional inclusive lower bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch
        :rtype: list of dict
        """
        if agent_filter is not None and not isinstance(agent_filter, DAMAgentFilter):
            raise TypeError("agent_filter must be a DAMAgentFilter")
        scoped_filter = copy.deepcopy(agent_filter) if agent_filter is not None else DAMAgentFilter()
        scoped_filter.with_infra_ids(self.infra_id)
        return DAM(self.client).get_metric_buckets(metrics, bucket, agent_filter=scoped_filter,
                                                   from_timestamp=from_timestamp, to_timestamp=to_timestamp)

    def create_agent(self, agent_id, display_name=None, description=None, tags=None, configuration=None, permissions=None):
        """
        Creates an agent manually and returns a handle to it.

        :param str agent_id: unique identifier of the agent
        :param str display_name: display name of the agent
        :param str description: agent description
        :param list tags: tags assigned to the agent
        :param dict configuration: provider-specific configuration
        :param list permissions: agent permissions
        :rtype: :class:`DAMAgent`
        """
        body = {
            "id": agent_id,
            "displayName": display_name,
            "description": description,
            "tags": tags or [],
            "configuration": configuration or {},
            "permissions": permissions or []
        }
        created = self.client._perform_json("POST", self._path("agents"), body=body)
        return DAMAgent(self.client, self.infra_id, created["id"])

    def get_agent(self, agent_id):
        """
        Returns a handle to an agent on this infrastructure.

        :param str agent_id: identifier of the agent
        :rtype: :class:`DAMAgent`
        """
        return DAMAgent(self.client, self.infra_id, agent_id)

    def scan(self):
        """
        Starts an infrastructure scan.

        Usage example:

        .. code-block:: python

            infra = client.get_dam().get_infra("my-infra")
            future = infra.scan()
            scan_result = future.wait_for_result()

        :returns: a future tracking the scan
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        response = self.client._perform_json("POST", self._path("actions/scan"))
        return _as_future(self.client, response)

    def run_uptime_tests(self, agent_ids=None):
        """
        Starts uptime tests for this infrastructure.

        Usage example:

        .. code-block:: python

            infra = client.get_dam().get_infra("my-infra")
            future = infra.run_uptime_tests(["my-agent"])
            uptime_test_results = future.wait_for_result()

        :param list agent_ids: agents to test, or None to test all eligible agents
        :returns: a future tracking the uptime tests
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        body = None if agent_ids is None else {"agentIds": agent_ids}
        response = self.client._perform_json("POST", self._path("actions/run-uptime-tests"), body=body)
        return _as_future(self.client, response)

    def list_operations(self, as_objects=True, current_only=False, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None):
        """
        Lists operations launched for this infrastructure.

        :param boolean as_objects: if True, returns a list of :class:`DAMOperation`, else returns a list of dict
        :param boolean current_only: whether to return only queued or running operations
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: optional maximum number of returned operations
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        return DAM(self.client).list_operations(
            agent_filter=DAMAgentFilter().with_infra_ids(self.infra_id),
            operation_types=operation_types,
            statuses=statuses,
            triggers=triggers,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            current_only=current_only,
            as_objects=as_objects)

    def get_operation(self, operation_id):
        """
        Returns a handle to an infrastructure operation.

        :param str operation_id: identifier of the operation
        :rtype: :class:`DAMOperation`
        """
        return DAMOperation(self.client, self.infra_id, operation_id)

    def _path(self, suffix=None):
        path = "/dam/infras/%s" % dku_quote_fn(self.infra_id, safe="")
        if suffix is not None:
            path += "/" + suffix
        return path


class DAMInfraStatus(object):
    """
    The status of a DAM infrastructure.

    Do not create this directly, use :meth:`DAMInfra.get_status`.
    """
    def __init__(self, client, infra_id, status):
        self.client = client
        self.infra_id = infra_id
        self.status = status

    def get_raw(self):
        """
        Returns the raw status of this infrastructure.

        :rtype: dict
        """
        return self.status


class DAMInfraSettings(object):
    """
    The settings of a DAM infrastructure.

    Do not create this directly, use :meth:`DAMInfra.get_settings`.
    """
    def __init__(self, client, infra_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw settings of this infrastructure.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Saves the settings of this infrastructure.

        :returns: the saved settings
        :rtype: :class:`DAMInfraSettings`
        """
        body = dict(self.settings)
        body["expectedRevision"] = self.settings.get("revision")
        path = "/dam/infras/%s/settings" % dku_quote_fn(self.infra_id, safe="")
        self.settings = self.client._perform_json("PUT", path, body=body,
                                                  headers={"If-Match": self.settings.get("revision", "")})
        return self


class DAMAgent(object):
    """
    A monitored DAM agent.

    Do not create this directly, use :meth:`DAMInfra.get_agent`.
    """

    def __init__(self, client, infra_id, agent_id):
        self.client = client
        self.infra_id = infra_id
        self.agent_id = agent_id

    @property
    def id(self):
        return CallableStr(self.agent_id)

    def __str__(self):
        return CallableStr(self.agent_id)

    def get_status(self):
        """
        Returns status information about this agent.

        :rtype: :class:`DAMAgentStatus`
        """
        light = self.client._perform_json("GET", self._path())
        heavy = self.client._perform_json("GET", self._path("status"))
        return DAMAgentStatus(self.client, self.infra_id, self.agent_id, light, heavy)

    def get_settings(self):
        """
        Returns the settings of this agent.

        :rtype: :class:`DAMAgentSettings`
        """
        settings = self.client._perform_json("GET", self._path("settings"))
        return DAMAgentSettings(self.client, self.infra_id, self.agent_id, settings)

    def delete(self):
        """Deletes the agent."""
        self.client._perform_empty("DELETE", self._path())

    def get_history(self, from_timestamp=None, to_timestamp=None, field_query=None, event_types=None, triggers=None):
        """
        Returns the agent change history.

        The server streams matching events and this method returns them as a single list.

        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional inclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param str field_query: optional case-insensitive search in the labels of changed fields,
            for example ``permissions`` or ``scheduled log fetch``. This does not search field
            values. Events without a matching changed field are omitted and only matching changes
            are included in returned events.
        :param list event_types: optional event types among ``CREATED``, ``UPDATED`` and ``DELETED``
        :param list triggers: optional triggers among ``EXPLICIT_REQUEST`` and ``SCAN``
        :rtype: list of dict
        """
        return self.client._perform_json("POST", self._path("history/search"), body={
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "eventTypes": list(event_types) if event_types is not None else [],
            "triggers": list(triggers) if triggers is not None else [],
            "fieldQuery": field_query
        })

    def get_metrics(self, family="performance", timezone=None):
        """
        Returns a family of computed metrics for the agent.

        :param str family: ``performance``, ``operational``, ``usage`` or ``business-kpi``
        :param str timezone: timezone used to present the metrics
        :returns: the metric data
        :rtype: dict
        """
        response = self.client._perform_json("GET", self._path("metrics"), params={"family": family, "timezone": timezone})
        return response.get("data")

    def get_metric_time_series(self, metrics, from_timestamp=None, to_timestamp=None, latest_only=False):
        """
        Returns stored time-series values for this agent.

        ``metrics`` uses the qualified identifiers and compact tabular response documented by
        :meth:`DAM.get_metric_time_series`. The agent is selected through the global endpoint.
        Set ``latest_only=True`` and omit both timestamps to get the latest available values.

        :param list metrics: qualified metric identifiers
        :param int from_timestamp: optional inclusive lower bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch
        :param boolean latest_only: return at most the latest row of each logical series
        :rtype: list of dict
        """
        agent_filter = DAMAgentFilter().with_infra_ids(self.infra_id).with_agent_ids(self.agent_id)
        return DAM(self.client).get_metric_time_series(metrics, agent_filter=agent_filter,
                                                       from_timestamp=from_timestamp, to_timestamp=to_timestamp,
                                                       latest_only=latest_only)

    def get_metric_buckets(self, metrics, bucket, from_timestamp=None, to_timestamp=None):
        """
        Returns bucketed metrics for this agent.

        ``metrics`` uses the qualified identifiers, bucket compatibility rules and compact tabular
        response documented by :meth:`DAM.get_metric_buckets`. The agent is selected through the
        global endpoint.

        :param list metrics: qualified metric identifiers
        :param str bucket: ``HOUR``, ``DAY``, ``WEEK`` or ``MONTH``
        :param int from_timestamp: optional inclusive lower bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper bound, in milliseconds since the Unix epoch
        :rtype: list of dict
        """
        agent_filter = DAMAgentFilter().with_infra_ids(self.infra_id).with_agent_ids(self.agent_id)
        return DAM(self.client).get_metric_buckets(metrics, bucket, agent_filter=agent_filter,
                                                   from_timestamp=from_timestamp, to_timestamp=to_timestamp)

    def get_uptime_results(self, from_time=None, to_time=None):
        """
        Returns the agent uptime test results.

        :param str from_time: optional lower time bound
        :param str to_time: optional upper time bound
        :rtype: list of dict
        """
        return self.client._perform_json("GET", self._path("uptime-results"), params={"from": from_time, "to": to_time})

    def get_topic_modeling(self, periodicity="QUARTER"):
        """
        Returns topic-modeling results for the agent.

        :param str periodicity: aggregation periodicity
        :rtype: dict
        """
        response = self.client._perform_json("GET", self._path("topic-modeling"), params={"periodicity": periodicity})
        return response.get("result")

    def validate_log_fetch(self, configuration=None):
        """
        Validates the persisted log-fetch configuration, or the supplied agent configuration, without saving it.

        :param dict configuration: optional agent configuration to validate
        :returns: True when the configuration is valid
        :rtype: boolean
        """
        body = None if configuration is None else {"configuration": configuration}
        response = self.client._perform_json("POST", self._path("log-fetch/actions/validate"), body=body)
        return response.get("valid", False)

    def fetch_logs(self):
        """
        Starts fetching execution logs for the agent.

        Usage example:

        .. code-block:: python

            agent = client.get_dam().get_agent("my-infra", "my-agent")
            future = agent.fetch_logs()
            log_fetch_result = future.wait_for_result()

        :returns: a future tracking the log fetch
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        response = self.client._perform_json("POST", self._path("actions/fetch-logs"))
        return _as_future(self.client, response)

    def fetch_platform_operational_metrics(self):
        """
        Starts fetching platform operational metrics for the agent.

        Usage example:

        .. code-block:: python

            agent = client.get_dam().get_agent("my-infra", "my-agent")
            future = agent.fetch_platform_operational_metrics()
            metrics_fetch_result = future.wait_for_result()

        :returns: a future tracking the platform operational metrics fetch
        :rtype: :class:`~dataikuapi.dss.future.DSSFuture`
        """
        response = self.client._perform_json("POST", self._path("actions/fetch-platform-operational-metrics"))
        return _as_future(self.client, response)

    def setup_log_fetch_dataset(self, project_key, dataset_name, connection_name, partitioning_time_dimension="NONE"):
        """
        Creates or configures the managed dataset used to store fetched logs.

        :param str project_key: project in which to create the dataset
        :param str dataset_name: name of the dataset
        :param str connection_name: connection used by the managed dataset
        :param str partitioning_time_dimension: time partitioning granularity
        :returns: identifiers of the configured dataset
        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("actions/setup-log-fetch-dataset"), body={
            "projectKey": project_key,
            "datasetName": dataset_name,
            "connectionName": connection_name,
            "partitioningTimeDimension": partitioning_time_dimension
        }).get("result")

    def create_external_agent(self, project_key, name):
        """
        Creates a DSS external agent backed by this monitored agent.

        :param str project_key: project in which to create the external agent
        :param str name: name of the external agent
        :returns: a reference to the created DSS object
        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("actions/create-external-agent"), body={"projectKey": project_key, "name": name})

    def list_operations(self, as_objects=True, current_only=False, operation_types=None, statuses=None, triggers=None,
                        from_timestamp=None, to_timestamp=None, limit=None):
        """
        Lists operations launched for this agent.

        :param boolean as_objects: if True, returns a list of :class:`DAMOperation`, else returns a list of dict
        :param boolean current_only: whether to return only queued or running operations
        :param list operation_types: operation types
        :param list statuses: operation statuses
        :param list triggers: operation triggers
        :param int from_timestamp: optional inclusive lower timestamp bound, in milliseconds since the Unix epoch
        :param int to_timestamp: optional exclusive upper timestamp bound, in milliseconds since the Unix epoch
        :param int limit: optional maximum number of returned operations
        :returns: a list - see ``as_objects`` for more information
        :rtype: list
        """
        return DAM(self.client).list_operations(
            agent_filter=DAMAgentFilter().with_infra_ids(self.infra_id).with_agent_ids(self.agent_id),
            operation_types=operation_types,
            statuses=statuses,
            triggers=triggers,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            current_only=current_only,
            as_objects=as_objects)

    def get_operation(self, operation_id):
        """
        Returns a handle to an operation for this agent.

        :param str operation_id: identifier of the operation
        :rtype: :class:`DAMOperation`
        """
        return DAMOperation(self.client, self.infra_id, operation_id, self.agent_id)

    def get_risk_assessment(self):
        """
        Returns the risk assessment settings of this agent.

        :rtype: :class:`DAMRiskAssessmentSettings`
        """
        assessment = self.client._perform_json("GET", self._path("risk-assessment"))
        return DAMRiskAssessmentSettings(self.client, self.infra_id, self.agent_id, assessment)

    def sign_off_risk_assessment(self):
        """
        Signs off the current risk assessment.

        :returns: the updated risk assessment
        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("risk-assessment/sign-off"))

    def remove_risk_sign_off(self):
        """
        Removes the sign-off from the current risk assessment.

        :returns: the updated risk assessment
        :rtype: dict
        """
        return self.client._perform_json("DELETE", self._path("risk-assessment/sign-off"))

    def get_risk_evidence_content(self, evidence_id):
        """
        Downloads the content of a document attached as risk evidence.

        :param str evidence_id: identifier of the evidence
        :rtype: :class:`requests.Response`
        """
        return self.client._perform_raw("GET", self._path("risk-assessment/evidences/%s/content" % dku_quote_fn(evidence_id, safe="")))

    def _path(self, suffix=None):
        path = "/dam/infras/%s/agents/%s" % (
            dku_quote_fn(self.infra_id, safe=""),
            dku_quote_fn(self.agent_id, safe=""))
        if suffix is not None:
            path += "/" + suffix
        return path


class DAMAgentStatus(object):
    """
    The status of a monitored agent.

    Do not create this directly, use :meth:`DAMAgent.get_status`.
    """
    def __init__(self, client, infra_id, agent_id, light, heavy):
        self.client = client
        self.infra_id = infra_id
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


class DAMAgentSettings(object):
    """
    The settings of a monitored agent.

    Do not create this directly, use :meth:`DAMAgent.get_settings`.
    """
    def __init__(self, client, infra_id, agent_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.agent_id = agent_id
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw settings of this agent.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Saves the settings of this agent.

        :returns: the saved settings
        :rtype: :class:`DAMAgentSettings`
        """
        body = dict(self.settings)
        body["expectedRevision"] = self.settings.get("revision")
        path = "/dam/infras/%s/agents/%s/settings" % (dku_quote_fn(self.infra_id, safe=""), dku_quote_fn(self.agent_id, safe=""))
        self.settings = self.client._perform_json("PUT", path, body=body,
                                                  headers={"If-Match": self.settings.get("revision", "")})
        return self


class DAMBusinessKPI(object):
    """
    A DAM business KPI definition.

    Do not create this directly, use :meth:`DAM.get_business_kpi`.
    """
    def __init__(self, client, kpi_id):
        self.client = client
        self.kpi_id = kpi_id

    @property
    def id(self):
        return CallableStr(self.kpi_id)

    def get_definition(self):
        """
        Returns the definition of this business KPI.

        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def set_definition(self, definition):
        """
        Replaces the business KPI definition.

        :param dict definition: new definition
        :returns: the saved definition
        :rtype: dict
        """
        return self.client._perform_json("PUT", self._path(), body=definition)

    def delete(self):
        """Deletes the business KPI definition."""
        self.client._perform_empty("DELETE", self._path())

    def _path(self):
        return "/dam/settings/business-kpis/%s" % dku_quote_fn(self.kpi_id, safe="")


class DAMTopicFamily(object):
    """
    A DAM topic family.

    Do not create this directly, use :meth:`DAM.get_topic_family`.
    """
    def __init__(self, client, family_id):
        self.client = client
        self.family_id = family_id

    @property
    def id(self):
        return CallableStr(self.family_id)

    def get_definition(self):
        """
        Returns the definition of this topic family.

        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def set_definition(self, definition):
        """
        Replaces the topic family definition.

        :param dict definition: new definition
        :returns: the saved definition
        :rtype: dict
        """
        return self.client._perform_json("PUT", self._path(), body=definition)

    def delete(self):
        """Deletes the topic family."""
        self.client._perform_empty("DELETE", self._path())

    def _path(self):
        return "/dam/settings/topic-families/%s" % dku_quote_fn(self.family_id, safe="")


class DAMOperation(object):
    """
    A DAM asynchronous operation.

    Do not create this directly, use :meth:`DAMInfra.get_operation` or :meth:`DAMAgent.get_operation`.
    """
    def __init__(self, client, infra_id, operation_id, agent_id=None):
        self.client = client
        self.infra_id = infra_id
        self.operation_id = operation_id
        self.agent_id = agent_id

    @property
    def id(self):
        return CallableStr(self.operation_id)

    def get_status(self):
        """
        Returns status information about this operation.

        :rtype: :class:`DAMOperationStatus`
        """
        status = self.client._perform_json("GET", self._path())
        return DAMOperationStatus(self.client, self.infra_id, self.operation_id, status)

    def get_result(self):
        """
        Returns the completed operation result.

        :rtype: dict
        """
        return self.client._perform_json("GET", self._path("result")).get("result")

    def abort(self):
        """Requests cancellation of the operation."""
        self.client._perform_empty("POST", self._path("actions/abort"))

    def _path(self, suffix=None):
        if self.agent_id is None:
            path = "/dam/infras/%s/operations/%s" % (
                dku_quote_fn(self.infra_id, safe=""),
                dku_quote_fn(self.operation_id, safe=""))
        else:
            path = "/dam/infras/%s/agents/%s/operations/%s" % (
                dku_quote_fn(self.infra_id, safe=""),
                dku_quote_fn(self.agent_id, safe=""),
                dku_quote_fn(self.operation_id, safe=""))
        if suffix is not None:
            path += "/" + suffix
        return path


class DAMOperationStatus(object):
    """
    The status of a DAM asynchronous operation.

    Do not create this directly, use :meth:`DAMOperation.get_status`.
    """
    def __init__(self, client, infra_id, operation_id, status):
        self.client = client
        self.infra_id = infra_id
        self.operation_id = operation_id
        self.status = status

    def get_raw(self):
        """
        Returns the raw status of this operation.

        :rtype: dict
        """
        return self.status


class DAMRiskTaxonomySettings(object):
    """
    The DAM risk taxonomy settings.

    Do not create this directly, use :meth:`DAM.get_risk_taxonomy`.
    """
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw risk taxonomy settings.

        :rtype: dict
        """
        return self.settings

    def compute_replacement_impact(self):
        """
        Computes the impact of replacing the current risk taxonomy.

        :rtype: dict
        """
        return self.client._perform_json("POST", "/dam/risk-taxonomy/actions/compute-replacement-impact",
                                         body={"taxonomy": self.settings["taxonomy"]})

    def save(self, impact):
        """
        Saves the DAM risk taxonomy.

        :param dict impact: impact returned by :meth:`compute_replacement_impact`
        :returns: the saved settings
        :rtype: :class:`DAMRiskTaxonomySettings`
        """
        if impact is None or impact.get("fingerprint") is None:
            raise ValueError("A replacement impact returned by compute_replacement_impact() is required")
        body = {
            "expectedRevision": self.settings.get("revision"),
            "expectedImpactFingerprint": impact["fingerprint"],
            "taxonomy": self.settings["taxonomy"]
        }
        self.settings = self.client._perform_json("PUT", "/dam/risk-taxonomy", body=body,
                                                  headers={"If-Match": self.settings.get("revision", "")})
        return self


class DAMRiskAssessmentSettings(object):
    """
    The risk assessment settings of a monitored agent.

    Do not create this directly, use :meth:`DAMAgent.get_risk_assessment`.
    """
    def __init__(self, client, infra_id, agent_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.agent_id = agent_id
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw risk assessment settings.

        :rtype: dict
        """
        return self.settings

    def save(self, documents=None):
        """
        Saves the risk assessment and optionally uploads document evidence.

        :param dict documents: optional mapping of evidence identifiers to file-like objects or ``(filename, file_object)`` tuples
        :returns: the saved settings
        :rtype: :class:`DAMRiskAssessmentSettings`
        """
        files = [
            ("assessment", (None, json.dumps(self.settings["assessment"]))),
            ("expectedRevision", (None, self.settings.get("revision", "")))
        ]
        for evidence_id, document in (documents or {}).items():
            if isinstance(document, tuple):
                filename, stream = document
            else:
                stream = document
                filename = os.path.basename(getattr(stream, "name", evidence_id))
            files.append(("documentEvidenceIds", (None, evidence_id)))
            files.append(("documents", (filename, stream)))
        path = "/dam/infras/%s/agents/%s/risk-assessment" % (dku_quote_fn(self.infra_id, safe=""), dku_quote_fn(self.agent_id, safe=""))
        self.settings = self.client._perform_json("PUT", path, files=files,
                                                  headers={"If-Match": self.settings.get("revision", "")})
        return self
