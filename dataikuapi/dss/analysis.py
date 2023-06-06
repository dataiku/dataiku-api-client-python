from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import time
from .metrics import ComputedMetrics
from .ml import DSSMLTask
from .utils import DSSDatasetSelectionBuilder

class DSSAnalysisStepBuilder(object):
    def __init__(self, step_type=None, step_name=None):
        self.step = {'metaType':'PROCESSOR', 'type':step_type, 'name':step_name, 'params':{}}

    def build(self):
        """Returns the built step dict"""
        return self.step

    def with_type(self, step_type):
        """Sets the step's type"""
        self.step["type"] = step_type
        return self

    def with_name(self, step_name):
        """Sets the step's name"""
        self.step["name"] = step_name
        return self


class DSSAnalysisDefinition():
    """
    Object to manipulate the definition of a visual analysis
    """

    def __init__(self, analysis, acp):
        self.analysis = analysis
        self.acp = acp

    def get_raw(self):
        """
        Gets the raw dictionary of the visual analysis definition
        """
        return self.acp

    def get_raw_script(self):
        """
        Gets the raw dictionary of visual analysis' script settings (including steps, sampling, ...)
        """
        acp = self.get_raw()
        if not 'script' in acp:
            acp['script'] = {'steps':[]}
        return acp['script']

    def get_raw_script_steps(self):
        """
        Gets the raw dictionary of visual analysis' script steps
        """
        script = self.get_raw_script()
        if not 'steps' in script:
            script['steps'] = []
        return script['steps']

    def get_raw_script_sampling(self):
        """
        Gets the raw dictionary of visual analysis' script sampling
        """
        script = self.get_raw_script()
        if not 'explorationSampling' in script:
            script['explorationSampling'] = {}
        return script['explorationSampling']

    def save(self):
        """
        Shortcut to :meth:`DSSAnalysis.set_definition()`
        """
        self.analysis.set_definition(self)

    def add_step(self, step):
        """
        Add a step to the script

        :param object selection: A :class:`DSSAnalysisStepBuilder` to build the settings of the step.
        """
        steps = self.get_raw_script_steps()
        if isinstance(step, DSSAnalysisStepBuilder):
            steps.append(step.build())
        else:
            steps.append(step)

    def set_script_sampling_selection(self, selection):    
        """
        Sets the sampling for the script

        :param object selection: A :class:`DSSDatasetSelectionBuilder` to build the settings of the extract of the dataset.
        """
        sampling = self.get_raw_script_sampling()
        if isinstance(selection, DSSDatasetSelectionBuilder):
            sampling['selection'] = selection.build()
        else:
            sampling['selection'] = selection


