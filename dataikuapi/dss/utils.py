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
        """
        :returns: the built selection dict
        :rtype: dict
        """
        return self.selection

    def with_head_sampling(self, limit):
        """
        Sets the sampling to 'first records' mode

        :param int limit: Maximum number of rows in the sample
        """
        self.selection["samplingMethod"] = "HEAD_SEQUENTIAL"
        self.selection["maxRecords"] = limit
        return self

    def with_all_data_sampling(self):
        """Sets the sampling to 'no sampling, all data' mode"""
        self.selection["samplingMethod"] = "FULL"
        return self

    def with_random_fixed_nb_sampling(self, nb):
        """
        Sets the sampling to 'Random sampling, fixed number of records' mode

        :param int nb: Maximum number of rows in the sample
        """
        self.selection["samplingMethod"] = "RANDOM_FIXED_NB"
        self.selection["maxRecords"] = nb
        return self

    def with_selected_partitions(self, ids):
        """
        Sets partition filtering on the given partition identifiers.

        .. warning::
            The dataset to select must be partitioned.

        :param list ids: list of selected partitions
        """
        self.selection["partitionSelectionMethod"] = "SELECTED"
        self.selection["selectedPartitions"] = ids
        return self


class DSSComputedColumn(object):

    @staticmethod
    def formula(name, formula, type="double"):
        """
        Create a computed column with a formula.

        :param string name: a name for the computed column
        :param string formula: formula to compute values, using the `GREL language <https://doc.dataiku.com/dss/latest/formula/index.html>`_ 
        :param string type: name of a DSS type for the values of the column

        :return: a computed column as a dict
        :rtype: dict
        """
        return {"expr": formula, "mode": "GREL", "name": name, "type": type}

import sys
if sys.version_info > (3,4):
    from enum import Enum
else:
    class Enum(object):
        pass

class DSSFilterOperator(Enum):
    EMPTY_ARRAY = "empty array"
    """
    Test if an array is empty.
    """

    NOT_EMPTY_ARRAY = "not empty array"
    """
    Test if an array is not empty.
    """

    CONTAINS_ARRAY = "array contains"
    """
    Test if an array contains a value.
    """

    NOT_EMPTY = "not empty"
    """
    Test if a value is not empty and not null.
    """

    EMPTY = "is empty"
    """
    Test if a value is empty or null.
    """

    NOT_EMPTY_STRING = "not empty string"
    """
    Test if a string is not empty.
    """

    EMPTY_STRING = "empty string"
    """
    Test if a string is empty.
    """

    IS_TRUE = "true"
    """
    Test if a boolean is true.
    """

    IS_FALSE = "false"
    """
    Test if a boolean is false.
    """

    EQUALS_STRING = "== [string]"
    """
    Test if a string is equal to a given value.
    """

    EQUALS_CASE_INSENSITIVE_STRING = "== [string]i"
    """
    Test if a string is equal to a given value, ignoring case.
    """

    NOT_EQUALS_STRING = "!= [string]"
    """
    Test if a string is not equal to a given value.
    """

    SAME = "== [NaNcolumn]"
    """
    Test if two columns have the same value when formatted to string.
    """

    DIFFERENT = "!= [NaNcolumn]"
    """
    Test if two columns have different values when formatted to string.
    """

    EQUALS_NUMBER = "== [number]"
    """
    Test if a number is equal to a given value.
    """

    NOT_EQUALS_NUMBER = "!= [number]"
    """
    Test if a number is not equal to a given value.
    """

    GREATER_NUMBER = ">  [number]"
    """
    Test if a number is greater than a given value.
    """

    LESS_NUMBER = "<  [number]"
    """
    Test if a number is less than a given value.
    """

    GREATER_OR_EQUAL_NUMBER = ">= [number]"
    """
    Test if a number is greater or equal to a given value.
    """

    LESS_OR_EQUAL_NUMBER = "<= [number]"
    """
    Test if a number is less or equal to a given value.
    """

    EQUALS_DATE = "== [date]"
    """
    Test if a date/time is equal to a given date/time (rounded).
    """

    GREATER_DATE = ">  [date]"
    """
    Test if a date/time is greater than a given date/time.
    """

    GREATER_OR_EQUAL_DATE = ">= [date]"
    """
    Test if a date/time is greater or equal than a given date/time.
    """

    LESS_DATE = "<  [date]"
    """
    Test if a date/time is less than a given date/time.
    """

    LESS_OR_EQUAL_DATE = "<= [date]"
    """
    Test if a date/time is less or equal than a given date/time.
    """

    BETWEEN_DATE = ">< [date]"
    """
    Test if a date/time is between two given date/times.
    """

    EQUALS_COL = "== [column]"
    """
    Test if two columns have the same (typed) value.
    """

    NOT_EQUALS_COL = "!= [column]"
    """
    Test if two columns have different (typed) values.
    """

    GREATER_COL = ">  [column]"
    """
    Test if one column is greater than another.
    """

    LESS_COL = "<  [column]"
    """
    Test if one column is less than another.
    """

    GREATER_OR_EQUAL_COL = ">= [column]"
    """
    Test if one column is greater or equal than another.
    """

    LESS_OR_EQUAL_COL = "<= [column]"
    """
    Test if one column is less or equal than another.
    """

    CONTAINS_STRING = "contains"
    """
    Test if a column contains a given string.
    """

    REGEX = "regex"
    """
    Test if a column matches a regular expression.
    """


