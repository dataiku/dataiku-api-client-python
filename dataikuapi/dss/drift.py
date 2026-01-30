import warnings


class DataDriftParams(object):
    """
    Object that represents parameters for data drift computation.

    .. warning::
        Do not create this object directly, use :meth:`dataikuapi.dss.modelevaluationstore.DataDriftParams.from_params` instead.

    .. attention::
        Deprecated. Use :class:`dataikuapi.dss.modelevaluationstore.DriftParams` instead
    """

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.data)

    @staticmethod
    def from_params(per_column_settings, nb_bins=10, compute_histograms=True, confidence_level=0.95):
        """
        Creates parameters for data drift computation from columns, number of bins, compute histograms and confidence level

        :param dict per_column_settings: A dict representing the per column settings.
            You should use a :class:`~dataikuapi.dss.modelevaluationstore.PerColumnDriftParamBuilder` to build it.
        :param int nb_bins: (optional) Nb. bins in histograms (apply to all columns) - default: 10
        :param bool compute_histograms: (optional) Enable/disable histograms - default: True
        :param float confidence_level: (optional) Used to compute confidence interval on drift's model accuracy - default: 0.95

        :rtype: :class:`dataikuapi.dss.modelevaluationstore.DataDriftParams`
        """
        warnings.warn("This method is deprecated. Use DriftParams.from_params() instead", DeprecationWarning)

        return DataDriftParams(
            {
                "columns": per_column_settings,
                "nbBins": nb_bins,
                "computeHistograms": compute_histograms,
                "confidenceLevel": confidence_level,
            }
        )


class DriftParams(object):
    """
    Object that represents parameters for drift computation.

    .. warning::
        Do not create this object directly, use :meth:`dataikuapi.dss.modelevaluationstore.DriftParams.from_params` instead.
    """

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.data)

    @staticmethod
    def from_params(per_column_settings, nb_bins=10, compute_histograms=True, confidence_level=0.95):
        """
        Creates parameters for drift computation from columns, number of bins, compute histograms and confidence level

        :param dict per_column_settings: A dict representing the per column settings.
            You should use a :class:`~dataikuapi.dss.modelevaluationstore.PerColumnDriftParamBuilder` to build it.
        :param int nb_bins: (optional) Nb. bins in histograms (apply to all columns) - default: 10
        :param bool compute_histograms: (optional) Enable/disable histograms - default: True
        :param float confidence_level: (optional) Used to compute confidence interval on drift's model accuracy - default: 0.95

        :rtype: :class:`dataikuapi.dss.modelevaluationstore.DriftParams`
        """
        return DriftParams(
            {
                "columns": per_column_settings,
                "nbBins": nb_bins,
                "computeHistograms": compute_histograms,
                "confidenceLevel": confidence_level,
            }
        )


class PerColumnDriftParamBuilder(object):
    """
    Builder for a map of per column drift params settings.
    Used as a helper before computing data drift to build columns param expected in
    :meth:`dataikuapi.dss.modelevaluationstore.DataDriftParams.from_params`.
    """

    def __init__(self):
        self.columns = {}

    def build(self):
        """Returns the built dict for per column drift params settings"""
        return self.columns

    def with_column_drift_param(self, name, handling="AUTO", enabled=True):
        """
        Sets the drift params settings for given column name.

        :param: string name: The name of the column
        :param: string handling: (optional) The column type, should be either NUMERICAL, CATEGORICAL or AUTO (default: AUTO)
        :param: bool enabled: (optional) False means the column is ignored in drift computation (default: True)
        """
        self.columns[name] = {"handling": handling, "enabled": enabled}
        return self


class DataDriftResult(object):
    """
    A handle on the data drift result of a model evaluation.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation.compute_data_drift`
    """

    def __init__(self, data):
        self.data = data
        self.drift_model_result = DriftModelResult(self.data["driftModelResult"])
        """Drift analysis based on drift modeling."""
        self.univariate_drift_result = UnivariateDriftResult(self.data["univariateDriftResult"])
        """Per-column drift analysis based on pairwise comparison of distributions."""
        self.per_column_settings = [ColumnSettings(cs) for cs in self.data["perColumnSettings"]]
        """Information about column handling that has been used (errors, types, etc)."""

    def get_raw(self):
        """
        :return: the raw data drift result
        :rtype: dict
        """
        return self.data


