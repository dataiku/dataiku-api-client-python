from copy import deepcopy

from ._utils import dku_quote_fn, _format_list


class AlertConfigurationBuilder(object):
    """
    Shared settings for metric and agent review alert builders.

    Obtain a builder through the owner's ``new_alert_configuration`` method.
    Configurations are enabled and close automatically on recovery by default.
    """

    def __init__(self, client, collection_path, name=None):
        self.client = client
        self.collection_path = collection_path
        self.definition = {"name": name}  # type: dict

    def create(self):
        """
        Creates the alert configuration on this builder's owner.

        :rtype: :class:`AlertConfiguration`
        """
        if not self.definition.get("subjectId"):
            raise ValueError("A metric or agent review is required before creating the alert configuration")
        created = self.client._perform_json("POST", self.collection_path, body=self.definition)
        return AlertConfiguration(self.client, self.collection_path, created["id"])

    def with_required_acknowledgement(self, required=True):
        """
        Requires human acknowledgement before automatic closure, in addition to the closure condition.

        :param bool required: whether acknowledgement is required (default: False on new configurations)
        :rtype: AlertConfigurationBuilder
        """
        self.definition["requireAcknowledgement"] = required
        return self

    def with_auto_close(self, mode="IMMEDIATE_UPON_BACK_TO_NORMAL", healthy_buckets=None, recovery_threshold=None):
        """
        Configures automatic closure independently of the trigger.

        :param str mode: ``IMMEDIATE_UPON_BACK_TO_NORMAL``, ``SUSTAINED_BACK_TO_NORMAL``,
                         ``BACK_TO_NORMAL_WITH_HYSTERESIS``, or ``NONE``. Agent reviews support immediate or manual closure only.
        :param int healthy_buckets: consecutive healthy buckets required for sustained closure (default: 3)
        :param float recovery_threshold: threshold strictly on the healthy side of all fixed trigger thresholds
        :rtype: AlertConfigurationBuilder
        """
        settings = self.definition["evaluationSettings"]
        settings["autoCloseMode"] = mode
        if healthy_buckets is not None:
            settings["sustainedBackToNormalCloseDurationInBuckets"] = healthy_buckets
        if recovery_threshold is not None:
            settings["hysteresisCloseThreshold"] = recovery_threshold
        return self

    def with_enabled(self, enabled):
        """
        Controls whether this configuration is evaluated.

        :param boolean enabled: whether the configuration is enabled (default: True)
        :returns: this builder
        :rtype: AlertConfigurationBuilder
        """
        self.definition["enabled"] = enabled
        return self

    def _as_dict(self):
        return self.definition


