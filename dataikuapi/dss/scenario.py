from datetime import datetime
import time
from ..utils import DataikuException
from .discussion import DSSObjectDiscussions


class DSSScenario(object):
    """
    A handle to interact with a scenario on the DSS instance
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Aborts the scenario if it currently running
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/abort" % (self.project_key, self.id))

    def run(self, params=None):
        """
        Requests a run of the scenario, which will start after a few seconds.

        :params dict params: additional parameters that will be passed to the scenario through trigger params (defaults to `{}`)
        """
        if params is None:
            params = {}
        trigger_fire = self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id), body=params)
        return DSSTriggerFire(self, trigger_fire)

    def get_trigger_fire(self, trigger_id, trigger_run_id):
        """
        Requests a trigger of the run of a scenario

        Args:
            trigger_id:  Id of trigger
            trigger_run_id: Id of the run of the trigger

        Returns:
            A :class:`dataikuapi.dss.admin.DSSTriggerFire` trigger handle
        """
        trigger_fire = self.client._perform_json(
            "GET", "/projects/%s/scenarios/trigger/%s/%s" % (self.project_key, self.id, trigger_id), params={
                'triggerRunId' : trigger_run_id
            })
        return DSSTriggerFire(self, trigger_fire)

    def run_and_wait(self, params=None, no_fail=False):
        """
        Requests a run of the scenario, which will start after a few seconds. Wait the end of the run to complete.

        :param dict params: additional parameters that will be passed to the scenario through trigger params (defaults to `{}`)

        :return: A :class:`dataikuapi.dss.admin.DSSScenarioRun` run handle
        """
        if params is None:
            params = {}
        trigger_fire = self.run(params)
        scenario_run = trigger_fire.wait_for_scenario_run(no_fail)
        waiter = DSSScenarioRunWaiter(scenario_run, trigger_fire)
        return waiter.wait(no_fail)

    def get_last_runs(self, limit=10, only_finished_runs=False):
        """
        Get the list of the last runs of the scenario.

        :return: A list of :class:`dataikuapi.dss.scenario.DSSScenarioRun`
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

        :return: A :class:`dataikuapi.dss.scenario.DSSScenarioRun`
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

        :return: A :class:`dataikuapi.dss.scenario.DSSScenarioRun`
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
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix))

    def set_definition(self, definition, with_status=True):
        """
        Updates the definition of this scenario

        Args:
            with_status: should be the same as the value passed to get_definition(). If True, the params, 
                         triggers and reporters fields of the scenario are ignored,
        """
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix), body = definition)

    def get_payload(self, extension='py'):
        """
        Returns the payload of the scenario

        :param str extension: the type of script. Default is 'py' for python
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id)).get('script', '')

    def set_payload(self, script, with_status=True):
        """
        Updates the payload of this scenario

        :param str extension: the type of script. Default is 'py' for python
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

    def delete(self):
        """
        Deletes this scenario
        """
        return self.client._perform_json(
            "DELETE", "/projects/%s/scenarios/%s" % (self.project_key, self.id))

    ########################################################
    # Discussions
    ########################################################
    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the scenario

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SCENARIO", self.id)


class DSSScenarioRun(object):
    """
    A handle containing basic info about a past run of a scenario.

    This handle can also be used to fetch additional information about the urn
    """

    def __init__(self, client, run):
        self.client = client
        self.run = run

    def get_info(self):
        """
        Get the basic information of the scenario run
        """
        return self.run

    def get_details(self):
        """
        Get the full details of the scenario run, including its step runs.

        Note: this perform another API call
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

class DSSScenarioRunWaiter(object):
    """
    Helper to wait for a job's completion
    """    
    def __init__(self, scenario_run, trigger_fire):
        self.trigger_fire = trigger_fire
        self.scenario_run = scenario_run

    def wait(self, no_fail=False):
        while not self.scenario_run.run.get('result', False):
            self.scenario_run = self.trigger_fire.get_scenario_run()
            time.sleep(5)
        outcome = self.scenario_run.run.get('result', None).get('outcome', 'UNKNOWN')
        if outcome == 'SUCCESS' or no_fail:
            return self.scenario_run
        else:
            raise DataikuException("Scenario run returned status %s" % outcome)

class DSSTriggerFire(object):
    """
    The activation of a trigger on the DSS instance
    """

    def __init__(self, scenario, trigger_fire):
        self.client = scenario.client
        self.project_key = scenario.project_key
        self.scenario_id = scenario.id
        self.trigger_id = trigger_fire['trigger']['id']
        self.run_id = trigger_fire['runId']
        self.trigger_fire = trigger_fire

    def get_scenario_run(self):
        """
        Get the run of the scenario that this trigger activation launched
        """
        run = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/get-run-for-trigger" % (self.project_key, self.scenario_id), params= {
               'triggerId' : self.trigger_id,
               'triggerRunId' : self.run_id
            })
        if 'scenarioRun' not in run:
            return None
        else:
            return DSSScenarioRun(self.client, run['scenarioRun'])

    def is_cancelled(self, refresh=False):
        """
        Whether the trigger has been cancelled

        :param refresh: get the state of the trigger from the backend
        """
        if refresh == True:
            self.trigger_fire = self.client._perform_json(
            "GET", "/projects/%s/scenarios/trigger/%s/%s" % (self.project_key, self.scenario_id, self.trigger_id), params={
                'triggerRunId' : self.run_id
            })
        return self.trigger_fire["cancelled"]

    def wait_for_scenario_run(self, no_fail=False):
        scenario_run = None
        refresh_trigger_counter = 0
        while scenario_run is None:
            refresh_trigger_counter += 1
            if refresh_trigger_counter == 10:
                refresh_trigger_counter = 0
            if self.is_cancelled(refresh=refresh_trigger_counter == 0):
                if no_fail:
                    return None
                else:
                    raise DataikuException("Scenario run has been cancelled")
            scenario_run = self.get_scenario_run()
            time.sleep(5)
        return scenario_run
