from ..utils import DataikuException
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

    def run_worksheet(self):
        """
        Computes the results of the whole worksheet.

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle
        """

        root_card = self.get_settings().get_raw()['rootCard']
        return self.run_card(root_card)

    def run_card(self, card):
        """
        Runs a card in the context of the worksheet.

        Note: the card does not need to belong to the worksheet.

        :param card: a card to compute
        :type card: :class:`DSSStatisticsCardSettings` or dict
        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of computing card's results
        """

        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        future_response = self.client._perform_json(
            "POST",
            "/projects/%s/datasets/%s/statistics/worksheets/%s/actions/run-card" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=card.get_raw()
        )
        return DSSFuture(self.client, future_response.get("jobId", None), future_response)

    def run_computation(self, computation):
        """
        Runs a computation in the context of the worksheet.

        :param computation: a card to compute
        :type computation: :class:`DSSStatisticsComputationSettings` or dict
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
        return DSSFuture(self.client, future_response.get("jobId", None), future_response)


class DSSStatisticsWorksheetSettings(object):
    def __init__(self, client, project_key, dataset_name, worksheet_id, worksheet_definition):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.worksheet_id = worksheet_id
        self._worksheet_definition = worksheet_definition

    def add_card(self, card):
        """
        Adds a new card to the worksheet.

        :param card: card to be added
        :type card: :class:`DSSStatisticsCardSettings` or dict
        """
        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        self._worksheet_definition['rootCard']['cards'].append(card)

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

    def save(self):
        """
        Saves the settings to DSS
        """
        return self.client._perform_json(
            "PUT",
            "/projects/%s/datasets/%s/statistics/worksheets/%s" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=self._worksheet_definition
        )


class DSSStatisticsCardSettings(object):
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


class DSSStatisticsComputationSettings(object):
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
