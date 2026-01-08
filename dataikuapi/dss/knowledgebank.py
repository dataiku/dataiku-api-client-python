import json
import logging

from .document_extractor import ManagedFolderImageRef, ManagedFolderDocumentRef
from .managedfolder import DSSManagedFolder
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings, AnyLoc

logger = logging.getLogger(__name__)


class DSSKnowledgeBankListItem(DSSTaggableObjectListItem):
    """
    An item in a list of knowledge banks

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_knowledge_banks`.
    """
    def __init__(self, client, data):
        super(DSSKnowledgeBankListItem, self).__init__(data)
        self.client = client

    def to_knowledge_bank(self):
        """
        Convert the current item.

        :returns: A handle for the knowledge_bank.
        :rtype: :class:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank`
        """
        return DSSKnowledgeBank(self.client, self._data["projectKey"], self._data["id"])

    def as_core_knowledge_bank(self):
        """
        Get the :class:`dataiku.KnowledgeBank` object corresponding to this knowledge bank

        :rtype: :class:`dataiku.KnowledgeBank`
        """
        import dataiku
        return dataiku.KnowledgeBank("%s.%s" % (self.project_key, self.id), context_project_key=self.project_key)

    @property
    def project_key(self):
        """
        :returns: The project key
        :rtype: string
        """
        return self._data["projectKey"]

    @property
    def id(self):
        """
        :returns: The id of the knowledge bank.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the knowledge bank.
        :rtype: string
        """
        return self._data["name"]

