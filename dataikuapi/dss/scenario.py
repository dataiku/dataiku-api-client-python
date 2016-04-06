
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

    def get_definition(self, with_status=True):
        """
        Returns the definition of the scenario

        Args:
            with_status: if True, the definition contains the run status of the scenario but not its 
                              actions' definition. If False, the definition doesn't contain the run status
                              but has the scenario's actions definition
        """
        suffix = '/no-params' if with_status else ''
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix))

    def set_definition(self, definition, with_status=True):
        """
        Updates the definition of this scenario
        
        Args:
            with_status: should be the same as the value passed to get_definition(). If True, the params, 
                         triggers and reporters fields of the scenario are ignored,
        """
        suffix = '/no-params' if with_status else ''
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix), body = definition)

    def get_payload(self, extension='py'):
        """
        Returns the payload of the scenario

        Args:
            extension: the type of script. Default is 'py' for python
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id)).get('script', '')

    def set_payload(self, script, with_status=True):
        """
        Updates the payload of this scenario
        
        Args:
            extension: the type of script. Default is 'py' for python
        """
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id), body = {'script' : script})

