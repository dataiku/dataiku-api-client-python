class Settings(object):
    """
    The global Agent Management settings.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_settings`.
    """
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings

    def get_raw(self):
        """
        Returns the raw Agent Management settings, including global business KPI definitions in ``businessKPIs``.

        :rtype: dict
        """
        return self.settings

    def save(self, confirm_metric_reset=False):
        """
        Saves the global Agent Management settings.

        Uses ``fetchedRevision`` from :meth:`get_raw` to detect concurrent changes.
        Remove it or set it to ``None`` to save without a revision check.

        :param boolean confirm_metric_reset: whether to confirm deletion of metrics made incompatible by the settings change (defaults to False)
        :returns: the saved settings
        :rtype: :class:`dataikuapi.agentmanagement.settings.Settings`
        """
        body = dict(self.settings)
        body["confirmMetricReset"] = confirm_metric_reset
        self.settings = self.client._perform_json("PUT", "/agent-management/settings", body=body)
        return self