class DriftResult(object):
    """
    A handle on the drift result of a model evaluation.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DSSModelEvaluation.compute_drift`

    """

    def __init__(self, data):
        self.data = data
        self.drift_model_result = (
            DriftModelResult(self.data["driftModelResult"]) if "driftModelResult" in self.data else None
        )
        """Drift analysis based on drift modeling."""
        self.univariate_drift_result = (
            UnivariateDriftResult(self.data["univariateDriftResult"]) if "univariateDriftResult" in self.data else None
        )
        """Per-column drift analysis based on pairwise comparison of distributions."""
        self.per_column_settings = (
            [ColumnSettings(cs) for cs in self.data["perColumnSettings"]] if "perColumnSettings" in self.data else None
        )
        """Information about column handling that has been used (errors, types, etc)."""
        self.prediction_drift_result = (
            PredictionDriftResult(self.data["predictionDriftResult"]) if "predictionDriftResult" in self.data else None
        )
        """Drift analysis based on the prediction column"""

    def get_raw(self):
        """
        :return: the raw data drift result
        :rtype: dict
        """
        return self.data


class DriftModelResult(object):
    """
    A handle on the drift model result.

    .. warning::
        Do not create this class directly, instead use :attr:`dataikuapi.dss.modelevaluationstore.DriftResult.drift_model_result`
    """

    def __init__(self, data):
        self.data = data
        self.drift_model_accuracy = DriftModelAccuracy(self.data["driftModelAccuracy"])
        self.feature_drift_importance = self.data["driftVersusImportance"]  # type: dict

    def get_raw(self):
        """
        :return: the raw drift model result
        :rtype: dict
        """
        return self.data


class UnivariateDriftResult(object):
    """
    A handle on the univariate data drift.

    .. warning::
        Do not create this class directly, instead use :attr:`dataikuapi.dss.modelevaluationstore.DriftResult.univariate_drift_result`
    """

    def __init__(self, data):
        self.data = data
        self.per_column_drift_data = self.data["columns"]  # type: dict
        """Drift data per column, as a dict of column name -> drift data."""

    def get_raw(self):
        """
        :return: the raw univariate data drift
        :rtype: dict
        """
        return self.data


class PredictionDriftResult(object):
    """
    A handle on the prediction drift result.

    .. warning::
        Do not create this class directly, instead use :attr:`dataikuapi.dss.modelevaluationstore.DriftResult.prediction_drift_result`
    """

    def __init__(self, data):
        self.data = data
        self.chiSquare = self.data.get("chiSquareTestPvalue", None)
        self.ks = self.data.get("ksTestPvalue", None)
        self.psi = self.data.get("populationStabilityIndex", None)

    def get_raw(self):
        """
        :return: the raw prediction drift
        :rtype: dict
        """
        return self.data


class ColumnSettings(object):
    """
    A handle on column handling information.

    .. warning::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.modelevaluationstore.DriftResult.get_per_column_settings`
    """

    def __init__(self, data):
        self.data = data
        self.name = self.data["name"]  # type: str
        self.actual_column_handling = self.data["actualHandling"]  # type: str
        """The actual column handling (either forced via drift params or inferred from model evaluation preprocessings).
        It can be any of NUMERICAL, CATEGORICAL, or IGNORED."""
        self.default_column_handling = self.data["defaultHandling"]  # type: str
        """The default column handling (based on model evaluation preprocessing only).
        It can be any of NUMERICAL, CATEGORICAL, or IGNORED."""
        self.error_message = self.data.get("errorMessage", None)

    def get_raw(self):
        """
        :return: the raw column handling information
        :rtype: dict
        """
        return self.data


class DriftModelAccuracy(object):
    """
    A handle on the drift model accuracy.

    .. warning::
        Do not create this class directly, instead use :attr:`dataikuapi.dss.modelevaluationstore.DriftModelResult.drift_model_accuracy`
    """

    def __init__(self, data):
        self.data = data
        self.value = self.data["value"]  # type: float
        self.lower_confidence_interval = self.data["lower"]  # type: float
        self.upper_confidence_interval = self.data["upper"]  # type: float
        self.pvalue = self.data["pvalue"]  # type: float

    def get_raw(self):
        """
        :return: the drift model accuracy data
        :rtype: dict
        """
        return self.data