class DSSAnalysis(object):
    """A handle to interact with a DSS visual analysis"""
    def __init__(self, client, project_key, analysis_id):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id

    ########################################################
    # Analysis deletion
    ########################################################

    def delete(self, drop_data=False):
        """
        Delete the dataset

        :param bool drop_data: Should the data of the dataset be dropped
        """
        return self.client._perform_empty("DELETE", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id))


    ########################################################
    # Analysis definition
    ########################################################

    def get_definition(self):
        """
        Get the definition of the analysis

        :return: a DSSAnalysisDefinition object to interact with the settings
        :rtype: :class:`dataikuapi.dss.analysis.DSSAnalysisDefinition`
        """
        acp = self.client._perform_json("GET", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id))
        return DSSAnalysisDefinition(self, acp)

    def set_definition(self, definition):
        """
        Set the definition of the analysis
        
        Args:
            definition: the definition, as a JSON object or a :class:`dataikuapi.dss.analysis.DSSAnalysisDefinition`.
            You should only set a definition object that has been retrieved using the get_definition call.
        """
        if isinstance(definition, DSSAnalysisDefinition):
            acp = definition.get_raw()
        else:
            acp = definition
        return self.client._perform_json("PUT", "/projects/%s/lab/%s/" % (self.project_key, self.analysis_id), body=acp)


    ########################################################
    # ML
    ########################################################

    def create_prediction_ml_task(self,
                                  target_variable,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="DEFAULT",
                                  prediction_type=None,
                                  wait_guess_complete=True):
        """Creates a new prediction task in this visual analysis lab
        for a dataset.

        :param string target_variable: Variable to predict
        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: DEFAULT, SIMPLE_FORMULA, DECISION_TREE, EXPLANATORY and PERFORMANCE
        :param string prediction_type: The type of prediction problem this is. If not provided the prediction type will be guessed. Valid values are: BINARY_CLASSIFICATION, REGRESSION, MULTICLASS
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        :return :class dataiku.dss.ml.DSSMLTask
        """

        obj = {
            "taskType" : "PREDICTION",
            "targetVariable" : target_variable,
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }
        if prediction_type is not None:
            obj["predictionType"] = prediction_type
        ref = self.client._perform_json("POST", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id), body=obj)
        mltask = DSSMLTask(self.client, self.project_key, self.analysis_id, ref["mlTaskId"])

        if wait_guess_complete:
            mltask.wait_guess_complete()
        return mltask

    def create_clustering_ml_task(self,
                                  ml_backend_type="PY_MEMORY",
                                  guess_policy="KMEANS",
                                  wait_guess_complete=True):
        """Creates a new clustering task in this visual analysis lab for a dataset.

        The returned ML task will be in 'guessing' state, i.e. analyzing
        the input dataset to determine feature handling and algorithms.

        You should wait for the guessing to be completed by calling
        ``wait_guess_complete`` on the returned object before doing anything
        else (in particular calling ``train`` or ``get_settings``)

        :param string ml_backend_type: ML backend to use, one of PY_MEMORY, MLLIB or H2O
        :param string guess_policy: Policy to use for setting the default parameters.  Valid values are: KMEANS and ANOMALY_DETECTION
        :param boolean wait_guess_complete: if False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        """

        obj = {
            "taskType" : "CLUSTERING",
            "backendType": ml_backend_type,
            "guessPolicy":  guess_policy
        }

        ref = self.client._perform_json("POST", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id), body=obj)
        mltask = DSSMLTask(self.client, self.project_key, self.analysis_id, ref["mlTaskId"])

        if wait_guess_complete:
            mltask.wait_guess_complete()
        return mltask

    def create_timeseries_forecasting_ml_task(self, target_variable,
                                              time_variable,
                                              timeseries_identifiers=None,
                                              guess_policy="TIMESERIES_DEFAULT",
                                              wait_guess_complete=True):
        """Creates a new time series forecasting task in this visual analysis lab for a dataset.

        :param string target_variable: The variable to forecast
        :param string time_variable:  Column to be used as time variable. Should be a Date (parsed) column.
        :param list timeseries_identifiers:  List of columns to be used as time series identifiers (when the dataset has multiple series)
        :param string guess_policy: Policy to use for setting the default parameters.
                                    Valid values are: TIMESERIES_DEFAULT, TIMESERIES_STATISTICAL, and TIMESERIES_DEEP_LEARNING
        :param boolean wait_guess_complete: If False, the returned ML task will be in 'guessing' state, i.e. analyzing the input dataset to determine feature handling and algorithms.
                                            You should wait for the guessing to be completed by calling
                                            ``wait_guess_complete`` on the returned object before doing anything
                                            else (in particular calling ``train`` or ``get_settings``)
        :return :class dataiku.dss.ml.DSSMLTask
        """
        obj = {
            "taskType": "PREDICTION",
            "targetVariable": target_variable,
            "timeVariable": time_variable,
            "timeseriesIdentifiers": timeseries_identifiers,
            "backendType": "PY_MEMORY",
            "guessPolicy":  guess_policy,
            "predictionType": "TIMESERIES_FORECAST"
        }

        ref = self.client._perform_json(
            "POST",
            "/projects/{project_key}/lab/{analysis_id}/models/".format(project_key=self.project_key, analysis_id=self.analysis_id),
            body=obj
        )
        mltask = DSSMLTask(self.client, self.project_key, self.analysis_id, ref["mlTaskId"])

        if wait_guess_complete:
            mltask.wait_guess_complete()
        return mltask

    def list_ml_tasks(self):
        """
        List the ML tasks in this visual analysis
        
        Returns:
            the list of the ML tasks summaries, each one as a JSON object
        """
        return self.client._perform_json("GET", "/projects/%s/lab/%s/models/" % (self.project_key, self.analysis_id))

    def get_ml_task(self, mltask_id):
        """
        Get a handle to interact with a specific ML task
       
        Args:
            mltask_id: the identifier of the desired ML task 
        
        Returns:
            A :class:`dataikuapi.dss.ml.DSSMLTask` ML task handle
        """
        return DSSMLTask(self.client, self.project_key, self.analysis_id, mltask_id)


