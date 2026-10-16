import json
import os

from ._utils import dku_quote_fn


class EstateRiskExposure(object):
    """
    The aggregated Agent Management risk exposure.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_risk_exposure`.
    """
    def __init__(self, exposure):
        self._raw = exposure

    @property
    def raw(self):
        """
        Returns the raw risk exposure.

        :rtype: dict
        """
        return self._raw


class RiskTaxonomySettings(object):
    """
    The Agent Management risk taxonomy settings.

    Do not create this directly, use :meth:`dataikuapi.AgentManagementClient.get_risk_taxonomy`
    or :meth:`dataikuapi.AgentManagementClient.get_default_risk_taxonomy`.
    """
    def __init__(self, client, settings):
        self.client = client
        self.settings = settings

    @property
    def raw(self):
        """
        Returns the raw risk taxonomy settings, including ``fetchedRevision`` and the taxonomy.

        :rtype: dict
        """
        return self.settings

    def get_raw(self):
        """
        Returns the raw risk taxonomy settings.

        :rtype: dict
        """
        return self.settings

    def compute_replacement_impact(self):
        """
        Computes the impact of replacing the current risk taxonomy.

        :rtype: dict
        """
        return self.client._perform_json("POST", "/agent-management/risk-taxonomy/actions/compute-replacement-impact",
                                         body={"taxonomy": self.settings["taxonomy"]})

    def save(self, impact):
        """
        Saves the Agent Management risk taxonomy.

        Uses ``fetchedRevision`` from :attr:`raw` to detect concurrent changes.
        Remove it or set it to ``None`` to skip the revision check. The replacement impact fingerprint is still checked.

        :param dict impact: impact returned by :meth:`compute_replacement_impact`
        :returns: the saved settings
        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskTaxonomySettings`
        """
        if impact is None or impact.get("fingerprint") is None:
            raise ValueError("A replacement impact returned by compute_replacement_impact() is required")
        body = {
            "fetchedRevision": self.settings.get("fetchedRevision"),
            "expectedImpactFingerprint": impact["fingerprint"],
            "taxonomy": self.settings["taxonomy"]
        }
        self.settings = self.client._perform_json("PUT", "/agent-management/risk-taxonomy", body=body)
        return self


class RiskAssessment(object):
    """
    The risk assessment of a monitored agent, including its evidence documents.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.agent.Agent.get_risk_assessment`.
    """
    def __init__(self, client, platform_id, agent_id, settings):
        self.client = client
        self.platform_id = platform_id
        self.agent_id = agent_id
        self.settings = settings

    def __repr__(self):
        return "<RiskAssessment platform_id=%r agent_id=%r>" % (self.platform_id, self.agent_id)

    @property
    def raw(self):
        """
        Returns the raw risk assessment response, including ``fetchedRevision`` and the assessment.

        :rtype: dict
        """
        return self.settings

    def get_raw(self):
        """
        Returns the raw risk assessment response.

        :rtype: dict
        """
        return self.settings

    def save(self, documents=None):
        """
        Saves the risk assessment and optionally uploads document evidence.

        Uses ``fetchedRevision`` from :attr:`raw` to detect concurrent changes.
        Remove it or set it to ``None`` to save without a revision check.

        :param dict documents: optional mapping of evidence identifiers to file-like objects or ``(filename, file_object)`` tuples
        :returns: this assessment with its saved data
        :rtype: :class:`dataikuapi.agentmanagement.risk.RiskAssessment`
        """
        files = [
            ("assessment", (None, json.dumps(self.settings["assessment"]))),
            ("fetchedRevision", (None, self.settings.get("fetchedRevision", "")))
        ]
        for evidence_id, document in (documents or {}).items():
            if isinstance(document, tuple):
                filename, stream = document
            else:
                stream = document
                filename = os.path.basename(getattr(stream, "name", evidence_id))
            files.append(("documentEvidenceIds", (None, evidence_id)))
            files.append(("documents", (filename, stream)))
        self.settings = self.client._perform_json("PUT", self._path(), files=files)
        return self

    def get_risk_evidence_content(self, evidence_id):
        """
        Downloads the content of a document attached as evidence in this assessment.

        :param str evidence_id: identifier of a document evidence entry in the assessment
        :rtype: :class:`requests.Response`
        """
        return self.client._perform_raw("GET", self._path() + "/evidences/%s/content" % dku_quote_fn(evidence_id, safe=""))

    def _path(self):
        return "/agent-management/platforms/%s/agents/%s/risk-assessment" % (
            dku_quote_fn(self.platform_id, safe=""), dku_quote_fn(self.agent_id, safe=""))
