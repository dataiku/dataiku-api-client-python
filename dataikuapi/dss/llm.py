from .utils import DSSTaggableObjectListItem
import json
import os
import logging
import threading

_dku_bypass_guardrail_ls = threading.local()


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
        self._guardrails = None
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

    def add_image(self, image, text = None):
        """
        Add an image to the embedding query.

        :param image: Image content as bytes or str (base64)
        :param text: Optional text (requires a multimodal model)
        """
        query = {}

        if isinstance(image, str):
            query["inlineImage"] = image
        elif isinstance(image, bytes):
            import base64
            query["inlineImage"] = base64.b64encode(image).decode("utf8")
        else:
            raise Exception("Expecting image to be an instance of str or bytes, got '%s' instead." % type(image) )

        if text is not None:
            query["text"] = text

        if query:
            self.eq["queries"].append(query)

        return self

    def new_guardrail(self, type):
        """
        Start adding a guardrail to the request. You need to configure the returned object, and call add() to actually add it
        """
        return DSSLLMRequestGuardrailBuilder(self, type)

    def execute(self):
        """
        Run the embedding query.

        :returns: The results of the embedding query.
        :rtype: :class:`DSSLLMEmbeddingsResponse`
        """

        if self._guardrails is not None:
            self.eq["guardrails"] = self._guardrails

        if hasattr(_dku_bypass_guardrail_ls, "current_bypass_token"):
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/embeddings" % (self.llm.project_key), body=self.eq,
                                        headers= {"x-dku-guardrails-bypass-token": _dku_bypass_guardrail_ls.current_bypass_token})
        else:
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

        .. caution::
            Tool calls support is experimental for locally-running Hugging Face models.

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

    def with_context(self, context):
        self.cq["context"] = context
        return self


class SettingsMixin(object):
    def with_json_output(self, schema=None, strict=None, compatible=None):
        """
        Request the model to generate a valid JSON response, for models that support it.

        Note that some models may require you to also explicitly request this in the user or system prompt to use this.

        .. caution::
            JSON output support is experimental for locally-running Hugging Face models.

        :param dict schema: (optional) If specified, request the model to produce a JSON response that adheres to the provided schema. Support varies across models/providers.
        :param bool strict: (optional) If a schema is provided, whether to strictly enforce it. Support varies across models/providers.
        :param bool compatible: (optional) Allow DSS to modify the schema in order to increase compatibility, depending on known limitations of the model/provider. Defaults to automatic.
        """
        self._settings["responseFormat"] = {
            "type": "json",
            "schema": schema,
            "strict": strict,
            "compatible": compatible,
        }
        return self

    def with_structured_output(self, model_type, strict=None, compatible=None):
        """
        Instruct the model to generate a response as an instance of a specified Pydantic model.

        This functionality depends on `with_json_output` and necessitates that the model supports JSON output with a schema.

        .. caution::
            Structured output support is experimental for locally-running Hugging Face models.

        :param pydantic.BaseModel model_type: A Pydantic model class used for structuring the response.
        :param bool strict: (optional) see :func:`with_json_output`
        :param bool compatible: (optional) see :func:`with_json_output`
        """
        if hasattr(model_type, "model_json_schema") and hasattr(model_type, "model_validate_json"):
            schema = model_type.model_json_schema()  # Pydantic 2 BaseModel
            self._response_parser = model_type.model_validate_json
        elif hasattr(model_type, "schema") and hasattr(model_type, "parse_raw"):
            schema = model_type.schema()  # Pydantic 1 BaseModel
            self._response_parser = model_type.parse_raw
        else:
            # 'model_type' is not a Pydantic BaseModel. Derive schema Python type hints.
            try:
                import pydantic
            except ImportError:
                raise Exception("Pydantic is required to use Python's type hints with structured output")

            if hasattr(pydantic, "TypeAdapter"):
                # Pydantic 2 provides a TypeAdapter to work with regular Python classes / type hints
                from pydantic import TypeAdapter
                adapter = TypeAdapter(model_type)
                schema = adapter.json_schema()
                self._response_parser = adapter.validate_json
            elif hasattr(pydantic, "schema_of") and hasattr(pydantic, "parse_obj_as"):
                # Pydantic 1 had similar functionality via 'schema_of' and 'parse_obj_as'
                schema = pydantic.schema_of(model_type)

                def response_parser(json_response):
                    parsed_json = json.loads(json_response)
                    return pydantic.parse_obj_as(model_type, parsed_json)

                self._response_parser = response_parser
            else:
                # Unsupported Pydantic version
                raise Exception("Incompatible Pydantic version")
        self.with_json_output(schema=schema, strict=strict, compatible=compatible)
        return self

