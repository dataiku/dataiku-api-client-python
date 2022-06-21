from datetime import datetime
import time, warnings
from ..utils import DataikuException
from .discussion import DSSObjectDiscussions
from .utils import DSSTaggableObjectListItem
from dateutil.tz import tzlocal

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
        Get the list of the last runs of the scenario

        :return: A list of :class:`dataikuapi.dss.scenario.DSSScenarioRun`
        """
        runs = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/get-last-runs" % (self.project_key, self.id), params={
                'limit' : limit,
                'onlyFinishedRuns' : only_finished_runs
            })
        return [DSSScenarioRun(self.client, run) for run in runs]

    def get_runs_by_date(self, from_date, to_date=datetime.now()):
        """
        Get the list of the runs of the scenario in a given date range, [from_date, to_date)

        :param datetime from_date: start of the date range to retrieve runs for, inclusive
        :param datetime to_date: end of the date range to retrieve runs for, or now(), exclusive

        :return: A list of :class:`dataikuapi.dss.scenario.DSSScenarioRun`
        """
        def as_date(d):
            if isinstance(d, datetime):
                return d.strftime("%Y-%m-%d")
            else:
                return d

        runs = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/get-runs-by-date" % (self.project_key, self.id), params={
                'fromDate': as_date(from_date),
                'toDate': as_date(to_date)
            })
        return [DSSScenarioRun(self.client, run) for run in runs]

    def get_last_finished_run(self):
        """
        Gets the last run that completed (successfully or not)
        :return: A :class:`dataikuapi.dss.scenario.DSSScenarioRun`
        """
        lr = [sr for sr in self.get_last_runs() if not sr.running]
        if len(lr) == 0:
            raise ValueError("No scenario run completed")
        return lr[0]

    def get_last_successful_run(self):
        """
        Gets the last run that completed successfully
        :return: A :class:`dataikuapi.dss.scenario.DSSScenarioRun`
        """
        lr = self.get_last_runs(only_finished_runs=True)
        if len(lr) == 0:
            raise ValueError("No scenario run completed successfully")
        return lr[0]

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

    def get_status(self):
        """
        Returns the status of this scenario

        :rtype: :class:`DSSScenarioStatus`
        """
        data = self.client._perform_json("GET", "/projects/%s/scenarios/%s/light" % (self.project_key, self.id))
        return DSSScenarioStatus(self, data)

    def get_settings(self):
        """
        Returns the settings of this scenario

        :rtype: :class:`StepBasedScenarioSettings` or :class:`PythonScriptBasedScenarioSettings`
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

class DSSScenarioStatus(object):
    """Status of a scenario. Do not instantiate this class, use :meth:`DSSScenario.get_status`"""

    def __init__(self, scenario, data):
        self.scenario = scenario
        self.data = data

    def get_raw(self):
        return self.data

    @property
    def running(self):
        return self.data["running"]

    @property
    def next_run(self):
        """
        Time at which the scenario is expected to next run based on its triggers.

        May be None if there are no temporal triggers

        This is an approximate indication as scenario run may be delayed, especially in the case of 
        multiple triggers or high load
        """
        if not "nextRun" in self.data or self.data["nextRun"] == 0:
            return None
        return datetime.fromtimestamp(self.data["nextRun"] / 1000)


