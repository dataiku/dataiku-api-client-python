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

class DSSComputedColumn(object):

    @staticmethod
    def formula(name, formula, type="double"):
        return {"expr": formula, "mode": "GREL", "name": name, "type": type}

import sys
if sys.version_info > (3,4):
    from enum import Enum
else:
    class Enum(object):
        pass

class DSSFilterOperator(Enum):
    EMPTY_ARRAY = "empty array"
    NOT_EMPTY_ARRAY = "not empty array"
    CONTAINS_ARRAY = "array contains"
    NOT_EMPTY = "not empty"
    EMPTY = "is empty"
    NOT_EMPTY_STRING = "not empty string"
    EMPTY_STRING = "empty string"
    IS_TRUE = "true"
    IS_FALSE = "false"
    EQUALS_STRING = "== [string]"
    EQUALS_CASE_INSENSITIVE_STRING = "== [string]i"
    NOT_EQUALS_STRING = "!= [string]"
    SAME = "== [NaNcolumn]"
    DIFFERENT = "!= [NaNcolumn]"
    EQUALS_NUMBER = "== [number]"
    NOT_EQUALS_NUMBER = "!= [number]"
    GREATER_NUMBER = ">  [number]"
    LESS_NUMBER = "<  [number]"
    GREATER_OR_EQUAL_NUMBER = ">= [number]"
    LESS_OR_EQUAL_NUMBER = "<= [number]"
    EQUALS_DATE = "== [date]"
    GREATER_DATE = ">  [date]"
    GREATER_OR_EQUAL_DATE = ">= [date]"
    LESS_DATE = "<  [date]"
    LESS_OR_EQUAL_DATE = "<= [date]"
    BETWEEN_DATE = ">< [date]"
    EQUALS_COL = "== [column]"
    NOT_EQUALS_COL = "!= [column]"
    GREATER_COL = ">  [column]"
    LESS_COL = "<  [column]"
    GREATER_OR_EQUAL_COL = ">= [column]"
    LESS_OR_EQUAL_COL = "<= [column]"
    CONTAINS_STRING = "contains"
    REGEX = "regex"

class DSSFilter(object):
    """Helper class to build filter objects for use in visual recipes"""
    @staticmethod
    def of_single_condition(column, operator, string = None, num = None, date = None, time = None, date2 = None, time2 = None, unit = None):
        return {
            "enabled": True,
            "uiData": {
                'conditions': [DSSFilter.condition(column, operator, string, num, date, time, date2, time2, unit)],
                "mode": "&&"
            }
        }

    @staticmethod
    def of_and_conditions(conditions):
        return {
            "enabled": True,
            "uiData": {
                'conditions': conditions,
                "mode": "&&"
            }
        }

    @staticmethod
    def of_or_conditions(conditions):
        return {
            "enabled": True,
            "uiData": {
                'conditions': conditions,
                "mode": "||"
            }
        }

    @staticmethod
    def of_formula(formula):
        return {
            "enabled": True,
            "uiData": {
                "mode": "CUSTOM"
            },
            "expression" : formula
        }

    @staticmethod
    def of_sql_expression(sql_expression):
        return {
            "enabled": True,
            "uiData": {
                "mode": "SQL"
            },
            "expression" : sql_expression
        }

    @staticmethod
    def condition(column, operator, string = None, num = None, date = None, time = None, date2 = None, time2 = None, unit = None):
        if isinstance(operator, DSSFilterOperator):
            operator = operator.value
        cond = {
            "input": column,
            "operator":  operator 
        }
        if string is not None:
            cond["string"] = string
        if num is not None:
            cond["num"] = num
        if date is not None:
            cond["date"] = date
        if time is not None:
            cond["time"] = time
        if date2 is not None:
            cond["date2"] = date2
        if time2 is not None:
            cond["time2"] = time2
        if unit is not None:
            cond["unit"] = unit

        return cond

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

class DSSTaggableObjectSettings(object):
    def __init__(self, taggable_object_data):
        self._tod = taggable_object_data

    @property
    def tags(self):
        """The tags of the object, as a list of strings"""
        return self._tod["tags"]

    @tags.setter
    def tags(self, tags):
        self._tod["tags"] = tags

    @property
    def description(self):
        """The description of the object as a string"""
        return self._tod.get("description", None)

    @description.setter
    def description(self, description):
        self._tod["description"] = description

    @property
    def short_description(self):
        """The short description of the object as a string"""
        return self._tod.get("shortDesc", None)

    @short_description.setter
    def short_description(self, short_description):
        self._tod["shortDesc"] = short_description

    @property
    def custom_fields(self):
        """The custom fields of the object as a dict. Returns None if there are no custom fields"""
        return self._tod.get("customFields", None)

    @custom_fields.setter
    def custom_fields(self, custom_fields):
        self._tod["customFields"] = custom_fields
