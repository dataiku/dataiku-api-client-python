from ..utils import DataikuException
from .future import DSSFuture
import json
from .metrics import ComputedMetrics
from .discussion import DSSObjectDiscussions


class DSSStatisticalWorksheet(object):
    """
    A handle to interact with a worksheet on the DSS instance
    """

    def __init__(self, client, project_key, worksheet_id):
        self.client = client
        self.project_key = project_key
        self.worksheet_id = worksheet_id

    ########################################################
    # Worksheet deletion
    ########################################################

    def delete(self):
        """
        Delete the worksheet
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/statistics/worksheets/%s" % (self.project_key, self.worksheet_id))

    ########################################################
    # Worksheet definition
    ########################################################

    def get_definition(self):
        """
        Get the definition of the worksheet

        Returns:
            the definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/statistics/worksheets/%s" % (self.project_key, self.worksheet_id))

    def set_definition(self, definition):
        """
        Set the definition of the dataset

        Args:
            definition: the definition, as a JSON object. You should only set a definition object 
            that has been retrieved using the get_definition call.
        """
        return self.client._perform_json(
            "PUT", "/projects/%s/statistics/worksheets/%s" % (self.project_key, self.worksheet_id), body=definition)

    def add_card(self, card_definition):
        """
        Add a new card to the worksheet

        The precise structure of ``card_definition`` depends on the specific card type. To know which 
        fields exist for a given card type, create a worksheet from the UI,  and use 
        :meth:`get_definition` to retrieve the configuration of the worksheet and inspect it.
        """
        worksheet = self.get_definition()
        worksheet["rootCard"]["cards"].append(card_definition)
        self.set_definition(worksheet)

    def get_standalone_cards(self):
        """
        Extract cards from this worksheet. A standalone card can be computed without worksheet.

        :returns: An list of :class:`dataikuapi.dss.worksheet.DSSStatisticsCard`
        """

        definition = self.get_definition()
        standalone_cards = []
        for card in definition["rootCard"]["cards"]:
            standalone_cards.append(DSSStatisticsCard(self.client, self.project_key, definition['dataSpec'], card))

        return standalone_cards

    ########################################################
    # Obtaining worksheet results
    ########################################################

    def compute(self):
        """
        Compute the results of the worksheet

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of computing worksheet's results
        """

        future_response = self.client._perform_json(
            "POST", "/projects/%s/statistics/worksheets/%s/actions/compute-worksheet" % (self.project_key, self.worksheet_id))

        return DSSFuture(self.client, future_response.get("jobId", None), future_response)


class DSSStatisticsCard(object):
    """
    A handle to interact with a standalone card (a card outside a worksheet)

    Unlike a worksheet, a standalone card is not persisted on the DSS instance
    """

    def __init__(self, client, project_key, data_spec, card):
        self.client = client
        self.project_key = project_key
        self.data_spec = data_spec
        self.card = card

    def compute(self):
        """
        Compute the results of a single card (without worksheet)

        :returns: a :class:`~dataikuapi.dss.future.DSSFuture` handle to the task of computing card's results
        """

        future_response = self.client._perform_json(
            "POST", "/projects/%s/statistics/cards/compute-card" % self.project_key,
            body={"card": self.card, "dataSpec": self.data_spec})
        return DSSFuture(self.client, future_response.get("jobId", None), future_response)
