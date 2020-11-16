from ..utils import DataikuException
from .utils import DSSDatasetSelectionBuilder
from .future import DSSFuture
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

        :returns: a :class:`DSSStatisticsCardResult` if `wait` is `True`, or a :class:`~dataikuapi.dss.future.DSSFuture` handle otherwise
        """

        root_card = self.get_settings().get_raw()['rootCard']
        return self.run_card(root_card, wait=wait)

    def run_card(self, card, wait=True):
        """
        Runs a card in the context of the worksheet.

        Note: the card does not need to belong to the worksheet.

        :param card: a card to compute
        :type card: :class:`DSSStatisticsCardSettings` or dict (obtained from ``DSSStatisticsCardSettings.get_raw()``)
        :returns: a :class:`DSSStatisticsCardResult` if `wait` is `True`, or a :class:`~dataikuapi.dss.future.DSSFuture` handle otherwise
        """

        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        future_response = self.client._perform_json(
            "POST",
            "/projects/%s/datasets/%s/statistics/worksheets/%s/actions/run-card" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=card.get_raw()
        )

        future = DSSFuture(self.client, future_response.get("jobId", None), future_response,
                           result_wrapper=lambda raw_result: DSSStatisticsCardResult(raw_result))

        return future.wait_for_result() if wait else future

    def run_computation(self, computation, wait=True):
        """
        Runs a computation in the context of the worksheet.

        :param computation: a card to compute
        :type computation: :class:`DSSStatisticsComputationSettings` or dict (obtained from ``DSSStatisticsComputationSettings.get_raw()``)
        :returns: a :class:`DSSStatisticsComputationResult`, or a :class:`~dataikuapi.dss.future.DSSFuture` handle otherwise
        """

        computation = DSSStatisticsComputationSettings._from_computation_or_dict(
            computation)
        future_response = self.client._perform_json(
            "POST",
            "/projects/%s/datasets/%s/statistics/worksheets/%s/actions/run-computation" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=computation.get_raw()
        )

        future = DSSFuture(self.client, future_response.get("jobId", None), future_response,
                           result_wrapper=lambda raw_result: DSSStatisticsComputationResult(raw_result))

        return future.wait_for_result() if wait else future


class DSSStatisticsWorksheetSettings(object):
    def __init__(self, client, project_key, dataset_name, worksheet_id, worksheet_definition):
        self._worksheet_definition = worksheet_definition
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
        self._worksheet_definition['rootCard']['cards'].append(card.get_raw())

    def list_cards(self):
        """
        Lists the cards of this worksheet.

        :rtype: list of :class:`DSSStatisticsCardSettings`
        """
        return [DSSStatisticsCardSettings(self.client, card_definition)
                for card_definition in self._worksheet_definition['rootCard']['cards']]

    def get_raw(self):
        """
        Gets a reference to the raw settings of the worksheet.

        :rtype: dict
        """
        return self._worksheet_definition

    def set_sampling_settings(self, selection):
        """
        Sets the sampling settings of the worksheet

        :type card: :class:`DSSDatasetSelectionBuilder` or dict (obtained from ``get_raw_sampling_selection()``)
        """
        raw_selection = selection.build() if isinstance(
            selection, DSSDatasetSelectionBuilder) else selection
        self._worksheet_definition['dataSpec']['datasetSelection'] = raw_selection

    def get_raw_sampling_settings(self):
        """
        Gets a reference to the raw sampling settings of the worksheet.

        :rtype: dict
        """
        return self._worksheet_definition['dataSpec']['datasetSelection']

    def save(self):
        """
        Saves the settings to DSS
        """
        self._worksheet_definition = self.client._perform_json(
            "PUT",
            "/projects/%s/datasets/%s/statistics/worksheets/%s" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=self._worksheet_definition
        )


class DSSStatisticsCardSettings(object):
    """
    Object to manipulate the settings of a card
    """

    def __init__(self, client, card_definition):
        self.client = client
        self._card_definition = card_definition

    def get_raw(self):
        """
        Gets a reference to the raw settings of the card.

        :rtype: dict
        """
        return self._card_definition

    def compile(self):
        """
        Gets the underlying computation used to compute the card results.

        :rtype: DSSStatisticsComputationSettings
        """
        computation_json = self.client._perform_json(
            "POST", "/statistics/cards/compile", body=self._card_definition
        )
        return DSSStatisticsComputationSettings(computation_json)

    @staticmethod
    def _from_card_or_dict(client, card_or_dict):
        if isinstance(card_or_dict, DSSStatisticsCardSettings):
            card_or_dict = card_or_dict.get_raw()
        return DSSStatisticsCardSettings(client, card_or_dict)


class DSSStatisticsCardResult(object):
    """
    Object storing the results of a :class:`DSSStatisticsCardSettings`
    """

    def __init__(self, card_result):
        self._card_result = card_result

    def get_raw(self):
        """
        Gets a reference to the raw results of the card

        :rtype: dict
        """
        return self._card_result


class DSSStatisticsComputationSettings(object):
    """
    Object to manipulate the settings of a computation
    """

    def __init__(self, computation_definition):
        self._computation_definition = computation_definition

    def get_raw(self):
        """
        Gets the raw settings of the computation.

        :rtype: dict
        """
        return self._computation_definition

    @staticmethod
    def _from_computation_or_dict(computation_or_dict):
        if isinstance(computation_or_dict, DSSStatisticsComputationSettings):
            computation_or_dict = computation_or_dict.get_raw()
        return DSSStatisticsComputationSettings(computation_or_dict)


class DSSStatisticsComputationResult(object):
    """
    Object storing the results of a :class:`DSSStatisticsComputationSettings`
    """

    def __init__(self, computation_result):
        self._computation_result = computation_result

    def get_raw(self):
        """
        Gets a reference to the raw results of the computation

        :rtype: dict
        """
        return self._computation_result
