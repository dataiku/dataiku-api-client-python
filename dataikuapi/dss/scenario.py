from datetime import datetime
import time, warnings
from dataikuapi.utils import DataikuException
from .discussion import DSSObjectDiscussions

class DSSScenario(object):
    """
    A handle to interact with a scenario on the DSS instance.
    Do not create this directly, use :meth:`dataikuapi.dss.DSSProject.get_scenario`
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Aborts the scenario if it currently running. Does nothing if the scenario is not currently running
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/abort" % (self.project_key, self.id))

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

    def run(self, params=None):
        """
        Requests a run of the scenario, which will start after a few seconds.

        :params dict params: additional parameters that will be passed to the scenario through trigger params (defaults to `{}`)
        :return the trigger fire object. Note that this is NOT a Scenario run object. The trigger fire may ultimately result in a run or not.
        :rtype :class:`DSSTriggerFire`
        """
        if params is None:
            params = {}
        trigger_fire = self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id), body=params)
        return DSSTriggerFire(self, trigger_fire)

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
        Get a handle to a run of the scenario based on a scenario run id

        :return: A :class:`dataikuapi.dss.scenario.DSSScenarioRun`
        """
        run_details = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/%s/" % (self.project_key, self.id, run_id))
        return DSSScenarioRun(self.client, run_details["scenarioRun"])

    def get_settings(self):
        """
        Returns the settings of this scenario
        :rtype :class:`StepBasedDSSScenarioSettings` or :class:`PythonScriptBasedScenarioSettings`
        """
        data = self.client._perform_json("GET", "/projects/%s/scenarios/%s" % (self.project_key, self.id))

        if data["type"] == "step_based":
            return StepBasedScenarioSettings(self.client, self, data)
        else:
            payload = self.client._perform_json(
                "GET", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id)).get('script', '')
            return PythonScriptBasedScenarioSettings(self.client, self, data, payload)

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

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the scenario

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SCENARIO", self.id)

    ########################################################
    # Advanced
    ########################################################

    def get_trigger_fire(self, trigger_id, trigger_run_id):
        """
        Gets the trigger fire object corresponding to a previous trigger fire id. Advanced usages only
        """
        trigger_fire = self.client._perform_json(
            "GET", "/projects/%s/scenarios/trigger/%s/%s" % (self.project_key, self.id, trigger_id), params={
                'triggerRunId' : trigger_run_id
            })
        return DSSTriggerFire(self, trigger_fire)

    ########################################################
    # Deprecated
    ########################################################

    def get_definition(self, with_status=True):
        """
        Deprecated, use :meth:`get_settings` and :meth:`get_summary`

        Returns the definition of the scenario
        :param bool status: if True, the definition contains the run status of the scenario but not its
                              actions' definition. If False, the definition doesn't contain the run status
                              but has the scenario's actions definition
        """
        warnings.warn("DSSScenario.get_definition is deprecated, please use get_settings", DeprecationWarning)
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix))

    def set_definition(self, definition, with_status=True):
        """
        Deprecated, use :meth:`get_settings` and :meth:`DSSScenarioSettings.save`

        Updates the definition of this scenario
        :param bool status: should be the same as the value passed to get_definition(). If True, the params, 
                         triggers and reporters fields of the scenario are ignored,
        """
        warnings.warn("DSSScenario.set_definition is deprecated, please use get_settings", DeprecationWarning)
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix), body = definition)

    def get_payload(self, extension='py'):
        """
        Deprecated, use :meth:`get_settings` and :meth:`DSSScenarioSettings.save`
        
        Returns the payload of the scenario
        :param str extension: the type of script. Default is 'py' for python
        """
        warnings.warn("DSSScenario.get_payload is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id)).get('script', '')

    def set_payload(self, script, with_status=True):
        """
        Deprecated, use :meth:`get_settings` and :meth:`DSSScenarioSettings.save`
        
        Updates the payload of this scenario
        :param str extension: the type of script. Default is 'py' for python
        """
        warnings.warn("DSSScenario.set_payload is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id), body = {'script' : script})


class DSSScenarioSettings(object):
    """Settings of a scenario. Do not instantiate this class, use :meth:`DSSScenario.get_settings`"""
    def __init__(self, client, scenario, data):
        self.client = client
        self.scenario = scenario
        self.data = data

    def get_raw(self):
        return self.data

    def set_active(self, active):
        self.data["active"] = active

    @property
    def raw_triggers(self):
        return self.data["triggers"]

    def add_periodic_trigger(self, every_minutes=5):
        """Adds a trigger that runs the scenario every X minutes"""
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Minutely", "count": every_minutes}}
        self.raw_triggers.append(trigger)

    def add_hourly_trigger(self, minute_of_hour=0):
        """Adds a trigger that runs the scenario each hour on a predefined minute"""
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Hourly", "minute":  minute_of_hour}}
        self.raw_triggers.append(trigger)

    def add_daily_trigger(self, hour=2, minute=0, days=None):
        """
        Adds a trigger that runs the scenario each day on a predefined time.

        :param day list: if not None, only runs on given days. Day must be given as english names with capitals
        """
        if days is None:
            trigger = {"active": True, "type": "temporal", "params": { "frequency": "Daily", "hour": hour, "minute":  minute}}
        else:
            trigger = {"active": True, "type": "temporal", "params": { "frequency": "Weekly", "hour": hour, "minute":  minute,
                            "daysOfWeek": days}}
        self.raw_triggers.append(trigger)

    def add_monthly_trigger(self, day=1, hour=2, minute=0):
        """Adds a trigger that runs the scenario once per month"""
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Monthly", "dayOfMonth": day, "hour": hour, "minute": minute}}
        self.raw_triggers.append(trigger)

    def save(self):
        """Saves the settings to the scenario"""
        self.client._perform_json("PUT",
            "/projects/%s/scenarios/%s" % (self.scenario.project_key, self.scenario.id), body = self.data)


class StepBasedScenarioSettings(DSSScenarioSettings):
    @property
    def raw_steps(self):
        """Returns raw definition of steps"""
        return self.data["params"]["steps"]


class PythonScriptBasedScenarioSettings(DSSScenarioSettings):
    def __init__(self, client, scenario, data, script):
        super(PythonScriptBasedScenarioSettings, self).__init__(client, scenario, data)
        self.script = script

    @property
    def code(self):
        return self.script

    @code.setter
    def code(self, script):
        self.script = script
    
    def save(self):
        """Saves the settings to the scenario"""
        super(PythonScriptBasedScenarioSettings, self).save()
        self.client._perform_json("PUT",
            "/projects/%s/scenarios/%s/payload" % (self.scenario.project_key, self.scenario.id), body = {'script' : self.script})

class DSSScenarioRun(object):
    """
    A handle containing basic info about a past run of a scenario.

    This handle can also be used to fetch additional information about the urn
    """

    def __init__(self, client, run):
        self.client = client
        self.run = run

    def refresh(self):
        """Refreshes the details (outcome, running, info, ...) from the scenario"""
        updated_run_details = self.client._perform_json("GET", "/projects/%s/scenarios/%s/%s/" % \
                 (self.run["scenario"]["projectKey"], self.run["scenario"]["id"], self.run["runId"]))
        self.run = updated_run_details["scenarioRun"]

    def wait_for_completion(self, no_fail=False):
        """
        If the scenario run is not complete, wait for it to complete
        :param boolean no_fail: if no_fail=False, raises an exception if scenario fails
        """
        while self.running:
            self.refresh()
            time.sleep(5)

        if self.outcome != 'SUCCESS' and no_fail == False:
            raise DataikuException("Scenario run returned status %s" % outcome)

    @property
    def running(self):
        """Returns whether this run is running"""
        return not "result" in self.run

    @property
    def outcome(self):
        """
        The outcome of this scenario run, if available
        :return one of  SUCCESS, WARNING, FAILED, or ABORTED
        :rtype str
        """
        if not "result" in self.run:
            raise ValueError("outcome not available for this scenario run. Maybe still running?")
        return self.run["result"]["outcome"]

    @property
    def trigger(self):
        """
        The raw details of the trigger that triggered this scenario run
        :rtype dict
        """
        return self.run["trigger"]["trigger"]

    def get_info(self):
        """
        Get the raw basic information of the scenario run
        :rtype dict
        """
        return self.run

    def get_details(self):
        """
        Get the full details of the scenario run, including its step runs.
        Note: this performs another API call

        :rtype dict
        """
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/%s/" % (self.run['scenario']['projectKey'], self.run['scenario']['id'], self.run['runId']))

    def get_start_time(self):
        """
        Get the start time of the scenario run
        """
        return datetime.fromtimestamp(self.run['start'] / 1000)
    start_time = property(get_start_time)

    def get_end_time(self):
        """
        Get the end time of the scenario run, if it completed. Else raises
        """
        if "end" in self.run and self.run["end"] > 0:
            return datetime.fromtimestamp(self.run['end'] / 1000)
        else:
            raise ValueError("Scenario run has not completed")
    end_time = property(get_end_time)

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
    duration = property(get_duration)

class DSSScenarioRunWaiter(object):
    """
    Helper to wait for a scenario to run to complete
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
    A handle representing the firing of a trigger on a scenario. Do not create this class directly, use
    :meth:`DSSScenario.run`
    """
    def __init__(self, scenario, trigger_fire):
        self.client = scenario.client
        self.project_key = scenario.project_key
        self.scenario_id = scenario.id
        self.trigger_id = trigger_fire['trigger']['id']
        self.run_id = trigger_fire['runId']
        self.trigger_fire = trigger_fire

    def wait_for_scenario_run(self, no_fail=False):
        """
        Polls, waiting for the run of the sceanrio that this trigger activation launched to be available, or 
        for the trigger fire to be cancelled (possibly cancelled by another firing)

        :param no_fail: If no_fail=True, will return None if the trigger fire is cancelled, else will raise
        :returns a scenario run object, or None
        :rtype :class:`DSSScenarioRun`
        """
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

    def get_scenario_run(self):
        """
        Get the run of the scenario that this trigger activation launched. May return None if the scenario run started
        from this trigger has not yet been created
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
        Whether the trigger fire has been cancelled

        :param refresh: get the state of the trigger from the backend
        """
        if refresh == True:
            self.trigger_fire = self.client._perform_json(
            "GET", "/projects/%s/scenarios/trigger/%s/%s" % (self.project_key, self.scenario_id, self.trigger_id), params={
                'triggerRunId' : self.run_id
            })
        return self.trigger_fire["cancelled"]