# some basic steps
class DSSFormulaStepBuilder(DSSAnalysisStepBuilder):
    def __init__(self, step_name=None):
        super(DSSFormulaStepBuilder, self).__init__(step_type='CreateColumnWithGREL', step_name=step_name)

    def with_output_column(self, column_name):
        """Sets the step's output column's name"""
        self.step["params"]["column"] = column_name
        return self

    def with_error_column(self, column_name):
        """Sets the step's output column's name"""
        self.step["params"]["errorColumn"] = column_name
        return self

    def with_expression(self, expression):
        """Sets the step's expression"""
        self.step["params"]["expression"] = expression
        return self

class AppliesToStepBuilder(DSSAnalysisStepBuilder):
    def __init__(self, step_type=None, step_name=None):
        super(AppliesToStepBuilder, self).__init__(step_type=step_type, step_name=step_name)
        self.step["params"]["appliesTo"] = 'SINGLE_COLUMN'

    def with_column_selection_mode(self, column_selection_mode):
        """Sets the step's column selection mode (SINGLE_COLUMN, COLUMNS, PATTERN, ALL)"""
        self.step["params"]["appliesTo"] = column_selection_mode
        return self

    def with_columns(self, *column_names):
        """Sets the step's selected columns"""
        self.step["params"]["columns"] = [c for c in column_names]
        return self

    def with_column_regex(self, regex):
        """Sets the step's column selection regular expression"""
        self.step["params"]["appliesToPattern"] = regex
        return self

    def with_single_column_selection(self, column_name):
        """Sets the step's as applying to a single column"""
        return self.with_column_selection_mode('SINGLE_COLUMN').with_columns(column_name)

    def with_multiple_column_selection(self, *column_names):
        """Sets the step's as applying to a single column"""
        return self.with_column_selection_mode('COLUMNS').with_columns(column_names)

    def with_regex_column_selection(self, regex):
        """Sets the step's as applying to a single column"""
        return self.with_column_selection_mode('PATTERN').with_column_regex(regex)

    def with_all_column_selection(self, column_name):
        """Sets the step's as applying to all columns"""
        return self.with_column_selection_mode('ALL')

class FilterAndFlagStepBuilder(AppliesToStepBuilder):
    def __init__(self, step_type=None, step_name=None):
        super(FilterAndFlagStepBuilder, self).__init__(step_type=step_type, step_name=step_name)
        self.step["params"]["booleanMode"] = 'AND'
        self.step["params"]["action"] = 'REMOVE_ROW'

    def with_action(self, action):
        """Sets the step's action on match (KEEP_ROW, REMOVE_ROW, CLEAR_CELL, DONTCLEAR_CELL, FLAG)"""
        self.step["params"]["action"] = action
        return self

    def with_boolean_mode(self, boolean_mode):
        """Sets the step's mode for combining matches in different columns (AND, OR)"""
        self.step["params"]["booleanMode"] = boolean_mode
        return self

    def with_flag_column(self, column_name):
        """Sets the step's column for outputing the flag"""
        self.step["params"]["flagColumn"] = column_name
        return self

class FilterOnValueStepBuilder(FilterAndFlagStepBuilder):
    def __init__(self, step_name=None):
        super(FilterOnValueStepBuilder, self).__init__(step_type='FlagOnValue', step_name=step_name)

    def with_values(self, *values):
        """Sets the step's flagged values"""
        self.step["params"]["values"] = [v for v in values]
        return self

    def with_matching_mode(self, matching_mode):
        """Sets the step's matching_mode (FULL_STRING, SUBSTRING, PATTERN)"""
        self.step["params"]["matchingMode"] = matching_mode
        return self

    def with_normalization_mode(self, normalization_mode):
        """Sets the step's normalization_mode (EXACT, LOWERCASE, NORMALIZED)"""
        self.step["params"]["normalizationMode"] = normalization_mode
        return self

class FilterOnBadTypeStepBuilder(FilterAndFlagStepBuilder):
    def __init__(self, step_name=None):
        super(FilterOnBadTypeStepBuilder, self).__init__(step_type='FilterOnBadType', step_name=step_name)

    def with_meaning(self, meaning):
        """Sets the step's meaning to check"""
        self.step["params"]["type"] = meaning
        return self

class RemoveRowsStepBuilder(AppliesToStepBuilder):
    def __init__(self, step_name=None):
        super(RemoveRowsStepBuilder, self).__init__(step_type='RemoveRowsOnEmpty', step_name=step_name)

    def with_meaning(self, keep):
        """Sets the step's behavior when an empty value is found : True=keep, False=drop (default)"""
        self.step["params"]["keep"] = keep
        return self


