from .utils import DSSTaggableObjectListItem
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
        return DSSAgentTool(self.client, self.project_key, self._data["id"], "descriptor" in self._data and self._data["desciptor"] or None)

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
    def description(self):
        """
        :returns: The description of the LLM (name, description, input schema)
        :rtype: string
        """
        return self._data["description"]



class DSSAgentTool(object):
    def __init__(self, client, project_key, tool_id, descriptor=None):
        self.client = client
        self.project_key = project_key
        self.tool_id = tool_id
        self._descriptor = descriptor

    def get_descriptor(self):
        if self._descriptor is None:
            self._descriptor =  self.client._perform_json("GET", "/projects/%s/agents/tools/%s/descriptor" % (self.project_key, self.tool_id))
        return self._descriptor


    def as_langchain_structured_tool(self, context = None):
        from dataikuapi.dss.langchain.tool import convert_to_langchain_structured_tool
        return convert_to_langchain_structured_tool(self, context)

    def run(self, input, context=None):
        invocation = {
            "toolId" : self.tool_id,
            "input" : {
                "input" : input
            }
        }
        if context is not None:
            invocation["input"]["context"] = context

        return self.client._perform_json("POST", "/projects/%s/agents/tools/%s/invocations" % (self.project_key, self.tool_id), body=invocation)
