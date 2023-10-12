class DSSLLM(object):
    """
    A handle to interact with a DSS-managed LLM
    """
    def __init__(self, client, project_key, llm_id):
        self.client = client
        self.project_key = project_key
        self.llm_id = llm_id

    def new_completion(self):
        return DSSLLMCompletionQuery(self)

    def new_embeddings(self):
        return DSSLLMEmbeddingsQuery(self)


class DSSLLMEmbeddingsQuery(object):
    def __init__(self, llm):
        self.llm = llm
        self.eq = {"queries": [], "llmId": llm.llm_id}

    def add_text(self, text):
        self.eq["queries"].append({"text": text})

    def execute(self):
        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/embeddings" % (self.llm.project_key), body=self.eq)
        return DSSLLMEmbeddingsResponse(ret)

class DSSLLMEmbeddingsResponse(object):
    def __init__(self, raw_resp):
        self._raw = raw_resp

    def get_embeddings(self):
        """
        returns all embeddings as a list of list of floats
        """
        return [r["embedding"] for r in self._raw["responses"]]

class DSSLLMCompletionQuery(object):
    def __init__(self, llm):
        self.llm = llm
        self.cq = {"messages": [], "settings": {}}

    def with_message(self, message, role="user"):
        self.cq["messages"].append({"content": message, "role": role})
        return self

    def execute(self):
        queries = {"queries": [self.cq], "llmId": self.llm.llm_id}
        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries)
        
        return DSSLLMCompletionResponse(ret["responses"][0])

class DSSLLMCompletionResponse(object):
    def __init__(self, raw_resp):
        self._raw = raw_resp

    @property
    def success(self):
        return self._raw["ok"]

    @property
    def text(self):
        return self._raw["text"]
