from .utils import DSSTaggableObjectListItem

class DSSLLMListItem(DSSTaggableObjectListItem):
    """
    An item in a list of llms

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_llms`.
    """
    def __init__(self, client, project_key, data):
        super(DSSLLMListItem, self).__init__(data)
        self.project_key = project_key
        self.client = client

    def to_llm(self):
        """
        Convert the current item.

        :returns: A handle for the llm.
        :rtype: :class:`dataikuapi.dss.llm.DSSLLM`
        """
        return DSSLLM(self.client, self.project_key, self._data["id"])

    @property
    def id(self):
        """
        :returns: The id of the llm.
        :rtype: string
        """
        return self._data["id"]

    @property
    def type(self):
        """
        :returns: The type of the LLM
        :rtype: string
        """
        return self._data["type"]

    @property
    def description(self):
        """
        :returns: The description of the LLM
        :rtype: string
        """
        return self._data["friendlyName"]

class DSSLLM(object):
    """
    A handle to interact with a DSS-managed LLM.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.project.DSSProject.get_llm` instead.
    """
    def __init__(self, client, project_key, llm_id):
        self.client = client
        self.project_key = project_key
        self.llm_id = llm_id

    def new_completion(self):
        """
        Create a new completion query.

        :returns: A handle on the generated completion query.
        :rtype: :class:`DSSLLMCompletionQuery`
        """
        return DSSLLMCompletionQuery(self)

    def new_completions(self):
        """
        Create a new multi-completion query.

        :returns: A handle on the generated multi-completion query.
        :rtype: :class:`DSSLLMCompletionsQuery`
        """
        return DSSLLMCompletionsQuery(self)

    def new_embeddings(self):
        """
        Create a new embedding query.

        :returns: A handle on the generated embeddings query.
        :rtype: :class:`DSSLLMEmbeddingsQuery`
        """
        return DSSLLMEmbeddingsQuery(self)


class DSSLLMEmbeddingsQuery(object):
    """
    A handle to interact with an embedding query.
    Embedding queries allow you to transform text into embedding vectors
    using a DSS-managed model.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_embeddings` instead.
    """
    def __init__(self, llm):
        self.llm = llm
        self.eq = {"queries": [], "llmId": llm.llm_id}

    def add_text(self, text):
        """
        Add text to the embedding query.

        :param str text: Text to add to the query.
        """
        self.eq["queries"].append({"text": text})
        return self

    def execute(self):
        """
        Run the embedding query.

        :returns: The results of the embedding query.
        :rtype: :class:`DSSLLMEmbeddingsResponse`
        """
        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/embeddings" % (self.llm.project_key), body=self.eq)
        return DSSLLMEmbeddingsResponse(ret)


class DSSLLMEmbeddingsResponse(object):
    """
    A handle to interact with an embedding query result.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMEmbeddingsQuery.execute` instead.
    """
    def __init__(self, raw_resp):
        self._raw = raw_resp

    def get_embeddings(self):
        """
        Retrieve vectors resulting from the embeddings query.

        :returns: A list of lists containing all embedding vectors.
        :rtype: list
        """
        for r in self._raw["responses"]:
            if not "embedding" in r:
                raise Exception("At least one embedding request failed: %s" % r.get("errorMessage", "Unknown error"))

        return [r["embedding"] for r in self._raw["responses"]]


class DSSLLMCompletionQuery(object):
    """
    A handle to interact with a completion query.
    Completion queries allow you to send a prompt to a DSS-managed LLM and
    retrieve its response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_completion` instead.
    """
    def __init__(self, llm):
        self.llm = llm
        self.cq = {"messages": []}
        self._settings = {}

    @property
    def settings(self):
        """
        :return: The completion query settings.
        :rtype: dict
        """
        return self._settings

    def with_message(self, message, role="user"):
        """
        Add  a message to the completion query.

        :param str message: The message text.
        :param str role: The message role. Use ``system`` to set the LLM behavior, ``assistant`` to store predefined
         responses, ``user`` to provide requests or comments for the LLM to answer to. Defaults to ``user``.
        """
        self.cq["messages"].append({"content": message, "role": role})
        return self

    def execute(self):
        """
        Run the completion query and retrieve the LLM response.

        :returns: The LLM response.
        :rtype: :class:`DSSLLMCompletionResponse`
        """
        queries = {"queries": [self.cq], "settings": self._settings, "llmId": self.llm.llm_id}
        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries)
        
        return DSSLLMCompletionResponse(ret["responses"][0])


class DSSLLMCompletionsQuerySingleQuery(object):
    def __init__(self):
        self.cq = {"messages": []}

    def with_message(self, message, role="user"):
        """
        Add a message to the completion query.

        :param str message: The message text.
        :param str role: The message role. Use ``system`` to set the LLM behavior, ``assistant`` to store predefined
         responses, ``user`` to provide requests or comments for the LLM to answer to. Defaults to ``user``.
        """
        self.cq["messages"].append({"content": message, "role": role})
        return self

class DSSLLMCompletionsQuery(object):
    """
    A handle to interact with a multi-completion query.
    Completion queries allow you to send a prompt to a DSS-managed LLM and
    retrieve its response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_completion` instead.
    """
    def __init__(self, llm):
        self.llm = llm
        self.queries = []
        self._settings = {}

    @property
    def settings(self):
        """
        :return: The completion query settings.
        :rtype: dict
        """
        return self._settings

    def new_completion(self):
        ret = DSSLLMCompletionsQuerySingleQuery()
        self.queries.append(ret)
        return ret

    def execute(self):
        """
        Run the completions query and retrieve the LLM response.

        :returns: The LLM response.
        :rtype: :class:`DSSLLMCompletionsResponse`
        """
        queries = {"queries": [q.cq for q in self.queries], "settings": self._settings, "llmId": self.llm.llm_id}
        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries)
        
        return DSSLLMCompletionsResponse(ret["responses"])

class DSSLLMCompletionResponse(object):
    """
    A handle to interact with a completion response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMCompletionQuery.execute` instead.
    """
    def __init__(self, raw_resp):
        self._raw = raw_resp

    @property
    def success(self):
        """
        :return: The outcome of the completion query.
        :rtype: bool
        """
        return self._raw["ok"]

    @property
    def text(self):
        """
        :return: The raw text of the LLM response.
        :rtype: str
        """
        return self._raw["text"]

class DSSLLMCompletionsResponse(object):
    """
    A handle to interact with a multi-completion response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMCompletionsQuery.execute` instead.
    """
    def __init__(self, raw_resp):
        self._raw = raw_resp

    @property
    def responses(self):
        """The array of responses"""
        return [DSSLLMCompletionResponse(x) for x in self._raw]
    