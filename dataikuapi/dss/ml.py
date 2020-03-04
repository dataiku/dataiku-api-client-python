from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import time
from .metrics import ComputedMetrics
from .utils import DSSDatasetSelectionBuilder, DSSFilterBuilder
from .future import DSSFuture

class PredictionSplitParamsHandler(object):
    """Object to modify the train/test splitting params."""

    def __init__(self, mltask_settings):
        """Do not call directly, use :meth:`DSSMLTaskSettings.get_split_params`"""
        self.mltask_settings = mltask_settings

    def set_split_random(self, train_ratio = 0.8, selection = None, dataset_name=None):
        """
        Sets the train/test split to random splitting of an extract of a single dataset

        :param float train_ratio: Ratio of rows to use for train set. Must be between 0 and 1
        :param object selection: A :class:`~dataikuapi.dss.utils.DSSDatasetSelectionBuilder` to build the settings of the extract of the dataset. May be None (won't be changed)
        :param str dataset_name: Name of dataset to split. If None, the main dataset used to create the visual analysis will be used.
        """
        sp = self.mltask_settings["splitParams"]
        sp["ttPolicy"] = "SPLIT_SINGLE_DATASET"
        if selection is not None:
            if isinstance(selection, DSSDatasetSelectionBuilder):
                sp["ssdSelection"] = selection.build()
            else:
                sp["ssdSelection"] = selection

        sp["ssdTrainingRatio"] = train_ratio
        sp["kfold"] = False

        if dataset_name is not None:
            sp["ssdDatasetSmartName"] = dataset_name

    def set_split_kfold(self, n_folds = 5, selection = None, dataset_name=None):
        """
        Sets the train/test split to k-fold splitting of an extract of a single dataset

        :param int n_folds: number of folds. Must be greater than 0
        :param object selection: A :class:`~dataikuapi.dss.utils.DSSDatasetSelectionBuilder` to build the settings of the extract of the dataset. May be None (won't be changed)
        :param str dataset_name: Name of dataset to split. If None, the main dataset used to create the visual analysis will be used.
        """
        sp = self.mltask_settings["splitParams"]
        sp["ttPolicy"] = "SPLIT_SINGLE_DATASET"
        if selection is not None:
            if isinstance(selection, DSSDatasetSelectionBuilder):
                sp["ssdSelection"] = selection.build()
            else:
                sp["ssdSelection"] = selection

        sp["kfold"] = True
        sp["nFolds"] = n_folds

        if dataset_name is not None:
            sp["ssdDatasetSmartName"] = dataset_name

    def set_split_explicit(self, train_selection, test_selection, dataset_name=None, test_dataset_name=None, train_filter=None, test_filter=None):
        """
        Sets the train/test split to explicit extract of one or two dataset(s)

        :param object train_selection: A :class:`~dataikuapi.dss.utils.DSSDatasetSelectionBuilder` to build the settings of the extract of the train dataset. May be None (won't be changed)
        :param object test_selection: A :class:`~dataikuapi.dss.utils.DSSDatasetSelectionBuilder` to build the settings of the extract of the test dataset. May be None (won't be changed)
        :param str dataset_name: Name of dataset to use for the extracts. If None, the main dataset used to create the ML Task will be used.
        :param str test_dataset_name: Name of a second dataset to use for the test data extract. If None, both extracts are done from dataset_name
        :param object train_filter: A :class:`~dataikuapi.dss.utils.DSSFilterBuilder` to build the settings of the filter of the train dataset. May be None (won't be changed)
        :param object test_filter: A :class:`~dataikuapi.dss.utils.DSSFilterBuilder` to build the settings of the filter of the test dataset. May be None (won't be changed)
        """
        sp = self.mltask_settings["splitParams"]
        if dataset_name is None:
            raise Exception("For explicit splitting a dataset_name is mandatory")
        if test_dataset_name is None or test_dataset_name == dataset_name:
            sp["ttPolicy"] = "EXPLICIT_FILTERING_SINGLE_DATASET"
            train_split ={}
            test_split = {}
            sp['efsdDatasetSmartName'] = dataset_name
            sp['efsdTrain'] = train_split
            sp['efsdTest'] = test_split
        else:
            sp["ttPolicy"] = "EXPLICIT_FILTERING_TWO_DATASETS"
            train_split ={'datasetSmartName' : dataset_name}
            test_split = {'datasetSmartName' : test_dataset_name}
            sp['eftdTrain'] = train_split
            sp['eftdTest'] = test_split

        if train_selection is not None:
            if isinstance(train_selection, DSSDatasetSelectionBuilder):
                train_split["selection"] = train_selection.build()
            else:
                train_split["selection"] = train_selection
        if test_selection is not None:
            if isinstance(test_selection, DSSDatasetSelectionBuilder):
                test_split["selection"] = test_selection.build()
            else:
                test_split["selection"] = test_selection

        if train_filter is not None:
            if isinstance(train_filter, DSSFilterBuilder):
                train_split["filter"] = train_filter.build()
            else:
                train_split["filter"] = train_filter
        if test_filter is not None:
            if isinstance(test_filter, DSSFilterBuilder):
                test_split["filter"] = test_filter.build()
            else:
                test_split["filter"] = test_filter


