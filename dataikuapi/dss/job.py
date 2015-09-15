
class DSSJob(object):

    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key
    
    def abort(self):
        """
        Delete the group
        """
        return self.client._perform_json(
            "POST", "/projects/%s/jobs/%s/abort" % (self.project_key, self.id))
    
    def get_status(self):
        """
        Get the current status of the job
        """
        return self.client._perform_json(
            "GET", "/projects/%s/jobs/%s/status" % (self.project_key, self.id))
    
    def get_log(self, activity=None):
        """
        Get the logs of the job
        """
        return self.client._perform_text(
            "GET", "/projects/%s/jobs/%s/log" % (self.project_key, self.id),
            params={
                "activity" : activity
            })
    
        
    
        