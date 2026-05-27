from .agent_tool import DSSAgentTool, DSSAgentToolListItem
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings


class DSSAgentInteractionLoggingSettings(object):
    """
    Settings for agent interaction logging.

    .. important::

        Do not instantiate this class directly, use :attr:`dataikuapi.dss.agent.DSSAgentInteractionLoggingSelection.settings` instead.
    """

    CONTENT_MODE_FULL = "FULL"
    CONTENT_MODE_NO_LOGS = "NO_LOGS"
    CONTENT_MODE_NO_LOGS_NO_TRACE = "NO_LOGS_NO_TRACE"

    _VALID_CONTENT_MODES = (
        CONTENT_MODE_FULL,
        CONTENT_MODE_NO_LOGS,
        CONTENT_MODE_NO_LOGS_NO_TRACE,
    )

    def __init__(self, settings):
        self._settings = settings

    def get_raw(self):
        """
        Returns the raw interaction logging settings.

        :rtype: dict
        """
        return self._settings

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def __getitem__(self, key):
        return self._settings[key]

    def __setitem__(self, key, value):
        if key == "writeAsUser":
            raise ValueError("writeAsUser is read-only")
        self._settings[key] = value

    @property
    def dataset_name(self):
        """
        The dataset name used for interaction logging.

        :rtype: str | None
        """
        return self._settings.get("datasetName")

    @dataset_name.setter
    def dataset_name(self, value):
        self._settings["datasetName"] = value

    @property
    def write_as_user(self):
        """
        The DSS user used to write logs.

        This value is read-only and is set automatically to the user who saves
        the agent settings.

        :rtype: str | None
        """
        return self._settings.get("writeAsUser")

    @property
    def flush_every_s(self):
        """
        The flush interval, in seconds.

        :rtype: int | None
        """
        return self._settings.get("flushEveryS")

    @flush_every_s.setter
    def flush_every_s(self, value):
        self._settings["flushEveryS"] = value

    @property
    def flush_every_bytes(self):
        """
        The maximum buffered payload size before a flush.

        :rtype: int | None
        """
        return self._settings.get("flushEveryBytes")

    @flush_every_bytes.setter
    def flush_every_bytes(self, value):
        self._settings["flushEveryBytes"] = value

    @property
    def content_mode(self):
        """
        The content logging mode.

        :rtype: str | None
        """
        return self._settings.get("contentMode")

    @content_mode.setter
    def content_mode(self, value):
        if value not in self._VALID_CONTENT_MODES:
            raise ValueError("Invalid content mode: %s" % value)
        self._settings["contentMode"] = value


class DSSAgentInteractionLoggingSelection(object):
    """
    Selection for agent interaction logging.

    .. important::

        Do not instantiate this class directly, use :attr:`dataikuapi.dss.agent.DSSAgentVersionSettings.interaction_logging_selection` instead.
    """

    MODE_INHERIT = "INHERIT"
    MODE_EXPLICIT = "EXPLICIT"
    MODE_NONE = "NONE"

    _VALID_MODES = (
        MODE_INHERIT,
        MODE_EXPLICIT,
        MODE_NONE,
    )

    def __init__(self, selection):
        self._selection = selection

    def get_raw(self):
        """
        Returns the raw interaction logging selection.

        :rtype: dict
        """
        return self._selection

    def get(self, key, default=None):
        return self._selection.get(key, default)

    def __getitem__(self, key):
        return self._selection[key]

    def __setitem__(self, key, value):
        self._selection[key] = value

    def _get_or_create_settings_raw(self):
        settings = self._selection.get("explicitSettings")
        if settings is None:
            settings = {}
            self._selection["explicitSettings"] = settings
        return settings

    @property
    def mode(self):
        """
        The interaction logging mode. One of INHERIT, EXPLICIT or NONE.

        In ``INHERIT`` mode, settings are inherited from the project-level
        configuration.

        :rtype: str | None
        """
        return self._selection.get("mode")

    @mode.setter
    def mode(self, value):
        if value not in self._VALID_MODES:
            raise ValueError("Invalid interaction logging mode: %s" % value)
        self._selection["mode"] = value

    @property
    def settings(self):
        """
        The explicit interaction logging settings.

        These settings are only used when the selection is in ``EXPLICIT`` mode.

        :rtype: :class:`dataikuapi.dss.agent.DSSAgentInteractionLoggingSettings`
        """
        return DSSAgentInteractionLoggingSettings(self._get_or_create_settings_raw())

    @settings.setter
    def settings(self, value):
        if isinstance(value, DSSAgentInteractionLoggingSettings):
            value = value.get_raw()
        if value is None:
            value = {}
        self._selection["explicitSettings"] = value

    def enable(self, dataset_name, settings=None):
        """
        Enable interaction logging on this agent version with explicit settings.

        This only controls the agent version setting itself. Interaction logging
        can still be effectively unavailable if it is disabled at the instance level.

        :param dataset_name: Dataset name used for interaction logging.
        :type dataset_name: str
        :param settings: Optional explicit settings payload or
            :class:`dataikuapi.dss.agent.DSSAgentInteractionLoggingSettings`.
        :type settings: dict | :class:`dataikuapi.dss.agent.DSSAgentInteractionLoggingSettings` | None
        """
        self.mode = self.MODE_EXPLICIT
        if settings is not None:
            self.settings = settings
        self.settings.dataset_name = dataset_name

    def inherit(self):
        """
        Enable interaction logging on this agent version in inherited mode.

        In this mode, the version inherits the project-level interaction logging settings.
        """
        self.mode = self.MODE_INHERIT

    def disable(self):
        """
        Disable interaction logging on this agent version.
        """
        self.mode = self.MODE_NONE


