class GovernTimeSeries(object):
    """
    A handle to interact with a time series.
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_time_series`
    """

    def __init__(self, client, time_series_id):
        self.client = client
        self.time_series_id = time_series_id

    def get_values(self, min_timestamp=None, max_timestamp=None, as_objects=True):
        """
        Get the values of the time series. Use the parameters `min_timestamp` and `max_timestamp` to define a time
        window. Only values within this window will be returned

        :param int min_timestamp: The minimum timestamp of the time window
        :param int max_timestamp: The maximum timestamp of the time window
        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.custom_page.GovernTimeSeriesDatapoint`,
         else returns a list of dict. Each dict contains at least a field "timeSeriesId"

        :return: the corresponding custom page definition object
        :rtype: list of :class:`~dataikuapi.govern.custom_page.GovernTimeSeriesDatapoint`or list of dict, see param
        as_objects
        """
        params = {}

        if min_timestamp is not None:
            params["timestampMin"] = min_timestamp
        if max_timestamp is not None:
            params["timestampMax"] = max_timestamp

        datapoints = self.client._perform_json("GET", "/time-series/%s" % self.time_series_id, params=params)

        if as_objects:
            return [GovernTimeSeriesDatapoint(datapoint.get("timeSeriesId"), datapoint.get("value"),
                                              datapoint.get("timestamp")) for datapoint in datapoints]
        else:
            return datapoints

    def push_values(self, datapoints, upsert=True):
        """
        Push a list of values inside the time series. To create a list of datapoints, instantiate `~dataikuapi.govern.time_series.GovernTimeSeriesDatapoint`.

        :param list datapoints: a list of :class: `~dataikuapi.govern.time_series.GovernTimeSeriesDatapoint`- The list of
        datapoints
        :param boolean upsert: (Optional) If set to false, values for existing timestamps will not be overridden.
        Default value is set to True
        :return: None
        """

        if not all(isinstance(datapoint, GovernTimeSeriesDatapoint) for datapoint in datapoints):
            raise ValueError("All items of the list must be instances of GovernTimeSeriesDatapoint")

        self.client._perform_json("PUT", "/time-series/%s" % self.time_series_id,
                                         body=[datapoint.build() for datapoint in datapoints],
                                         params={"upsert": upsert})

    def delete(self, min_timestamp=None, max_timestamp=None):
        """
        Delete the values of the time series. Use the parameters `min_timestamp` and `max_timestamp` to define a time
        window. Only values within this window will be deleted.

        :param int min_timestamp: The minimum timestamp of the time window
        :param int max_timestamp: The maximum timestamp of the time window

        :return: None
        """
        params = {}

        if min_timestamp is not None:
            params["timestampMin"] = min_timestamp
        if max_timestamp is not None:
            params["timestampMax"] = max_timestamp

        self.client._perform_empty("DELETE", "/time-series/%s" % self.time_series_id, params=params)


class GovernTimeSeriesDatapoint(object):
    """
    A handle to interact with a time series datapoint.
    Recover the list of existing datapoints in a time series using :meth:`~dataikuapi.GovernClient.get_time_series.get_values`
    or create directly instance of this object and push datapoints to a time series using:
    :meth:`~dataikuapi.GovernClient.get_time_series.push_values`
    """

    def __init__(self, time_series_id, value, timestamp):
        """
        :param str time_series_id: the ID of the time series
        :param any value: the value of the datapoint
        :param int timestamp: the timestamp value as epoch in milliseconds
        """
        self.time_series_id = time_series_id
        self.value = value
        self.timestamp = timestamp

    def build(self):
        return {
            "timeSeriesId": self.time_series_id,
            "timestamp": self.timestamp,
            "value": self.value
        }
