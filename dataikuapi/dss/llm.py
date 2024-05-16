from .utils import DSSTaggableObjectListItem
import json

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

    def new_images_generation(self):
        return DSSLLMImageGenerationQuery(self)



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
        self.eq = {
            "queries": [],
            "llmId": llm.llm_id,
            "settings": {
                # TODO: include textOverflowMode when merging into master
            }
        }

    def add_text(self, text):
        """
        Add text to the embedding query.

        :param str text: Text to add to the query.
        """
        self.eq["queries"].append({"text": text})
        return self

    def add_image(self, image_base64):
        """
        Add an image to the embedding query.

        :param str image_base64: Image content, as a base 64 formatted string.
        """
        self.eq["queries"].append({"inlineImage": image_base64})
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

    def execute_streamed(self):
        """
        Prevent documentation as it's still preview.
        :meta private:
        """
        request = {"query": self.cq, "settings": self.settings, "llmId": self.llm.llm_id}
        ret = self.llm.client._perform_raw("POST", "/projects/%s/llms/streamed-completion" % (self.llm.project_key), body=request)

        sseclient = _SSEClient(ret.raw)

        for evt in sseclient.iterevents():
            if evt.event == "completion-chunk":
                yield DSSLLMStreamedCompletionChunk(json.loads(evt.data))
            else:
                yield DSSLLMStreamedCompletionFooter(json.loads(evt.data))


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


class DSSLLMStreamedCompletionChunk(object):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "<completion-chunk: %s>" % self.data


class DSSLLMStreamedCompletionFooter(object):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return "<completion-footer: %s>" % self.data


class _SSEEvent(object):
    def __init__(self, id=None, event=None, data=""):
        self.id = id
        self.event = event
        self.data = data

class _SSEClient(object):
    def __init__(self, raw_source):
        self.raw_source = raw_source

    def _read(self):
        """Reads the raw source and yields events. Reassembles events
        that may span multiple HTTP chunks"""

        data = b''
        for chunk in self.raw_source:
            for line in chunk.splitlines(True):
                data += line
                if data.endswith(b'\r\r') or data.endswith(b'\n\n') or data.endswith(b'\r\n\r\n'):
                    yield data
                    data = b''
        if data:
            yield data

    def iterevents(self):
        for event_chunk in self._read():
            evt = _SSEEvent()

            for line in event_chunk.splitlines():
                line = line.decode("utf8")

                # Start with : --> comment
                if line.startswith(":"):
                    continue

                data = line.split(":", 1)
                field = data[0]

                if len(data) > 1:
                    value = data[1].strip()
                else:
                    value = ''

                if field == 'data':
                    evt.__dict__[field] += value + '\n'
                else:
                    evt.__dict__[field] = value

            #print("Yielding event: %s" % evt.__dict__)
            yield evt


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
    




class DSSLLMImageGenerationQuery(object):
    """
    A handle to interact with an image generation query.
    
    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_images_generation` instead.
    """
    def __init__(self, llm):
        self.llm = llm
        self.gq = {
            "prompts": [],
            "negativePrompts": [],
            "llmId": self.llm.llm_id
        }

    def with_prompt(self, prompt, weight=None):
        """
        """
        self.gq["prompts"].append({"prompt": prompt, "weight": weight})
        return self
 
    def with_negative_prompt(self, prompt, weight=None):
        """
        """
        self.gq["negativePrompts"].append({"prompt": prompt, "weight": weight})
        return self

    def with_original_image(self, image, mode=None, weight=None):
        if isinstance(image, str):
            self.gq["originalImage"] = image
        elif isinstance(image, bytes):
            import base64
            self.gq["originalImage"] = base64.b64encode(image).decode("utf8")

        if mode is not None:
            self.gq["originalImageEditionMode"] = mode

        if weight is not None:
            self.gq["originalImageWeight"] = weight
        return self

    def with_mask(self, mode, image=None, text=None):
        self.gq["maskMode"] = mode
        
        if image is not None:
            if isinstance(image, str):
                self.gq["maskImage"] = image
            elif isinstance(image, bytes):
                import base64
                self.gq["maskImage"] = base64.b64encode(image).decode("utf8")
        return self

    @property
    def height(self):
        return self.gq.get("height", None)
    @height.setter
    def height(self, new_value):
        self.gq["height"] = new_value

    @property
    def width(self):
        return self.gq.get("width", None)
    @width.setter
    def width(self, new_value):
        self.gq["width"] = new_value

    @property
    def fidelity(self):
        return self.gq.get("fidelity", None)
    @fidelity.setter
    def fidelity(self, new_value):
        self.gq["fidelity"] = new_value

    @property
    def quality(self):
        return self.gq.get("quality", None)
    @quality.setter
    def quality(self, new_value):
        self.gq["quality"] = new_value

    @property
    def seed(self):
        return self.gq.get("seed", None)
    @seed.setter
    def seed(self, new_value):
        self.gq["seed"] = new_value

    @property
    def style(self):
        """Style of the image to generate. Valid values depend on the targeted model"""
        return self.gq.get("style", None)
    @style.setter
    def style(self, new_value):
        self.gq["style"] = new_value

    @property
    def images_to_generate(self):
        return self.gq.get("nbImagesToGenerate", None)
    @images_to_generate.setter
    def images_to_generate(self, new_value):
        self.gq["nbImagesToGenerate"] = new_value

    def with_aspect_ratio(self, ar):
        self.gq["height"] = 1024
        self.gq["width"] = int(1024 * ar)
        return self

    def execute(self):
        """
        Executes the image generation

        :rtype: :class:DSSLLMImageGenerationResponse
        """

        ret = self.llm.client._perform_json("POST", "/projects/%s/llms/images" % (self.llm.project_key), body=self.gq)
        return DSSLLMImageGenerationResponse(ret)

class DSSLLMImageGenerationResponse(object):
    """
    A handle to interact with an image generation response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMImageGenerationQuery.execute` instead.
    """
    def __init__(self, raw_resp):
        self._raw = raw_resp

    @property
    def success(self):
        """
        :return: The outcome of the image generation query.
        :rtype: bool
        """
        return self._raw["ok"]

    def first_image(self, as_type="bytes"):
        """
        :return: The first generated image.
        :rtype: str
        """

        if not self.success:
            raise Exception("Image generation did not succeed: %s" % self._raw["errorMessage"])

        if len(self._raw["images"]) == 0:
            raise Exception("Image generation succeeded but did not return any image")

        if as_type == "bytes":
            import base64
            return base64.b64decode(self._raw["images"][0]["data"])

        else:
            return self._raw["images"][0]["data"]