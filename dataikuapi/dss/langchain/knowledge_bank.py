from typing import Any, ClassVar, List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class DKUKnowledgeBankRetriever(BaseRetriever):
    """
    Langchain-compatible retriever for a knowledge bank

    .. important::
        Do not instantiate directly, use :meth:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank.as_langchain_retriever()` instead
    """

    # keep synced with DSSKnowledgeBank.search()
    SEARCH_PARAMETERS_NAMES: ClassVar = [
        'max_documents',
        'search_type',
        'similarity_threshold',
        'mmr_documents_count',
        'mmr_factor',
        'hybrid_use_advanced_reranking',
        'hybrid_rrf_rank_constant',
        'hybrid_rrf_rank_window_size',
    ]
    """ Valid parameter names for the search method
    """

    def __init__(self, kb_handle, **data: Any):
        super().__init__(**data)
        self._kb_handle = kb_handle
        self._search_kwargs = {k: v for k, v in data.items() if k in self.SEARCH_PARAMETERS_NAMES}

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        result = self._kb_handle.search(query, **self._search_kwargs)
        return [
            Document(
                page_content=document.text,
                metadata=document.metadata
            )
            for document in result.documents
        ]
