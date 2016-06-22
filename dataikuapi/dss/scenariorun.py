from datetime import datetime

class DSSScenarioRun(object):
    """
    A run of a scenario
    """
    
    def __init__(self, client, run):
        self.client = client
        self.run = run

    def get_details(self):
        """
        Get the full details of the scenario run, including its step runs
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/%s/" % (self.run['scenario']['projectKey'], self.run['scenario']['id'], self.run['runId']))
    
    def get_start_time(self):
        """
        Get the start time of the scenario run
        """
        return datetime.fromtimestamp(self.run['start'] / 1000)
        
    def get_duration(self):
        """
        Get the duration of this run (in fractional seconds).
        
        If the run is still running, get the duration since it started
        """
        end_time = datetime.now()
        if self.run['end'] > 0:
            end_time = datetime.fromtimestamp(self.run['end'] / 1000)
        duration = (end_time - self.get_start_time()).total_seconds()
        return duration