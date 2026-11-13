class DSSLLMUsage(dict):
    """
    An item in a list of LLM usages.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_llm_usages` instead.
    """

    @property
    def llm_id(self):
        """
        The ID of the LLM.

        :rtype: string
        """
        return self["llmId"]

    @property
    def project_key(self):
        """
        The key of the project containing the usage.

        :rtype: string
        """
        return self["projectKey"]

    @property
    def object_type(self):
        """
        The type of the object referencing the LLM.

        :rtype: string
        """
        return self["objectType"]

    @property
    def object_id(self):
        """
        The ID of the object referencing the LLM.

        :rtype: string
        """
        return self["objectId"]

    @property
    def object_name(self):
        """
        The name of the object referencing the LLM.

        :rtype: string
        """
        return self["objectName"]

    @property
    def saved_model_type(self):
        """
        The saved model type, or None when not applicable.

        :rtype: string | None
        """
        return self.get("savedModelType")

    @property
    def editable(self):
        """
        Whether this usage can be replaced. Historical and trained references cannot be replaced.

        :rtype: bool
        """
        return self["editable"]

    @property
    def non_editable_reason(self):
        """
        The reason the usage cannot be replaced, or None when editable.

        :rtype: string | None
        """
        return self.get("nonEditableReason")


class DSSLLMReplacedObject(dict):
    """
    An object updated by an LLM replacement.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.replace_llms` instead.
    """

    @property
    def object_type(self):
        """
        The type of the updated object.

        :rtype: string
        """
        return self["objectType"]

    @property
    def object_id(self):
        """
        The ID of the updated object.

        :rtype: string
        """
        return self["objectId"]


class DSSLLMReplacementResult(dict):
    """
    The result of an LLM replacement.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.replace_llms` instead.
    """

    def __init__(self, data):
        super(DSSLLMReplacementResult, self).__init__(data)
        self["replacedObjects"] = [DSSLLMReplacedObject(item) for item in data["replacedObjects"]]

    @property
    def replaced_object_count(self):
        """
        The total number of updated objects.

        :rtype: int
        """
        return self["replacedObjectCount"]

    @property
    def replaced_objects(self):
        """
        The updated objects in this project.

        :rtype: list[DSSLLMReplacedObject]
        """
        return self["replacedObjects"]
