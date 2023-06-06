import time
import sys
from ..utils import DataikuException


class DSSJob(object):
    """
    A job on the DSS instance.

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.get_job`
        or :meth:`dataikuapi.dss.project.DSSProject.start_job`.
    """

    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Aborts the job.

        :returns: a confirmation message for the request
        :rtype: dict
        """
        return self.client._perform_json(
            "POST", "/projects/%s/jobs/%s/abort" % (self.project_key, self.id))

    def get_status(self):
        """
        Gets the current status of the job.

        :returns: the state of the job
        :rtype: dict
        """
        return self.client._perform_json(
            "GET", "/projects/%s/jobs/%s/" % (self.project_key, self.id))

    def get_log(self, activity=None):
        """
        Gets the logs of the job. If an activity is passed in the parameters
        the logs will be scoped to that activity.

        :param string activity: (optional) the name of the activity in the job whose log is requested (defaults to **None**)

        :returns: the job logs
        :rtype: string
        """
        return self.client._perform_text(
            "GET", "/projects/%s/jobs/%s/log" % (self.project_key, self.id),
            params={
                "activity" : activity
            })


class DSSJobWaiter(object):
    """
    Creates a helper to wait for the completion of a job.
    
    :param job: The job to wait for
    :type job: :class:`dataikuapi.dss.job.DSSJob`
    """
    def __init__(self, job):
        self.job = job

    def wait(self, no_fail=False):
        """
        Waits for the job. While waiting, if the job was aborted or if it failed
        an exception is raised depending on the `no_fail` parameter.
        If the job already stopped before entering this function
        its state will be returned regardless and no error will be raised.
        
        :param boolean no_fail: (optional) should an error be raised if the job finished with another status than `DONE` (defaults to **False**)

        :raises DataikuException: when the job does not complete successfully

        :returns: the job state
        :rtype: dict
        """
        job_state = self.job.get_status().get("baseStatus", {}).get("state", "")
        sleep_time = 2
        while job_state not in ["DONE", "ABORTED", "FAILED"]:
            sleep_time = 60 if sleep_time >= 60 else sleep_time * 1.2
            time.sleep(int(sleep_time))
            job_state = self.job.get_status().get("baseStatus", {}).get("state", "")
            if job_state in ["ABORTED", "FAILED"]:
                if no_fail:
                    break
                else:
                    raise DataikuException("Job run did not finish. Status: %s" % (job_state))
        return job_state