class MetricAlertConfigurationBuilder(AlertConfigurationBuilder):
    """
    Builds a metric alert configuration for creation globally, on an platform, or on an agent.

    The metric is fixed after creation. Thresholds and the time-bucket granularity may be completed later.
    Evaluation requires a time bucket and at least one threshold. By default, a single breach opens an alert.

    Usage example:

    .. code-block:: python

        alert_configuration = (agent.new_alert_configuration(type="metric", name="Daily cost")
                         .with_metric("consumption.cost.total")
                         .with_time_bucket()
                         .with_thresholds(warning=10, critical=20)
                         .create())

    Obtain this builder through the owner's ``new_alert_configuration(type="metric")`` method.
    """

    def __init__(self, client, collection_path, name=None):
        super(MetricAlertConfigurationBuilder, self).__init__(client, collection_path, name)
        self.definition.update({
            "evaluationSettings": {"type": "TIME_BUCKETED_METRIC"},
        })

    def with_metric(self, metric_id):
        """
        Selects the metric to evaluate.

        :param str metric_id: ID of the metric
        :rtype: MetricAlertConfigurationBuilder
        """
        if not metric_id or not metric_id.strip():
            raise ValueError("A metric ID is required")
        self.definition["subjectId"] = metric_id
        return self

    def with_time_bucket(self, granularity="DAY", include_current_bucket=False):
        """
        Selects a time bucket for Operational, Usage, Cost, Uptime, or Business KPI metrics.

        :param str granularity: ``HOUR``, ``DAY``, ``WEEK``, or ``MONTH``
        :param bool include_current_bucket: evaluate available data before the current bucket ends (default: False)
        :rtype: MetricAlertConfigurationBuilder
        """
        self.definition["evaluationSettings"]["granularity"] = granularity
        self.definition["evaluationSettings"]["includeCurrentBucket"] = include_current_bucket
        return self

    def with_thresholds(self, warning=None, critical=None, breach_direction="AT_OR_ABOVE"):
        """
        Selects fixed-threshold detection. Either threshold may be left unset, but evaluation requires at least one.

        :param float warning: warning threshold
        :param float critical: critical threshold
        :param str breach_direction: ``AT_OR_ABOVE`` or ``AT_OR_BELOW``
        :rtype: MetricAlertConfigurationBuilder
        """
        self.definition["evaluationSettings"]["detectionPolicy"] = {
            "type": "FIXED_THRESHOLD",
            "warningThreshold": warning,
            "criticalThreshold": critical,
            "breachDirection": breach_direction,
        }
        return self

    def with_multi_bucket_aggregate_thresholds(self, warning=None, critical=None, buckets=3, aggregation=None, breach_direction="AT_OR_ABOVE"):
        """
        Applies fixed thresholds to an aggregate over the last completed buckets, rather than to each bucket separately.

        The metric determines the calculation: totals are added, means and ratios use their contributing
        populations, identities are counted distinctly, and percentiles use source observations across the period.
        For ``consumption.cost.total``, ``buckets=3`` and ``critical=20`` compare the total estimated cost over
        three completed buckets with 20 in the configured currency.

        ``aggregation`` is available only for business KPIs. A mean or percentile without contributing values
        is unavailable, and failed reads cannot clear an existing alert. Stored platform percentiles support
        one bucket only. Either threshold may be left unset, but evaluation requires at least one.

        :param float warning: warning threshold in the metric's unit; omit to disable warnings
        :param float critical: critical threshold in the metric's unit; omit to disable critical alerts
        :param int buckets: number of completed calendar buckets in the aggregate (default: 3); server limits depend on the granularity
        :param str aggregation: business KPI calculation, ``AVG`` or ``P95``; when omitted, the server uses ``AVG`` for business KPIs.
            Omit for built-in metrics, which determine their own calculation
        :param str breach_direction: ``AT_OR_ABOVE`` or ``AT_OR_BELOW``
        :rtype: MetricAlertConfigurationBuilder
        """
        self.with_thresholds(warning=warning, critical=critical, breach_direction=breach_direction)
        self.definition["evaluationSettings"]["detectionPolicy"].update({
            "type": "ROLLING_THRESHOLD",
            "bucketCount": buckets,
        })
        if aggregation is not None:
            self.definition["evaluationSettings"]["detectionPolicy"]["aggregation"] = aggregation
        return self

    def with_historical_change(self, warning=None, critical=None, baseline_buckets=7, recent_buckets=3,
                               aggregation=None, change_direction="EITHER"):
        """
        Alerts on percentage changes in a metric compared with its earlier history, rather than a fixed value.

        The selected metric determines the calculation on both periods. Totals are compared as raw totals,
        even when the periods have different lengths. For example, 700 in the baseline and 300 in the recent
        period represent a decrease of about 57.14%, regardless of their respective bucket counts.
        Percentages describe relative changes, not percentage points.

        ``aggregation`` is available only for business KPIs. Missing observations remain unavailable rather
        than zero. Stored platform percentiles require one bucket in each period.
        A change from a valid zero baseline to a non-zero value in the selected direction qualifies every enabled severity.

        :param float warning: positive percentage change for a warning (for example, 10 for 10%); omit to disable warnings
        :param float critical: positive percentage change for a critical alert; omit to disable critical alerts
        :param int baseline_buckets: number of earlier buckets used as the reference (default: 7)
        :param int recent_buckets: number of completed buckets immediately after the reference period to compare (default: 3)
        :param str aggregation: business KPI calculation, ``AVG`` or ``P95``; when omitted, the server uses ``AVG`` for business KPIs.
            Omit for built-in metrics, which determine their own calculation
        :param str change_direction: alert on ``INCREASE``, ``DECREASE`` or ``EITHER`` direction (default: ``EITHER``)
        :rtype: MetricAlertConfigurationBuilder
        """
        self.definition["evaluationSettings"]["detectionPolicy"] = {
            "type": "BASELINE_DEVIATION",
            "changeDirection": change_direction,
            "baselineBucketCount": baseline_buckets,
            "recentBucketCount": recent_buckets,
            "warningChangePercentThreshold": warning,
            "criticalChangePercentThreshold": critical,
        }
        if aggregation is not None:
            self.definition["evaluationSettings"]["detectionPolicy"]["aggregation"] = aggregation
        return self

    def with_sustained_thresholds(self, warning=None, critical=None, warning_breaches=3, critical_breaches=3,
                                 breach_direction="AT_OR_ABOVE"):
        """
        Requires threshold breaches in consecutive completed buckets before opening or escalating an alert.
        Warning and critical counts are independent. Improvement remains immediate; recovery follows the closure mode.

        :param float warning: warning threshold in the metric's unit; omit to disable warnings
        :param float critical: critical threshold in the metric's unit; omit to disable critical alerts
        :param int warning_breaches: consecutive warning breaches required (default: 3)
        :param int critical_breaches: consecutive critical breaches required (default: 3)
        :param str breach_direction: ``AT_OR_ABOVE`` or ``AT_OR_BELOW``
        :rtype: MetricAlertConfigurationBuilder
        """
        self.with_thresholds(warning=warning, critical=critical, breach_direction=breach_direction)
        self.definition["evaluationSettings"]["detectionPolicy"].update({
            "type": "SUSTAINED_THRESHOLD",
            "warningConsecutiveBreaches": warning_breaches,
            "criticalConsecutiveBreaches": critical_breaches,
        })
        return self


