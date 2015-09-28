
class DSSJob(object):
    """
    A job on the DSS instance
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Aborts the job
        """
        return self.client._perform_json(
            "POST", "/projects/%s/jobs/%s/abort" % (self.project_key, self.id))

    def get_status(self):
        """
        Get the current status of the job
        
        Returns:
            the state of the job, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/projects/%s/jobs/%s/" % (self.project_key, self.id))

    def get_log(self, activity=None):
        """
        Get the logs of the job
        
        Args:
            activity: (optional) the name of the activity in the job whose log is requested
            
           Returns:
               the log, as a string
        """
        return self.client._perform_text(
            "GET", "/projects/%s/jobs/%s/log" % (self.project_key, self.id),
            params={
                "activity" : activity
            })
