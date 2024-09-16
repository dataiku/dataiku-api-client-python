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

    def new_embeddings(self, text_overflow_mode="FAIL"):
        """
        Create a new embedding query.

        :param str text_overflow_mode: How to handle longer texts than what the model supports. Either 'TRUNCATE' or 'FAIL'.
        :returns: A handle on the generated embeddings query.
        :rtype: :class:`DSSLLMEmbeddingsQuery`
        """
        return DSSLLMEmbeddingsQuery(self, text_overflow_mode)

    def new_images_generation(self):
        return DSSLLMImageGenerationQuery(self)
    
    def as_langchain_llm(self, **data):
        """
        Create a langchain-compatible LLM object for this LLM.

        :returns: A langchain-compatible LLM object.
        :rtype: :class:`dataikuapi.dss.langchain.llm.DKULLM`
        """
        from dataikuapi.dss.langchain.llm import DKULLM
        return DKULLM(llm_handle=self, **data)

    def as_langchain_chat_model(self, **data):
        """
        Create a langchain-compatible chat LLM object for this LLM.

        :returns: A langchain-compatible LLM object.
        :rtype: :class:`dataikuapi.dss.langchain.llm.DKUChatModel`
        """
        from dataikuapi.dss.langchain.llm import DKUChatModel
        return DKUChatModel(llm_handle=self, **data)

    def as_langchain_embeddings(self, **data):
        """
        Create a langchain-compatible embeddings object for this LLM.

        :returns: A langchain-compatible embeddings object.
        :rtype: :class:`dataikuapi.dss.langchain.embeddings.DKUEmbeddings`
        """
        from dataikuapi.dss.langchain.embeddings import DKUEmbeddings
        return DKUEmbeddings(llm_handle=self, **data)


class DSSLLMEmbeddingsQuery(object):
    """
    A handle to interact with an embedding query.
    Embedding queries allow you to transform text into embedding vectors
    using a DSS-managed model.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_embeddings` instead.
    """
    def __init__(self, llm, text_overflow_mode):
        self.llm = llm
        self.eq = {
            "queries": [],
            "llmId": llm.llm_id,
            "settings": {
                "textOverflowMode": text_overflow_mode
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


class DSSLLMCompletionsQuerySingleQuery(object):
    def __init__(self):
        self.cq = {"messages": []}

    def new_multipart_message(self, role="user"):
        """
        Start adding a multipart-message to the completion query.

        Use this to add image parts to the message.

        :param str role: The message role. Use ``system`` to set the LLM behavior, ``assistant`` to store predefined
          responses, ``user`` to provide requests or comments for the LLM to answer to. Defaults to ``user``.

        :rtype: :class:`DSSLLMCompletionQueryMultipartMessage`
        """
        return DSSLLMCompletionQueryMultipartMessage(self, role)

    def with_message(self, message, role="user"):
        """
        Add a message to the completion query.

        :param str message: The message text.
        :param str role: The message role. Use ``system`` to set the LLM behavior, ``assistant`` to store predefined
          responses, ``user`` to provide requests or comments for the LLM to answer to. Defaults to ``user``.
        """
        role_message = {
            "role": role,
            "content": message,
        }

        self.cq["messages"].append(role_message)
        return self

    def with_tool_calls(self, tool_calls, role="assistant"):
        """
        Add tool calls to the completion query.

        :param list[dict] tool_calls: Calls to tools that the LLM requested to use.
        :param str role: The message role. Defaults to ``assistant``.
        """
        role_message = {
            "role": role,
            "toolCalls": tool_calls,
        }

        self.cq["messages"].append(role_message)
        return self

    def with_tool_output(self, tool_output, tool_call_id, role="tool"):
        """
        Add a tool message to the completion query.

        :param str tool_output: The tool output, as a string.
        :param str tool_call_id: The tool call id, as provided by the LLM in the conversation messages.
        :param str role: The message role. Defaults to ``tool``.
        """
        role_message = {
            "role": role,
            "toolOutputs": [{
                "callId": tool_call_id,
                "output": tool_output,
            }],
        }

        self.cq["messages"].append(role_message)
        return self


class DSSLLMCompletionQuery(DSSLLMCompletionsQuerySingleQuery):
    """
    A handle to interact with a completion query.
    Completion queries allow you to send a prompt to a DSS-managed LLM and
    retrieve its response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_completion` instead.
    """
    def __init__(self, llm):
        super().__init__()
        self.llm = llm
        self._settings = {}

    @property
    def settings(self):
        """
        :return: The completion query settings.
        :rtype: dict
        """
        return self._settings

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
        Run the completion query and retrieve the LLM response as streamed chunks.

        :returns: An iterator over the LLM response chunks
        :rtype: Iterator[Union[:class:`DSSLLMStreamedCompletionChunk`, :class:`DSSLLMStreamedCompletionFooter`]]
        """
        request = {"query": self.cq, "settings": self.settings, "llmId": self.llm.llm_id}
        ret = self.llm.client._perform_raw("POST", "/projects/%s/llms/streamed-completion" % (self.llm.project_key), body=request)

        sseclient = _SSEClient(ret.raw)

        for evt in sseclient.iterevents():
            if evt.event == "completion-chunk":
                yield DSSLLMStreamedCompletionChunk(json.loads(evt.data))
            else:
                yield DSSLLMStreamedCompletionFooter(json.loads(evt.data))


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


class DSSLLMCompletionQueryMultipartMessage(object):
    """
      .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMCompletionQuery.new_multipart_message` or 
        :meth:`dataikuapi.dss.llm.DSSLLMCompletionsQuerySingleQuery.new_multipart_message`.

    """
    def __init__(self, q, role):
        self.q = q
        self.msg = {"role": role, "parts" : []}

    def with_text(self, text):
        """
        Add a text part to the multipart message
        """
        self.msg["parts"].append({"type": "TEXT", "text": text})
        return self

    def with_inline_image(self, image, mime_type=None):
        """
        Add an image part to the multipart message

        :param image: bytes or str (base64)
        :param mime_type str: None for default
        """
        img_b64 = None
        if isinstance(image, str):
            img_b64 = image
        elif isinstance(image, bytes):
            import base64
            img_b64 = base64.b64encode(image).decode("utf8")

        part = {
            "type": "IMAGE_INLINE",
            "inlineImage": img_b64
        }

        if mime_type is not None:
            part["imageMimeType"] = mime_type

        self.msg["parts"].append(part)
        return self

    def add(self):
        """Add this message to the completion query"""
        self.q.cq["messages"].append(self.msg)
        return self.q


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
        :rtype: Union[str, None]
        """
        return self._raw.get("text")

    @property
    def tool_calls(self):
        """
        :return: The tool calls of the LLM response.
        :rtype: Union[list, None]
        """
        return self._raw.get("toolCalls")

    @property
    def log_probs(self):
        """
        :return: The log probs of the LLM response.
        :rtype: Union[list, None]
        """
        return self._raw.get("logProbs")

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
