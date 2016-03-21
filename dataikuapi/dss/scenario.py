
class DSSScenario(object):
    """
    A scenario on the DSS instance
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Aborts the scenario
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/abort" % (self.project_key, self.id))

    def run(self):
        """
        Requests a run of the scenario, which will start after a few seconds
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id))