class AgentReviewAlertConfigurationBuilder(AlertConfigurationBuilder):
    """
    Builds an agent review alert configuration for creation on an agent only.

    The review must be linked to that agent. Its project and ID are fixed after creation and encoded
    as ``agent_review.<project_key>.<agent_review_id>`` in ``subjectId``.
    No metric thresholds or time buckets are used. By default, one completed failed run opens a critical alert.

    Usage example:

    .. code-block:: python

        alert_configuration = (agent.new_alert_configuration(type="agent_review", name="Review failures")
                         .with_agent_review("PROJECT", "review-id")
                         .with_consecutive_failed_runs(2)
                         .create())

    Obtain this builder through ``agent.new_alert_configuration(type="agent_review")``.
    """

    def __init__(self, client, collection_path, name=None):
        super(AgentReviewAlertConfigurationBuilder, self).__init__(client, collection_path, name)
        self.definition["evaluationSettings"] = {"type": "AGENT_REVIEW", "consecutiveFailedRuns": 1}

    def with_agent_review(self, project_key, agent_review_id):
        """
        Selects the agent review linked to this agent.

        :param str project_key: project containing the linked agent review
        :param str agent_review_id: agent review ID
        :rtype: AgentReviewAlertConfigurationBuilder
        """
        if not project_key or not project_key.strip() or "." in project_key or not agent_review_id or not agent_review_id.strip():
            raise ValueError("An agent review project and ID are required")
        self.definition["subjectId"] = "agent_review.{}.{}".format(project_key, agent_review_id)
        return self

    def with_consecutive_failed_runs(self, count=1):
        """
        Requires consecutive completed failed runs before opening an alert.

        Each distinct run counts once, including runs completed before configuration creation.
        Re-evaluating unchanged runs does not advance progress; one healthy run recovers immediately.
        Missing or unlinked reviews and read errors trigger alerts without waiting for this count.

        :param int count: consecutive failed runs required, from 1 to 10 (default: 1)
        :rtype: AgentReviewAlertConfigurationBuilder
        """
        self.definition["evaluationSettings"]["consecutiveFailedRuns"] = count
        return self


