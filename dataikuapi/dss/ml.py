from ..utils import DataikuException
from ..utils import DataikuUTF8CSVReader
from ..utils import DataikuStreamedHttpUTF8CSVReader
import json
import time
from .metrics import ComputedMetrics
from .utils import DSSDatasetSelectionBuilder, DSSFilterBuilder

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
            "SVC_CLASSIFICATION" : "svc_classifier",
            "SGD_CLASSIFICATION" : "sgd_classifier",
            "SPARKLING_DEEP_LEARNING" : "deep_learning_sparkling",
            "SPARKLING_GBM" : "gbm_sparkling",
            "SPARKLING_RF" : "rf_sparkling",
            "SPARKLING_GLM" : "glm_sparkling",
            "SPARKLING_NB" : "nb_sparkling",
            "XGBOOST_CLASSIFICATION" : "xgboost",
            "XGBOOST_REGRESSION" : "xgboost",
            "MLLIB_LOGISTIC_REGRESSION" : "mllib_logit",
            "MLLIB_LINEAR_REGRESSION" : "mllib_linreg",
            "MLLIB_RANDOM_FOREST" : "mllib_rf"
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

    def ensemble(self, model_ids=[], method=None):
        """
        Create an ensemble model of a set of models
        
        :param list model_ids: A list of model identifiers
        :param str method: the ensembling method. One of: AVERAGE, PROBA_AVERAGE, MEDIAN, VOTE, LINEAR_MODEL, LOGISTIC_MODEL

        This method waits for the ensemble train to complete. If you want to train asynchronously, use :meth:`start_ensembling` and :meth:`wait_train_complete`

        This method returns the identifier of the trained ensemble.
        To get all identifiers for all models trained across all training sessions,
        use :meth:`get_trained_models_ids`

        This identifier can be used for :meth:`get_trained_model_snippet`, :meth:`get_trained_model_details` and :meth:`deploy_to_flow`

        :return: A model identifier
        :rtype: string
        """
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


    def start_ensembling(self, model_ids=[], method=None):
        """
        Creates asynchronously a new ensemble models of a set of models.

        :param list model_ids: A list of model identifiers
        :param str method: the ensembling method (AVERAGE, PROBA_AVERAGE, MEDIAN, VOTE, LINEAR_MODEL, LOGISTIC_MODEL)

        This returns immediately, before train is complete. To wait for train to complete, use :meth:`wait_train_complete`

        :return: the model identifier of the ensemble
        :rtype: string
        """
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

