class GovernTimeSeries(object):
    """
    A handle to interact with a time series.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_time_series`
    """

    def __init__(self, client, time_series_id):
        self.client = client
        self.time_series_id = time_series_id

    def get_values(self, min_timestamp=None, max_timestamp=None):
        """
        Get the values of the time series. Use the parameters `min_timestamp` and `max_timestamp` to define a time
        window. Only values within this window will be returned

        :param int min_timestamp: (Optional) The minimum timestamp of the time window as an epoch in milliseconds
        :param int max_timestamp: (Optional) The maximum timestamp of the time window as an epoch in milliseconds

        :return: a list data points of the time series as Python dict
        :rtype: list of dict
        """
        params = {}

        if min_timestamp is not None:
            params["timestampMin"] = min_timestamp
        if max_timestamp is not None:
            params["timestampMax"] = max_timestamp

        datapoints = self.client._perform_json(
            "GET", "/time-series/%s" % self.time_series_id, params=params)
        return datapoints

    def push_values(self, datapoints, upsert=True):
        """
        Push a list of values inside the time series.

        :param list datapoints: a list of Python dict - The list of datapoints as Python dict containing the following keys "timeSeriesId", "timestamp" (an epoch in milliseconds), and "value" (an object)
        :param boolean upsert: (Optional) If set to false, values for existing timestamps will not be overridden. Default value is True.
        :return: None
        """

        for datapoint in datapoints:
            datapoint['timeSeriesId'] = self.time_series_id

        self.client._perform_json("PUT", "/time-series/%s" %
                                  self.time_series_id, body=datapoints, params={"upsert": upsert})

    def delete(self, min_timestamp=None, max_timestamp=None):
        """
        Delete the values of the time series. Use the parameters `min_timestamp` and `max_timestamp` to define a time
        window. Only values within this window will be deleted.

        :param int min_timestamp: (Optional) The minimum timestamp of the time window as an epoch in milliseconds
        :param int max_timestamp: (Optional) The maximum timestamp of the time window as an epoch in milliseconds

        :return: None
        """
        params = {}

        if min_timestamp is not None:
            params["timestampMin"] = min_timestamp
        if max_timestamp is not None:
            params["timestampMax"] = max_timestamp

        self.client._perform_empty(
            "DELETE", "/time-series/%s" % self.time_series_id, params=params)