# Neutral aliases for shared LLM interaction logging concepts.
DSSLLMInteractionLoggingSettings = DSSAgentInteractionLoggingSettings
DSSLLMInteractionLoggingSelection = DSSAgentInteractionLoggingSelection


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
        """
        :returns: this agent as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying
        :rtype: dataikuapi.dss.llm.DSSLLM
        """
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
        """
        :returns: this agent as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying
        :rtype: dataikuapi.dss.llm.DSSLLM
        """
        return self.client.get_project(self.project_key).get_llm("agent:%s" % self.id)

    def get_settings(self):
        """
        :return: a handle on the agent's definition
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

    def shutdown(self, version_id=None, force=False):
        """
        Shutdown all instances of the given version of this agent

        :param version_id: If unspecified, uses the active version.
        :type version_id: str | None
        :param force: If True, cancel requests being processed and stop the instances. If False, let those active requests complete before stopping.
        :type force: bool
        """
        return self.client._perform_empty(
            "POST", "/projects/%s/agents/%s/actions/shutdown" % (self.project_key, self.id), body={
                "versionId": version_id,
                "force": force
            })

    def status(self, version_id=None):
        """
        Query status of instances of the given version of this agent

        :param version_id: If unspecified, uses the active version.
        :type version_id: str | None
        :return: A dict holding the list of the status for each instance.
        """
        return self.client._perform_json(
            "GET", "/projects/%s/agents/%s/status" % (self.project_key, self.id), body={
                "versionId": version_id
            })

    def wake_up(self, version_id=None):
        """
        Start an instance of an agent if none is started

        :param version_id: If unspecified, uses the active version.
        :type version_id: str | None
        """
        return self.client._perform_empty(
            "POST", "/projects/%s/agents/%s/actions/wakeup" % (self.project_key, self.id), body={
                "versionId": version_id
            })


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
        """
        List the ids of each version of this agent

        :rtype: list[str]
        """
        return [v["versionId"] for v in self._settings["versions"]]

    @property
    def active_version(self):
        """
        :returns: the active version of this agent, or None if no version is declared as active
        :rtype: str | None
        """
        return self._settings.get("activeVersion")

    def get_version_settings(self, version_id):
        """
        :returns: the settings of the given version of this agent
        :rtype: DSSAgentVersionSettings
        """
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
        :returns: the raw settings of this agent
        :rtype: dict
        """
        return self._settings

    def save(self):
        """
        Saves the settings for this agent
        """
        self._client._perform_empty(
            "PUT", "/projects/%s/agents/%s" % (self._settings["projectKey"], self._settings["id"]), body=self._settings)

