class DSSDatasetSelectionBuilder(object):
    """Builder for a "dataset selection". In DSS, a dataset selection is used to select a part of a dataset for processing.

    Depending on the location where it is used, a selection can include:
    * Sampling
    * Filtering by partitions (for partitioned datasets)
    * Filtering by an expression
    * Selection of columns
    * Ordering

    Please see the sampling documentation of DSS for a detailed explanation of the sampling methods.

    """
    def __init__(self):
        self.selection = {}

    def build(self):
        """Returns the built selection dict"""
        return self.selection

    def with_head_sampling(self, limit):
        """Sets the sampling to 'first records' mode"""
        self.selection["samplingMethod"] = "HEAD_SEQUENTIAL"
        self.selection["maxRecords"] = limit
        return self

    def with_all_data_sampling(self):
        """Sets the sampling to 'no sampling, all data' mode"""
        self.selection["samplingMethod"] = "FULL"
        return self

    def with_random_fixed_nb_sampling(self, nb):
        """Sets the sampling to 'Random sampling, fixed number of records' mode"""
        self.selection["samplingMethod"] = "RANDOM_FIXED_NB"
        self.selection["maxRecords"] = nb
        return self

    def with_selected_partitions(self, ids):
        """Sets partition filtering on the given partition identifiers. The dataset to select must be partitioned."""
        self.selection["partitionSelectionMethod"] = "SELECTED"
        self.selection["selectedPartitions"] = ids
        return self


class DSSFilterBuilder(object):
    """
    Builder for a "filter". In DSS, a filter is used to define a subset of rows for processing.
    """
    def __init__(self):
        self.filter = {"enabled":False, "distinct":False, "expression":None, "uiData":{"mode":"CUSTOM"}}

    def build(self):
        """Returns the built filter dict"""
        return self.filter

    def with_distinct(self):
        """Sets the filter to deduplicate"""
        self.filter["distinct"] = True
        return self

    def with_formula(self, expression):
        """Sets the formula (DSS formula) used to filter rows"""
        self.filter["enabled"] = True
        self.filter["expression"] = expression
        self.filter["uiData"]["mode"] = "CUSTOM"
        return self
