class DSSLabelingTask(object):
    """
    A handle to an existing labeling task on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_labeling_task()`
    """

    def __init__(self, client, project_key, task_id):
        self.client = client
        self.project_key = project_key
        self.task_id = task_id

    @property
    def id(self):
        """
        Returns the internal identifier of the labeling task

        :rtype: string
        """
        return self.task_id
