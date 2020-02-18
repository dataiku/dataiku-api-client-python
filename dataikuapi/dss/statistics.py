from ..utils import DataikuException
from .utils import DSSDatasetSelectionBuilder
from .future import DSSFuture
from ..utils import DSSInternalDict
import json
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions


class DSSStatisticsWorksheet(object):
    """
    A handle to interact with a worksheet.
    """

    def __init__(self, client, project_key, dataset_name, worksheet_id):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.worksheet_id = worksheet_id

    def delete(self):
        """
        Deletes the worksheet
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s/statistics/worksheets/%s" % (self.project_key, self.dataset_name, self.worksheet_id))

    def get_settings(self):
        """
        Fetches the settings of this worksheet.

        :return: an object to interact with the settings
        :rtype: :class:`DSSStatisticsWorksheetSettings`
        """
        worksheet_json = self.client._perform_json(
            "GET", "/projects/%s/datasets/%s/statistics/worksheets/%s" % (
                self.project_key, self.dataset_name, self.worksheet_id)
        )
        return DSSStatisticsWorksheetSettings(self.client, self.project_key,
                                              self.dataset_name, self.worksheet_id, worksheet_json)

    def run_worksheet(self, wait=True):
        """
        Computes the results of the whole worksheet.

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle
        """

        root_card = self.get_settings().get_raw()['rootCard']
        return self.run_card(root_card, wait=wait)

    def run_card(self, card, wait=True):
        """
        Runs a card in the context of the worksheet.

        Note: the card does not need to belong to the worksheet.

        :param card: a card to compute
        :type card: :class:`DSSStatisticsCardSettings` or dict (obtained from ``DSSStatisticsCardSettings.get_raw()``)
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of computing card's results
        """

        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        future_response = self.client._perform_json(
            "POST",
            "/projects/%s/datasets/%s/statistics/worksheets/%s/actions/run-card" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=card.get_raw()
        )
        future = DSSFuture(self.client, future_response.get(
            "jobId", None), future_response)
        return future.wait_for_result() if wait else future

    def run_computation(self, computation, wait=True):
        """
        Runs a computation in the context of the worksheet.

        :param computation: a card to compute
        :type computation: :class:`DSSStatisticsComputationSettings` or dict (obtained from ``DSSStatisticsComputationSettings.get_raw()``)
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of computing computation's results
        """

        computation = DSSStatisticsComputationSettings._from_computation_or_dict(
            computation)
        future_response = self.client._perform_json(
            "POST",
            "/projects/%s/datasets/%s/statistics/worksheets/%s/actions/run-computation" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=computation.get_raw()
        )
        future = DSSFuture(self.client, future_response.get(
            "jobId", None), future_response)
        return future.wait_for_result() if wait else future


class DSSStatisticsWorksheetSettings(DSSInternalDict):
    def __init__(self, client, project_key, dataset_name, worksheet_id, worksheet_definition):
        super(DSSStatisticsWorksheetSettings,
              self).__init__(worksheet_definition)
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.worksheet_id = worksheet_id

    def add_card(self, card):
        """
        Adds a new card to the worksheet.

        :param card: card to be added
        :type card: :class:`DSSStatisticsCardSettings` or dict (obtained from ``DSSStatisticsCardSettings.get_raw()``)
        """
        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        self._internal_dict['rootCard']['cards'].append(card.get_raw())

    def list_cards(self):
        """
        Lists the cards of this worksheet.

        :rtype: list of :class:`DSSStatisticsCardSettings`
        """
        return [DSSStatisticsCardSettings(self.client, card_definition)
                for card_definition in self._internal_dict['rootCard']['cards']]

    def get_raw(self):
        """
        Gets a reference to the raw settings of the worksheet.

        :rtype: dict
        """
        return self._internal_dict

    def set_sampling_settings(self, selection):
        """
        Sets the sampling settings of the worksheet

        :type card: :class:`DSSDatasetSelectionBuilder` or dict (obtained from ``get_raw_sampling_selection()``)
        """
        raw_selection = selection.build() if isinstance(
            selection, DSSDatasetSelectionBuilder) else selection
        self._internal_dict['dataSpec']['datasetSelection'] = raw_selection

    def get_raw_sampling_settings(self):
        """
        Gets a reference to the raw sampling settings of the worksheet.

        :rtype: dict
        """
        return self._internal_dict['dataSpec']['datasetSelection']

    def save(self):
        """
        Saves the settings to DSS
        """
        self._internal_dict = self.client._perform_json(
            "PUT",
            "/projects/%s/datasets/%s/statistics/worksheets/%s" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=self._internal_dict
        )


class DSSStatisticsCardSettings(DSSInternalDict):
    def __init__(self, client, card_definition):
        super(DSSStatisticsCardSettings, self).__init__(card_definition)
        self.client = client
        self._internal_dict = card_definition

    def get_raw(self):
        """
        Gets a reference to the raw settings of the card.

        :rtype: dict
        """
        return self._internal_dict

    def compile(self):
        """
        Gets the underlying computation used to compute the card results.

        :rtype: DSSStatisticsComputationSettings
        """
        computation_json = self.client._perform_json(
            "POST", "/statistics/cards/compile", body=self._internal_dict
        )
        return DSSStatisticsComputationSettings(computation_json)

    @staticmethod
    def _from_card_or_dict(client, card_or_dict):
        if isinstance(card_or_dict, DSSStatisticsCardSettings):
            card_or_dict = card_or_dict.get_raw()
        return DSSStatisticsCardSettings(client, card_or_dict)


class DSSStatisticsComputationSettings(DSSInternalDict):
    def __init__(self, computation_definition):
        super(DSSStatisticsComputationSettings,
              self).__init__(computation_definition)
        self._internal_dict = computation_definition

    def get_raw(self):
        """
        Gets the raw settings of the computation.

        :rtype: dict
        """
        return self._internal_dict

    @staticmethod
    def _from_computation_or_dict(computation_or_dict):
        if isinstance(computation_or_dict, ComputationBase):
            computation_or_dict = computation_or_dict.to_model()
        if isinstance(computation_or_dict, DSSStatisticsComputationSettings):
            computation_or_dict = computation_or_dict.get_raw()
        return DSSStatisticsComputationSettings(computation_or_dict)

class ComputationBase(object):
    def __init__(self):
        pass

    def grouped_by_alphanum(self, column, max_values=10, group_others=False):
        return GroupedComputation(self, {
            "type" : "anum",
            "column" : column,
            "maxValues":  max_values,
            "groupOthers": group_others
        })

    def grouped_by_bins(self, column, nb_bins=None, bin_size=None, keep_na=False):
        if nb_bins is not None:
            return GroupedComputation(self, {
                "type" : "binned",
                "column" : column,
                "mode":  "FIXED_NB",
                "nbBins" : nb_bins,
                "keepNA" : keep_na
            })
        elif bin_size is not None:
            return GroupedComputation(self, {
                "type" : "binned",
                "column" : column,
                "mode":  "FIXED_SIZE",
                "binSize" : bin_size,
                "keepNA" : keep_na
            })

class DescriptiveStatistics(ComputationBase):
    def __init__(self, columns, mean=False, sum=False, stddev=False, variance=False, skewness=False,kurtosis=False,sem=False):
        self.columns = columns
        self.mean = mean
        self.sum = sum
        self.stddev = stddev
        self.variance = variance
        self.skewness = skewness
        self.kurtosis = kurtosis
        self.sem = sem

    def to_model(self):
        computations = []
        for col in self.columns:
            if self.mean:
                computations.append({"type": "mean", "column": col})
            if self.sum:
                computations.append({"type": "sum", "column": col})
            if self.stddev:
                computations.append({"type": "std_dev", "column": col})
            if self.variance:
                computations.append({"type": "variance", "column": col})
            if self.skewness:
                computations.append({"type": "skewness", "column": col})
            if self.kurtosis:
                computations.append({"type": "kurtosis", "column": col})
            if self.sem:
                computations.append({"type": "sem", "column": col})
        return {"type": "multi", "computations" : computations}

class TTest1Sample(ComputationBase):
    def __init__(self, column, hypothesized_mean):
        self.column = column
        self.hypothesized_mean = hypothesized_mean
    def to_model(self):
        return {
            "type": "ttest_1samp",
            "column": self.column,
            "hypothesizedMean" : self.hypothesized_mean
        }

class DistributionFit(ComputationBase):
    def __init__(self, column, type="normal", test=True, **kwargs):
        self.column = column
        self.type = type
        self.test = test
        self.distribution_args = kwargs

    def to_model(self):
        distribution = {
            "type" : self.type
        }
        distribution.update(self.distribution_args)
        return {
            "type": "fit_distribution",
            "column" : self.column,
            "distribution": distribution,
            "test" :self.test
        }

class _BasicBivariateComputation(ComputationBase):
    def __init__(self, type, column1, column2):
        self.type = type
        self.column1 = column1
        self.column2 = column2

    def to_model(self):
        return {
            "type": self.type,
            "xColumn": self.column1,
            "yColumn": self.column2
        }


class Pearson(_BasicBivariateComputation):
    def __init__(self, column1, column2):
        super(Pearson, self).__init__("pearson", column1, column2)
class Covariance(_BasicBivariateComputation):
    def __init__(self, column1, column2):
        super(Pearson, self).__init__("covariance", column1, column2)
class Spearman(_BasicBivariateComputation):
    def __init__(self, column1, column2):
        super(Pearson, self).__init__("spearman", column1, column2)


class GroupedComputation(ComputationBase):
    def __init__(self, computation, grouping):
        self.computation = computation
        self.grouping = grouping

    def to_model(self):
        return {
            "type": "grouped",
            "computation" : self.computation.to_model(),
            "grouping":  self.grouping
        }