class DSSMLTaskSettings(object):
    """
    Object to read and modify the settings of a ML task.

    Do not create this object directly, use :meth:`DSSMLTask.get_settings()` instead
    """
    def __init__(self, client, project_key, analysis_id, mltask_id, mltask_settings):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id
        self.mltask_id = mltask_id
        self.mltask_settings = mltask_settings

    def get_raw(self):
        """
        Gets the raw settings of this ML Task. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.mltask_settings

    def get_split_params(self):
        """
        Gets an object to modify train/test splitting params.

        :rtype: :class:`PredictionSplitParamsHandler`
        """
        return PredictionSplitParamsHandler(self.mltask_settings)

    def split_ordered_by(self, feature_name, ascending=True):
        """
        Uses a variable to sort the data for train/test split and hyperparameter optimization
        :param str feature_name: Name of the variable to use
        :param bool ascending: True iff the test set is expected to have larger time values than the train set
        """
        self.remove_ordered_split()
        if not feature_name in self.mltask_settings["preprocessing"]["per_feature"]:
            raise ValueError("Feature %s doesn't exist in this ML task, can't use as time" % feature_name)
        self.mltask_settings['time']['enabled'] = True
        self.mltask_settings['time']['timeVariable'] = feature_name
        self.mltask_settings['time']['ascending'] = ascending
        self.mltask_settings['preprocessing']['per_feature'][feature_name]['missing_handling'] = "DROP_ROW"
        if self.mltask_settings['splitParams']['ttPolicy'] == "SPLIT_SINGLE_DATASET":
            self.mltask_settings['splitParams']['ssdSplitMode'] = "SORTED"
            self.mltask_settings['splitParams']['ssdColumn'] = feature_name
        if self.mltask_settings['modeling']['gridSearchParams']['mode'] == "KFOLD":
            self.mltask_settings['modeling']['gridSearchParams']['mode'] = "TIME_SERIES_KFOLD"
        elif self.mltask_settings['modeling']['gridSearchParams']['mode'] == "SHUFFLE":
            self.mltask_settings['modeling']['gridSearchParams']['mode'] = "TIME_SERIES_SINGLE_SPLIT"

    def remove_ordered_split(self):
        """
        Remove time-based ordering.
        """
        self.mltask_settings['time']['enabled'] = False
        self.mltask_settings['time']['timeVariable'] = None
        if self.mltask_settings['splitParams']['ttPolicy'] == "SPLIT_SINGLE_DATASET":
            self.mltask_settings['splitParams']['ssdSplitMode'] = "RANDOM"
            self.mltask_settings['splitParams']['ssdColumn'] = None
        if self.mltask_settings['modeling']['gridSearchParams']['mode'] == "TIME_SERIES_KFOLD":
            self.mltask_settings['modeling']['gridSearchParams']['mode'] = "KFOLD"
        elif self.mltask_settings['modeling']['gridSearchParams']['mode'] == "TIME_SERIES_SINGLE_SPLIT":
            self.mltask_settings['modeling']['gridSearchParams']['mode'] = "SHUFFLE"

    def get_feature_preprocessing(self, feature_name):
        """
        Gets the feature preprocessing params for a particular feature. This returns a reference to the
        feature's settings, not a copy, so changes made to the returned object will be reflected when saving

        :return: A dict of the preprocessing settings for a feature
        :rtype: dict 
        """
        return self.mltask_settings["preprocessing"]["per_feature"][feature_name]

    def foreach_feature(self, fn, only_of_type = None):
        """
        Applies a function to all features (except target)

        :param function fn: Function that takes 2 parameters: feature_name and feature_params and returns modified feature_params
        :param str only_of_type: if not None, only applies to feature of the given type. Can be one of ``CATEGORY``, ``NUMERIC``, ``TEXT`` or ``VECTOR``
        """
        import copy
        new_per_feature = {}
        for (k, v) in self.mltask_settings["preprocessing"]["per_feature"].items():
            if v["role"] == "TARGET" or (only_of_type is not None and v["type"] != only_of_type):
                new_per_feature[k] = v
            else:
                new_per_feature[k] = fn(k, copy.deepcopy(v))
        self.mltask_settings["preprocessing"]["per_feature"] = new_per_feature

    def reject_feature(self, feature_name):
        """
        Marks a feature as rejected and not used for training
        :param str feature_name: Name of the feature to reject
        """
        self.get_feature_preprocessing(feature_name)["role"] = "REJECT"

    def use_feature(self, feature_name):
        """
        Marks a feature as input for training
        :param str feature_name: Name of the feature to reject
        """
        self.get_feature_preprocessing(feature_name)["role"] = "INPUT"

    def use_sample_weighting(self, feature_name):
        """
        Uses a feature as sample weight
        :param str feature_name: Name of the feature to use
        """
        self.remove_sample_weighting()
        if not feature_name in self.mltask_settings["preprocessing"]["per_feature"]:
            raise ValueError("Feature %s doesn't exist in this ML task, can't use as weight" % feature_name)
        self.mltask_settings['weight']['weightMethod'] = 'SAMPLE_WEIGHT'
        self.mltask_settings['weight']['sampleWeightVariable'] = feature_name
        self.mltask_settings['preprocessing']['per_feature'][feature_name]['role'] = 'WEIGHT'

    def remove_sample_weighting(self):
        """
        Remove sample weighting. If a feature was used as weight, it's set back to being an input feature
        """
        self.mltask_settings['weight']['weightMethod'] = 'NO_WEIGHTING'
        for feature_name in self.mltask_settings['preprocessing']['per_feature']:
            if self.mltask_settings['preprocessing']['per_feature'][feature_name]['role'] == 'WEIGHT':
                 self.mltask_settings['preprocessing']['per_feature'][feature_name]['role'] = 'INPUT'

    def get_algorithm_settings(self, algorithm_name):
        """
        Gets the training settings for a particular algorithm. This returns a reference to the
        algorithm's settings, not a copy, so changes made to the returned object will be reflected when saving.

        This method returns a dictionary of the settings for this algorithm.
        All algorithm dicts have at least an "enabled" key in the dictionary.
        The 'enabled' key indicates whether this algorithm will be trained

        Other settings are algorithm-dependent and are the various hyperparameters of the 
        algorithm. The precise keys for each algorithm are not all documented. You can print
        the returned dictionary to learn more about the settings of each particular algorithm

        Please refer to the documentation for details on available algorithms.

        :param str algorithm_name: Name (in capitals) of the algorithm.
        :return: A dict of the settings for an algorithm
        :rtype: dict 
        """
        if algorithm_name in self.__class__.algorithm_remap:
            algorithm_name = self.__class__.algorithm_remap[algorithm_name]

        return self.mltask_settings["modeling"][algorithm_name.lower()]

    def set_algorithm_enabled(self, algorithm_name, enabled):
        """
        Enables or disables an algorithm based on its name.

        Please refer to the documentation for details on available algorithms.

        :param str algorithm_name: Name (in capitals) of the algorithm.
        """
        self.get_algorithm_settings(algorithm_name)["enabled"] = enabled

    def disable_all_algorithms(self):
        """Disables all algorithms"""

        for algorithm_name in self.__class__.algorithm_remap.keys():
            key = self.__class__.algorithm_remap[algorithm_name]
            if key in self.mltask_settings["modeling"]:
                self.mltask_settings["modeling"][key]["enabled"] = False

        for custom_mllib in self.mltask_settings["modeling"]["custom_mllib"]:
            custom_mllib["enabled"] = False
        for custom_python in self.mltask_settings["modeling"]["custom_python"]:
            custom_python["enabled"] = False
        for plugin in self.mltask_settings["modeling"]["plugin"].values():
            plugin["enabled"] = False

    def get_all_possible_algorithm_names():
        """
        Returns the list of possible algorithm names, i.e. the list of valid
        identifiers for :meth:`set_algorithm_enabled` and :meth:`get_algorithm_settings`

        This does not include Custom Python models, Custom MLLib models, plugin models.
        This includes all possible algorithms, regardless of the prediction kind (regression/classification)
        or engine, so some algorithms may be irrelevant

        :returns: the list of algorithm names as a list of strings
        :rtype: list of string
        """
        return self.__class__.algorithm_remap.keys()

    def set_metric(self, metric=None, custom_metric=None, custom_metric_greater_is_better=True, custom_metric_use_probas=False):
        """
        Sets the score metric to optimize for a prediction ML Task

        :param str metric: metric to use. Leave empty to use a custom metric. You need to set the ``custom_metric`` value in that case
        :param str custom_metric: code of the custom metric
        :param bool custom_metric_greater_is_better: whether the custom metric is a score or a loss
        :param bool custom_metric_use_probas: whether to use the classes' probas or the predicted value (for classification)
        """
        if custom_metric is None and metric is None:
            raise ValueError("Either metric or custom_metric must be defined")
        self.mltask_settings["modeling"]["metrics"]["evaluationMetric"] = metric if custom_metric is None else 'CUSTOM'
        self.mltask_settings["modeling"]["metrics"]["customEvaluationMetricCode"] = custom_metric
        self.mltask_settings["modeling"]["metrics"]["customEvaluationMetricGIB"] = custom_metric_greater_is_better
        self.mltask_settings["modeling"]["metrics"]["customEvaluationMetricNeedsProba"] = custom_metric_use_probas

    def save(self):
        """Saves back these settings to the ML Task"""

        self.client._perform_empty(
                "POST", "/projects/%s/models/lab/%s/%s/settings" % (self.project_key, self.analysis_id, self.mltask_id),
                body = self.mltask_settings)

class DSSPredictionMLTaskSettings(DSSMLTaskSettings):
    __doc__ = []
    algorithm_remap = {
            "RANDOM_FOREST_CLASSIFICATION": "random_forest_classification",
            "RANDOM_FOREST_REGRESSION" : "random_forest_regression",
            "EXTRA_TREES": "extra_trees",
            "GBT_CLASSIFICATION" : "gbt_classification",
            "GBT_REGRESSION" : "gbt_regression",
            "DECISION_TREE_CLASSIFICATION" : "decision_tree_classification",
            "DECISION_TREE_REGRESSION" : "decision_tree_regression",
            "RIDGE_REGRESSION": "ridge_regression",
            "LASSO_REGRESSION" : "lasso_regression",
            "LEASTSQUARE_REGRESSION": "leastsquare_regression",
            "SGD_REGRESSION" : "sgd_regression",
            "KNN": "knn",
            "LOGISTIC_REGRESSION" : "logistic_regression",
            "NEURAL_NETWORK" :"neural_network",
            "SVC_CLASSIFICATION" : "svc_classifier",
            "SVM_REGRESSION" : "svm_regression",
            "SGD_CLASSIFICATION" : "sgd_classifier",
            "LARS" : "lars_params",
            "XGBOOST_CLASSIFICATION" : "xgboost",
            "XGBOOST_REGRESSION" : "xgboost",
            "SPARKLING_DEEP_LEARNING" : "deep_learning_sparkling",
            "SPARKLING_GBM" : "gbm_sparkling",
            "SPARKLING_RF" : "rf_sparkling",
            "SPARKLING_GLM" : "glm_sparkling",
            "SPARKLING_NB" : "nb_sparkling",
            "MLLIB_LOGISTIC_REGRESSION" : "mllib_logit",
            "MLLIB_NAIVE_BAYES" : "mllib_naive_bayes",
            "MLLIB_LINEAR_REGRESSION" : "mllib_linreg",
            "MLLIB_RANDOM_FOREST" : "mllib_rf",
            "MLLIB_GBT": "mllib_gbt",
            "MLLIB_DECISION_TREE" : "mllib_dt",
            "VERTICA_LINEAR_REGRESSION" : "vertica_linear_regression",
            "VERTICA_LOGISTIC_REGRESSION" : "vertica_logistic_regression",
            "KERAS_CODE" : "keras"
        }


class DSSClusteringMLTaskSettings(DSSMLTaskSettings):
    __doc__ = []
    algorithm_remap = {
            "DBSCAN" : "db_scan_clustering",
        }



class DSSTrainedModelDetails(object):
    def __init__(self, details, snippet, saved_model=None, saved_model_version=None, mltask=None, mltask_model_id=None):
        self.details = details
        self.snippet = snippet
        self.saved_model = saved_model
        self.saved_model_version = saved_model_version
        self.mltask = mltask
        self.mltask_model_id = mltask_model_id

    def get_raw(self):
        """
        Gets the raw dictionary of trained model details
        """
        return self.details

    def get_raw_snippet(self):
        """
        Gets the raw dictionary of trained model snippet. 
        The snippet is a lighter version than the details.
        """
        return self.snippet

    def get_train_info(self):
        """
        Returns various information about the train process (size of the train set, quick description, timing information)

        :rtype: dict
        """
        return self.details["trainInfo"]

    def get_user_meta(self):
        """
        Gets the user-accessible metadata (name, description, cluster labels, classification threshold)
        Returns the original object, not a copy. Changes to the returned object are persisted to DSS by calling
        :meth:`save_user_meta`

        """
        return self.details["userMeta"]

    def save_user_meta(self):
        um = self.details["userMeta"]

        if self.mltask is not None:
            self.mltask.client._perform_empty(
                "PUT", "/projects/%s/models/lab/%s/%s/models/%s/user-meta" % (self.mltask.project_key,
                    self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id), body = um)
        else:
            self.saved_model.client._perform_empty(
                "PUT", "/projects/%s/savedmodels/%s/versions/%s/user-meta" % (self.saved_model.project_key,
                    self.saved_model.sm_id, self.saved_model_version), body = um)

class DSSTreeNode(object):
    def __init__(self, tree, i):
        self.tree = tree
        self.i = i

    def get_left_child(self):
        """Gets a :class:`dataikuapi.dss.ml.DSSTreeNode` representing the left side of the tree node (or None)"""
        left = self.tree.tree['leftChild'][self.i]
        if left < 0:
            return None
        else:
            return DSSTreeNode(self.tree, left)

    def get_right_child(self):
        """Gets a :class:`dataikuapi.dss.ml.DSSTreeNode` representing the right side of the tree node (or None)"""
        left = self.tree.tree['rightChild'][self.i]
        if left < 0:
            return None
        else:
            return DSSTreeNode(self.tree, left)

    def get_split_info(self):
        """Gets the information on the split, as a dict"""
        info = {}
        features = self.tree.tree.get("feature", None)
        probas = self.tree.tree.get("probas", None)
        leftCategories = self.tree.tree.get("leftCategories", None)
        impurities = self.tree.tree.get("impurity", None)
        predicts = self.tree.tree.get("predict", None)
        thresholds = self.tree.tree.get("threshold", None)
        nSamples = self.tree.tree.get("nSamples", None)
        info['feature'] = self.tree.feature_names[features[self.i]] if features is not None else None
        info['probas'] = probas[self.i] if probas is not None else None
        info['leftCategories'] = leftCategories[self.i] if leftCategories is not None else None
        info['impurity'] = impurities[self.i] if impurities is not None else None
        info['predict'] = predicts[self.i] if predicts is not None else None
        info['nSamples'] = nSamples[self.i] if nSamples is not None else None
        info['threshold'] = thresholds[self.i] if thresholds is not None else None
        return info

class DSSTree(object):
    def __init__(self, tree, feature_names):
        self.tree = tree
        self.feature_names = feature_names

    def get_raw(self):
        """Gets the raw tree data structure"""
        return self.tree

    def get_root(self):
        """Gets a :class:`dataikuapi.dss.ml.DSSTreeNode` representing the root of the tree"""
        return DSSTreeNode(self, 0)

class DSSTreeSet(object):
    def __init__(self, trees):
        self.trees = trees

    def get_raw(self):
        """Gets the raw trees data structure"""
        return self.trees

    def get_feature_names(self):
        """Gets the list of feature names (after dummification) """
        return self.trees["featureNames"]

    def get_trees(self):
        """Gets the list of trees as :class:`dataikuapi.dss.ml.DSSTree` """
        return [DSSTree(t, self.trees["featureNames"]) for t in self.trees["trees"]]

class DSSCoefficientPaths(object):
    def __init__(self, paths):
        self.paths = paths

    def get_raw(self):
        """Gets the raw paths data structure"""
        return self.paths

    def get_feature_names(self):
        """Get the feature names (after dummification)"""
        return self.paths['features']

    def get_coefficient_path(self, feature, class_index=0):
        """Get the path of the feature"""
        i = self.paths['features'].index(feature)
        if i >= 0 and i < len(self.paths['path'][0][class_index]):
            n = len(self.paths['path'])
            return [self.paths['path'][j][class_index][i] for j in range(0, n)]
        else:
            return None

class DSSScatterPlots(object):
    def __init__(self, scatters):
        self.scatters = scatters

    def get_raw(self):
        """Gets the raw scatters data structure"""
        return self.scatters

    def get_feature_names(self):
        """Get the feature names (after dummification)"""
        feature_names = []
        for k in self.scatters['features']:
            feature_names.append(k)
        return feature_names

    def get_scatter_plot(self, feature_x, feature_y):
        """Get the scatter plot between feature_x and feature_y"""
        ret = {'cluster':self.scatters['cluster'], 'x':self.scatters['features'].get(feature_x, None), 'y':self.scatters['features'].get(feature_x, None)}
        return ret

class DSSTrainedPredictionModelDetails(DSSTrainedModelDetails):
    """
    Object to read details of a trained prediction model

    Do not create this object directly, use :meth:`DSSMLTask.get_trained_model_details()` instead
    """

    def __init__(self, details, snippet, saved_model=None, saved_model_version=None, mltask=None, mltask_model_id=None):
        DSSTrainedModelDetails.__init__(self, details, snippet, saved_model, saved_model_version, mltask, mltask_model_id)

    def get_roc_curve_data(self):
        roc = self.details.get("perf", {}).get("rocVizData",{})
        if roc is None:
            raise ValueError("This model does not have ROC visualization data")

        return roc

    def get_performance_metrics(self):
        """
        Returns all performance metrics for this model.

        For binary classification model, this includes both "threshold-independent" metrics like AUC and
        "threshold-dependent" metrics like precision. Threshold-dependent metrics are returned at the
        threshold value that was found to be optimal during training.

        To get access to the per-threshold values, use the following:

        .. code-block:: python

            # Returns a list of tested threshold values
            details.get_performance()["perCutData"]["cut"]
            # Returns a list of F1 scores at the tested threshold values
            details.get_performance()["perCutData"]["f1"]
            # Both lists have the same length

        If K-Fold cross-test was used, most metrics will have a "std" variant, which is the standard deviation
        accross the K cross-tested folds. For example, "auc" will be accompanied with "aucstd"

        :returns: a dict of performance metrics values
        :rtype: dict
        """
        import copy
        clean_snippet = copy.deepcopy(self.snippet)
        for x in ["gridsearchData", "trainDate", "topImportance", "backendType", "userMeta", "sessionDate", "trainInfo", "fullModelId", "gridLength", "algorithm", "sessionId"]:
            if x in clean_snippet:
                del clean_snippet[x]
        return clean_snippet


    def get_hyperparameter_search_points(self):
        """
        Gets the list of points in the hyperparameter search space that have been tested.

        Returns a list of dict. Each entry in the list represents a point.

        For each point, the dict contains at least:
            - "score": the average value of the optimization metric over all the folds at this point
            - "params": a dict of the parameters at this point. This dict has the same structure 
               as the params of the best parameters
        """

        if not "gridCells" in self.details["iperf"]:
            raise ValueError("No hyperparameter search result, maybe this model did not perform hyperparameter optimization")
        return self.details["iperf"]["gridCells"]

    def get_preprocessing_settings(self):
        """
        Gets the preprocessing settings that were used to train this model

        :rtype: dict
        """
        return self.details["preprocessing"]

    def get_modeling_settings(self):
        """
        Gets the modeling (algorithms) settings that were used to train this model.

        Note: the structure of this dict is not the same as the modeling params on the ML Task
        (which may contain several algorithm)

        :rtype: dict
        """
        return self.details["modeling"]

    def get_actual_modeling_params(self):
        """
        Gets the actual / resolved parameters that were used to train this model, post
        hyperparameter optimization.

        :return: A dictionary, which contains at least a "resolved" key, which is a dict containing the post-optimization parameters
        :rtype: dict
        """
        return self.details["actualParams"]

    def get_trees(self):
        """
        Gets the trees in the model (for tree-based models) 

        :return: a DSSTreeSet object to interact with the trees
        :rtype: :class:`dataikuapi.dss.ml.DSSTreeSet`
        """
        data = self.mltask.client._perform_json(
            "GET", "/projects/%s/models/lab/%s/%s/models/%s/trees" % (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id))
        if data is None:
            raise ValueError("This model has no tree data")
        return DSSTreeSet(data)

    def get_coefficient_paths(self):
        """
        Gets the coefficient paths for Lasso models

        :return: a DSSCoefficientPaths object to interact with the coefficient paths
        :rtype: :class:`dataikuapi.dss.ml.DSSCoefficientPaths`
        """
        data = self.mltask.client._perform_json(
            "GET", "/projects/%s/models/lab/%s/%s/models/%s/coef-paths" % (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id))
        if data is None:
            raise ValueError("This model has no coefficient paths")
        return DSSCoefficientPaths(data)

    ## Model export

    def get_scoring_jar_stream(self, model_class="model.Model", include_libs=False):
        """
        Get a scoring jar for this trained model,
        provided that you have the license to do so and that the model is compatible with optimized scoring.
        You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :param str  model_class: fully-qualified class name, e.g. "com.company.project.Model"
        :param bool include_libs: if True, also packs the required dependencies;
                if False, runtime will require the scoring libs given by :func:`DSSClient.scoring_libs`
        :returns: a jar file, as a stream
        :rtype: file-like
        """
        include_libs = "true" if include_libs else "false"
        if self.mltask is not None:
            return self.mltask.client._perform_raw(
                "GET", "/projects/%s/models/lab/%s/%s/models/%s/scoring-jar?fullClassName=%s&includeLibs=%s" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id,
                model_class, include_libs))
        else:
            return self.saved_model.client._perform_raw(
                "GET", "/projects/%s/savedmodels/%s/versions/%s/scoring-jar?fullClassName=%s&includeLibs=%s" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version,
                model_class, include_libs))

    def get_scoring_pmml_stream(self):
        """
        Get a scoring PMML for this trained model,
        provided that you have the license to do so and that the model is compatible with PMML scoring
        You need to close the stream after download. Failure to do so will result in the DSSClient becoming unusable.

        :returns: a PMML file, as a stream
        :rtype: file-like
        """
        if self.mltask is not None:
            return self.mltask.client._perform_raw(
                "GET", "/projects/%s/models/lab/%s/%s/models/%s/scoring-pmml" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id))
        else:
            return self.saved_model.client._perform_raw(
                "GET", "/projects/%s/savedmodels/%s/versions/%s/scoring-pmml" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version))

    ## Post-train computations

    def compute_subpopulation_analyses(self, split_by, wait=True, sample_size=1000, random_state=1337, n_jobs=1, debug_mode=False):
        """
        Launch computation of Subpopulation analyses for this trained model.

        :param list|str split_by: column(s) on which subpopulation analyses are to be computed (one analysis per column)
        :param bool wait: if True, the call blocks until the computation is finished and returns the results directly
        :param int sample_size: number of records of the dataset to use for the computation 
        :param int random_state: random state to use to build sample, for reproducibility
        :param int n_jobs: number of cores used for parallel training. (-1 means 'all cores')
        :param bool debug_mode: if True, output all logs (slower)

        :returns: if wait is True, an object containing the Subpopulation analyses, else a future to wait on the result
        :rtype: :class:`dataikuapi.dss.ml.DSSSubpopulationAnalyses` or :class:`dataikuapi.dss.future.DSSFuture`
        """
        body = {
            "features": split_by if isinstance(split_by, list) else [split_by],
            "computationParams": {
                "sample_size": sample_size,
                "random_state": random_state,
                "n_jobs": n_jobs,
                "debug_mode": debug_mode,
            }}
        if self.mltask is not None:
            future_response = self.mltask.client._perform_json(
                "POST", "/projects/%s/models/lab/%s/%s/models/%s/subpopulation-analyses" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id),
                body=body
            )
            future = DSSFuture(self.mltask.client, future_response.get("jobId", None), future_response)
        else:
            future_response = self.saved_model.client._perform_json(
                "POST", "/projects/%s/savedmodels/%s/versions/%s/subpopulation-analyses" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version),
                body=body
            )
            future = DSSFuture(self.saved_model.client, future_response.get("jobId", None), future_response)
        if wait:
            prediction_type = self.details.get("coreParams", {}).get("prediction_type")
            return DSSSubpopulationAnalyses(future.wait_for_result(), prediction_type)
        else:
            return future


    def get_subpopulation_analyses(self):
        """
        Retrieve all subpopulation analyses computed for this trained model
        
        :returns: the subpopulation analyses
        :rtype: :class:`dataikuapi.dss.ml.DSSSubpopulationAnalyses`
        """
        
        if self.mltask is not None:
            data = self.mltask.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/models/%s/subpopulation-analyses" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id)
            )
        else:
            data = self.saved_model.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions/%s/subpopulation-analyses" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version),
            )
        prediction_type = self.details.get("coreParams", {}).get("prediction_type")
        return DSSSubpopulationAnalyses(data, prediction_type)

    def compute_partial_dependencies(self, features, wait=True, sample_size=1000, random_state=1337, n_jobs=1, debug_mode=False):
        """
        Launch computation of Partial dependencies for this trained model.

        :param list|str features: feature(s) on which partial dependencies are to be computed
        :param bool wait: if True, the call blocks until the computation is finished and returns the results directly
        :param int sample_size: number of records of the dataset to use for the computation 
        :param int random_state: random state to use to build sample, for reproducibility
        :param int n_jobs: number of cores used for parallel training. (-1 means 'all cores')
        :param bool debug_mode: if True, output all logs (slower)

        :returns: if wait is True, an object containing the Partial dependencies, else a future to wait on the result
        :rtype: :class:`dataikuapi.dss.ml.DSSPartialDependencies` or :class:`dataikuapi.dss.future.DSSFuture`
        """

        body = {
            "features": features if isinstance(features, list) else [features],
            "computationParams": {
                "sample_size": sample_size,
                "random_state": random_state,
                "n_jobs": n_jobs,
                "debug_mode": debug_mode,
            }}
        if self.mltask is not None:
            future_response = self.mltask.client._perform_json(
                "POST", "/projects/%s/models/lab/%s/%s/models/%s/partial-dependencies" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id),
                body=body
            )
            future = DSSFuture(self.mltask.client, future_response.get("jobId", None), future_response)
        else:
            future_response = self.saved_model.client._perform_json(
                "POST", "/projects/%s/savedmodels/%s/versions/%s/partial-dependencies" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version),
                body=body
            )
            future = DSSFuture(self.saved_model.client, future_response.get("jobId", None), future_response)
        if wait:
            return DSSPartialDependencies(future.wait_for_result()) 
        else:
            return future

    def get_partial_dependencies(self):
        """
        Retrieve all partial dependencies computed for this trained model

        :returns: the partial dependencies
        :rtype: :class:`dataikuapi.dss.ml.DSSPartialDependencies`
        """

        if self.mltask is not None:
            data = self.mltask.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/models/%s/partial-dependencies" %
                (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id)
            )
        else:
            data = self.saved_model.client._perform_json(
                "GET", "/projects/%s/savedmodels/%s/versions/%s/partial-dependencies" %
                (self.saved_model.project_key, self.saved_model.sm_id, self.saved_model_version),
            )
        return DSSPartialDependencies(data)


class DSSSubpopulationGlobal(object):
    """
    Object to read details of performance on global population used for subpopulation analyses.

    Do not create this object directly, use :meth:`DSSSubpopulationAnalyses.get_global()` instead
    """

    def __init__(self, data, prediction_type):
        self._internal_dict = data
        self.prediction_type = prediction_type

    def get_raw(self):
        """
        Gets the raw dictionary of the global subpopulation performance

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        return "{cls}(prediction_type={type})".format(cls=self.__class__.__name__, type=self.prediction_type)

    def get_performance_metrics(self):
        """
        Gets the performance results of the global population used for the subpopulation analysis
        """
        return self._internal_dict["performanceMetrics"]

    def get_prediction_info(self):
        """
        Gets the prediction info of the global population used for the subpopulation analysis
        """
        global_metrics = self._internal_dict["perf"]["globalMetrics"]
        if self.prediction_type == "BINARY_CLASSIFICATION":
            return {
                "predictedPositiveRatio": global_metrics["predictionAvg"][0],
                "actualPositiveRatio": global_metrics["targetAvg"][0],
                "testWeight": global_metrics["testWeight"]
            }
        elif self.prediction_type == "REGRESSION":
            return {
                "predictedAvg":global_metrics["predictionAvg"][0],
                "predictedStd":global_metrics["predictionStd"][0],
                "actualAvg":global_metrics["targetAvg"][0],
                "actualStd":global_metrics["targetStd"][0],
                "testWeight":global_metrics["testWeight"]
            }


