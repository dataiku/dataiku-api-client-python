
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

    def run(self, params={}):
        """
        Requests a run of the scenario, which will start after a few seconds.

        :params: params: additional parameters that will be passed to the scenario through trigger params
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id), body=params)