class DSSFilter(object):
    """
    Helper class to build filter objects for use in visual recipes.
    """

    @staticmethod
    def of_single_condition(column, operator, string=None, num=None, date=None, time=None, date2=None, time2=None, unit=None):
        """
        Create a simple filter on a column.

        Which of the 'string', 'num', 'date', 'time', 'date2' and 'time2' parameter holds the literal to filter against
        depends on the filter operator.

        :param string column: name of a column to filter (left operand)
        :param string operator: type of filter applied to the column, one of the values in the :class:`DSSFilterOperator` enum
        :param string string: string literal for the right operand 
        :param string num: numeric literal for the right operand 
        :param string date: date part literal for the right operand 
        :param string time: time part literal for the right operand 
        :param string date2: date part literal for the right operand of BETWEEN_DATE
        :param string time2: time part literal for the right operand of BETWEEN_DATE
        :param string unit: date/time rounding for date operations. Possible values are YEAR, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND
        """
        return {
            "enabled": True,
            "uiData": {
                'conditions': [DSSFilter.condition(column, operator, string, num, date, time, date2, time2, unit)],
                "mode": "&&"
            }
        }

    @staticmethod
    def of_and_conditions(conditions):
        """
        Create a filter as an intersection of conditions.

        The resulting filter keeps rows that match all the conditions in the list. Conditions are
        for example the output of :meth:`condition()`.

        :param list conditions: a list of conditions

        :return: a filter, as a dict
        :rtype: dict
        """
        return {
            "enabled": True,
            "uiData": {
                'conditions': conditions,
                "mode": "&&"
            }
        }

    @staticmethod
    def of_or_conditions(conditions):
        """
        Create a filter as an union of conditions.

        The resulting filter keeps rows that match any of the conditions in the list. Conditions are
        for example the output of :meth:`condition()`.

        :param list conditions: a list of conditions

        :return: a filter, as a dict
        :rtype: dict
        """
        return {
            "enabled": True,
            "uiData": {
                'conditions': conditions,
                "mode": "||"
            }
        }

    @staticmethod
    def of_formula(formula):
        """
        Create a filter that applies a GREL formula.

        The resulting filter evaluates the formula and keeps rows for which the formula returns
        a True value.

        :param string formula: a `GREL formula <https://doc.dataiku.com/dss/latest/formula/index.html>`_

        :return: a filter, as a dict
        :rtype: dict
        """
        return {
            "enabled": True,
            "uiData": {
                "mode": "CUSTOM"
            },
            "expression": formula
        }

    @staticmethod
    def of_sql_expression(sql_expression):
        """
        Create a filter that applies a SQL expression.

        The resulting filter evaluates the sql expression and keeps rows for which the sql expression returns
        a True value.

        :param string sql_expression: a SQL expression

        :return: a filter, as a dict
        :rtype: dict
        """
        return {
            "enabled": True,
            "uiData": {
                "mode": "SQL"
            },
            "expression": sql_expression
        }

    @staticmethod
    def condition(column, operator, string=None, num=None, date=None, time=None, date2=None, time2=None, unit=None):
        """
        Create a condition on a column for a filter.

        Which of the 'string', 'num', 'date', 'time', 'date2' and 'time2' parameter holds the literal to filter against
        depends on the filter operator.

        :param string column: name of a column to filter (left operand)
        :param string operator: type of filter applied to the column, one of the values in the :class:`DSSFilterOperator` enum
        :param string string: string literal for the right operand 
        :param string num: numeric literal for the right operand 
        :param string date: date part literal for the right operand 
        :param string time: time part literal for the right operand 
        :param string date2: date part literal for the right operand of BETWEEN_DATE
        :param string time2: time part literal for the right operand of BETWEEN_DATE
        :param string unit: date/time rounding for date operations. Possible values are YEAR, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND
        """
        if isinstance(operator, DSSFilterOperator):
            operator = operator.value
        cond = {
            "input": column,
            "operator": operator
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
        self.filter = {"enabled": False, "distinct": False, "expression": None, "uiData": {"mode": "CUSTOM"}}

    def build(self):
        """
        :returns: the built filter
        :rtype: dict
        """
        return self.filter

    def with_distinct(self):
        """Sets the filter to deduplicate"""
        self.filter["distinct"] = True
        return self

    def with_formula(self, expression):
        """
        Sets the formula (DSS formula) used to filter rows

        :param str expression: the DSS formula
        """
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


class DSSInfoMessages(object):
    """
    Contains a list of :class:`dataikuapi.dss.utils.DSSInfoMessage`.

    .. important::
        Do not instantiate this class.
    """

    def __init__(self, data):
        self._data = data

    def __repr__(self):
        return "DSSInfoMessages(has_messages: {}, max_severity: {}, has_error: {}, has_warning: {}, has_success: {}, messages: {})".format(
            self.has_messages,
            self.max_severity,
            self.has_error,
            self.has_warning,
            self.has_success,
            "[...]" if self.has_messages else "[]"
        )

    @property
    def messages(self):
        """The messages as a list of :class:`dataikuapi.dss.utils.DSSInfoMessage`"""
        return [DSSInfoMessage(message) for message in self._data.get("messages", [])]

    @property
    def has_messages(self):
        """`True` if there is any message"""
        return self._data.get("anyMessage", False)

    @property
    def has_error(self):
        """`True` if there is any error message"""
        return self._data.get("error", False)

    @property
    def max_severity(self):
        """The max severity of the messages"""
        return self._data.get("maxSeverity", None)

    @property
    def has_success(self):
        """`True` if there is any success message"""
        return self._data.get("success", False)

    @property
    def has_warning(self):
        """`True` if there is any warning message"""
        return self._data.get("warning", False)


class DSSInfoMessage(object):
    """
    A message with a code, a title, a severity and a content. 

    .. important::
        Do not instantiate this class.
    """

    def __init__(self, data):
        self._data = data

    def __str__(self):
        return "{severity} - {title} - {details}".format(
            severity=self.severity,
            title=self.title,
            details=self.details
        )

    @property
    def severity(self):
        """The severity of the message"""
        return self._data.get("severity", None)

    @property
    def code(self):
        """The code of the message"""
        return self._data.get("code", None)

    @property
    def details(self):
        """The details of the message"""
        return self._data.get("details", None)

    @property
    def title(self):
        """The title of the message"""
        return self._data.get("title", None)

    @property
    def message(self):
        """The full message"""
        return self._data.get("message", None)