class DSSScenarioSettings(object):
    """Settings of a scenario. Do not instantiate this class, use :meth:`DSSScenario.get_settings`"""
    def __init__(self, client, scenario, data):
        self.client = client
        self.scenario = scenario
        self.data = data

    def get_raw(self):
        return self.data

    @property 
    def active(self):
        """
        Whether this scenario is currently active, i.e. its auto-triggers are executing
        """
        return self.data["active"]
    @active.setter
    def active(self, active):
        self.data["active"] = active

    @property 
    def run_as(self):
        """
        The configured 'run as' of the scenario. None means that the scenario runs as its last modifier.
        Only administrators may set a non-None value
        """
        return self.data.get("runAsUser", None)
    @run_as.setter
    def run_as(self, run_as):
        self.data["runAsUser"] = run_as

    @property
    def effective_run_as(self):
        """
        The effective 'run as' of the scenario. If a run_as has been configured by an administrator, 
        this will be used. Else, this will be the last modifier of the scenario.

        If this method returns None, it means that it was not possible to identify who this
        scenario runs as. This scenario is probably not currently functioning.
        """
        # Note: this logic must match the one in ScenarioBaseService
        if "runAsUser" in self.data:
            return self.data["runAsUser"]
        elif "versionTag" in self.data:
            return self.data["versionTag"]["lastModifiedBy"]["login"]
        elif "creationTag" in self.data:
            return self.data["creationTag"]["lastModifiedBy"]["login"]
        else:
            return None

    @property
    def raw_triggers(self):
        return self.data["triggers"]

    @property
    def raw_reporters(self):
        return self.data["reporters"]

    def add_periodic_trigger(self, every_minutes=5):
        """Adds a trigger that runs the scenario every X minutes"""
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Minutely", "repeatFrequency": every_minutes }}
        self.raw_triggers.append(trigger)

    def add_hourly_trigger(self, minute_of_hour=0, year=None, month=None, day=None, starting_hour=0, repeat_every=1, timezone="SERVER"):
        """Adds a trigger that runs the scenario each hour on a predefined minute"""
        starting_date =self.__get_starting_date__(year=year, month=month, day=day)
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Hourly", "hour": starting_hour, "minute": minute_of_hour,
                                                                   "startingFrom": starting_date, "repeatFrequency": repeat_every, "timezone": timezone }}
        self.raw_triggers.append(trigger)

    def add_daily_trigger(self, hour=2, minute=0, days=None, year=None, month=None, day=None, repeat_every=1, timezone="SERVER"):
        """
        Adds a trigger that runs the scenario each day on a predefined time.

        :param day list: if not None, only runs on given days. Day must be given as english names with capitals
        """
        starting_date =self.__get_starting_date__(year=year, month=month, day=day)
        if days is None:
            trigger = {"active": True, "type": "temporal", "params": { "frequency": "Daily", "hour": hour, "minute": minute, "startingFrom": starting_date,
                                                                       "repeatFrequency": repeat_every, "timezone": timezone }}
        else:
            trigger = {"active": True, "type": "temporal", "params": { "frequency": "Weekly", "hour": hour, "minute": minute, "startingFrom": starting_date,
                                                                       "daysOfWeek": days, "repeatFrequency": repeat_every, "timezone": timezone }}
        self.raw_triggers.append(trigger)

    def add_monthly_trigger(self, day=1, hour=2, minute=0, year=None, month=None, run_on="ON_THE_DAY", repeat_every=1, timezone="SERVER"):
        """Adds a trigger that runs the scenario once per month"""
        # We want the default value to be the First of January is nothing was set.
        starting_date = self.__get_starting_date__(year=year, month=month, day=day, default_is_today=False)
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Monthly", "startingFrom": starting_date, "hour": hour, "minute": minute,
                                                                   "monthlyRunOn": run_on, "repeatFrequency": repeat_every, "timezone": timezone }}
        self.raw_triggers.append(trigger)

    def __get_starting_date__(self, year, month, day, default_is_today=True):
        today = datetime.now(tzlocal())
        if day is None or not isinstance(day, int) or day < 1 or day > 31:
            if default_is_today:
                day = today.day
            else:
                # Will be use to avoid Monthly trigger on the 31 of February if the day is not set
                day = 1
        if month is None or not isinstance(month, int) or month < 1 or month > 12:
            if default_is_today:
                month = today.month
            else:
                # Will be use to avoid Monthly trigger on the 31 of February if the month is not set
                month = 1
        if year is None or not isinstance(year, int):
            year = today.year
        start_date = today.replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
        return start_date.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + start_date.strftime('%z')


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

    @property
    def id(self):
        """The run id of this run"""
        return self.run["runId"]

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
        raw_data = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/%s/" % (self.run['scenario']['projectKey'], self.run['scenario']['id'], self.run['runId']))

        details = DSSScenarioRunDetails(raw_data)
        if "stepRuns" in details:
            structured_steps = []
            for step in details["stepRuns"]:
                structured_steps.append(DSSStepRunDetails(step))
            details["stepRuns"] = structured_steps
        return details

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

class DSSScenarioRunDetails(dict):
    def __init__(self, data):
        super(DSSScenarioRunDetails, self).__init__(data)

    @property
    def steps(self):
        return self["stepRuns"]

    @property
    def last_step(self):
        return self["stepRuns"][len(self["stepRuns"]) - 1]

    @property
    def first_error_details(self):
        """
        Try to get the details of the first error if this run failed. This will not always be able
        to find the error details (it returns None in that case)
        """
        for step in self.steps:
            step_error = step.first_error_details
            if step_error is not None:
                return step_error


class DSSStepRunDetails(dict):
    def __init__(self, data):
        super(DSSStepRunDetails, self).__init__(data)

    @property
    def outcome(self):
        return self["result"]["outcome"]

    @property
    def job_ids(self):
        """The list of DSS job ids that were ran as part of this step"""
        return [ri["jobId"] for ri in self["additionalReportItems"] if ri["type"] == "JOB_EXECUTED"]

    @property
    def first_error_details(self):
        """
        Try to get the details of the first error if this step failed. This will not always be able
        to find the error details (it returns None in that case)
        """
        if self.outcome == 'FAILED':
            step_thrown = self.get('result').get('thrown', None)
            if step_thrown is not None:
                return step_thrown

        for item in self['additionalReportItems']:
            if item.get("outcome", None) == 'FAILED':
                item_thrown = item.get('thrown', None)
                if item_thrown is not None:
                    return item_thrown

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


class DSSScenarioListItem(DSSTaggableObjectListItem):
    """An item in a list of scenarios. Do not instantiate this class, use :meth:`dataikuapi.dss.project.DSSProject.list_scenarios"""
    def __init__(self, client, data):
        super(DSSScenarioListItem, self).__init__(data)
        self.client = client

    def to_scenario(self):
        """Gets the :class:`DSSScenario` corresponding to this scenario"""
        return DSSScenario(self.client, self._data["projectKey"], self._data["name"])

    @property
    def id(self):
        return self._data["name"]