class DSSLLMRequestGuardrailBuilder(object):
    def __init__(self, request, type):
        self.request = request
        self.guardrail = { "type" : type, "enabled": True, "params" : {}}

    @property
    def params(self):
        return self.guardrail["params"]

    def add(self):
        if self.request._guardrails is None:
            self.request._guardrails = {"guardrails" : []}
        self.request._guardrails["guardrails"].append(self.guardrail)


class DSSLLMCompletionQuery(DSSLLMCompletionsQuerySingleQuery, SettingsMixin):
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
        self._guardrails = None
        self._response_parser = None

    @property
    def settings(self):
        """
        :return: The completion query settings.
        :rtype: dict
        """
        return self._settings

    def new_guardrail(self, type):
        """
        Start adding a guardrail to the request. You need to configure the returned object, and call add() to actually add it
        """
        return DSSLLMRequestGuardrailBuilder(self, type)

    def execute(self):
        """
        Run the completion query and retrieve the LLM response.

        :returns: The LLM response.
        :rtype: :class:`DSSLLMCompletionResponse`
        """
        queries = {"queries": [self.cq], "settings": self._settings, "llmId": self.llm.llm_id}

        if self._guardrails is not None:
            queries["guardrails"] = self._guardrails

        if hasattr(_dku_bypass_guardrail_ls, "current_bypass_token"):
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries,
                        headers= {"x-dku-guardrails-bypass-token": _dku_bypass_guardrail_ls.current_bypass_token})
        else:
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries)

        return DSSLLMCompletionResponse(raw_resp=ret["responses"][0], response_parser=self._response_parser)

    def execute_streamed(self):
        """
        Run the completion query and retrieve the LLM response as streamed chunks.

        :returns: An iterator over the LLM response chunks
        :rtype: Iterator[Union[:class:`DSSLLMStreamedCompletionChunk`, :class:`DSSLLMStreamedCompletionFooter`]]
        """
        request = {"query": self.cq, "settings": self.settings, "llmId": self.llm.llm_id}

        if self._guardrails is not None:
            request["guardrails"] = self._guardrails

        if hasattr(_dku_bypass_guardrail_ls, "current_bypass_token"):
            ret = self.llm.client._perform_raw("POST", "/projects/%s/llms/streamed-completion" % (self.llm.project_key), body=request,
                        headers= {"x-dku-guardrails-bypass-token": _dku_bypass_guardrail_ls.current_bypass_token})
        else:
            ret = self.llm.client._perform_raw("POST", "/projects/%s/llms/streamed-completion" % (self.llm.project_key), body=request)

        sseclient = _SSEClient(ret.iter_content(128))

        for evt in sseclient.iterevents():
            if evt.event == "completion-chunk":
                yield DSSLLMStreamedCompletionChunk(json.loads(evt.data))
            else:
                yield DSSLLMStreamedCompletionFooter(json.loads(evt.data))


class DSSLLMCompletionsQuery(SettingsMixin):
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
        self._guardrails = None
        self._response_parser = None

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

    def new_guardrail(self, type):
        """
        Start adding a guardrail to the request. You need to configure the returned object, and call add() to actually add it
        """
        return DSSLLMRequestGuardrailBuilder(self, type)

    def execute(self):
        """
        Run the completions query and retrieve the LLM response.

        :returns: The LLM response.
        :rtype: :class:`DSSLLMCompletionsResponse`
        """
        queries = {"queries": [q.cq for q in self.queries], "settings": self._settings, "llmId": self.llm.llm_id}

        if self._guardrails is not None:
            queries["guardrails"] = self._guardrails

        if hasattr(_dku_bypass_guardrail_ls, "current_bypass_token"):
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries,
                        headers= {"x-dku-guardrails-bypass-token": _dku_bypass_guardrail_ls.current_bypass_token})
        else:
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/completions" % (self.llm.project_key), body=queries)

        return DSSLLMCompletionsResponse(ret["responses"], response_parser=self._response_parser)


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

        :param Union[str, bytes] image: The image
        :param str mime_type: None for default
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

    def with_image_url(self, image):
        """
        Add an image url part to the multipart message

        :param image: str the image url
        """

        self.msg["parts"].append({"type": "IMAGE_URI", "imageUrl": image})
        return self

    def add(self):
        """Add this message to the completion query"""
        self.q.cq["messages"].append(self.msg)
        return self.q