class AlertConfiguration(object):
    """
    An alert configuration owned by global settings, an platform, or an agent.

    Obtain this handle through the owner's ``get_alert_configuration`` method.
    """

    def __init__(self, client, collection_path, configuration_id):
        self.client = client
        self.collection_path = collection_path
        self.configuration_id = configuration_id

    @property
    def id(self):
        return self.configuration_id

    def __repr__(self):
        return "<AlertConfiguration collection_path=%r id=%r>" % (self.collection_path, self.configuration_id)

    def get_settings(self):
        """
        Returns editable settings, including the metric or agent review, evaluation settings, and recovery policy.

        Modify :meth:`AlertConfigurationSettings.get_raw`, then call :meth:`AlertConfigurationSettings.save`.

        :rtype: :class:`AlertConfigurationSettings`
        """
        settings = self.client._perform_json("GET", self._path())
        return AlertConfigurationSettings(self, settings)

    def delete(self):
        """Deletes this configuration and reconciles its alerts without affecting other configurations."""
        self.client._perform_empty("DELETE", self._path())

    def _path(self):
        return "%s/%s" % (self.collection_path, dku_quote_fn(self.configuration_id, safe=""))


class AlertConfigurationSettings(object):
    """
    Editable settings of an alert configuration.

    Obtain these through :meth:`AlertConfiguration.get_settings`.
    """

    def __init__(self, configuration, settings):
        self.configuration = configuration
        self.settings = settings
        self.initial_settings = deepcopy(settings)

    def get_raw(self):
        """
        Returns the mutable configuration settings. Changes are persisted by :meth:`save`.

        :rtype: dict
        """
        return self.settings

    @property
    def raw(self):
        """The mutable configuration settings, also available through :meth:`get_raw`."""
        return self.settings

    def save(self):
        """
        Saves the complete configuration settings and refreshes them from the server response.

        The ID and metric or agent review reference must remain unchanged. Incomplete evaluation settings may be saved.
        To change the metric or agent review, create a new configuration.
        A concurrent edit since these settings were read causes the save to fail.

        :returns: these settings with their saved data
        :rtype: :class:`AlertConfigurationSettings`
        """
        self.settings = self.configuration.client._perform_json("PUT", self.configuration._path(), body={
            "configuration": self.settings,
            "initialConfiguration": self.initial_settings,
        })
        self.initial_settings = deepcopy(self.settings)
        return self


class TriggeredAlertSearchResult(object):
    """
    A bounded triggered-alert search result.

    Use :attr:`has_more` to determine whether more alerts matched and narrower filters are needed.
    Do not create this directly; use :meth:`dataikuapi.AgentManagementClient.search_triggered_alerts`.
    """
    def __init__(self, client, response, as_objects):
        alerts = response["alerts"]
        self.alerts = ([Alert(client, alert["id"]) for alert in alerts] if as_objects else alerts)
        self.has_more = response["hasMore"]


class TriggeredAlertHistoryResult(object):
    """
    A bounded triggered-alert history result.

    Use :attr:`has_more` to determine whether older events were omitted.
    Do not create this directly; use :meth:`dataikuapi.agentmanagement.alerting.Alert.get_history`.
    """
    def __init__(self, response):
        self.entries = response["entries"]
        self.has_more = response["hasMore"]