class DSSSubpopulationModality(object):
    """
    Object to read details of a subpopulation analysis modality

    Do not create this object directly, use :meth:`DSSSubpopulationAnalysis.get_modality_data(definition)` instead
    """

    def __init__(self, feature_name, computed_as_type, data, prediction_type):
        self._internal_dict = data
        self.prediction_type = prediction_type
        if computed_as_type == "CATEGORY":
            self.definition = DSSSubpopulationCategoryModalityDefinition(feature_name, data)
        elif computed_as_type == "NUMERIC":
            self.definition = DSSSubpopulationNumericModalityDefinition(feature_name, data)

    def get_raw(self):
        """
        Gets the raw dictionary of the subpopulation analysis modality

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        computed_as_type = "CATEGORY" if isinstance(self.definition, DSSSubpopulationCategoryModalityDefinition) else 'NUMERIC'
        return "{cls}(prediction_type={type}, feature={feature}, computed_as={computed_as_type})".format(
            cls=self.__class__.__name__,
            type=self.prediction_type,
            feature=self.definition.feature_name,
            computed_as_type=computed_as_type)

    def get_definition(self):
        """
        Gets the definition of the subpopulation analysis modality

        :returns: definition
        :rtype: :class:`dataikuapi.dss.ml.DSSSubpopulationModalityDefinition`
        """
        return self.definition
    
    def is_excluded(self):
        """
        Whether modality has been excluded from analysis (e.g. too few rows in the subpopulation)
        """
        return self._internal_dict.get("excluded", False)

    def get_performance_metrics(self):
        """
        Gets the performance results of the modality
        """
        if self.is_excluded():
            raise ValueError("Excluded modalities do not have performance metrics")
        return self._internal_dict["performanceMetrics"]

    def get_prediction_info(self):
        """
        Gets the prediction info of the modality
        """
        if self.is_excluded():
            raise ValueError("Excluded modalities do not have prediction info")
        global_metrics = self._internal_dict["perf"]["globalMetrics"]
        if self.prediction_type == "BINARY_CLASSIFICATION":
            return {
                "predictedPositiveRatio": global_metrics["predictionAvg"][0],
                "actualPositiveRatio": global_metrics["targetAvg"][0],
                "testWeight": global_metrics["testWeight"]
            }
        elif self.prediction_type == "REGRESSION":
            return {
                "predictedAvg":global_metrics["predictionAvg"][0],
                "predictedStd":global_metrics["predictionStd"][0],
                "actualAvg":global_metrics["targetAvg"][0],
                "actualStd":global_metrics["targetStd"][0],
                "testWeight":global_metrics["testWeight"]
            }


class DSSSubpopulationModalityDefinition(object):

    MISSING_VALUES = "__DSSSubpopulationModalidityDefinition__MISSINGVALUES"

    def __init__(self, feature_name, data):
        self.missing_values = data.get("missing_values", False)
        self.index = data.get("index")
        self.feature_name = feature_name
    
    def is_missing_values(self):
        return self.missing_values


class DSSSubpopulationNumericModalityDefinition(DSSSubpopulationModalityDefinition):
    
    def __init__(self, feature_name, data):
        super(DSSSubpopulationNumericModalityDefinition, self).__init__(feature_name, data)
        self.lte = data.get("lte", None)
        self.gt = data.get("gt", None)
        self.gte = data.get("gte", None)
    
    def contains(self, value):
        lte = self.lte if self.lte is not None else float("inf")
        gt = self.gt if self.gt is not None else float("-inf")
        gte = self.gte if self.gte is not None else float("-inf")
        return not self.missing_values and gt < value and gte <= value and lte >= value
    
    def __repr__(self):
        if self.missing_values:
            return "DSSSubpopulationNumericModalityDefinition(missing_values)"
        else:
            if self.gt is not None:
                repr_gt = "%s<" % self.gt
            elif self.gte is not None:
                repr_gt = "%s<=" % self.gte
            else:
                repr_gt = ""

            if self.lte is not None:
                repr_lt = "<=%s" % self.lte
            else:
                repr_lt = ""

            return "DSSSubpopulationNumericModalityDefinition(%s%s%s)" % (repr_gt, self.feature_name, repr_lt)

class DSSSubpopulationCategoryModalityDefinition(DSSSubpopulationModalityDefinition):

    def __init__(self, feature_name, data):
        super(DSSSubpopulationCategoryModalityDefinition, self).__init__(feature_name, data)
        self.value = data.get("value", None)
    
    def contains(self, value):
        return value == self.value

    def __repr__(self):
        if self.missing_values:
            return "DSSSubpopulationCategoryModalityDefinition(missing_values)"
        else:
            return "DSSSubpopulationCategoryModalityDefinition(%s='%s')" % (self.feature_name, self.value)


class DSSSubpopulationAnalysis(object):
    """
    Object to read details of a subpopulation analysis of a trained model

    Do not create this object directly, use :meth:`DSSSubpopulationAnalyses.get_analysis(feature)` instead
    """

    def __init__(self, analysis, prediction_type):
        self._internal_dict = analysis
        self.computed_as_type = analysis["computed_as_type"]
        self.modalities = [DSSSubpopulationModality(analysis["feature"], self.computed_as_type, m, prediction_type) for m in analysis.get("modalities", [])]

    def get_raw(self):
        """
        Gets the raw dictionary of the subpopulation analysis

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        return "{cls}(computed_as_type={type}, feature={feature}, modalities_count={modalities_count})".format(
            cls=self.__class__.__name__,
            type=self.computed_as_type,
            feature=self._internal_dict["feature"],
            modalities_count=len(self.modalities))

    def get_computation_params(self):
        """
        Gets computation params
        """
        return {
            "nbRecords":  self._internal_dict["nbRecords"],
            "randomState":  self._internal_dict["randomState"],
            "onSample":  self._internal_dict["onSample"]
        }
    
    def list_modalities(self):
        """
        List definitions of modalities
        """
        return [m.definition for m in self.modalities]

    def get_modality_data(self, definition):
        """
        Retrieves modality from definition

        :param definition: definition of modality to retrieve. Can be:
                   * :class:`dataikuapi.dss.ml.DSSSubpopulationModalityDefinition`
                   * `dataikuapi.dss.ml.DSSSubpopulationModalityDefinition.MISSING_VALUES` 
                      to retrieve modality corresponding to missing values
                   * for category modality, can be a str corresponding to the value of the modality
                   * for numeric modality, can be a number inside the modality

        :returns: the modality
        :rtype: :class:`dataikuapi.dss.ml.DSSSubpopulationModality`
        """

        if definition == DSSSubpopulationModalityDefinition.MISSING_VALUES:
            for m in self.modalities:
                if m.definition.missing_values:
                    return m
            raise ValueError("No 'missing values' modality found")

        if isinstance(definition, DSSSubpopulationModalityDefinition):
            modality_candidates = [m for m in self.modalities if m.definition.index == definition.index]
            if len(modality_candidates) == 0:
                raise ValueError("Modality with index '%s' not found" % definition.index)
            return modality_candidates[0]
        
        for m in self.modalities:
            if m.definition.contains(definition):
                return m
        raise ValueError("Modality not found: %s" % definition)