class DSSLLMStreamedCompletionChunk(object):
    def __init__(self, data):
        self.data = data

    @property
    def type(self):
        """Type of this chunk, either "content" or "event" """
        return self.data.get("type", "content")

    @property
    def text(self):
        """If this chunk is content and has text, the (partial) text"""
        return self.data.get("text", None)

    @property
    def event_kind(self):
        """If this chunk is an event, its kind"""
        return self.data.get("eventKind", None)

    def __repr__(self):
        return "<completion-chunk: %s>" % self.data


class DSSLLMStreamedCompletionFooter(object):
    def __init__(self, data):
        self.data = data

    # Compatibility for code that just checks for "type""
    @property
    def type(self):
        return "footer"

    @property
    def trace(self):
        return self.data.get("trace", None)

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
        #logging.debug("SSEClient._read")
        data = b''
        for chunk in self.raw_source:
            #logging.info("SSEClient._read: got chunk (len=%s): %s" % (len(chunk), chunk))
            for line in chunk.splitlines(True):
                data += line
                if data.endswith(b'\r\r') or data.endswith(b'\n\n') or data.endswith(b'\r\n\r\n'):
                    yield data
                    data = b''
        #logging.info("SSEClient._read: no more chunk")
        if data:
            yield data

    def iterevents(self):
        for event_chunk in self._read():
            #logging.info("SSEClient._iterevents: got event")
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

            if evt.event is not None:
                #logging.info("Yielding event: %s" % evt.__dict__)
                yield evt


class DSSLLMCompletionResponse(object):
    """
    Response to a completion
    """
    def __init__(self, raw_resp=None, text=None, finish_reason=None, response_parser=None, trace=None):
        if raw_resp is not None:
            self._raw = raw_resp
        else:
            self._raw = {}
            self._raw["text"] = text
            self._raw["finishReason"] = finish_reason
            self._raw["trace"] = trace

        self._json = None
        self._response_parser = response_parser
        self._parsed = None

    @property
    def json(self):
        """
        :return: LLM response parsed as a JSON object
        """
        self._fail_unless_success()
        if self._json is None and self.text is not None:
            self._json = json.loads(self.text)
        return self._json

    @property
    def parsed(self):
        self._fail_unless_success()
        if self._parsed is None and self.text is not None:
            if not self._response_parser:
                raise Exception("Structured output is not enabled for this completion query")
            self._parsed = self._response_parser(self.text)
        return self._parsed

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
        self._fail_unless_success()
        return self._raw.get("text")

    @property
    def tool_calls(self):
        """
        :return: The tool calls of the LLM response.
        :rtype: Union[list, None]
        """
        self._fail_unless_success()
        return self._raw.get("toolCalls")

    @property
    def log_probs(self):
        """
        :return: The log probs of the LLM response.
        :rtype: Union[list, None]
        """
        self._fail_unless_success()
        return self._raw.get("logProbs")

    @property
    def trace(self):
        return self._raw.get("trace", None)

    def _fail_unless_success(self):
        if not self.success:
            error_message = self._raw.get("errorMessage", "An unknown error occurred")
            raise Exception(error_message)

class DSSLLMCompletionsResponse(object):
    """
    A handle to interact with a multi-completion response.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLMCompletionsQuery.execute` instead.
    """
    def __init__(self, raw_resp, response_parser=None):
        self._raw = raw_resp
        self._response_parser = response_parser

    @property
    def responses(self):
        """The array of responses"""
        return [DSSLLMCompletionResponse(raw_resp=x, response_parser=self._response_parser) for x in self._raw]


