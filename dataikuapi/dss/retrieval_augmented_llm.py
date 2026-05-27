from .agent import DSSLLMInteractionLoggingSelection
from .utils import DSSTaggableObjectListItem, DSSTaggableObjectSettings

class DSSRetrievalAugmentedLLMListItem(DSSTaggableObjectListItem):
    """
    An item in a list of retrieval-augmented LLMs

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_retrieval_augmented_llms`.
    """
    def __init__(self, client, data):
        super(DSSRetrievalAugmentedLLMListItem, self).__init__(data)
        self.client = client


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
        :returns: The id of the retrieval-augmented LLM.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the retrieval-augmented LLM.
        :rtype: string
        """
        return self._data["name"]

    def as_llm(self):
        """Returns this retrieval-augmented LLM as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying"""
        return self.client.get_project(self.project_key).get_llm("retrieval-augmented-llm:%s" % self.id)


class DSSRetrievalAugmentedLLM(object):
    """
    A handle to interact with a DSS-managed retrieval-augmented LLM.

    .. important::

        Do not create this class directly, use :meth:`dataikuapi.dss.project.DSSProject.get_retrieval_augmented_llm` instead.
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.project_key = project_key
        self._id = id

    @property
    def id(self):
        return self._id

    def as_llm(self):
        """Returns this retrieval-augmented LLM as a usable :class:`dataikuapi.dss.llm.DSSLLM` for querying"""
        return self.client.get_project(self.project_key).get_llm("retrieval-augmented-llm:%s" % self.id)

    def get_settings(self):
        """
        Get the retrieval-augmented LLM's definition

        :return: a handle on the retrieval-augmented LLM definition
        :rtype: :class:`dataikuapi.dss.retrieval_augmented_llm.DSSRetrievalAugmentedLLMSettings`
        """
        settings = self.client._perform_json(
            "GET", "/projects/%s/retrieval-augmented-llms/%s" % (self.project_key, self.id))
        return DSSRetrievalAugmentedLLMSettings(self.client, settings)

    def delete(self):
        """
        Delete the retrieval-augmented LLM
        """
        return self.client._perform_empty("DELETE", "/projects/%s/retrieval-augmented-llms/%s" % (self.project_key, self.id))

class DSSRetrievalAugmentedLLMSettings(DSSTaggableObjectSettings):
    """
    Settings for a retrieval-augmented LLM

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.retrieval_augmented_llm.DSSRetrievalAugmentedLLM.get_settings` instead

    """
    def __init__(self, client, settings):
        super(DSSRetrievalAugmentedLLMSettings, self).__init__(settings)
        self._client = client
        self._settings = settings

    def get_version_ids(self):
        return [v["versionId"] for v in self._settings["versions"]]

    @property
    def active_version(self):
        """Returns the active version of this retrieval-augmented LLM. May return None if no version is declared as active"""
        return self._settings.get("activeVersion")

    def get_version_settings(self, version_id):

        version_settings = None
        for vs in self._settings["versions"]:
            if vs["versionId"] == version_id:
                version_settings = vs
                break
        if version_settings is None:
            raise Exception("version %s not found" % version_id)
        if not "ragllmSettings" in version_settings:
            raise Exception("Not a retrieval-augmented-llm?")
        return DSSRetrievalAugmentedLLMVersionSettings(version_settings)

    def get_raw(self):
        """
        Returns the raw settings of the retrieval-augmented LLM

        :return: the raw settings of the retrieval-augmented LLM
        :rtype: dict
        """
        return self._settings

    def save(self):
        """
        Saves the settings on the retrieval-augmented LLM
        """
        self._client._perform_empty(
            "PUT", "/projects/%s/retrieval-augmented-llms/%s" % (self._settings["projectKey"], self._settings["id"]), body=self._settings)

class DSSRetrievalAugmentedLLMVersionSettings(object):
    def __init__(self, version_settings):
        self._version_settings = version_settings

    def get_raw(self):
        return self._version_settings

    def _get_or_create_interaction_logging_selection(self):
        rag_settings = self._version_settings["ragllmSettings"]
        interaction_logging_selection = rag_settings.get("interactionLoggingSelection")
        if interaction_logging_selection is None:
            interaction_logging_selection = {
                "mode": DSSLLMInteractionLoggingSelection.MODE_INHERIT,
                "explicitSettings": {},
            }
            rag_settings["interactionLoggingSelection"] = interaction_logging_selection
        return interaction_logging_selection

    @property
    def llm_id(self):
        """
        Get or set the name of the Data Collection

        :rtype: :class:`str`
        """
        return self._version_settings["ragllmSettings"]["llmId"]

    @llm_id.setter
    def llm_id(self, value):
        self._version_settings["ragllmSettings"]["llmId"] = value

    @property
    def interaction_logging_selection(self):
        """
        Get the interaction logging selection for this version.

        Before configuring interaction logging on a retrieval-augmented LLM version,
        create the target dataset on the project:

        .. code-block:: python

            project = client.get_project("MYPROJECT")
            project.create_llm_interaction_logging_dataset(
                "llm_logs",
                connection_id="filesystem_managed",
                time_partitioning="DAY",
            )

        Example using inherited settings:

        .. code-block:: python

            rag = project.get_retrieval_augmented_llm("my_rag")
            rag_settings = rag.get_settings()
            version_settings = rag_settings.get_version_settings("v1")

            logging_selection = version_settings.interaction_logging_selection
            logging_selection.inherit()

            rag_settings.save()

        Example using explicit settings:

        .. code-block:: python

            rag = project.get_retrieval_augmented_llm("my_rag")
            rag_settings = rag.get_settings()
            version_settings = rag_settings.get_version_settings("v1")

            logging_selection = version_settings.interaction_logging_selection
            logging_selection.enable(
                "llm_logs",
                settings={
                    "flushEveryS": 60,
                    "flushEveryBytes": 1_000_000,
                    "contentMode": "FULL",
                },
            )

            rag_settings.save()

        Example disabling interaction logging:

        .. code-block:: python

            rag = project.get_retrieval_augmented_llm("my_rag")
            rag_settings = rag.get_settings()
            version_settings = rag_settings.get_version_settings("v1")

            logging_selection = version_settings.interaction_logging_selection
            logging_selection.disable()

            rag_settings.save()

        :rtype: :class:`dataikuapi.dss.agent.DSSLLMInteractionLoggingSelection`
        """
        return DSSLLMInteractionLoggingSelection(self._get_or_create_interaction_logging_selection())

    @interaction_logging_selection.setter
    def interaction_logging_selection(self, value):
        if isinstance(value, DSSLLMInteractionLoggingSelection):
            value = value.get_raw()
        self._version_settings["ragllmSettings"]["interactionLoggingSelection"] = value
