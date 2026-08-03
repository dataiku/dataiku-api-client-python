from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings, AnyLoc
from .knowledgebank import DSSKnowledgeBank, DSSKnowledgeBankListItem
from .llm_tracing import prepare_query_for_nested_llm_mesh_call
import json

class DSSAgentToolListItem(DSSTaggableObjectListItem):
    """
    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_agent_tools`.
    """
    def __init__(self, client, project_key, data):
        super(DSSAgentToolListItem, self).__init__(data)
        self.project_key = project_key
        self.client = client

    def to_agent_tool(self):
        """
        Convert the current item.
        """
        return DSSAgentTool(self.client, self.project_key, self._data["id"], "descriptor" in self._data and self._data["descriptor"] or None)

    @property
    def id(self):
        """
        :returns: The id of the tool.
        :rtype: string
        """
        return self._data["id"]

    @property
    def type(self):
        """
        :returns: The type of the tool
        :rtype: string
        """
        return self._data["type"]

    @property
    def name(self):
        """
        :returns: The name of the tool
        :rtype: string
        """
        return self._data["name"]



class DSSAgentTool(object):
    """
    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.get_agent_tool`.
    """
    def __init__(self, client, project_key, tool_id, descriptor=None):
        self.client = client
        self.project_key = project_key
        self.tool_id = tool_id
        self._descriptor = descriptor

    @property
    def id(self):
        """
        :returns: The id of the tool.
        :rtype: string
        """
        return self.tool_id

    def get_descriptor(self, context=None):
        """
        Get the descriptor of the tool

        :return: a descriptor of the tool
        :rtype: dict
        """

        if self._descriptor is None:
            if context is None:
                self._descriptor = self.client._perform_json("GET", "/projects/%s/agents/tools/%s/descriptor" % (self.project_key, self.tool_id))
            else:
                self._descriptor = self.client._perform_json("POST", "/projects/%s/agents/tools/%s/descriptor" % (self.project_key, self.tool_id), body={"context": context})
        return self._descriptor

    def get_settings(self):
        """
        Get the agent tools' settings

        :return: a handle on the tool settings
        :rtype: :class:`dataikuapi.dss.agent_tool.DSSAgentToolSettings` or a subclass
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/agents/tools/%s" % (self.project_key, self.id))

        if settings["type"] == "VectorStoreSearch":
            return DSSVectorStoreSearchAgentToolSettings(self, settings)
        else:
            return DSSAgentToolSettings(self, settings)

    def delete(self):
        """
        Delete the agent tool
        """
        return self.client._perform_empty("DELETE", "/projects/%s/agents/tools/%s" % (self.project_key, self.id))

    def as_langchain_structured_tool(self, context = None):
        """
        :returns: this tool as a LangChain StructuredTool
        :rtype: langchain_core.tools.StructuredTool
        """
        from dataikuapi.dss.langchain.tool import convert_to_langchain_structured_tool
        return convert_to_langchain_structured_tool(self, context)

    def run(self, input, context=None, subtool_name=None, memory_fragment=None, tool_validation_responses=None, tool_validation_requests=None):
        """
        Execute a tool call

        :param str input: Text input
        :param dict context: Additional request context
        :param str subtool_name: Name of the sub-tool, if applicable (e.g., for a MCP tool)
        :rtype: dict
        :returns: The result of running this tool
        """

        invocation = {
            "toolId" : self.tool_id,
            "input" : {
                "input" : input
            }
        }

        if tool_validation_responses:
            invocation["input"]["toolValidationResponses"] = tool_validation_responses
        if tool_validation_requests:
            invocation["input"]["toolValidationRequests"] = tool_validation_requests
        if memory_fragment:
            invocation["input"]["memoryFragment"] = memory_fragment

        if subtool_name is not None:
            invocation["input"]["subtoolName"] = subtool_name
        if context is not None:
            invocation["input"]["context"] = context
        # Note that 'prepare_query_for_nested_llm_mesh_call' throws an exception when the max LLM mesh stack depth is reached
        invocation["input"] = prepare_query_for_nested_llm_mesh_call(invocation["input"])

        return self.client._perform_json("POST", "/projects/%s/agents/tools/%s/invocations" % (self.project_key, self.tool_id), body=invocation)

    def describe_tool_call(self, input, descriptor, context=None, subtool_name=None):
        """
        Get a description for a tool call before it is executed

        :return: a string description of the tool call
        :rtype: Optional[str]
        """

        description_request = {
            "input" : {
                "input" : input
            },
            "descriptor": descriptor
        }

        if subtool_name is not None:
            description_request["input"]["subtoolName"] = subtool_name
        if context is not None:
            description_request["input"]["context"] = context
        description_request["input"] = prepare_query_for_nested_llm_mesh_call(description_request["input"])

        tool_call_descriptor = self.client._perform_json("POST", "/projects/%s/agents/tools/%s/describe-tool-call" % (self.project_key, self.tool_id), body=description_request)
        if tool_call_descriptor is None:
            return None

        return tool_call_descriptor.get("description", None)



#####################################################
# Creation and Edition - Base Classes
#####################################################

class DSSAgentToolCreator(object):
    """
    Helper to create new agent tools

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.new_agent_tool()` instead.
    """
    def __init__(self, project, type, name, id):
        self.project = project
        self.proto = {
            "type": type,
            "name": name,
            "id":id,
            "creationParams" : {}
        }

    def create(self):
        """
        Creates the new agent tool in the project, and return a handle to interact with it.

        :rtype: :class:`dataikuapi.dss.agent_tool.DSSAgentTool`
        """
        self._finish_creation()


        id = self.project.client._perform_json("POST", "/projects/%s/agents/tools" % self.project.project_key, body=self.proto)
        return DSSAgentTool(self.project.client, self.project.project_key, id["id"])

    def _finish_creation(self):
        pass

class DSSAgentToolSettings(DSSTaggableObjectSettings):
    def __init__(self, agent_tool, settings):
        super(DSSAgentToolSettings, self).__init__(settings)
        self.agent_tool = agent_tool
        self._settings = settings

    def get_raw(self):
        """
        :returns: the raw settings dict for this agent tool
        :rtype: dict
        """
        return self._settings

    @property
    def params(self):
        """
        The parameters of the tool, as a dict. Changes to the dict will be reflected when saving
        """
        return self._settings["params"]


    def save(self):
        """
        Saves the settings of the agent tool
        """
        self.agent_tool.client._perform_empty(
            "PUT", "/projects/%s/agents/tools/%s" % (self.agent_tool.project_key, self.agent_tool.id), body=self._settings)

#####################################################
# Creation and Edition - Per-type
#####################################################

def _kb_to_loc(context_project_key, kb):
    if isinstance(kb, DSSKnowledgeBank):
        return AnyLoc(kb.project_key, kb.id)
    elif isinstance(kb, DSSKnowledgeBankListItem):
        return AnyLoc(kb.project_key, kb.id)
    elif isinstance(kb, str):
        return AnyLoc.from_ref(context_project_key, kb)
    else:
        raise Exception("Invalid kb object: %s" % kb)

class DSSVectorStoreSearchAgentToolCreator(DSSAgentToolCreator):
    def __init__(self, project, type, name, id):
        DSSAgentToolCreator.__init__(self, project, type, name, id)

    def with_knowledge_bank(self, kb):
        """
        :param kb: Knowledge Bank (object, list item, or identifier) to use in this tool
        :type kb: DSSKnowledgeBank | DSSKnowledgeBankListItem | str
        """
        loc = _kb_to_loc(self.project.project_key, kb)
        self.proto["creationParams"]["knowledgeBankRef"] = loc.to_ref(self.project.project_key)
        return self

class DSSVectorStoreSearchAgentToolSettings(DSSAgentToolSettings):
    def __init__(self, agent_tool, settings):
        DSSAgentToolSettings.__init__(self, agent_tool, settings)

    def set_knowledge_bank(self, kb):
        """
        :param kb: Knowledge Bank (object, list item, or identifier) to use in this tool
        :type kb: DSSKnowledgeBank | DSSKnowledgeBankListItem | str
        """
        loc = _kb_to_loc(self.project.project_key, kb)
        self.settings["params"]["knowledgeBankRef"] = loc.to_ref(self.agent_tool.project_key)