class DSSSubpopulationAnalyses(object):
    """
    Object to read details of subpopulation analyses of a trained model

    Do not create this object directly, use :meth:`DSSTrainedPredictionModelDetails.get_subpopulation_analyses()` instead
    """

    def __init__(self, data, prediction_type):
        self._internal_dict = data
        self.prediction_type = prediction_type
        self.analyses = []
        for analysis in data.get("subpopulationAnalyses", []):
            self.analyses.append(DSSSubpopulationAnalysis(analysis, prediction_type))

    def get_raw(self):
        """
        Gets the raw dictionary of subpopulation analyses

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        return "{cls}(prediction_type={type}, analyses={analyses})".format(cls=self.__class__.__name__,
                                                                           type=self.prediction_type,
                                                                           analyses=self.list_analyses())
    def get_global(self):
        """
        Retrieves information and performance on the full dataset used to compute the subpopulation analyses
        """
        return DSSSubpopulationGlobal(self._internal_dict["global"], self.prediction_type)

    def list_analyses(self):
        """
        Lists all features on which subpopulation analyses have been computed
        """
        return [analysis.get_raw()["feature"] for analysis in self.analyses]
    
    def get_analysis(self, feature):
        """
        Retrieves the subpopulation analysis for a particular feature
        """
        try:
            return next(analysis for analysis in self.analyses if analysis.get_raw()["feature"] == feature)
        except StopIteration:
            raise ValueError("Subpopulation analysis for feature '%s' cannot be found" % feature)


class DSSPartialDependence(object):
    """
    Object to read details of partial dependence of a trained model

    Do not create this object directly, use :meth:`DSSPartialDependencies.get_partial_dependence(feature)` instead
    """

    def __init__(self, data):
        self._internal_dict = data

    def get_raw(self):
        """
        Gets the raw dictionary of the partial dependence

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        return "{cls}(feature={feature})".format(cls=self.__class__.__name__, feature=self._internal_dict["feature"])

    def get_computation_params(self):
        """
        Gets computation params
        """
        return {
            "nbRecords":  self._internal_dict["nbRecords"],
            "randomState":  self._internal_dict["randomState"],
            "onSample":  self._internal_dict["onSample"]
        }


