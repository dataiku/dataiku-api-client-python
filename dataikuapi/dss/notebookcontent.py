from .discussion import DSSObjectDiscussions

class DSSNotebookContent(object):
    """
    A Python/R/Scala notebook on the DSS instance
    """
    def __init__(self, client, project_key, notebook_name, content=None):
       self.client = client
       self.project_key = project_key
       self.notebook_name = notebook_name
       self.content = content

    def get_raw(self):
        """
        Get the content of this Jupyter notebook (metadata, cells, nbformat)
        :rtype: list with the full content of a notebook
        """
        if self.content is None:
            self.content = self.client._perform_json("GET",
                                                     "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name))
        return self.content

    def get_metadata(self):
        """
        Get the metadata associated to this Jupyter notebook
        :rtype: list with metadata
        """
        return self.get_raw()["metadata"]

    def get_cells(self):
        """
        Get the cells associated to this Jupyter notebook
        :rtype: list of cells
        """
        return self.get_raw()["cells"]


    def save(self):
        """
        Save the content of this Jupyter notebook
        """
        if self.content is None:
            raise ValueError("Notebook content is empty, use \"get_content()\" or manually set the content of the notebook before saving")
        return self.client._perform_json("PUT",
                                         "/projects/%s/jupyter-notebooks/%s" % (self.project_key, self.notebook_name),
                                         body=self.content)
