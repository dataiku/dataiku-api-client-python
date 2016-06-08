from triggerfire import DSSTriggerFire
from scenariorun import DSSScenarioRun

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
        trigger_fire = self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id), body=params)
        return DSSTriggerFire(self, trigger_fire)
        
    def get_last_runs(self, limit=10, only_finished_runs=False):
        """
        Get the list of the last runs of the scenario
        """
        runs = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/get-last-runs" % (self.project_key, self.id), params={
                'limit' : limit,
                'onlyFinishedRuns' : only_finished_runs
            })
        return [DSSScenarioRun(self.client, run) for run in runs]
    
    def get_current_run(self):
        """
        Get the current run of the scenario, or None if it is not running at the moment
        """
        last_run = self.get_last_runs(1)
        if len(last_run) == 0:
            return None
        last_run = last_run[0]
        if 'result' in last_run.run:
            return None # has a result means it's done
        else:
            return last_run
    
    def get_run(self, run_id):
        """
        Get a handle to a run of the scenario
        """
        return DSSScenarioRun(self.client, {'scenario' : {'projectKey':self.project_key, 'id':self.id}, 'runId' : run_id})
    
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

    def get_average_duration(self, limit=3):
        """
        Get the average duration (in fractional seconds) of the last runs of this
        scenario that finished, where finished means it ended with SUCCESS or WARNING.
        If there are not enough runs to perform the average, returns None
        
        Args:
            limit: number of last runs to average on
        """
        last_runs = self.get_last_runs(limit=limit, only_finished_runs=True)
        if len(last_runs) < limit:
            return None
        return sum([run.get_duration() for run in last_runs]) / len(last_runs)
