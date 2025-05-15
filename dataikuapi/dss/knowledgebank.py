from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings

class DSSKnowledgeBankListItem(DSSTaggableObjectListItem):
    """
    An item in a list of knowledege banks

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
        return dataiku.KnowledgeBank("%s.%s" % (self.project_key, self.id))

    @property
    def project_key(self):
        """
        :returns: The project        
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
        return dataiku.KnowledgeBank("%s.%s" % (self.project_key, self.id))

    def get_settings(self):
        """
        Get the knowledge bank's definition

        :return: a handle on the knowledge bank definition
        :rtype: :class:`dataikuapi.dss.knowledgebank.DSSKnowledgeBankSettings`
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/knowledge-banks/%s" % (self.project_key, self.id))
        return DSSKnowledgeBankSettings(self.client, settings)

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

class DSSKnowledgeBankSettings(DSSTaggableObjectSettings):
    """
    Settings for a knowledge bank

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.knowledgebank.DSSKnowledgeBank.get_settings` instead

    """
    def __init__(self, client, settings):
        super(DSSKnowledgeBankSettings, self).__init__(settings)
        self._client = client
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
