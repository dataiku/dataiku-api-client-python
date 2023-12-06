from .utils import DSSTaggableObjectListItem

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
        self.id = id

    def as_core_knowledge_bank(self):
        """
        Get the :class:`dataiku.KnowledgeBank` object corresponding to this knowledge bank

        :rtype: :class:`dataiku.KnowledgeBank`
        """
        import dataiku
        return dataiku.KnowledgeBank("%s.%s" % (self.project_key, self.id))