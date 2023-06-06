from .utils import DSSDatasetSelectionBuilder
from .future import DSSFuture


class DSSStatisticsWorksheet(object):
    """
    A handle to interact with a worksheet.

    .. important::
        Do not create this class directly, instead use :meth:`dataikuapi.dss.dataset.DSSDataset.get_statistics_worksheet`
    """

    def __init__(self, client, project_key, dataset_name, worksheet_id):
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.worksheet_id = worksheet_id

    def delete(self):
        """
        Deletes the worksheet.
        """
        self.client._perform_empty(
            "DELETE", "/projects/%s/datasets/%s/statistics/worksheets/%s" % (self.project_key, self.dataset_name, self.worksheet_id))

    def get_settings(self):
        """
        Gets the worksheet settings.

        :returns: a handle for the worksheet settings
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
        Computes the result of the whole worksheet.

        When `wait` is `True`, the method waits for the computation to complete and returns the corresponding result,
        otherwise it returns immediately a handle for a :class:`~dataikuapi.dss.future.DSSFuture` result.

        :param bool wait: a flag to wait for the computation to complete (defaults to **True**)

        :returns: the corresponding card result or a handle for the future result
        :rtype: :class:`~DSSStatisticsCardResult` or :class:`~dataikuapi.dss.future.DSSFuture`
        """
        root_card = self.get_settings().get_raw()['rootCard']
        return self.run_card(root_card, wait=wait)

    def run_card(self, card, wait=True):
        """
        Computes the result of a card in the context of the worksheet.

        When `wait` is `True`, the method waits for the computation to complete and returns the corresponding result,
        otherwise it returns immediately a handle for a :class:`~dataikuapi.dss.future.DSSFuture` result.

        .. note::
            The card does not need to belong to the worksheet.

        :param card: the card to compute
        :type card: :class:`~DSSStatisticsCardSettings` or dict obtained from :meth:`DSSStatisticsCardSettings.get_raw`

        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)

        :returns: the corresponding card result or a handle for the future result
        :rtype: :class:`DSSStatisticsCardResult` or :class:`~dataikuapi.dss.future.DSSFuture`
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

        When `wait` is `True`, the method waits for the computation to complete and returns the corresponding result,
        otherwise it returns immediately a handle for a :class:`~dataikuapi.dss.future.DSSFuture` result.

        :param computation: the computation to perform
        :type computation: :class:`DSSStatisticsComputationSettings` or dict obtained from
            :meth:`DSSStatisticsComputationSettings.get_raw`

        :param bool wait: a flag to wait for the computations to complete (defaults to **True**)

        :returns: the corresponding computation result or a handle for the future result
        :returns: :class:`DSSStatisticsComputationResult` or :class:`~dataikuapi.dss.future.DSSFuture`
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
    """
    A handle to interact with the worksheet settings.

    .. important::
        Do not create this class directly, instead use :meth:`DSSStatisticsWorksheet.get_settings`
    """

    def __init__(self, client, project_key, dataset_name, worksheet_id, worksheet_definition):
        self._worksheet_definition = worksheet_definition
        self.client = client
        self.project_key = project_key
        self.dataset_name = dataset_name
        self.worksheet_id = worksheet_id

    def add_card(self, card):
        """
        Adds a new card to the worksheet.

        :param card: the card to add
        :type card: :class:`DSSStatisticsCardSettings` or dict obtained from :meth:`DSSStatisticsCardSettings.get_raw`
        """
        card = DSSStatisticsCardSettings._from_card_or_dict(self.client, card)
        self._worksheet_definition['rootCard']['cards'].append(card.get_raw())

    def list_cards(self):
        """
        Lists the cards for the worksheet.

        :returns: a list of card handles
        :rtype: list of :class:`DSSStatisticsCardSettings`
        """
        return [DSSStatisticsCardSettings(self.client, card_definition)
                for card_definition in self._worksheet_definition['rootCard']['cards']]

    def get_raw(self):
        """
        Gets a reference to the raw representation of the worksheet settings.

        :returns: the worksheet settings
        :rtype: dict
        """
        return self._worksheet_definition

    def set_sampling_settings(self, selection):
        """
        Sets the worksheet sampling settings.

        :param selection: the sampling settings
        :type selection: :class:`~dataikuapi.dss.utils.DSSDatasetSelectionBuilder` or dict obtained from
            :meth:`get_raw_sampling_settings`
        """
        raw_selection = selection.build() if isinstance(
            selection, DSSDatasetSelectionBuilder) else selection
        self._worksheet_definition['dataSpec']['datasetSelection'] = raw_selection

    def get_raw_sampling_settings(self):
        """
        Gets a reference to the raw representation of the worksheet sampling settings.

        :returns: the sampling settings
        :rtype: dict
        """
        return self._worksheet_definition['dataSpec']['datasetSelection']

    def save(self):
        """
        Saves the settings of the worksheet.
        """
        self._worksheet_definition = self.client._perform_json(
            "PUT",
            "/projects/%s/datasets/%s/statistics/worksheets/%s" % (
                self.project_key, self.dataset_name, self.worksheet_id),
            body=self._worksheet_definition
        )


class DSSStatisticsCardSettings(object):
    """
    A handle to interact with the card settings.
    """

    def __init__(self, client, card_definition):
        self.client = client
        self._card_definition = card_definition

    def get_raw(self):
        """
        Gets a reference to the raw representation of the card settings.

        :returns: the card settings
        :rtype: dict
        """
        return self._card_definition

    def compile(self):
        """
        Gets the computation used to compute the card result.

        :returns: the computation settings
        :rtype: :class:`DSSStatisticsComputationSettings`
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
    A handle to interact with the computed result of a :class:`DSSStatisticsCardSettings`.
    """

    def __init__(self, card_result):
        self._card_result = card_result

    def get_raw(self):
        """
        Gets a reference to the raw representation of the card result.

        :returns: the card result
        :rtype: dict
        """
        return self._card_result


class DSSStatisticsComputationSettings(object):
    """
    A handle to interact with the computation settings.
    """

    def __init__(self, computation_definition):
        self._computation_definition = computation_definition

    def get_raw(self):
        """
        Gets a reference to the raw representation of the computation settings.

        :returns: the computation settings
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
    A handle to interact with the computed result of a :class:`DSSStatisticsComputationSettings`.
    """

    def __init__(self, computation_result):
        self._computation_result = computation_result

    def get_raw(self):
        """
        Gets a reference to the raw representation of the computation result.

        :returns: the computation result
        :rtype: dict
        """
        return self._computation_result