class DSSKnowledgeBank(object):
    """
    A handle to interact with a DSS-managed knowledge bank.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.project.DSSProject.get_knowledge_bank` instead.
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.project_key = project_key
        self._id = id

    @property
    def id(self):
        return self._id

    def as_core_knowledge_bank(self):
        """
        Get the :class:`dataiku.KnowledgeBank` object corresponding to this knowledge bank

        :rtype: :class:`dataiku.KnowledgeBank`
        """
        import dataiku
        return dataiku.KnowledgeBank("%s.%s" % (self.project_key, self.id), context_project_key=self.project_key)

    def as_langchain_retriever(self, **data):
        """
        Get the current version of this knowledge bank as a Langchain Retriever object.

        :param dict data: keyword arguments to pass to the :meth:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank.search` function
        :returns: a langchain-compatible retriever
        :rtype: :class:`dataikuapi.dss.langchain.knowledge_bank.DKUKnowledgeBankRetriever`
        """
        from dataikuapi.dss.langchain.knowledge_bank import DKUKnowledgeBankRetriever
        return DKUKnowledgeBankRetriever(kb_handle=self, **data)

    def get_settings(self):
        """
        Get the knowledge bank's definition

        :return: a handle on the knowledge bank definition
        :rtype: :class:`dataikuapi.dss.knowledgebank.DSSKnowledgeBankSettings`
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/knowledge-banks/%s" % (self.project_key, self.id))
        return DSSKnowledgeBankSettings(self.client, self.project_key, settings)

    def delete(self):
        """
        Delete the knowledge bank
        """
        return self.client._perform_empty("DELETE", "/projects/%s/knowledge-banks/%s" % (self.project_key, self.id))

    def build(self, job_type="NON_RECURSIVE_FORCED_BUILD", wait=True):
        """
        Start a new job to build this knowledge bank and wait for it to complete.
        Raises if the job failed.

        .. code-block:: python

            job = knowledge_bank.build()
            print("Job %s done" % job.id)

        :param job_type: the job type. One of RECURSIVE_BUILD, NON_RECURSIVE_FORCED_BUILD or RECURSIVE_FORCED_BUILD
        :param bool wait: whether to wait for the job completion before returning the job handle, defaults to True
        :returns: the :class:`dataikuapi.dss.job.DSSJob` job handle corresponding to the built job
        :rtype: :class:`dataikuapi.dss.job.DSSJob`
        """
        project = self.client.get_project(self.project_key)
        jd = project.new_job(job_type)
        jd.with_output(self._id, object_type="RETRIEVABLE_KNOWLEDGE")
        if wait:
            return jd.start_and_wait()
        else:
            return jd.start()

    # Keep args in sync with dataikuapi.dss.langchain.knowledge_bank.DKUKnowledgeBankRetriever
    def search(self, query,
               max_documents=10, search_type="SIMILARITY",
               similarity_threshold=0.5,
               mmr_documents_count=20, mmr_factor=0.25,
               hybrid_use_advanced_reranking=False, hybrid_rrf_rank_constant=60, hybrid_rrf_rank_window_size=4):
        """
        Search for documents in a knowledge bank

        MMR and HYBRID search types are not supported by every vector stores.

        :param str query: what to search for
        :param int max_documents: the maximum number of documents to return, default to 10
        :param str search_type: the search algorithm to use. One of SIMILARITY, SIMILARITY_THRESHOLD, MMR or HYBRID. Defaults to SIMILARITY
        :param float similarity_threshold: only return documents with a similarity score above this threshold, typically between 0 and 1, only applied with search_type=SIMILARITY_THRESHOLD, defaults to 0.5
        :param int mmr_documents_count: number of documents to consider before selecting the documents to retrieve, only applied with search_type=MMR, defaults to 20
        :param float mmr_factor: weight of diversity vs relevancy, between 0 and 1, where 0 favors maximum diversity and 1 favors maximum relevancy, only applied with search_type=MMR, defaults to 0.25
        :param bool hybrid_use_advanced_reranking: whether to use proprietary rerankers, valid for Azure AI and ElasticSearch vector stores, defaults to False
        :param int hybrid_rrf_rank_constant: higher values give more weight to lower-ranked documents, valid for ElasticSearch vector stores, defaults to 60
        :param int hybrid_rrf_rank_window_size: number of documents to consider from each search type, valid for ElasticSearch vector stores, defaults to 4
        :returns: a result object with a list of documents that matched the query
        :rtype: :class:`dataikuapi.dss.knowledgebank.DSSKnowledgeBankSearchResult`
        """
        assert query, "the query is required"
        assert type(max_documents) is int and max_documents > 0, "max_documents should be a positive integer"
        valid_search_types = ["SIMILARITY", "SIMILARITY_THRESHOLD", "MMR", "HYBRID"]
        assert search_type in valid_search_types, "invalid search_type, it should be one of " + ",".join(valid_search_types)
        if search_type == "SIMILARITY_THRESHOLD":
            assert type(similarity_threshold) is float, "similarity_threshold should be a float, typically between 0 and 1"
        if search_type == "MMR":
            assert type(mmr_documents_count) is int and mmr_documents_count > 0, "mmr_documents_count should be a positive integer"
            assert type(mmr_factor) is float and 0 <= mmr_factor <= 1, "mmr_factor should be a float between 0 and 1"
        if search_type == "HYBRID" and hybrid_use_advanced_reranking:
            assert type(hybrid_rrf_rank_constant) is int and hybrid_rrf_rank_constant > 0, "hybrid_rrf_rank_constant should be a positive integer"
            assert type(hybrid_rrf_rank_window_size) is int and hybrid_rrf_rank_window_size > 0, "hybrid_rrf_rank_window_size should be a positive integer"

        response = self.client._perform_json("POST", "/projects/%s/knowledge-banks/%s/search" % (self.project_key, self.id), params={
            "query": query,
            "params": json.dumps({
                "maxDocuments": max_documents,
                "searchType": search_type,
                "similarityThreshold": similarity_threshold,
                "mmrK": mmr_documents_count,
                "mmrDiversity": mmr_factor,
                "useAdvancedReranking": hybrid_use_advanced_reranking,
                "rrfRankConstant": hybrid_rrf_rank_constant,
                "rrfRankWindowSize": hybrid_rrf_rank_window_size,
                "includeScore": True,
                "filter": {},
                "includeMultimodalContent": True
            })
        })
        if response.get("error"):
            raise Exception("search failed: " + response["error"].get("message", json.dumps(response)))
        return DSSKnowledgeBankSearchResult(self, response["documents"])


class DSSKnowledgeBankSettings(DSSTaggableObjectSettings):
    """
    Settings for a knowledge bank

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank.get_settings` instead

    """
    def __init__(self, client, project_key, settings):
        super(DSSKnowledgeBankSettings, self).__init__(settings)
        self._client = client
        self._project_key = project_key
        self._settings = settings

    @property
    def project_key(self):
        """
        Returns the project key of the knowledge bank

        :rtype: str
        """
        return self._settings['projectKey']

    @property
    def id(self):
        """
        Returns the identifier of the knowledge bank

        :rtype: str
        """
        return self._settings['id']

    @property
    def vector_store_type(self):
        """
        Returns the type of storage backing the vector store (could be CHROMA, PINECONE, ELASTICSEARCH, AZURE_AI_SEARCH, VERTEX_AI_GCS_BASED, FAISS, QDRANT_LOCAL)

        :rtype: str
        """
        return self._settings['vectorStoreType']

    def set_metadata_schema(self, schema):
        """
        Sets the schema for metadata fields.

        :param schema: the schema, as a mapping metadata_field -> type
        :type schema: Dict[str, str]
        """
        self._settings["metadataColumnsSchema"] = list(
            {"name": k, "type": v}
            for k, v in schema.items()
        )

    def set_images_folder(self, managed_folder_id, project_key=None):
        """
        Sets the images folder to use with this knowledge bank.

        :param managed_folder_id: The (managed) images folder id.
        :type managed_folder_id: str
        :param project_key: The image folder project key, if different from
            this knowledge bank project key. Default to None.
        :type project_key: Optional[str]
        """
        if "." not in managed_folder_id:
            if project_key is None:
                project_key = self._project_key

            managed_folder_id = "{}.{}".format(
                project_key, managed_folder_id
            )

        self._settings["managedFolderId"] = managed_folder_id
        self._settings["multimodalColumn"] = "DKU_MULTIMODAL_CONTENT"

    def get_images_folder(self):
        """
        Returns the images folder of the knowledge bank, if any.

        :return: the managed folder or None
        :rtype: DSSManagedFolder | None
        """
        full_managed_folder_id = self._settings.get("managedFolderId")
        if not full_managed_folder_id:
            return None
        if "." in full_managed_folder_id:
            project_key, managed_folder_id = full_managed_folder_id.split(".")
        else:
            project_key, managed_folder_id = self._project_key, full_managed_folder_id
        project = self._client.get_project(project_key)
        managed_folder = project.get_managed_folder(managed_folder_id)
        return managed_folder

    def get_raw(self):
        """
        Returns the raw settings of the knowledge bank

        :return: the raw settings of the knowledge bank
        :rtype: dict
        """
        return self._settings

    def save(self):
        """
        Saves the settings on the knowledge bank
        """
        self._client._perform_json(
            "PUT", "/projects/%s/knowledge-banks/%s" % (self.project_key, self.id),
            body=self._settings)


class DSSKnowledgeBankSearchResult(object):
    """
    The result of a search in a knowledge bank, contains documents that matched the query

    Each document is a :class:`dataikuapi.dss.knowledgebank.DSSKnowledgeBankSearchResultDocument`
    """
    def __init__(self, kb, documents):
        self._documents = [DSSKnowledgeBankSearchResultDocument(self, d["text"], d.get("score"), d.get("metadata", {})) for d in documents]
        self._kb = kb
        self._managed_folder_id = None

    @property
    def documents(self):
        """
        Returns a list of documents that matched a search query

        :return: a list of result documents
        :rtype: list[DSSKnowledgeBankSearchResultDocument]
        """
        return self._documents

    @property
    def managed_folder_id(self):
        if self._managed_folder_id is None:
            self._managed_folder_id = self._kb.get_settings().get_images_folder().id
        return self._managed_folder_id


class DSSKnowledgeBankSearchResultDocument(object):
    """
    A document found by searching a knowledge bank with :meth:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank.search`
    """
    def __init__(self, result, text, score, metadata):
        self._result = result
        self._text = text
        self._score = score
        self._metadata = metadata

    @property
    def text(self):
        """
        Returns the text from the knowledge bank for this document

        :return: the text for this document
        :rtype: str
        """
        return self._text

    @property
    def score(self):
        """
        Returns the match score for this document

        :return: the score for this document
        :rtype: float
        """
        return self._score

    @property
    def metadata(self):
        """
        Returns metadata from the knowledge bank for this document

        :return: metadata for this document
        :rtype: dict
        """
        return {
            key: value for key, value in self._metadata.items()
            if key not in {'DKU_MULTIMODAL_CONTENT', 'DKU_DOCUMENT_INFO'}
        }

    @property
    def images(self):
        """
        Returns images for this document

        :return: a list of images references or None
        :rtype: list[ManagedFolderImageRef] | None
        """
        multimodal_raw = self._metadata.get("DKU_MULTIMODAL_CONTENT")
        if not multimodal_raw:
            return None
        try:
            multimodal = json.loads(multimodal_raw)
        except ValueError as e:
            logger.error("Failed to decode JSON payload for multimodal content: {}, {}".format(e, multimodal_raw))
            return None
        if multimodal.get("type") != "images":
            return None
        if multimodal.get("content") is None:
            return None
        return [
            ManagedFolderImageRef(self._result.managed_folder_id, path) for path in multimodal["content"]
        ]
    
    @property
    def file_ref(self):
        """
        Returns the file reference for this document

        :return: a file reference or None
        :rtype: ManagedFolderDocumentRef | None
        """
        document_info_raw = self._metadata.get("DKU_DOCUMENT_INFO")
        if not document_info_raw:
            return None
        try:
            document_info = json.loads(document_info_raw)
        except ValueError as e:
            logger.error("Failed to decode JSON payload for document info: {}, {}".format(e, document_info_raw))
            return None
        
        source_file_info = document_info.get("source_file")
        if source_file_info is None:
            return None
        
        folder_full_id = source_file_info.get("folder_full_id")
        path = source_file_info.get("path")
        if folder_full_id is None or path is None:
            return None
        
        try:
            folder_loc = AnyLoc.from_full(folder_full_id)
        except ValueError as e:
            logger.error("Invalid folder_full_id in DKU_DOCUMENT_INFO: {}, {}".format(e, document_info))
            return None

        return ManagedFolderDocumentRef(path, folder_loc.object_id)