class DSSAgentVersionSettings(object):
    def __init__(self, settings, version_settings):
        self._agent_settings = settings
        self._version_settings = version_settings

    def get_raw(self):
        """
        :returns: the raw settings of this agent version
        :rtype: dict
        """
        return self._version_settings

    @property
    def llm_id(self):
        """
        Only for Visual Agents

        :rtype: str
        """
        if not self._agent_settings.type == "TOOLS_USING_AGENT":
            raise ValueError("Only valid for Simple Visual Agents")
        return self._version_settings["toolsUsingAgentSettings"]["llmId"]

    @llm_id.setter
    def llm_id(self, value):
        if not self._agent_settings.type == "TOOLS_USING_AGENT":
            raise ValueError("Only valid for Simple Visual Agents")
        self._version_settings["toolsUsingAgentSettings"]["llmId"] = value

    @property
    def tools(self):
        """
        Returns the list of tools of the agent. The list can be modified.

        Each tool is a dict, containing at least "toolRef", which is the identifier of the tool.
        The dict may also contain "additionalDescription" which is added to the description of the tool
        """
        if not self._agent_settings.type == "TOOLS_USING_AGENT":
            raise ValueError("Only valid for Simple Visual Agents")
        return self._version_settings["toolsUsingAgentSettings"]["tools"]

    def add_tool(self, tool):
        """
        Adds a tool to the agent

        :param tool: a string (identifier of the tool), or a :class:`dataikuapi.dss.agent_tool.DSSAgentTool`
        """

        def get_tool_ref():
            is_foreign = self._agent_settings._settings["projectKey"] != tool.project_key
            if is_foreign:
                return tool.project_key + "." + tool.id
            else:
                return tool.id

        if isinstance(tool, DSSAgentToolListItem):
            tool_dict = { "toolRef" : get_tool_ref()}
        elif isinstance(tool, DSSAgentTool):
            tool_dict = { "toolRef" : get_tool_ref()}
        elif isinstance(tool, str):
            tool_dict = { "toolRef" : tool}
        else:
            raise Exception("Cannot add agent tool: %s" % tool)

        self.tools.append(tool_dict)

    def _get_internal_agent_settings(self):
        """
        Returns internal agent settings (SavedModel#AgentSettings in Java) matching the agent type.

        :rtype: dict
        """
        settings_key_by_type = {
            "TOOLS_USING_AGENT": "toolsUsingAgentSettings",
            "STRUCTURED_AGENT": "structuredAgentSettings",
            "PYTHON_AGENT": "pythonAgentSettings",
            "PLUGIN_AGENT": "pluginAgentSettings",
        }

        try:
            settings_key = settings_key_by_type[self._agent_settings.type]
            return self._version_settings[settings_key]
        except KeyError:
            raise ValueError("Unsupported agent type: %s" % self._agent_settings.type)

    def _get_or_create_interaction_logging_selection(self):
        internal_settings = self._get_internal_agent_settings()
        interaction_logging_selection = internal_settings.get("interactionLoggingSelection")
        if interaction_logging_selection is None:
            interaction_logging_selection = {
                "mode": DSSAgentInteractionLoggingSelection.MODE_INHERIT,
                "explicitSettings": {},
            }
            internal_settings["interactionLoggingSelection"] = interaction_logging_selection
        return interaction_logging_selection

    @property
    def interaction_logging_selection(self):
        """
        Get the interaction logging selection for this version.

        Before configuring interaction logging on an agent version, create the
        target dataset on the project:

        .. code-block:: python

            project = client.get_project("MYPROJECT")
            project.create_llm_interaction_logging_dataset(
                "agent_logs",
                connection_id="filesystem_managed",
                time_partitioning="DAY",
            )

        Example using inherited settings:

        .. code-block:: python

            agent = project.get_agent("my_agent")
            agent_settings = agent.get_settings()
            version_settings = agent_settings.get_version_settings("v1")

            agent_logging_selection = version_settings.interaction_logging_selection
            agent_logging_selection.inherit()

            agent_settings.save()

        Example using explicit settings:

        .. code-block:: python

            agent = project.get_agent("my_agent")
            agent_settings = agent.get_settings()
            version_settings = agent_settings.get_version_settings("v1")

            agent_logging_selection = version_settings.interaction_logging_selection
            agent_logging_selection.enable(
                "agent_logs",
                settings={
                    "flushEveryS": 60,
                    "flushEveryBytes": 1_000_000,
                    "contentMode": "FULL",
                },
            )

            agent_settings.save()

        Example disabling interaction logging:

        .. code-block:: python

            agent = project.get_agent("my_agent")
            agent_settings = agent.get_settings()
            version_settings = agent_settings.get_version_settings("v1")

            agent_logging_selection = version_settings.interaction_logging_selection
            agent_logging_selection.disable()

            agent_settings.save()

        :rtype: :class:`dataikuapi.dss.agent.DSSAgentInteractionLoggingSelection`
        """
        return DSSAgentInteractionLoggingSelection(self._get_or_create_interaction_logging_selection())

    @interaction_logging_selection.setter
    def interaction_logging_selection(self, value):
        if isinstance(value, DSSAgentInteractionLoggingSelection):
            value = value.get_raw()
        self._get_internal_agent_settings()["interactionLoggingSelection"] = value