class DSSPartialDependencies(object):
    """
    Object to read details of partial dependencies of a trained model

    Do not create this object directly, use :meth:`DSSTrainedPredictionModelDetails.get_partial_dependencies()` instead
    """

    def __init__(self, data):
        self._internal_dict = data
        self.partial_dependencies = []
        for pd in data.get("partialDependencies", []):
            self.partial_dependencies.append(DSSPartialDependence(pd))

    def get_raw(self):
        """
        Gets the raw dictionary of partial dependencies

        :rtype: dict
        """
        return self._internal_dict

    def __repr__(self):
        return "{cls}(features={features})".format(cls=self.__class__.__name__, features=self.list_features())

    def list_features(self):
        """
        Lists all features on which partial dependencies have been computed
        """
        return [partial_dep.get_raw()["feature"] for partial_dep in self.partial_dependencies]

    def get_partial_dependence(self, feature):
        """
        Retrieves the partial dependencies for a particular feature
        """
        try:
            return next(pd for pd in self.partial_dependencies if pd.get_raw()["feature"] == feature)
        except StopIteration:
            raise ValueError("Partial dependence for feature '%s' cannot be found" % feature)


class DSSClustersFacts(object):
    def __init__(self, clusters_facts):
        self.clusters_facts = clusters_facts

    def get_raw(self):
        """Gets the raws facts data structure"""
        return self.clusters_facts

    def get_cluster_size(self, cluster_index):
        """Gets the size of a cluster identified by its index"""
        return self.clusters_facts["clusters"][cluster_index]["size"]

    def get_facts_for_cluster(self, cluster_index):
        """
        Gets all facts for a cluster identified by its index. Returns a list of dicts

        :rtype: list
        """
        return self.clusters_facts["clusters"][cluster_index]["facts"]

    def get_facts_for_cluster_and_feature(self, cluster_index, feature_name):
        """
        Gets all facts for a cluster identified by its index, limited to a feature name. Returns a list of dicts

        :rtype: list
        """
        return [x for x in self.get_facts_for_cluster(cluster_index) if x["feature_label"] == feature_name]