class Alert(object):
    """
    An Agent Management triggered alert.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_triggered_alert`.
    """
    def __init__(self, client, alert_id):
        self.client = client
        self.alert_id = alert_id

    @property
    def id(self):
        return self.alert_id

    def __repr__(self):
        return "<Alert id=%r>" % self.alert_id

    def get_details(self):
        """
        Returns the triggered alert details, including its opening evidence and actor.

        ``loc`` identifies the evaluated target and, for configuration-based alerts, the configuration origin and ID
        and evaluation subject (``subjectId``: a metric or agent review). ``observedStatus`` is ``HEALTHY``, ``WARNING``,
        ``CRITICAL``, or ``UNKNOWN``; ``unknownReason`` explains unavailable evaluations.
        These describe the current observed outcome for an open occurrence, or the final outcome for a closed occurrence.
        The occurrence's ``severity`` retains its last breach severity, independently of recovery or unavailable data.

        When opening evidence is present, ``openingEvidence.type`` identifies its shape: ``TIME_BUCKETED_METRIC``
        includes ``observation`` and ``windowStartInclusive``/``windowEndExclusive``; ``AGENT_REVIEW`` includes
        ``agentReviewResult`` instead. Both include the captured configuration fields, detection result and observation source.
        AI-generated alerts have no opening evidence.

        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def get_history(self, limit=None):
        """
        Returns the most recent triggered alert history events in chronological order.

        Each event's ``state`` contains ``observedStatus``, ``unknownReason``, ``occurrenceSeverity``, and
        ``occurrenceState`` immediately after the event. Observation-driven events also include historical ``evidence``.
        Its ``type`` is ``TIME_BUCKETED_METRIC`` or ``AGENT_REVIEW``, with the same fields as the opening evidence
        described in :meth:`get_details`. Events without an evaluation have no evidence.

        Use :attr:`TriggeredAlertHistoryResult.has_more` to determine whether older events were omitted.

        :param int limit: optional maximum number of events to return; the server enforces its own upper bound
        :rtype: :class:`dataikuapi.agentmanagement.alerting.TriggeredAlertHistoryResult`
        """
        response = self.client._perform_json("GET", self._path("history"), params={"limit": limit})
        return TriggeredAlertHistoryResult(response)

    def acknowledge(self):
        """
        Acknowledges the triggered alert and returns its current details.

        Repeating this call returns the existing acknowledgement without changing it.

        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("actions/acknowledge"), body={})

    def close(self):
        """
        Manually closes this alert without changing its observed state or acknowledgement.

        For metric and agent review alerts, if the problem persists or its observation is unavailable,
        a current healthy observation is required before the configuration can open another alert
        for this agent. For AI alerts, this stops evaluation of the current occurrence.

        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("actions/close"), body={})

    def _path(self, suffix=None):
        path = "/agent-management/alerts/%s" % dku_quote_fn(self.alert_id, safe="")
        if suffix is not None:
            path += "/" + suffix
        return path


class AlertConfigurationListItem(dict):
    """
    An alert configuration listing entry returned by ``list_alert_configurations`` or ``list_applicable_alert_configurations``.

    Applicable entries retain their nested ``configuration``, ``loc``, and ``latestEvaluation`` data.
    """

    def __init__(self, client, data, collection_path=None):
        super(AlertConfigurationListItem, self).__init__(data)
        self.client = client
        if collection_path is None and "loc" in self:
            loc = self["loc"]
            if loc["origin"] == "GLOBAL":
                collection_path = "/agent-management/alert-configurations"
            elif loc["origin"] == "INFRA":
                collection_path = "/agent-management/platforms/%s/alert-configurations" % dku_quote_fn(loc["infraName"], safe="")
            elif loc["origin"] == "AGENT":
                collection_path = "/agent-management/platforms/%s/agents/%s/alert-configurations" % (
                    dku_quote_fn(loc["infraName"], safe=""), dku_quote_fn(loc["agentId"], safe=""))
        self.collection_path = collection_path

    @property
    def configuration(self):
        """The configuration definition, whether listed directly or as an applicable entry."""
        return self.get("configuration", self)

    @property
    def id(self):
        """The listing entry's id."""
        return self.configuration["id"]

    @property
    def name(self):
        """The listing entry's name."""
        return self.configuration.get("name")

    @property
    def enabled(self):
        """The listing entry's enabled."""
        return self.configuration.get("enabled")

    @property
    def type(self):
        """The evaluation type: ``TIME_BUCKETED_METRIC`` or ``AGENT_REVIEW``."""
        return self.configuration.get("evaluationSettings", {}).get("type")

    @property
    def loc(self):
        """The resolved location for an applicable entry, or None for a direct listing."""
        return self.get("loc")

    @property
    def latest_evaluation(self):
        """The latest evaluation for an applicable entry, or None when unavailable."""
        return self.get("latestEvaluation")

    def to_alert_configuration(self):
        """
        Return a :class:`AlertConfiguration` handle without making an API call.

        :raises ValueError: if the origin has no public configuration endpoint (for example, a scope)
        """
        if self.collection_path is None:
            raise ValueError("This alert configuration's origin has no public configuration endpoint")
        return AlertConfiguration(self.client, self.collection_path, self.id)

    def _to_object(self):
        return self.to_alert_configuration()
