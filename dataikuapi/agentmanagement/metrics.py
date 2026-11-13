"""Accessors for bucketed Agent Management metrics."""
from datetime import datetime, timedelta, timezone

from ._utils import _to_timestamp_ms


class BucketedMetricsFetchResults(object):
    """Bucketed metrics for multiple agents, retaining the original grouped series.

    Unified tables contain all requested metric columns in request order, with ``None`` for
    missing values. Rows are joined on exact ``(start, end)`` boundaries and sorted chronologically.
    Agents returned with empty series are retained; agents absent from the response are unknown.
    """

    def __init__(self, raw_data, metrics):
        self._metrics = list(dict.fromkeys(metrics))
        self._agents = {}
        for series in raw_data:
            key = (series["infrastructureName"], series["agentId"])
            self._agents.setdefault(key, []).append(series)

    def agents(self):
        """Return represented agents as ``(platform_name, agent_id)`` tuples in response order."""
        return list(self._agents)

    def raw_agent_data(self, platform_name, agent_id):
        """Return the original grouped dictionaries, including metadata and UTC-aware datetimes.

        :raises KeyError: if the agent is absent from the response
        """
        return self._agents[(platform_name, agent_id)]

    def agent_series(self, platform_name, agent_id):
        """Return a unified ``{columns, rows}`` table for the agent.

        Columns are ``start``, ``end`` and every requested metric. Only bucket boundaries present
        in the response produce rows. An agent with empty data has an empty ``rows`` list.
        :raises KeyError: if the agent is absent from the response
        """
        groups = self.raw_agent_data(platform_name, agent_id)
        columns = ["start", "end"] + self._metrics
        metric_positions = {metric: index + 2 for index, metric in enumerate(self._metrics)}
        rows = {}
        for group in groups:
            start_index = group["columns"].index("start")
            end_index = group["columns"].index("end")
            positions = [(index, metric_positions[column]) for index, column in enumerate(group["columns"])
                         if column in metric_positions]
            for values in group["rows"]:
                boundary = (values[start_index], values[end_index])
                row = rows.setdefault(boundary, list(boundary) + [None] * len(self._metrics))
                for source, target in positions:
                    row[target] = values[source]
        return {"columns": columns, "rows": [rows[boundary] for boundary in sorted(rows)]}

    def agent_single_series(self, platform_name, agent_id, metric_id):
        """Return chronological ``(start, end, value)`` tuples, including missing values.

        :raises KeyError: if the agent is unknown or the metric was not requested
        """
        if metric_id not in self._metrics:
            raise KeyError(metric_id)
        series = self.agent_series(platform_name, agent_id)
        index = series["columns"].index(metric_id)
        return [(row[0], row[1], row[index]) for row in series["rows"]]

    def agent_values_at_time(self, platform_name, agent_id, time):
        """Return all requested metric values in the bucket containing ``time``, or ``{}``.

        Buckets include their start and exclude their end. ``time`` must be integer epoch
        milliseconds or a timezone-aware datetime. Missing metric values are ``None``.
        :raises KeyError: if the agent is absent from the response
        :raises ValueError: if a datetime is timezone-naive
        :raises TypeError: if time has an unsupported type
        """
        timestamp = _to_timestamp_ms(time, "time")
        if timestamp is None:
            raise TypeError("time must be an integer epoch millisecond timestamp or a timezone-aware datetime")
        instant = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=timestamp)
        # Preserve sub-millisecond precision for datetime lookups at bucket boundaries.
        if isinstance(time, datetime):
            instant = time
        for row in self.agent_series(platform_name, agent_id)["rows"]:
            if row[0] <= instant < row[1]:
                return dict(zip(self._metrics, row[2:]))
        return {}


class AgentBucketedMetricsFetchResults(object):
    """Bucketed metrics for a single agent, with grouped and unified accessors."""

    def __init__(self, results, platform_name, agent_id):
        self._platform_name = platform_name
        self._agent_id = agent_id
        if (platform_name, agent_id) not in results._agents:
            results = BucketedMetricsFetchResults([], results._metrics)
            results._agents[(platform_name, agent_id)] = []
        self._results = results

    def raw_data(self):
        """Return the original grouped dictionaries, or an empty list if no agent data was returned."""
        return self._results.raw_agent_data(self._platform_name, self._agent_id)

    def series(self):
        """Return a unified ``{columns, rows}`` table with requested columns and missing values as ``None``."""
        return self._results.agent_series(self._platform_name, self._agent_id)

    def single_series(self, metric_id):
        """Return ``(start, end, value)`` tuples, including ``None``; unrequested metrics raise ``KeyError``."""
        return self._results.agent_single_series(self._platform_name, self._agent_id, metric_id)

    def values_at_time(self, time):
        """Return values for ``start <= time < end``, or ``{}`` if no bucket contains the instant.

        Accepts integer epoch milliseconds or a timezone-aware datetime, just like
        :meth:`BucketedMetricsFetchResults.agent_values_at_time`.
        """
        return self._results.agent_values_at_time(self._platform_name, self._agent_id, time)