class DSSLLMImageGenerationQuery(object):
    """
    A handle to interact with an image generation query.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.llm.DSSLLM.new_images_generation` instead.
    """
    def __init__(self, llm):
        self.llm = llm
        self._guardrails = None
        self.gq = {
            "prompts": [],
            "negativePrompts": [],
            "llmId": self.llm.llm_id
        }

    def with_prompt(self, prompt, weight=None):
        """
        Add a prompt to the image generation query.

        :param str prompt: The prompt text.
        :param float weight: Optional weight between 0 and 1 for the prompt.
        """
        self.gq["prompts"].append({"prompt": prompt, "weight": weight})
        return self

    def with_negative_prompt(self, prompt, weight=None):
        """
        Add a negative prompt to the image generation query.

        :param str prompt: The prompt text.
        :param float weight: Optional weight between 0 and 1 for the negative prompt.
        """
        self.gq["negativePrompts"].append({"prompt": prompt, "weight": weight})
        return self

    def with_original_image(self, image, mode=None, weight=None):
        """
        Add an image to the generation query.

        To edit specific pixels of the original image. A mask can be applied by calling `with_mask()`:

        >>> query.with_original_image(image, mode="INPAINTING") # replace the pixels using a mask

        To edit an image:

        >>> query.with_original_image(image, mode="MASK_FREE") # edit the original image according to the prompt

        >>> query.with_original_image(image, mode="VARY") # generates a variation of the original image

        :param Union[str, bytes] image: The original image as `str` in base 64 or `bytes`.
        :param str mode: The edition mode. Modes support varies across models/providers.
        :param float weight: The original image weight between 0 and 1.
        """
        if isinstance(image, str):
            self.gq["originalImage"] = image
        elif isinstance(image, bytes):
            import base64
            self.gq["originalImage"] = base64.b64encode(image).decode("utf8")
        else:
            raise Exception(u"The `image` parameter has to be of type `str` in base 64 or `bytes`. Got {} instead.".format(type(image)))

        if mode is not None:
            self.gq["originalImageEditionMode"] = mode

        if weight is not None:
            self.gq["originalImageWeight"] = weight
        return self

    def with_mask(self, mode, image=None):
        """
        Add a mask for edition to the generation query. Call this method alongside `with_original_image()`.

        To edit parts of the image using a black mask (replace the black pixels):

        >>> query.with_mask("MASK_IMAGE_BLACK", image=black_mask)

        To edit parts of the image that are transparent (replace the transparent pixels):

        >>> query.with_mask("ORIGINAL_IMAGE_ALPHA")

        :param str mode: The mask mode. Modes support varies across models/providers.
        :param Union[str, bytes] image: The mask image to apply to the image edition. As `str` in base 64 or `bytes`.
        """
        self.gq["maskMode"] = mode

        if image is not None:
            if isinstance(image, str):
                self.gq["maskImage"] = image
            elif isinstance(image, bytes):
                import base64
                self.gq["maskImage"] = base64.b64encode(image).decode("utf8")
            else:
                raise Exception(u"When specified, the mask `image` parameter has to be of type `str` in base 64 or `bytes`. Got type {} instead.".format(type(image)))
        return self

    def new_guardrail(self, type):
        """
        Start adding a guardrail to the request. You need to configure the returned object, and call add() to actually add it
        """
        return DSSLLMRequestGuardrailBuilder(self, type)

    @property
    def height(self):
        """
        :return: The generated image height in pixels.
        :rtype: Optional[int]
        """
        return self.gq.get("height", None)
    @height.setter
    def height(self, new_value):
        """
        The generated image height in pixels.

        :param Optional[int] new_value: The generated image height in pixels.
        """
        self.gq["height"] = int(new_value) if new_value is not None else None

    @property
    def width(self):
        """
        :return: The generated image width in pixels.
        :rtype: Optional[int]
        """
        return self.gq.get("width", None)
    @width.setter
    def width(self, new_value):
        """
        The generated image width in pixels.

        :param Optional[int] new_value: The generated image width in pixels.
        """
        self.gq["width"] = int(new_value) if new_value is not None else None

    @property
    def fidelity(self):
        """
        :return: From 0.0 to 1.0, how strongly to adhere to prompt.
        :rtype: Optional[float]
        """
        return self.gq.get("fidelity", None)
    @fidelity.setter
    def fidelity(self, new_value):
        """
        Quality of the image to generate. Valid values depend on the targeted model.

        :param Optional[float] new_value: From 0.0 to 1.0, how strongly to adhere to prompt.
        """
        self.gq["fidelity"] = new_value

    @property
    def quality(self):
        """
        :return: Quality of the image to generate. Valid values depend on the targeted model.
        :rtype: Optional[str]
        """
        return self.gq.get("quality", None)
    @quality.setter
    def quality(self, new_value):
        """
        Quality of the image to generate. Valid values depend on the targeted model.

        :param str new_value: Quality of the image to generate.
        """
        self.gq["quality"] = new_value

    @property
    def seed(self):
        """
        :return: Seed of the image to generate, gives deterministic results when set.
        :rtype: Optional[int]
        """
        return self.gq.get("seed", None)
    @seed.setter
    def seed(self, new_value):
        """
        Seed of the image to generate, gives deterministic results when set.

        :param str new_value: Seed of the image to generate.
        """
        self.gq["seed"] = new_value

    @property
    def style(self):
        """
        :return: Style of the image to generate. Valid values depend on the targeted model.
        :rtype: Optional[str]
        """
        return self.gq.get("style", None)
    @style.setter
    def style(self, new_value):
        """
        Style of the image to generate. Valid values depend on the targeted model.

        :param str new_value: Style of the image to generate.
        """
        self.gq["style"] = new_value

    @property
    def images_to_generate(self):
        """
        :return: Number of images to generate per query. Valid values depend on the targeted model.
        :rtype: Optional[int]
        """
        return self.gq.get("nbImagesToGenerate", None)
    @images_to_generate.setter
    def images_to_generate(self, new_value):
        """
        Number of images to generate per query. Valid values depend on the targeted model.

        :param int new_value: Number of images to generate. Valid values depend on the targeted model.
        """
        self.gq["nbImagesToGenerate"] = new_value

    @property
    def aspect_ratio(self):
        """
        :return: The width/height aspect ratio or `None` if either is not set.
        :rtype: Optional[float]
        """
        if self.width is not None and self.width > 0 and self.height is not None and self.height > 0:
            return self.width / self.height
        return None
    @aspect_ratio.setter
    def aspect_ratio(self, ar):
        """
        Aspect ratio of the image to generate. Valid values depend on the targeted model. Set/update the width or height, or both if none are set.

        :param float ar: The width/height aspect ratio.
        """
        if self.height is not None and self.height > 0:
            self.width = self.height * ar
        elif self.width is not None and self.width > 0:
            self.height = self.width / ar
        else:
            self.height = 1024
            self.width = 1024 * ar

    def execute(self):
        """
        Executes the image generation

        :rtype: :class:`DSSLLMImageGenerationResponse`
        """

        if self._guardrails is not None:
            self.gq["guardrails"] = self._guardrails

        if hasattr(_dku_bypass_guardrail_ls, "current_bypass_token"):
            ret = self.llm.client._perform_json("POST", "/projects/%s/llms/images" % (self.llm.project_key), body=self.gq,
                                        headers= {"x-dku-guardrails-bypass-token": _dku_bypass_guardrail_ls.current_bypass_token})
        else:
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
        :param str as_type: The type of image to return, 'bytes' for `bytes` otherwise 'str' for base 64 `str`.
        :return: The first generated image as `bytes` or `str` depending on the `as_type` parameter.
        :rtype: Union[bytes,str]
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

    def get_images(self, as_type="bytes"):
        """
        :param str as_type: The type of images to return, 'bytes' for `bytes` otherwise 'str' for base 64 `str`.
        :return: The generated images as `bytes` or `str` depending on the `as_type` parameter.
        :rtype: Union[List[bytes], List[str]]
        """

        if not self.success:
            raise Exception("Image generation did not succeed: %s" % self._raw["errorMessage"])

        if len(self._raw["images"]) == 0:
            raise Exception("Image generation succeeded but did not return any image")

        if as_type == "bytes":
            import base64
            return [base64.b64decode(image["data"]) for image in self._raw["images"]]
        else:
            return [image["data"] for image in self._raw["images"]]

    @property
    def images(self):
        """
        :return: The generated images in bytes format.
        :rtype: List[bytes]
        """
        return self.get_images(as_type="bytes")
