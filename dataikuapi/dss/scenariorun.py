
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
        