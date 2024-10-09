"""Wrapper around Dataiku-mediated LLM"""

import json
import logging
import re

from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
)

from langchain.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain.llms.base import BaseLLM
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    InvalidToolCall,
    SystemMessage,
    ToolCall,
    ToolMessage,
)
from langchain_core.outputs import Generation, GenerationChunk, ChatGenerationChunk, LLMResult, ChatResult
from langchain_core.output_parsers.openai_tools import (
    make_invalid_tool_call,
    parse_tool_call,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain.schema import ChatGeneration
from pydantic import Extra

from dataikuapi.dss.tools.langchain import StopSequencesAwareStreamer

logger = logging.getLogger(__name__)


def _llm_settings(llm, stop_sequences, tools=None, tool_choice=None):
    """Returns a settings dict from a DKULLM or DKUChatLLM object"""
    settings = {
        "temperature": llm.temperature,
        "maxOutputTokens": llm.max_tokens,
    }
    if llm.top_p is not None:
        settings["topP"] = llm.top_p
    if llm.top_k is not None:
        settings["topK"] = llm.top_k
    if stop_sequences is not None:
        settings["stopSequences"] = stop_sequences
    if tool_choice is not None:
        settings["toolChoice"] = tool_choice
    if tools is not None:
        settings["tools"] = tools
    return settings


def _completion_with_typed_messages(completion, messages):
    """Add all messages, with their proper type, to a completion object"""
    for message in messages:
        if isinstance(message, ChatMessage):
            completion.with_message(message.content, message.role)
        elif isinstance(message, HumanMessage):
            completion.with_message(message.content, "user")

        elif isinstance(message, AIMessage):
            raw_tool_calls = message.additional_kwargs.get("tool_calls")
            if message.tool_calls or message.invalid_tool_calls:
                # if there is an assistant message, add it first
                if message.content is not None and len(message.content) > 0:
                    completion.with_message(message.content, "assistant")

                all_tool_calls = [
                    _lc_tool_call_to_dku_tool_call(tc)
                    for tc in message.tool_calls
                ] + [
                    _lc_invalid_tool_call_to_dku_tool_call(tc)
                    for tc in message.invalid_tool_calls
                ]

                completion.with_tool_calls(all_tool_calls, "assistant")

            # also considering the extra kwargs to replicate the behavior from
            # the official OpenAI wrapper. See
            # https://github.com/langchain-ai/langchain/blob/9ef15691d62c1f9f18fe7520cce7dafa82ea517e/libs/partners/openai/langchain_openai/chat_models/base.py#L196-L211
            elif raw_tool_calls:
                # if there is an assistant message, add it first
                if message.content is not None and len(message.content) > 0:
                    completion.with_message(message.content, "assistant")

                completion.with_tool_calls(raw_tool_calls, "assistant")

            else:
                # no tools, just add the assistant message, as is
                completion.with_message(message.content, "assistant")

        elif isinstance(message, SystemMessage):
            completion.with_message(message.content, "system")

        elif isinstance(message, ToolMessage):
            completion.with_tool_output(message.content, message.tool_call_id, "tool")

        else:
            raise ValueError(f"Got unknown type {message}")
        # TODO @langchain: named messages
        #if "name" in message.additional_kwargs:
        #    message_dict["name"] = message.additional_kwargs["name"]
    return completion


def _enforce_stop_sequences(text: str, stop: List[str]) -> str:
    """Cut off the text as soon as any stop words occur.
        Note: Same as the langchain version but with proper regex special character escaping.
        See: https://github.com/langchain-ai/langchain/blob/2f8dd1a1619f25daa4737df4d378b1acd6ff83c4/libs/community/langchain_community/llms/utils.py#L6
    """
    if stop is None:
        return text

    escaped_stop = [re.escape(s) for s in stop]
    return re.split("|".join(escaped_stop), text, maxsplit=1)[0]


class DKULLM(BaseLLM):
    """
    Langchain-compatible wrapper around Dataiku-mediated LLMs

    .. note::
        Direct instantiation of this class is possible from within DSS, though it's recommended to instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_llm`.

    Example:

    .. code-block:: python

        llm = dkullm.as_langchain_llm()

        # single prompt
        print(llm.invoke("tell me a joke"))

        # multiple prompts with batching
        for response in llm.batch(["tell me a joke in English", "tell me a joke in French"]):
            print(response)

        # streaming, with stop sequence
        for chunk in llm.stream("Explain photosynthesis in a few words in English then French", stop=["dioxyde de"]):
            print(chunk, end="", flush=True)
    """

    llm_id: str
    """LLM identifier to use"""

    max_tokens: int = 1024
    """Denotes the number of tokens to predict per generation."""

    temperature: float = 0
    """A non-negative float that tunes the degree of randomness in generation."""

    top_k: int = None
    """Number of tokens to pick from when sampling."""

    top_p: float = None
    """Sample from the top tokens whose probabilities add up to p."""

    _llm_handle = None
    """:class:`dataikuapi.dss.llm.DSSLLM` object to wrap."""

    class Config:
        extra = Extra.forbid
        underscore_attrs_are_private = True

    def __init__(self, llm_handle=None, **data: Any):
        if llm_handle is None:
            if data.get("llm_id") is None:
                raise Exception("One of llm_handle or llm_id is required")
            try:
                import dataiku
            except ImportError:
                raise Exception("llm_handle is required")
            llm_handle = dataiku.api_client().get_default_project().get_llm(data["llm_id"])
        else:
            data['llm_id'] = llm_handle.llm_id

        super().__init__(**data)
        self._llm_handle = llm_handle

    @property
    def _llm_type(self):
        """Return type of llm."""
        return "dku"

    def _generate(
            self,
            prompts: List[str],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> LLMResult:
        completions = self._llm_handle.new_completions()
        completions.settings.update(_llm_settings(self, stop))

        for prompt in prompts:
            completion = completions.new_completion()
            completion.with_message(prompt)

        logger.info("Executing completion on DKULLM with settings: %s" % completions.settings)

        resp = completions.execute()

        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_total_tokens = 0
        token_counts_are_estimated = False
        total_estimated_cost = 0.0

        generations = []
        for prompt_resp in resp.responses:
            if not prompt_resp.success:
                raise Exception("LLM call failed: %s" % prompt_resp._raw.get("errorMessage", "Unknown error"))

            total_prompt_tokens += prompt_resp._raw.get("promptTokens", 0)
            total_completion_tokens += prompt_resp._raw.get("completionTokens", 0)
            total_total_tokens += prompt_resp._raw.get("totalTokens", 0)
            token_counts_are_estimated = token_counts_are_estimated or prompt_resp._raw.get("tokenCountsAreEstimated", False)
            total_estimated_cost += prompt_resp._raw.get("estimatedCost", 0)
            # Post enforcing them because stopSequences are not supported by all of our connections/models
            text = _enforce_stop_sequences(prompt_resp.text, stop)
            generations.append([Generation(text=text)])

        llm_output = {
            'promptTokens': total_prompt_tokens,
            'completionTokens': total_completion_tokens,
            'totalTokens': total_total_tokens,
            'tokenCountsAreEstimated': token_counts_are_estimated,
            'estimatedCost': total_estimated_cost
        }

        return LLMResult(generations=generations, llm_output=llm_output)

    def _stream(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        completion = self._llm_handle.new_completion()
        completion.with_message(prompt)
        completion.settings.update(_llm_settings(self, stop))
        logger.info("Executing streamed completion on DKULLM with settings: %s" % completion.settings)

        def produce_chunk(chunk: GenerationChunk):
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            return chunk

        # manually enforce stop sequences for models that don't support the stopSequences setting
        streamer = StopSequencesAwareStreamer(stop, _enforce_stop_sequences)

        for raw_chunk in completion.execute_streamed():
            text = raw_chunk.data.get("text", "")
            new_chunk = GenerationChunk(text=text, generation_info=raw_chunk.data)
            streamer.append(new_chunk)
            if streamer.should_stop():
                break
            if streamer.can_yield():
                yield streamer.yield_(produce_chunk)

        # flush any remaining chunk
        if streamer and streamer.can_yield():
            yield streamer.yield_(produce_chunk)


class DKUChatModel(BaseChatModel):
    """
    Langchain-compatible wrapper around Dataiku-mediated chat LLMs

    .. note::
        Direct instantiation of this class is possible from within DSS, though it's recommended to instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_chat_model`.

    Example:

    .. code-block:: python

        from langchain_core.prompts import ChatPromptTemplate

        llm = dkullm.as_langchain_chat_model()
        prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")
        chain = prompt | llm
        for chunk in chain.stream({"topic": "parrot"}):
            print(chunk.content, end="", flush=True)
    """

    llm_id: str
    """LLM identifier to use"""

    max_tokens: int = 1024
    """Denotes the number of tokens to predict per generation."""

    temperature: float = 0
    """A non-negative float that tunes the degree of randomness in generation."""

    top_k: int = None
    """Number of tokens to pick from when sampling."""

    top_p: float = None
    """Sample from the top tokens whose probabilities add up to p."""

    _llm_handle = None
    """:class:`dataikuapi.dss.llm.DSSLLM` object to wrap."""

    class Config:
        extra = Extra.forbid
        underscore_attrs_are_private = True

    def __init__(self, llm_handle=None, **data: Any):
        if llm_handle is None:
            if data.get("llm_id") is None:
                raise Exception("One of llm_handle or llm_id is required")
            try:
                import dataiku
            except ImportError:
                raise Exception("llm_handle is required")
            llm_handle = dataiku.api_client().get_default_project().get_llm(data["llm_id"])
        else:
            data['llm_id'] = llm_handle.llm_id

        super().__init__(**data)
        self._llm_handle = llm_handle

    @property
    def _llm_type(self):
        """Return type of chat model."""
        return "dku-chat"

    def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> ChatResult:
        tools = kwargs.get("tools", None)
        tool_choice = kwargs.get("tool_choice", None)
        logging.debug("DKUChatModel _generate called, messages=%s tools=%s stop=%s" % (messages, tools, stop))

        completions = self._llm_handle.new_completions()
        completions.settings.update(_llm_settings(self, stop, tools, tool_choice))
        _completion_with_typed_messages(completions.new_completion(), messages)

        resp = completions.execute()

        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_total_tokens = 0
        token_counts_are_estimated = False
        total_estimated_cost = 0.0
        generations = []
        for prompt_resp in resp.responses:
            if not prompt_resp.success:
                raise Exception("LLM call failed: %s" % prompt_resp._raw.get("errorMessage", "Unknown error"))

            total_prompt_tokens += prompt_resp._raw.get("promptTokens", 0)
            total_completion_tokens += prompt_resp._raw.get("completionTokens", 0)
            total_total_tokens += prompt_resp._raw.get("totalTokens", 0)
            token_counts_are_estimated = token_counts_are_estimated or prompt_resp._raw.get("tokenCountsAreEstimated", False)
            total_estimated_cost += prompt_resp._raw.get("estimatedCost", 0)

            # Post enforcing them because stopSequences are not supported by all of our connections/models
            # Default to empty string because AIMessage does not accept a None content
            text = _enforce_stop_sequences(prompt_resp.text, stop) if prompt_resp.text else ""

            additional_kwargs: Dict = {}
            tool_calls = []
            invalid_tool_calls = []
            raw_tool_calls = prompt_resp.tool_calls

            if raw_tool_calls:
                # adding the raw tool calls to the extra kwargs to replicate
                # the behavior from the official OpenAI wrapper.
                # https://github.com/langchain-ai/langchain/blob/9ef15691d62c1f9f18fe7520cce7dafa82ea517e/libs/partners/openai/langchain_openai/chat_models/base.py#L105-L130
                additional_kwargs["tool_calls"] = raw_tool_calls

                for raw_tool_call in raw_tool_calls:
                    try:
                        tool_calls.append(
                            parse_tool_call(raw_tool_call, return_id=True)
                        )
                    except Exception as e:
                        invalid_tool_calls.append(
                            make_invalid_tool_call(raw_tool_call, str(e))
                        )

            generations.append(
                ChatGeneration(message=AIMessage(
                    content=text,
                    additional_kwargs=additional_kwargs,
                    tool_calls=tool_calls,
                    invalid_tool_calls=invalid_tool_calls
                ))
            )

        llm_output = {
            'promptTokens': total_prompt_tokens,
            'completionTokens': total_completion_tokens,
            'totalTokens': total_total_tokens,
            'tokenCountsAreEstimated': token_counts_are_estimated,
            'estimatedCost': total_estimated_cost
        }

        return ChatResult(generations=generations, llm_output=llm_output)

    def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        # Due to internals of how Langchain calls this, "tools" and "tool_choice" must not be declared
        # as params. Else, Langchain ends up putting them both in args and kwargs and leading to failure
        # when using agent_executor.astream_events
        tools = kwargs.get("tools", None)
        tool_choice = kwargs.get("tool_choice", None)
        logging.debug("DKUChatModel _stream called, messages=%s tools=%s stop=%s" % (messages, tools, stop))

        completion = self._llm_handle.new_completion()
        completion = _completion_with_typed_messages(completion, messages)
        completion.settings.update(_llm_settings(self, stop, tools, tool_choice))

        def produce_chunk(chunk: ChatGenerationChunk):
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            return chunk

        # manually enforce stop sequences for models that don't support the stopSequences setting
        streamer = StopSequencesAwareStreamer(stop, _enforce_stop_sequences)

        for raw_chunk in completion.execute_streamed():
            text = raw_chunk.data.get("text", "")

            additional_kwargs: Dict = {}
            tool_call_chunks = []
            raw_tool_calls = raw_chunk.data.get("toolCalls")
            if raw_tool_calls:
                # adding the raw tool calls to the extra kwargs to replicate
                # the behavior from the official OpenAI wrapper. cf
                # https://github.com/langchain-ai/langchain/blob/86ca44d4514b409fed65e2ad8b2ae3c1ee7da48d/libs/partners/openai/langchain_openai/chat_models/base.py#L243
                additional_kwargs["tool_calls"] = raw_tool_calls
                tool_call_chunks = _parse_tool_call_chunks(raw_tool_calls)

            new_chunk = ChatGenerationChunk(
                message=AIMessageChunk(
                    content=text,
                    tool_call_chunks=tool_call_chunks,
                    additional_kwargs=additional_kwargs,
                ),
                generation_info=raw_chunk.data,
            )

            streamer.append(new_chunk)
            if streamer.should_stop():
                break
            if streamer.can_yield():
                yield streamer.yield_(produce_chunk)

        # flush any remaining chunk
        if streamer and streamer.can_yield():
            yield streamer.yield_(produce_chunk)

    def bind_tools(
            self,
            tools: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]],
            tool_choice: Optional[
                Union[dict, str, Literal["auto", "none", "required", "any"], bool]
            ] = None,
            **kwargs: Any,
    ):
        """
        Bind tool-like objects to this chat model.

        Args:
            tools: A list of tool definitions to bind to this chat model.
                Can be  a dictionary, pydantic model, callable, or BaseTool. Pydantic
                models, callables, and BaseTools will be automatically converted to
                their schema dictionary representation.

            tool_choice: Which tool to request the model to call.
                Options are:
                    - name of the tool (str): call the corresponding tool;
                    - "auto": automatically select a tool (or no tool);
                    - "none": do not call a tool;
                    - "any" or "required": force at least one tool call;
                    - True: call the one given tool (requires `tools` to be of length 1);
                    - a dict of the form: {"type": "tool_name", "name": "<<tool_name>>"},
                      or {"type": "required"}, or {"type": "any"} or {"type": "none"},
                      or {"type": "auto"};

            kwargs: Any additional parameters to bind.
        """
        formatted_tools = [convert_to_openai_tool(tool) for tool in tools]
        if tool_choice:
            kwargs["tool_choice"] = _convert_to_llm_mesh_tool_choice(tool_choice, formatted_tools)

        return super().bind(tools=formatted_tools, **kwargs)


def _lc_tool_call_to_dku_tool_call(
        tool_call: ToolCall
) -> dict:
    return {
        "type": "function",
        "id": tool_call["id"],
        "function": {
            "name": tool_call["name"],
            "arguments": json.dumps(tool_call["args"]),
        },
    }


def _lc_invalid_tool_call_to_dku_tool_call(
        invalid_tool_call: InvalidToolCall,
) -> dict:
    return {
        "type": "function",
        "id": invalid_tool_call["id"],
        "function": {
            "name": invalid_tool_call["name"],
            "arguments": invalid_tool_call["args"],
        },
    }


def _parse_tool_call_chunks(raw_tool_calls):
    try:
        return [
            {
                "id": rtc.get("id"),
                "index": rtc.get("index"),
                "name": rtc["function"].get("name"),
                "args": rtc["function"].get("arguments"),
            }
            for rtc in raw_tool_calls
        ]
    except KeyError as e:
        logger.error("Error when constructing the tool call chunk: ", str(e))
        return []


def _convert_to_llm_mesh_tool_choice(
        tool_choice: Union[dict, str, Literal["auto", "none", "required", "any"], bool],
        formatted_tools: Sequence[Dict[str, Any]]
) -> Dict[str, Any]:
    """Map the tool choice to its LLM mesh compatible representation"""
    tool_names = [
        formatted_tool["function"]["name"]
        for formatted_tool in formatted_tools
    ]

    if isinstance(tool_choice, str):
        # supporting "any" because it seems common in the LangChain vocabulary
        if tool_choice == "any":
            tool_choice = "required"

        if tool_choice in ("auto", "none", "required"):
            return {"type": tool_choice}

        # tool_choice refers to a dedicated tool name
        if tool_choice not in tool_names:
            raise ValueError(
                f"Tool choice {tool_choice} was specified, but the only "
                f"provided tools were {tool_names}."
            )

        return {"type": "tool_name", "name": tool_choice}

    if isinstance(tool_choice, bool) and tool_choice:
        if len(tool_names) != 1:
            raise ValueError(
                "tool_choice=True can only be used when a single tool is "
                f"passed in, received {len(tool_names)} tools."
            )

        return {
            "type": "tool_name",
            "name": tool_names[0]
        }

    if isinstance(tool_choice, dict):
        expected_tool_choice_types = ["auto", "none", "any", "required", "tool_name"]

        if "type" not in tool_choice:
            raise ValueError(
                f'Tool choice {tool_choice} must contain a "type" property. '
                f"Allowed values are {expected_tool_choice_types}."
            )

        if tool_choice["type"] not in expected_tool_choice_types:
            raise ValueError(
                f'Invalid tool choice type: {tool_choice["type"]}. '
                f"Allowed values are {expected_tool_choice_types}."
            )

        # supporting "any" because it seems common in the LangChain vocabulary
        # note: we already support it for the 'string' case
        if tool_choice["type"] == "any":
            tool_choice["type"] = "required"

        if tool_choice["type"] == "tool_name":
            if "name" not in tool_choice:
                raise ValueError(
                    f'Tool choice {tool_choice} must contain a "name" property.'
                )

            if tool_choice["name"] not in tool_names:
                raise ValueError(
                    f"Tool choice {tool_choice} was specified, but the only "
                    f"provided tools were {tool_names}."
                )

        return tool_choice

    # default, unknown case
    raise ValueError(
        f"Unrecognized tool_choice type. Expected str, bool or dict. "
        f"Received: {tool_choice}"
    )
