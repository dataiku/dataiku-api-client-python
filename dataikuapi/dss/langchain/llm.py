"""Wrapper around Dataiku-mediated LLM"""

import logging
import re
from typing import Any, List, Optional, Iterator, AsyncIterator

from langchain.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain.llms.base import BaseLLM
from langchain_core.outputs import Generation, GenerationChunk, ChatGenerationChunk, LLMResult, ChatResult
from langchain_core.language_models import BaseChatModel
from langchain.schema import ChatGeneration
from langchain.schema.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import Extra

from .utils import StopSequencesAwareStreamer

logger = logging.getLogger(__name__)


def _llm_settings(llm, stop_sequences):
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
    return settings


def _completion_with_typed_messages(completion, messages):
    """Add all messages, with their proper type, to a completion object"""
    for message in messages:
        if isinstance(message, ChatMessage):
            completion.with_message(message.content, message.role)
        elif isinstance(message, HumanMessage):
            completion.with_message(message.content, "user")
        elif isinstance(message, AIMessage):
            completion.with_message(message.content, "assistant")
            # TODO @langchain: function calls
            # if "function_call" in message.additional_kwargs:
            # message_dict["function_call"] = message.additional_kwargs["function_call"]
        elif isinstance(message, SystemMessage):
            completion.with_message(message.content, "system")
        elif isinstance(message, FunctionMessage):
            raise Exception("function calls are not supported yet")
            # TODO @langchain: function calls
            #message_dict = {
            #    "role": "function",
            #    "content": message.content,
            #    "name": message.name,
            #}
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

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_llm`.

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

    class Config:
        extra = Extra.forbid
        underscore_attrs_are_private = True

    def __init__(self, llm_handle, **data: Any):
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

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_chat_model`.

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
    """:class:`dataikuapi.dss.llm.DKULLM` object to wrap."""

    class Config:
        extra = Extra.forbid
        underscore_attrs_are_private = True

    def __init__(self, llm_handle, **data: Any):
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
        completions = self._llm_handle.new_completions()
        completions.settings.update(_llm_settings(self, stop))
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
            text = _enforce_stop_sequences(prompt_resp.text, stop)
            generations.append(ChatGeneration(message=AIMessage(content=text)))

        # TODO: Support for function calls or tool invocations

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
        completion = self._llm_handle.new_completion()
        completion = _completion_with_typed_messages(completion, messages)
        completion.settings.update(_llm_settings(self, stop))

        def produce_chunk(chunk: ChatGenerationChunk):
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            return chunk

        # manually enforce stop sequences for models that don't support the stopSequences setting
        streamer = StopSequencesAwareStreamer(stop, _enforce_stop_sequences)

        for raw_chunk in completion.execute_streamed():
            text = raw_chunk.data.get("text", "")
            new_chunk = ChatGenerationChunk(message=AIMessageChunk(content=text), generation_info=raw_chunk.data)
            streamer.append(new_chunk)
            if streamer.should_stop():
                break
            if streamer.can_yield():
                yield streamer.yield_(produce_chunk)

        # flush any remaining chunk
        if streamer and streamer.can_yield():
            yield streamer.yield_(produce_chunk)
