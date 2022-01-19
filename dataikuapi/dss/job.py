import time
import sys
from ..utils import DataikuException

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

class DSSJobWaiter(object):
    """
    Helper to wait for a job's completion
    """    
    def __init__(self, job):
        self.job = job

    def wait(self, no_fail=False):
        job_state = self.job.get_status().get("baseStatus", {}).get("state", "")
        sleep_time = 2
        while job_state not in ["DONE", "ABORTED", "FAILED"]:
            sleep_time = 300 if sleep_time >= 300 else sleep_time * 2
            time.sleep(sleep_time)
            job_state = self.job.get_status().get("baseStatus", {}).get("state", "")
            if job_state in ["ABORTED", "FAILED"]:
                if no_fail:
                    break
                else:
                    raise DataikuException("Job run did not finish. Status: %s" % (job_state))
        return job_state
