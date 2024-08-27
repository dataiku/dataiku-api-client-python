"""Wrapper around Dataiku-mediated embedding LLMs"""
import asyncio
import concurrent
import logging
from typing import List, Any

from pydantic import BaseModel, Extra

from langchain.embeddings.base import Embeddings


logger = logging.getLogger(__name__)
CHUNK_SIZE = 1000


class DKUEmbeddings(BaseModel, Embeddings):
    """
    Langchain-compatible wrapper around Dataiku-mediated embedding LLMs

    .. note::
        Direct instantiation of this class is possible from within DSS, though it's recommended to instead use :meth:`dataikuapi.dss.llm.DSSLLM.as_langchain_embeddings`.
    """

    llm_id: str
    """LLM identifier to use"""

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

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call out to Dataiku-mediated LLM

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """
        logging.info("Performing embedding of {num_texts} texts".format(num_texts=len(texts)))

        embeddings = []
        for i in range(0, len(texts), CHUNK_SIZE):
            query = self._llm_handle.new_embeddings(text_overflow_mode="FAIL")

            for text in texts[i:i+CHUNK_SIZE]:
                query.add_text(text)

            resp = query.execute()

            # TODO
            #if not resp.success:
            #    raise Exception("LLM call failed: %s" % resp._raw.get("errorMessage", "Unknown error"))

            embeddings.extend(resp.get_embeddings())

            logging.info("Finished a chunk. Embedded {num_embedded} of {num_texts} texts".format(
                num_embedded=min(i + CHUNK_SIZE, len(texts)), num_texts=len(texts)))

        logging.info("Done performing embedding of {num_texts} texts".format(num_texts=len(texts)))

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