class DSSTrainedClusteringModelDetails(DSSTrainedModelDetails):
    """
    Object to read details of a trained clustering model

    Do not create this object directly, use :meth:`DSSMLTask.get_trained_model_details()` instead
    """

    def __init__(self, details, snippet, saved_model=None, saved_model_version=None, mltask=None, mltask_model_id=None):
        DSSTrainedModelDetails.__init__(self, details, snippet, saved_model, saved_model_version, mltask, mltask_model_id)


    def get_raw(self):
        """
        Gets the raw dictionary of trained model details
        """
        return self.details

    def get_train_info(self):
        """
        Returns various information about the train process (size of the train set, quick description, timing information)

        :rtype: dict
        """
        return self.details["trainInfo"]

    def get_facts(self):
        """
        Gets the 'cluster facts' data, i.e. the structure behind the screen "for cluster X, average of Y is Z times higher than average

        :rtype: :class:`DSSClustersFacts`
        """
        return DSSClustersFacts(self.details["facts"])

    def get_performance_metrics(self):
        """
        Returns all performance metrics for this clustering model.
        :returns: a dict of performance metrics values
        :rtype: dict
        """
        import copy
        clean_snippet = copy.deepcopy(self.snippet)
        for x in ["fullModelId", "algorithm", "trainInfo", "userMeta", "backendType", "sessionId", "sessionDate", "facts"]:
            if x in clean_snippet:
                del clean_snippet[x]
        return clean_snippet

    def get_preprocessing_settings(self):
        """
        Gets the preprocessing settings that were used to train this model

        :rtype: dict
        """
        return self.details["preprocessing"]

    def get_modeling_settings(self):
        """
        Gets the modeling (algorithms) settings that were used to train this model.

        Note: the structure of this dict is not the same as the modeling params on the ML Task
        (which may contain several algorithm)

        :rtype: dict
        """
        return self.details["modeling"]

    def get_actual_modeling_params(self):
        """
        Gets the actual / resolved parameters that were used to train this model.
        :return: A dictionary, which contains at least a "resolved" key
        :rtype: dict
        """
        return self.details["actualParams"]

    def get_scatter_plots(self):
        """
        Gets the cluster scatter plot data 

        :return: a DSSScatterPlots object to interact with the scatter plots
        :rtype: :class:`dataikuapi.dss.ml.DSSScatterPlots`
        """
        scatters = self.mltask.client._perform_json(
            "GET", "/projects/%s/models/lab/%s/%s/models/%s/scatter-plots" % (self.mltask.project_key, self.mltask.analysis_id, self.mltask.mltask_id, self.mltask_model_id))
        return DSSScatterPlots(scatters)


