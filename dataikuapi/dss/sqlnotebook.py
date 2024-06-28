from .discussion import DSSObjectDiscussions
from .utils import DSSTaggableObjectListItem

class DSSSQLNotebookListItem(DSSTaggableObjectListItem):
    """
    An item in a list of SQL notebooks

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_sql_notebooks`
    """
    def __init__(self, client, data):
        super(DSSSQLNotebookListItem, self).__init__(data)
        self.client = client

    def to_notebook(self):
        """
        Get a handle on the corresponding notebook

        :rtype: :class:`DSSSQLNotebook`
        """
        return DSSSQLNotebook(self.client, self._data["projectKey"], self._data["id"])

    @property
    def id(self):
        """
        Get the id of the notebook

        Used as identifier
        """
        return self._data["id"]

    @property
    def language(self):
        """
        Get the language of the notebook

        Possible values are 'SQL', 'HIVE', 'IMPALA', 'SPARKSQL'

        :rtype: string
        """
        return self._data["language"]

class DSSSQLNotebook(object):
    """
    A handle on a SQL notebook

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_sql_notebook()` or
        :meth:`dataikuapi.dss.project.DSSProject.create_sql_notebook()`
    """
    def __init__(self, client, project_key, notebook_id):
       self.client = client
       self.project_key = project_key
       self.notebook_id = notebook_id

    def get_content(self):
        """
        Get the full content of this SQL notebook

        The content comprises cells

        Usage example:

        .. code-block:: python

            # collect all the SQL source code of a notebook
            lines = []
            for cell in notebook.get_content().get_cells():
                if cell["cell_type"] != 'QUERY':
                    continue
                lines = lines + cell["code"]
            print('\\n'.join(lines))

        :return: A list of :class:`dataikuapi.dss.sqlnotebook.DSSNotebookContent`
        :rtype: list
        """
        raw_content = self.client._perform_json("GET", "/projects/%s/sql-notebooks/%s" %
                                                (self.project_key, self.notebook_id))
        return DSSNotebookContent(self.client, self.project_key, self.notebook_id, raw_content)

    def delete(self):
        """
        Delete this SQL notebook
        """
        return self.client._perform_json("DELETE",
                                         "/projects/%s/sql-notebooks/%s" % (self.project_key, self.notebook_id))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the notebook

        :return: The handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SQL_NOTEBOOK", self.notebook_id)

class DSSNotebookContent(object):
    """
    The content of a SQL notebook

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.sqlnotebook.DSSSQLNotebook.get_content`
    """
    def __init__(self, client, project_key, notebook_id, content):
        self.client = client
        self.project_key = project_key
        self.notebook_id = notebook_id
        self.content = content

    def get_raw(self):
        """
        Get the raw content of this SQL notebook

        The content comprises cells

        :return: A dict containing the full content of a notebook. Notable fields are:

            * **cells**: list of cells, each one a dict (see :meth:`get_cells()`)

        :rtype: dict
        """
        return self.content

    def get_cells(self):
        """
        Get the cells of this SQL notebook

        :return: A list of cells. Each cell is a dict, with notable fields:

            * **type**: type of the cell, for example 'QUERY' or 'MARKDOWN'
            * **name**: name of the cell
            * **code**: content of the cell

        :rtype: list[dict]
        """
        return self.content["cells"]

    def save(self):
        """
        Save the content of this SQL notebook
        """
        return self.client._perform_json("PUT",
                                         "/projects/%s/sql-notebooks/%s" % (self.project_key, self.notebook_id),
                                         body=self.content)
