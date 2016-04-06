

class ComputedMetrics(object):
    def __init__(self, raw):
        self.raw = raw

    def get_metric_by_id(self, id):
        all_ids = []
        for metric in self.raw["metrics"]:
            all_ids.append(metric["metric"]["id"])
            if metric["metric"]["id"] == id:
                return metric
        raise Exception("Metric %s not found among: %s" % (id, all_ids))

    def get_global_data(self, metric_id):
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            if partition_data["partition"]== "NP" or partition_data["partition"] == "ALL":
                return partition_data
        raise Exception("No data found for global partition for metric %s" % metric_id)

    def get_global_value(self, metric_id):
        return ComputedMetrics.get_value_from_data(self.get_global_data(metric_id))

    def get_partition_data(self, metric_id, partition):
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            if partition_data["partition"] == partition:
                return partition_data

    def get_partition_value(self, metric_id, partition):
        return ComputedMetrics.get_value_from_data(self.get_partition_data(metric_id, partition))

    def get_first_partition_data(self, metric_id):
        for partition_data in self.get_metric_by_id(metric_id)["lastValues"]:
            return partition_data
        raise Exception("No partition data for metric %s" % metric_id)

    def get_all_ids(self):
        all_ids = []
        for metric in self.raw["metrics"]:
            all_ids.append(metric["metric"]["id"])
        return all_ids


    @staticmethod
    def get_value_from_data(data):
        dtype = data.get("dataType", "STRING")
        if dtype in ["BIGINT", "INT"]:
            return int(data["value"])
        elif dtype in ["FLOAT", "DOUBLE"]:
            return float(data["value"])
        else:
            return data["value"]