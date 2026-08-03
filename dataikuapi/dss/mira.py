import sys
from ..utils import CallableStr

if sys.version_info >= (3, 0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote


class DSSMIRA(object):
    """
    Handle to interact with MIRA.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSClient.get_mira`
    """
    def __init__(self, client):
        self.client = client

    def list_infras(self, as_objects=True):
        """
        Lists MIRA infrastructures.

        :param boolean as_objects: if True, returns a list of :class:`DSSMIRAInfra`, else returns a list of dict.
        :returns: a list - see as_objects for more information
        :rtype: list
        """
        response = self.client._perform_json("GET", "/mira/infras")
        infras = response["infras"]
        if as_objects:
            return [DSSMIRAInfra(self.client, infra["name"]) for infra in infras]
        else:
            return infras

    def get_infra(self, infra_name):
        """
        Returns a handle to interact with a MIRA infrastructure.

        :param str infra_name: MIRA infrastructure name
        :rtype: :class:`DSSMIRAInfra`
        """
        return DSSMIRAInfra(self.client, infra_name)

    def get_agent(self, infra_name, agent_id):
        """
        Returns a handle to interact with a MIRA agent.

        :param str infra_name: MIRA infrastructure name
        :param str agent_id: MIRA agent id
        :rtype: :class:`DSSMIRAAgent`
        """
        return DSSMIRAAgent(self.client, infra_name, agent_id)


class DSSMIRAInfra(object):
    """
    Handle to interact with a MIRA infrastructure.

    Do not create this directly, use :meth:`DSSMIRA.get_infra`.
    """
    def __init__(self, client, infra_name):
        self.client = client
        self.infra_name = infra_name

    @property
    def name(self):
        return CallableStr(self.infra_name)

    def __str__(self):
        return CallableStr(self.infra_name)

    def get_info(self):
        """
        Gets this MIRA infrastructure.

        :returns: infrastructure data as a dict
        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def list_agents(self, as_objects=True):
        """
        Lists agents of this MIRA infrastructure.

        :param boolean as_objects: if True, returns a list of :class:`DSSMIRAAgent`, else returns a list of dict.
        :returns: a list - see as_objects for more information
        :rtype: list
        """
        response = self.client._perform_json("GET", self._path("agents"))
        agents = response["agents"]
        if as_objects:
            return [DSSMIRAAgent(self.client, self.infra_name, agent["id"]) for agent in agents]
        else:
            return agents

    def get_agent(self, agent_id):
        """
        Returns a handle to interact with a MIRA agent in this infrastructure.

        :param str agent_id: MIRA agent id
        :rtype: :class:`DSSMIRAAgent`
        """
        return DSSMIRAAgent(self.client, self.infra_name, agent_id)

    def get_uptime_metrics(self, bucket="HOUR", from_time=None, to_time=None, agent_ids=None):
        """
        Get uptime metrics aggregated over MIRA agents in this infrastructure.

        :param str bucket: time bucket, "HOUR" or "DAY"
        :param str from_time: optional inclusive ISO timestamp lower bound
        :param str to_time: optional exclusive ISO timestamp upper bound
        :param list agent_ids: optional list of agent ids to aggregate. Defaults to all allowed agents.
        :returns: uptime metrics response as a dict
        :rtype: dict
        """
        params = {"bucket": bucket}
        if agent_ids is not None:
            params["agentIds"] = agent_ids
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        return self.client._perform_json("GET", self._path("uptime-metrics"), params=params)

    def _path(self, suffix=None):
        path = "/mira/infras/%s" % dku_quote_fn(self.infra_name, safe="")
        if suffix is not None:
            path += "/" + suffix
        return path


class DSSMIRAAgent(object):
    """
    Handle to interact with a MIRA agent.

    Do not create this directly, use :meth:`DSSMIRA.get_agent` or :meth:`DSSMIRAInfra.get_agent`.
    """
    def __init__(self, client, infra_name, agent_id):
        self.client = client
        self.infra_name = infra_name
        self.agent_id = agent_id

    @property
    def id(self):
        return CallableStr(self.agent_id)

    def __str__(self):
        return CallableStr(self.agent_id)

    def get_info(self):
        """
        Gets this MIRA agent.

        :returns: agent data as a dict
        :rtype: dict
        """
        return self.client._perform_json("GET", self._path())

    def get_uptime_metrics(self, bucket="HOUR", from_time=None, to_time=None):
        """
        Get uptime metrics computed from MIRA uptime tests for this agent.

        :param str bucket: time bucket, "HOUR" or "DAY"
        :param str from_time: optional inclusive ISO timestamp lower bound
        :param str to_time: optional exclusive ISO timestamp upper bound
        :returns: uptime metrics response as a dict
        :rtype: dict
        """
        params = {"bucket": bucket}
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        return self.client._perform_json("GET", self._path("uptime-metrics"), params=params)

    def list_uptime_tests(self, from_time=None, to_time=None):
        """
        List raw MIRA uptime tests for this agent.

        :param str from_time: optional inclusive ISO timestamp lower bound
        :param str to_time: optional exclusive ISO timestamp upper bound
        :returns: uptime tests response as a dict
        :rtype: dict
        """
        params = {}
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        return self.client._perform_json("GET", self._path("uptime-tests"), params=params)

    def insert_uptime_tests(self, tests):
        """
        Insert raw MIRA uptime test values for this agent.

        :param list tests: list of test dictionaries with timestamp, responseStatus and responseTimeMs
        :returns: mutation response as a dict
        :rtype: dict
        """
        return self.client._perform_json("POST", self._path("uptime-tests"), body={"tests": tests})

    def delete_uptime_tests(self, from_time=None, to_time=None):
        """
        Delete raw MIRA uptime tests for this agent, optionally restricted to a time range.

        :param str from_time: optional inclusive ISO timestamp lower bound
        :param str to_time: optional exclusive ISO timestamp upper bound
        :returns: deletion response as a dict
        :rtype: dict
        """
        params = {}
        if from_time is not None:
            params["from"] = from_time
        if to_time is not None:
            params["to"] = to_time
        return self.client._perform_json("DELETE", self._path("uptime-tests"), params=params)

    def _path(self, suffix=None):
        path = "/mira/infras/%s/agents/%s" % (
            dku_quote_fn(self.infra_name, safe=""),
            dku_quote_fn(self.agent_id, safe="")
        )
        if suffix is not None:
            path += "/" + suffix
        return path