class DSSMLTask(object):
    """A handle to interact with a MLTask for prediction or clustering in a DSS visual analysis"""
    def __init__(self, client, project_key, analysis_id, mltask_id):
        self.client = client
        self.project_key = project_key
        self.analysis_id = analysis_id
        self.mltask_id = mltask_id

    def delete(self):
        """
        Delete the present ML task
        """
        return self.client._perform_json(
                "DELETE", "/projects/%s/models/lab/%s/%s/" % (self.project_key, self.analysis_id, self.mltask_id))


    def wait_guess_complete(self):
        """
        Waits for guess to be complete. This should be called immediately after the creation of a new ML Task
        (if the ML Task was created with wait_guess_complete=False),
        before calling ``get_settings`` or ``train``
        """
        while True:
            status = self.get_status()
            if status.get("guessing", "???") == False:
                break
            time.sleep(0.2)


    def get_status(self):
        """
        Gets the status of this ML Task

        :return: a dict
        """
        return self.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/status" % (self.project_key, self.analysis_id, self.mltask_id))


    def get_settings(self):
        """
        Gets the settings of this ML Tasks

        :return: a DSSMLTaskSettings object to interact with the settings
        :rtype: :class:`dataikuapi.dss.ml.DSSMLTaskSettings`
        """
        settings =  self.client._perform_json(
                "GET", "/projects/%s/models/lab/%s/%s/settings" % (self.project_key, self.analysis_id, self.mltask_id))

        if settings["taskType"] == "PREDICTION":
            return DSSPredictionMLTaskSettings(self.client, self.project_key, self.analysis_id, self.mltask_id, settings)
        else:
            return DSSClusteringMLTaskSettings(self.client, self.project_key, self.analysis_id, self.mltask_id, settings)

    def train(self, session_name=None, session_description=None):
        """
        Trains models for this ML Task
        
        :param str session_name: name for the session
        :param str session_description: description for the session

        This method waits for train to complete. If you want to train asynchronously, use :meth:`start_train` and :meth:`wait_train_complete`

        This method returns the list of trained model identifiers. It returns models that have been trained  for this train
        session, not all trained models for this ML task. To get all identifiers for all models trained across all training sessions,
        use :meth:`get_trained_models_ids`

        These identifiers can be used for :meth:`get_trained_model_snippet`, :meth:`get_trained_model_details` and :meth:`deploy_to_flow`

        :return: A list of model identifiers
        :rtype: list of strings
        """
        train_ret = self.start_train(session_name, session_description)
        self.wait_train_complete()
        return self.get_trained_models_ids(session_id = train_ret["sessionId"])

    def ensemble(self, model_ids=None, method=None):
        """
        Create an ensemble model of a set of models
        
        :param list model_ids: A list of model identifiers (defaults to `[]`)
        :param str method: the ensembling method. One of: AVERAGE, PROBA_AVERAGE, MEDIAN, VOTE, LINEAR_MODEL, LOGISTIC_MODEL

        This method waits for the ensemble train to complete. If you want to train asynchronously, use :meth:`start_ensembling` and :meth:`wait_train_complete`

        This method returns the identifier of the trained ensemble.
        To get all identifiers for all models trained across all training sessions,
        use :meth:`get_trained_models_ids`

        This identifier can be used for :meth:`get_trained_model_snippet`, :meth:`get_trained_model_details` and :meth:`deploy_to_flow`

        :return: A model identifier
        :rtype: string
        """
        if model_ids is None:
            model_ids = []
        train_ret = self.start_ensembling(model_ids, method)
        self.wait_train_complete()
        return train_ret


    def start_train(self, session_name=None, session_description=None):
        """
        Starts asynchronously a new train session for this ML Task.

        :param str session_name: name for the session
        :param str session_description: description for the session

        This returns immediately, before train is complete. To wait for train to complete, use ``wait_train_complete()``
        """
        session_info = {
                            "sessionName" : session_name,
                            "sessionDescription" : session_description
                        }

        return self.client._perform_json(
                "POST", "/projects/%s/models/lab/%s/%s/train" % (self.project_key, self.analysis_id, self.mltask_id), body=session_info)


    def start_ensembling(self, model_ids=None, method=None):
        """
        Creates asynchronously a new ensemble models of a set of models.

        :param list model_ids: A list of model identifiers (defaults to `[]`)
        :param str method: the ensembling method (AVERAGE, PROBA_AVERAGE, MEDIAN, VOTE, LINEAR_MODEL, LOGISTIC_MODEL)

        This returns immediately, before train is complete. To wait for train to complete, use :meth:`wait_train_complete`

        :return: the model identifier of the ensemble
        :rtype: string
        """
        if model_ids is None:
            model_ids = []
        ensembling_request = {
                            "method" : method,
                            "modelsIds" : model_ids
                        }

        return self.client._perform_json(
                "POST", "/projects/%s/models/lab/%s/%s/ensemble" % (self.project_key, self.analysis_id, self.mltask_id), body=ensembling_request)['id']


    def wait_train_complete(self):
        """
        Waits for train to be complete (if started with :meth:`start_train`)
        """
        while True:
            status = self.get_status()
            if status.get("training", "???") == False:
                break
            time.sleep(2)


    def get_trained_models_ids(self, session_id=None, algorithm=None):
        """
        Gets the list of trained model identifiers for this ML task.

        These identifiers can be used for :meth:`get_trained_model_snippet` and :meth:`deploy_to_flow`

        :return: A list of model identifiers
        :rtype: list of strings
        """
        full_model_ids = self.get_status()["fullModelIds"]
        if session_id is not None:
            full_model_ids = [fmi for fmi in full_model_ids if fmi.get('fullModelId', {}).get('sessionId', '') == session_id]
        model_ids = [x["id"] for x in full_model_ids]
        if algorithm is not None:
            # algorithm is in the snippets
            model_ids = [fmi for fmi, s in self.get_trained_model_snippet(ids=model_ids).iteritems() if s.get("algorithm", "") == algorithm]
        return model_ids


    def get_trained_model_snippet(self, id=None, ids=None):
        """
        Gets a quick summary of a trained model, as a dict. For complete information and a structured object, use :meth:`get_trained_model_detail`

        :param str id: a model id
        :param list ids: a list of model ids

        :rtype: dict
        """
        if id is not None:
            obj = {
                "modelsIds" : [id]
            }
        elif ids is not None:
            obj = {
                "modelsIds" : ids
            }
        else:
            obj = {}

        ret = self.client._perform_json(
            "GET", "/projects/%s/models/lab/%s/%s/models-snippets" % (self.project_key, self.analysis_id, self.mltask_id),
            body = obj)
        if id is not None:
            return ret[id]
        else:
            return ret

    def get_trained_model_details(self, id):
        """
        Gets details for a trained model
        
        :param str id: Identifier of the trained model, as returned by :meth:`get_trained_models_ids`

        :return: A :class:`DSSTrainedPredictionModelDetails` or :class:`DSSTrainedClusteringModelDetails` representing the details of this trained model id
        :rtype: :class:`DSSTrainedPredictionModelDetails` or :class:`DSSTrainedClusteringModelDetails`
        """
        ret = self.client._perform_json(
            "GET", "/projects/%s/models/lab/%s/%s/models/%s/details" % (self.project_key, self.analysis_id, self.mltask_id,id))
        snippet = self.get_trained_model_snippet(id)

        if "facts" in ret:
            return DSSTrainedClusteringModelDetails(ret, snippet, mltask=self, mltask_model_id=id)
        else:
            return DSSTrainedPredictionModelDetails(ret, snippet, mltask=self, mltask_model_id=id)

    def deploy_to_flow(self, model_id, model_name, train_dataset, test_dataset=None, redo_optimization=True):
        """
        Deploys a trained model from this ML Task to a saved model + train recipe in the Flow.

        :param str model_id: Model identifier, as returned by :meth:`get_trained_models_ids`
        :param str model_name: Name of the saved model to deploy in the Flow
        :param str train_dataset: Name of the dataset to use as train set. May either be a short name or a PROJECT.name long name (when using a shared dataset)
        :param str test_dataset: Name of the dataset to use as test set. If null, split will be applied to the train set. May either be a short name or a PROJECT.name long name (when using a shared dataset). Only for PREDICTION tasks
        :param bool redo_optimization: Should the hyperparameters optimization phase be done ? Defaults to True. Only for PREDICTION tasks
        :return: A dict containing: "savedModelId" and "trainRecipeName" - Both can be used to obtain further handles
        :rtype: dict
        """
        obj = {
            "trainDatasetRef" : train_dataset,
            "testDatasetRef" : test_dataset,
            "modelName" : model_name,
            "redoOptimization":  redo_optimization
        }
        return self.client._perform_json(
            "POST", "/projects/%s/models/lab/%s/%s/models/%s/actions/deployToFlow" % (self.project_key, self.analysis_id, self.mltask_id, model_id),
            body = obj)


    def redeploy_to_flow(self, model_id, recipe_name=None, saved_model_id=None, activate=True):
        """
        Redeploys a trained model from this ML Task to a saved model + train recipe in the Flow. Either 
        recipe_name of saved_model_id need to be specified

        :param str model_id: Model identifier, as returned by :meth:`get_trained_models_ids`
        :param str recipe_name: Name of the training recipe to update
        :param str saved_model_id: Name of the saved model to update
        :param bool activate: Should the deployed model version become the active version 
        :return: A dict containing: "impactsDownstream" - whether the active version changed and downstream recipes are impacted 
        :rtype: dict
        """
        obj = {
            "recipeName" : recipe_name,
            "savedModelId" : saved_model_id,
            "activate" : activate
        }
        return self.client._perform_json(
            "POST", "/projects/%s/models/lab/%s/%s/models/%s/actions/redeployToFlow" % (self.project_key, self.analysis_id, self.mltask_id, model_id),
            body = obj)

    def guess(self, prediction_type=None):
        """
        Guess the feature handling and the algorithms.
        :param string prediction_type: In case of a prediction problem the prediction type can be specify. Valid values are BINARY_CLASSIFICATION, REGRESSION, MULTICLASS.
        """
        obj = {}
        if prediction_type is not None:
            obj["predictionType"] = prediction_type

        self.client._perform_empty(
            "PUT",
            "/projects/%s/models/lab/%s/%s/guess" % (self.project_key, self.analysis_id, self.mltask_id),
            params = obj)
