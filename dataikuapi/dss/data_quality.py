from dataikuapi.dss.future import DSSFuture


class DSSDataQualityRuleSet(object):
    """
    Base settings class for dataset data quality rules.
    
    .. caution:: 
        Do not instantiate this class directly, use :meth:`dataikuapi.dss.dataset.DSSDataset.get_data_quality_rules`
    """
    def __init__(self, project_key, dataset_name, client):
        self.ruleset = { "checks": [] }
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.client = client

    def list_rules(self, as_type="objects"):
        """
        Get the list of rules defined on the dataset.

        :param str as_type: How to return the rules. Possible values are "dict" and "objects" (defaults to **objects**)

        :returns: The rules defined on the dataset.
        :rtype: a list of :class:`DSSDataQualityRule` if as_type is "objects",
            a list of dict if as_type is "dict"
        """
        self.ruleset = self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/rules" % (self.project_key, self.dataset_name))
        if as_type == "dict":
            return self.ruleset["checks"]
        elif as_type == "objects" or as_type == "object":
            return [DSSDataQualityRule(rule, self.dataset_name, self.project_key, self.client) for rule in self.ruleset["checks"]]
        else:
            raise ValueError("Unknown as_type")
    
    def create_rule(self, config=None):
        """
        Create a data quality rule on the current dataset.

        :param object config: The config of the rule

        :returns: The created data quality rule
        :rtype: :class:`DSSDataQualityRule`
        """
        if not config:
            raise ValueError("Config is required")
        rule = self.client._perform_json("POST", "/projects/%s/datasets/%s/data-quality/rules" % (self.project_key, self.dataset_name), body=config)
        self.ruleset["checks"].append(rule)
        return DSSDataQualityRule(rule, self.dataset_name, self.project_key, self.client)
    
    def get_partitions_status(self, partitions="NP"):
        """
        Get the last computed status of the specified partition(s).

        :param partitions: The list of partitions name or the name of the partition to get the last status (or "ALL" to retrieve the whole dataset partition). If the dataset is not partitioned use "NP" or None.

        :return: the status of the specified partitions if they exists
        :rtype: object
        """

        if not partitions:
            partitions = ["NP"]
        if isinstance(partitions, str):
            partitions = [partitions]
        return self.client._perform_json("POST", "/projects/%s/datasets/%s/data-quality/get-partitions-status" % (self.project_key, self.dataset_name), params={"partitions": partitions})

    def compute_rules(self, partition="NP"):
        """
        Compute all data quality enabled rules of the current dataset.
        
        :param str partition: If the dataset is partitioned, the name of the partition to compute (or "ALL" to compute on the whole dataset). If the dataset is not partitioned use "NP" or None.

        :returns: Job of the currently computed data quality rules.
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        if not partition:
            partition = "NP"
        future_resp = self.client._perform_json("POST", "/projects/%s/datasets/%s/data-quality/actions/compute-rules" % (self.project_key, self.dataset_name), params={"partition": partition})
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)
    
    def get_status(self):
        """
        Get the status of the dataset. For partitioned dataset this is the worst result of the last computed partitions.

        :returns: The status of the dataset.
        :rtype: str
        """
        return self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/status" % (self.project_key, self.dataset_name))
    
    def get_status_by_partition(self, include_all_partitions=False):
        """
        Return the status of a dataset detailed per partition used to compute it if any. If the dataset is not partitioned it will contain only one result.

        :param boolean include_all_partitions: Include all the partition having a data quality status or only the one relevant to the current status of the dataset. Default is False.

        :returns: The current status of each last built partitions of the dataset
        :rtype: dict
        """
        return  self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/status-by-partition" % (self.project_key, self.dataset_name), params={ "includeAllPartitions": include_all_partitions})
    
    def get_last_rules_results(self, partition="NP"):
        """
        Return the last result of all the rules defined on the dataset on a specified partition. If the dataset is not partitioned it will get all the last rules results

        :param str partition: If the dataset is partitioned, the name of the partition to get the detailed rules results (or "ALL" to compute on the whole dataset). If the dataset is not partitioned use "NP" or None.

        :returns: The last result of each rule on the specified partition
        :rtype: a list of :class:`DSSDataQualityRuleResult`   
        """
        if not partition:
            partition = "NP"
        rule_results = self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/last-rules-result" % (self.project_key, self.dataset_name), params={ "partition": partition})
        return [DSSDataQualityRuleResult(result) for result in rule_results]

    def get_rules_history(self, min_timestamp=None, max_timestamp=None, results_per_page=10000, page=0, rule_ids=None):
        """
        Get the history of computed rules.

        :param int min_timestamp: Timestamp representing the beginning of the timeframe. (included)
        :param int max_timestamp: Timestamp representing the end of the timeframe. (included)
        :param int results_per_page: The maximum number of records to be returned, default will be the last 10 000 records.
        :param int page: The page to be returned, default will be first page (page=0). 
        :param list rule_ids: A list of rule ids to get the history from. Default is all the rules on the dataset.

        :returns: The detailed execution of data quality rules matching the filters set
        :rtype: a list of :class:`DSSDataQualityRuleResult` 
        """
        rule_results = self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/rules-history" % (self.project_key, self.dataset_name), params={ "minTimestamp": min_timestamp, "maxTimestamp": max_timestamp, "resultsPerPage": results_per_page, "page": page, "ruleIds": rule_ids })
        return [DSSDataQualityRuleResult(result) for result in rule_results]
    

class DSSDataQualityRule(object):
    """
    A rule defined on a dataset.

    .. caution:: Do not instantiate this class, use :meth:`DSSDataQualityRuleSet.list_rules`
    """
    def __init__(self, rule, dataset_name, project_key, client):
        self.rule = rule
        self.dataset_name = dataset_name
        self.project_key = project_key
        self.client = client

    def get_raw(self):
        """
        Get the raw representation of this :class:`DSSDataQualityRule`

        :rtype: :class:`dict`
        """
        return self.rule
    
    @property
    def id(self):
        return self.rule["id"]
    
    @property
    def name(self):
        return self.rule["displayName"]

    def compute(self, partition="NP"):
        """
        Compute the rule on a given partition or the full dataset.

        :param str partition: If the dataset is partitioned, the name of the partition to compute (or "ALL" to compute on the whole dataset). If the dataset is not partitioned use "NP" or None.

        :returns: A job of the computation of the rule.
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        if not partition:
            partition = "NP"
        future_resp = self.client._perform_json("POST", "/projects/%s/datasets/%s/data-quality/actions/compute-rules" % (self.project_key, self.dataset_name), params={"partition": partition, "ruleId": self.rule["id"]})
        return DSSFuture(self.client, future_resp.get("jobId", None), future_resp)
    
    def save(self): 
        """
        Save the settings of a rule.

        :returns: 'Success'
        :rtype: str
        """
        self.client._perform_empty("PUT", "/projects/%s/datasets/%s/data-quality/rules/%s" % (self.project_key, self.dataset_name, self.id), body=self.rule)
        return "Success"

    def delete(self):
        """
        Delete the rule from the dataset configuration.
        """
        self.client._perform_empty("DELETE", "/projects/%s/datasets/%s/data-quality/rules/%s" % (self.project_key, self.dataset_name, self.id), params={ "ruleId": self.rule["id"] })
    
    def get_last_result(self, partition="NP"):
        """
        Return the last result of the rule on a specified dataset/partition.

        :param str partition: If the dataset is partitioned, the name of the partition to get the detailed rules results (or "ALL" to refer to the whole dataset). If the dataset is not partitioned use "NP" or None.

        :returns: The last result of the rule on the specified partition
        :rtype: :class:`DSSDataQualityRuleResult`
        """
        if not partition:
            partition = "NP"
        result = self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/last-rules-result" % (self.project_key, self.dataset_name), params={ "partition": partition, "ruleId": self.rule["id"]})
        if len(result) == 0:
            # The rule has not been executed yet.
            return None
        return DSSDataQualityRuleResult(result[0])
    
    def get_rule_history(self, min_timestamp=None, max_timestamp=None, results_per_page=10000, page=0):
        """
        Get the history of the current rule.

        :param int min_timestamp: Timestamp representing the beginning of the timeframe. (included)
        :param int max_timestamp: Timestamp representing the end of the timeframe. (included)
        :param int results_per_page: The maximum number of records to be returned, default will be the last 10 000 records.
        :param int page: The page to be returned, default will be first page. 

        :returns: The detailed execution of data quality rule matching the timeframe set
        :rtype: a list of :class:`DSSDataQualityRuleResult`  
        """
        rule_results = self.client._perform_json("GET", "/projects/%s/datasets/%s/data-quality/rules-history" % (self.project_key, self.dataset_name), params={ "minTimestamp": min_timestamp, "maxTimestamp": max_timestamp, "resultsPerPage": results_per_page, "page": page, "ruleId": self.rule["id"] })
        return [DSSDataQualityRuleResult(result) for result in rule_results]

class DSSDataQualityRuleResult(object):
    """
    The result of a rule defined on a dataset

    .. caution:: Do not instantiate this class, use: :meth:`DSSDataQualityRuleSet.get_last_rules_results` or :meth:`DSSDataQualityRuleSet.get_rules_history` or :meth:`DSSDataQualityRule.get_last_result` or :meth:`DSSDataQualityRule.get_rule_history`
    """
    def __init__(self, data):
        self.data = data

    def get_raw(self):
        """
        Get the raw representation of this :class:`DSSDataQualityRuleResult`

        :rtype: :class:`dict`
        """
        return self.data

    @property
    def id(self):
        return self.data["id"]
    
    @property
    def name(self):
        return self.data["name"]
    
    @property
    def outcome(self):
        return self.data["outcome"]
    
    @property
    def message(self):
        return self.data["message"]
    
    @property
    def compute_date(self):
        return self.data["computeDate"]
    
    @property
    def run_origin(self):
        return self.data["runOrigin"]

    @property
    def partition(self):
        return self.data["partition"]
