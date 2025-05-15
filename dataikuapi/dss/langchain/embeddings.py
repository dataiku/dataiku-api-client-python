"""Wrapper around Dataiku-mediated embedding LLMs"""
import asyncio
import concurrent
import logging
import threading 

from typing import Callable, List, Any, Union

import pydantic
try:
    from langchain_core.embeddings.embeddings import Embeddings
except ModuleNotFoundError:
    from langchain.embeddings.base import Embeddings
from langchain_core.callbacks import BaseCallbackHandler, LLMManagerMixin
from dataikuapi.dss.llm_tracing import new_trace, SpanBuilder

from dataikuapi.dss.langchain.utils import must_use_deprecated_pydantic_config

logger = logging.getLogger(__name__)
CHUNK_SIZE = 1000


if must_use_deprecated_pydantic_config():
    class LockedDownBaseModel(pydantic.BaseModel):
        class Config:
            extra = pydantic.Extra.forbid
            underscore_attrs_are_private = True
else:
    class LockedDownBaseModel(pydantic.BaseModel):
        model_config = {
            'extra': 'forbid',
        }


class DKUEmbeddings(LockedDownBaseModel, Embeddings):
    """
    Langchain-compatible wrapper around Dataiku-mediated embedding LLMs

    .. note::
        Direct instantiation of this class is possible from within DSS, though it's recommended to instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_embeddings`.
    """

    llm_id: str
    """LLM identifier to use"""

    _llm_handle = None
    """:class:`dataikuapi.dss.llm.DSSLLM` object to wrap."""

    # The embeddings class of LangChain can only return raw embedding, without any additional information
    # (unlike ChatModel, which supports additional information), so we cannot use this to return the last
    # trace to the caller.
    # So, instead, we keep a thread local with the last trace, and the caller can get it from here
    # (at the moment, it's mostly done by rag_query_server.py)
    _last_trace = None

    # `_last_trace` is unique to the thread using the DKUEmbeddings instance but when the instance is passed
    # to another thread we don't have access to the last trace in the calling thread. To work around this we
    # allow a list of callbacks to be passed. These callbacks will be called back once the model has been called.
    # See how TraceableDKUEmbeddings is used
    _callbacks: List[Callable[[Union[dict, SpanBuilder]], None]] = []

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
        self._last_trace = threading.local()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call out to Dataiku-mediated LLM

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """

        with new_trace("DKUEmbeddings") as trace:
            self._last_trace.trace = trace

            logger.info("Performing embedding of {num_texts} texts".format(num_texts=len(texts)))

            embeddings = []
            for i in range(0, len(texts), CHUNK_SIZE):
                query = self._llm_handle.new_embeddings(text_overflow_mode="FAIL")

                for text in texts[i:i+CHUNK_SIZE]:
                    query.add_text(text)

                resp = query.execute()

                # TODO
                #if not resp.success:
                #    raise Exception("LLM call failed: %s" % resp._raw.get("errorMessage", "Unknown error"))

                if "responses" in resp._raw and len(resp._raw["responses"]) == 1:
                    if "trace" in resp._raw["responses"][0]:
                        trace_response = resp._raw["responses"][0]["trace"]
                        trace.append_trace(trace_response)
                        for callback in self._callbacks:
                            callback(trace_response)

                embeddings.extend(resp.get_embeddings())

                logger.info("Finished a chunk. Embedded {num_embedded} of {num_texts} texts".format(
                    num_embedded=min(i + CHUNK_SIZE, len(texts)), num_texts=len(texts)))

            logger.info("Done performing embedding of {num_texts} texts".format(num_texts=len(texts)))

            return embeddings

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, self.embed_documents, texts)
        return result

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    async def aembed_query(self, text: str) -> List[float]:
        embeddings = await self.aembed_documents([text])
        return embeddings[0]
