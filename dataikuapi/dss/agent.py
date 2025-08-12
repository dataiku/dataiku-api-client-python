from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings
from .agent_tool import DSSAgentTool, DSSAgentToolListItem

class DSSAgentListItem(DSSTaggableObjectListItem):
    """
    An item in a list of agents

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_agents`.
    """
    def __init__(self, client, data):
        super(DSSAgentListItem, self).__init__(data)
        self.client = client


    @property
    def project_key(self):
        """
        :returns: The project        
        :rtype: string
        """
        return self._data["projectKey"]

    @property
    def id(self):
        """
        :returns: The id of the agent.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the agent.
        :rtype: string
        """
        return self._data["name"]

    def as_llm(self):
        """Returns this agent as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying"""
        return self.client.get_project(self.project_key).get_llm("agent:%s" % self.id)


class DSSAgent(object):
    """
    A handle to interact with a DSS-managed agent.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.project.DSSProject.get_agent` instead.
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.project_key = project_key
        self._id = id

    @property
    def id(self):
        return self._id

    def as_llm(self):
        """Returns this agent as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying"""
        return self.client.get_project(self.project_key).get_llm("agent:%s" % self.id)

    def get_settings(self):
        """
        Get the agent's definition

        :return: a handle on the agent definition
        :rtype: :class:`dataikuapi.dss.agent.DSSAgentSettings`
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/agents/%s" % (self.project_key, self.id))
        return DSSAgentSettings(self.client, settings)

    def delete(self):
        """
        Delete the agent
        """
        return self.client._perform_empty("DELETE", "/projects/%s/agents/%s" % (self.project_key, self.id))

class DSSAgentSettings(DSSTaggableObjectSettings):
    """
    Settings for a agent

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.agent.DSSAgent.get_settings` instead

    """
    def __init__(self, client, settings):
        super(DSSAgentSettings, self).__init__(settings)
        self._client = client
        self._settings = settings

    def get_version_ids(self):
        return [v["versionId"] for v in self._settings["versions"]]

    @property
    def active_version(self):
        """Returns the active version of this agent. May return None if no version is declared as active"""
        return self._settings.get("activeVersion")

    def get_version_settings(self, version_id):

        version_settings = None
        for vs in self._settings["versions"]:
            if vs["versionId"] == version_id:
                version_settings = vs
                break
        if version_settings is None:
            raise Exception("version %s not found" % version_id)
        
        return DSSAgentVersionSettings(self, version_settings)

    @property
    def type(self):
        return self._settings["type"]
    

    def get_raw(self):
        """
        Returns the raw settings of the agent
        :return: the raw settings of the agent
        :rtype: dict
        """
        return self._settings

    def save(self):
        """
        Saves the settings on the agent
        """
        self._client._perform_empty(
            "PUT", "/projects/%s/agents/%s" % (self._settings["projectKey"], self._settings["id"]), body=self._settings)

class DSSAgentVersionSettings(object):
    def __init__(self, settings, version_settings):
        self._agent_settings = settings
        self._version_settings = version_settings

    def get_raw(self):
        return self._version_settings

    @property
    def llm_id(self):
        """
        Only for Visual Agents
        :rtype: :class:`str`
        """
        if not self._agent_settings.type == "TOOLS_USING_AGENT":
            raise ValueError("Only valid for Visual Agents")
        return self._version_settings["toolsUsingAgentSettings"]["llmId"]

    @llm_id.setter
    def llm_id(self, value):
        if not self._agent_settings.type == "TOOLS_USING_AGENT":
            raise ValueError("Only valid for Visual Agents")
        self._version_settings["toolsUsingAgentSettings"]["llmId"] = value

    @property
    def tools(self):
        """
        Returns the list of tools of the agent. The list can be modified.

        Each tool is a dict, containing at least "toolRef", which is the identifier of the tool.
        The dict may also contain "additionalDescription" which is added to the description of the tool
        """
        return self._version_settings["toolsUsingAgentSettings"]["tools"]


    def add_tool(self, tool):
        """
        Adds a tool to the agent

        :param tool: a string (identifier of the tool), or a :class:`dataikuapi.dss.agent_tool.DSSAgentTool`
        """

        if isinstance(tool, DSSAgentToolListItem):
            tool_dict = { "toolRef" : tool.id}
        elif isinstance(tool, DSSAgentTool):
            tool_dict = { "toolRef" : tool.id}
        elif isinstance(tool, str):
            tool_dict = { "toolRef" : tool}
        else:
            raise Exception("Cannot add agent tool: %s" % tool)

        self.tools.append(tool_dict)