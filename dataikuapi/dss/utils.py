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

class AnyLoc(object):
    def __init__(self, project_key, object_id):
        self.project_key = project_key
        self.object_id = object_id

    def __eq__(self, obj):
        return isinstance(obj, AnyLoc) and obj.project_key == self.project_key and obj.object_id == self.object_id

    @staticmethod
    def from_ref(context_project_key, ref):
        if ref.find(".") >= 0:
            elts = ref.split(".")
            return AnyLoc(elts[0], elts[1])
        else:
            return AnyLoc(context_project_key, ref)

    @staticmethod
    def from_full(ref):
        if ref.find(".") >= 0:
            elts = ref.split(".")
            return AnyLoc(elts[0], elts[1])
        else:
            raise Exception("Cannot parse object id, it's not a full id")


class DSSTaggableObjectListItem(dict):
    """An item in a list of taggable objects. Do not instantiate this class"""
    def __init__(self, data):
        super(DSSTaggableObjectListItem, self).__init__(data)
        self._data = data

    @property
    def tags(self):
        return self._data["tags"]
