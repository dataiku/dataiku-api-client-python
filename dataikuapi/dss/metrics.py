

class ComputedMetrics(object):
    """
    Handle to the metrics of a DSS object and their last computed value

    .. important::
        Do not create this class directly, instead use :meth:`.DSSDataset.get_last_metric_values`, 
        :meth:`.DSSSavedModel.get_metric_values`, :meth:`.DSSManagedFolder.get_last_metric_values`.

    """

    def __init__(self, raw):
        self.raw = raw

    def get_raw(self):
        """
        Get the raw metrics data

        :rtype: dict
        """
        return self.raw

    def get_metric_by_id(self, id):
        """
        Retrieve the info for a given metric
        
        Usage example

        .. code-block:: python

            dataset = project.get_ataset("my_dataset")
            metrics = dataset.get_last_metric_values()
            count_files_metric = metrics.get_metric_by_id("basic:COUNT_FILES")
            for value in count_files_metric['lastValues']:
                print("partition=%s -> count of files=%s" % (value['partition'], value['value']))        

        :param string metric_id: identifier of the metric

        :return: information about the metric and its values. Since the last value of the metric depends on
                 the partition considered, the last values of the metric are given in a sub-list of the dict. 
        :rtype: dict
        """
        all_ids = []
        for metric in self.raw["metrics"]:
            all_ids.append(metric["metric"]["id"])
            if metric["metric"]["id"] == id:
                return metric
        raise Exception("Metric %s not found among: %s" % (id, all_ids))

    def get_global_data(self, metric_id):
        """
        Get the global value point of a given metric, or throws.
        
        For a partitioned dataset, the global value is the value of the metric computed
        on the whole dataset (coded as partition 'ALL').
        
        :param string metric_id: identifier of the metric

        :returns: the metric data, as a dict. The value itself is a **value** string field.
        :rtype: dict        
        """
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            if partition_data["partition"]== "NP" or partition_data["partition"] == "ALL":
                return partition_data
        raise Exception("No data found for global partition for metric %s" % metric_id)

    def get_global_value(self, metric_id):
        """
        Get the global value of a given metric, or throws.
        
        For a partitioned dataset, the global value is the value of the metric computed
        on the whole dataset (coded as partition 'ALL').

        Usage example

        .. code-block:: python

            dataset = project.get_ataset("my_dataset")
            metrics = dataset.get_last_metric_values()
            print("record count = %s" % metrics.get_global_value('records:COUNT_RECORDS'))
        
        :param string metric_id: identifier of the metric

        :returns: the value of the metric for the partition
        :rtype: str, int or float
        """
        return ComputedMetrics.get_value_from_data(self.get_global_data(metric_id))

    def get_partition_data(self, metric_id, partition):
        """
        Get the value point of a given metric for a given partition, or throws.
        
        :param string metric_id: identifier of the metric
        :param string partition: partition identifier

        :returns: the metric data, as a dict. The value itself is a **value** string field.
        :rtype: dict        
        """
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            if partition_data["partition"] == partition:
                return partition_data

    def get_partition_value(self, metric_id, partition):
        """
        Get the value of a given metric for a given partition, or throws.
        
        :param string metric_id: identifier of the metric
        :param string partition: partition identifier

        :returns: the value of the metric for the partition
        :rtype: str, int or float
        """
        return ComputedMetrics.get_value_from_data(self.get_partition_data(metric_id, partition))

    def get_first_partition_data(self, metric_id):
        """
        Get a value point of a given metric, or throws. The first value encountered is returned.
        
        :param string metric_id: identifier of the metric

        :returns: the metric data, as a dict. The value itself is a **value** string field.
        :rtype: dict        
        """
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            return partition_data
        raise Exception("No partition data for metric %s" % metric_id)

    def get_all_ids(self):
        """
        Get the identifiers of all metrics defined in this object

        :returns: list of metric identifiers
        :rtype: list[string]
        """
        all_ids = []
        for metric in self.raw["metrics"]:
            all_ids.append(metric["metric"]["id"])
        return all_ids


    @staticmethod
    def get_value_from_data(data):
        """
        Retrieves the value from a metric point, cast in the appropriate type (str, int or float).
        
        For other types, the value is not cast and left as a string.
        
        :param dict data: a value point for a metric, retrieved with :meth:`~get_global_data`, :meth:`~get_partition_data`
                          or :meth:`~get_first_partition_data`
        
        :returns: the value, cast to the appropriate Python type
        :rtype: str, int or float
        """
        dtype = data.get("dataType", "STRING")
        if dtype in ["BIGINT", "INT"]:
            return int(data["value"])
        elif dtype in ["FLOAT", "DOUBLE"]:
            return float(data["value"])
        else:
            return data["value"]
