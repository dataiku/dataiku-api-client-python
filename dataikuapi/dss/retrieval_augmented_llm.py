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