from datetime import datetime
import time, warnings
from ..utils import DataikuException
from .discussion import DSSObjectDiscussions
from .utils import DSSTaggableObjectListItem
from dateutil.tz import tzlocal

class DSSScenario(object):
    """
    A handle to interact with a scenario on the DSS instance.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.get_scenario`
    """
    def __init__(self, client, project_key, id):
        self.client = client
        self.id = id
        self.project_key = project_key

    def abort(self):
        """
        Abort the scenario.

        This method does nothing if the scenario is not currently running.
        """
        return self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/abort" % (self.project_key, self.id))

    def run_and_wait(self, params=None, no_fail=False):
        """
        Request a run of the scenario and wait the end of the run to complete.

        The method requests a new run, which will start after a few seconds.

        :param dict params: additional parameters that will be passed to the scenario through trigger params (defaults to `{}`)
        :param boolean no_fail: if False, raises if the run doesn't end with a SUCCESS outcome

        :return: a handle on the run
        :rtype: :class:`DSSScenarioRun`
        """
        if params is None:
            params = {}
        trigger_fire = self.run(params)
        scenario_run = trigger_fire.wait_for_scenario_run(no_fail)
        waiter = DSSScenarioRunWaiter(scenario_run, trigger_fire)
        return waiter.wait(no_fail)

    def run(self, params=None):
        """
        Request a run of the scenario.

        The method requests a new run, which will start after a few seconds.

        .. note::

            This method returns a trigger fire, NOT a Scenario run object. The trigger fire may ultimately result
            in a run or not.

        Usage example:

        .. code-block:: python

            scenario = project.get_scenario("myscenario")
            trigger_fire = scenario.run()

            # When you call `run` a scenario, the scenario is not immediately
            # started. Instead a "manual trigger" fires.
            # 
            # This trigger fire can be cancelled if the scenario was already running,
            # or if another trigger fires. Thus, the scenario run is not available 
            # immediately, and we must "wait" for it
            scenario_run = trigger_fire.wait_for_scenario_run()

            # Now the scenario is running. We can wait for it synchronously with
            # scenario_run.wait_for_completion(), but if we want to do other stuff
            # at the same time, we can use refresh
            while True:
                scenario_run.refresh()
                if scenario_run.running:
                    print("Scenario is still running ...")
                else:
                    print("Scenario is not running anymore")
                    break

                time.sleep(5)

        :params dict params: additional parameters that will be passed to the scenario through trigger params (defaults to `{}`)

        :return: a request for a run, as a trigger fire object
        :rtype: :class:`DSSTriggerFire`
        """
        if params is None:
            params = {}
        trigger_fire = self.client._perform_json(
            "POST", "/projects/%s/scenarios/%s/run" % (self.project_key, self.id), body=params)
        return DSSTriggerFire(self, trigger_fire)

    def get_last_runs(self, limit=10, only_finished_runs=False):
        """
        Get the list of the last runs of the scenario.

        :param int limit: maximum number of last runs to retrieve
        :param boolean only_finished_runs: if True, currently running runs are not returned.

        :return: a list of :class:`DSSScenarioRun`
        :rtype: list
        """
        runs = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/get-last-runs" % (self.project_key, self.id), params={
                'limit' : limit,
                'onlyFinishedRuns' : only_finished_runs
            })
        return [DSSScenarioRun(self.client, run) for run in runs]

    def get_runs_by_date(self, from_date, to_date=datetime.now()):
        """
        Get the list of the runs of the scenario in a given date range.

        :param datetime from_date: start of the date range to retrieve runs for, inclusive
        :param datetime to_date: end of the date range to retrieve runs for, exclusive

        :return: a list of :class:`DSSScenarioRun`
        :rtype: list
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
        Get the last run that completed.

        The run may be successful or failed, or even aborted.

        :rtype: :class:`DSSScenarioRun`
        """
        lr = [sr for sr in self.get_last_runs() if not sr.running]
        if len(lr) == 0:
            raise ValueError("No scenario run completed")
        return lr[0]

    def get_last_successful_run(self):
        """
        Get the last run that completed successfully.

        :rtype: :class:`DSSScenarioRun`
        """
        lr = self.get_last_runs(only_finished_runs=True)
        if len(lr) == 0:
            raise ValueError("No scenario run completed successfully")
        return lr[0]

    def get_current_run(self):
        """
        Get the current run of the scenario.

        If the scenario is not running at the moment, returns None.

        :rtype: :class:`DSSScenarioRun`
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
        Get a handle to a run of the scenario.

        :param string run_id: identifier of the run.

        :rtype: :class:`DSSScenarioRun`
        """
        run_details = self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/%s/" % (self.project_key, self.id, run_id))
        return DSSScenarioRun(self.client, run_details["scenarioRun"])

    def get_status(self):
        """
        Get the status of this scenario.

        :rtype: :class:`DSSScenarioStatus`
        """
        data = self.client._perform_json("GET", "/projects/%s/scenarios/%s/light" % (self.project_key, self.id))
        return DSSScenarioStatus(self, data)

    def get_settings(self):
        """
        Get the settings of this scenario.

        :return: a :class:`StepBasedScenarioSettings` for step-based scenarios, or a :class:`PythonScriptBasedScenarioSettings`
                 for scenarios defined by a python script.
        :rtype: :class:`DSSScenarioSettings`
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
        Get the average duration of the last runs of this scenario.

        The duration is computed on successful runs only, that is, on runs that ended
        with SUCCESS or WARNING satus.

        If there are not enough runs to perform the average, returns None

        :param int limit: number of last runs to average on

        :return: the average duration of the last runs, in seconds
        :rtype: float
        """
        last_runs = self.get_last_runs(limit=limit, only_finished_runs=True)
        if len(last_runs) < limit:
            return None
        return sum([run.get_duration() for run in last_runs]) / len(last_runs)

    def delete(self):
        """
        Delete this scenario.
        """
        return self.client._perform_json(
            "DELETE", "/projects/%s/scenarios/%s" % (self.project_key, self.id))

    def get_object_discussions(self):
        """
        Get a handle to manage discussions on the scenario.

        :returns: the handle to manage discussions
        :rtype: :class:`dataikuapi.dss.discussion.DSSObjectDiscussions`
        """
        return DSSObjectDiscussions(self.client, self.project_key, "SCENARIO", self.id)

    ########################################################
    # Advanced
    ########################################################

    def get_trigger_fire(self, trigger_id, trigger_run_id):
        """
        Get a trigger fire object. 

        .. caution::

            Advanced usages only (see :meth:`run()`)

        :param string trigger_id: identifier of the trigger, in the scenario's settings
        :param string trigger_run_id: identifier of the run of the trigger

        :rtype: :class:`DSSTriggerFire`
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
        Get the definition of the scenario.
        
        .. attention::

            Deprecated, use :meth:`get_settings` and :meth:`get_status`

        :param bool with_status: if True, get only the run status of the scenario. If False, get the 
                                 raw definition of the scenario.

        :return: if **with_status** is False, the scenario's definition as returned by :meth:`DSSScenarioSettings.get_raw()`.
                 If **with_status** is True, a summary of the scenario as returned by :meth:`DSSScenarioStatus.get_raw()`

        :rtype: dict
        """
        warnings.warn("DSSScenario.get_definition is deprecated, please use get_settings", DeprecationWarning)
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix))

    def set_definition(self, definition, with_status=True):
        """
        Update the definition of this scenario.

        .. attention::

            Deprecated, use :meth:`get_settings` and :meth:`DSSScenarioSettings.save`

        :param dict definition: a scenario definition obtained by calling :meth:`get_definition()`, then modified
        :param bool with_status: should be the same as the value passed to :meth:`get_definition()`. If True, the only 
                                 fields that can be modified are active, checklists, description, shortDesc and tags
        """
        warnings.warn("DSSScenario.set_definition is deprecated, please use get_settings", DeprecationWarning)
        suffix = '/light' if with_status else ''
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s%s" % (self.project_key, self.id, suffix), body = definition)

    def get_payload(self, extension='py'):
        """
        Get the payload of the scenario.
        
        .. attention::

            Deprecated, use :meth:`get_settings` and :meth:`get_status`
        
        :param string extension: the type of script. Default is 'py' for python
        """
        warnings.warn("DSSScenario.get_payload is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
            "GET", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id), body = {'extension' : extension}).get('script', '')

    # used to have a with_status parameter, that was unused and had a default value, so was likely never used by callers
    def set_payload(self, script, extension='py'):
        """
        Update the payload of this scenario.

        .. attention::

            Deprecated, use :meth:`get_settings` and :meth:`DSSScenarioSettings.save`
        
        :param string script: the new value of the script
        :param string extension: the type of script. Default is 'py' for python
        """
        warnings.warn("DSSScenario.set_payload is deprecated, please use get_settings", DeprecationWarning)
        return self.client._perform_json(
            "PUT", "/projects/%s/scenarios/%s/payload" % (self.project_key, self.id), body = {'script' : script, 'extension' : extension})

class DSSScenarioStatus(object):
    """
    Status of a scenario. 

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.get_status()`
    """

    def __init__(self, scenario, data):
        self.scenario = scenario
        self.data = data

    def get_raw(self):
        """
        Get the raw status data.

        :return: the status, as a dict with fields:

                    * **projectKey** and **id** : identifiers of the scenario
                    * **name** : name of the scenario, can be distinct from **id**
                    * **shortDesc** : short description of the scenario
                    * **description** : longer description of the scenario, can use markdown
                    * **tags** : list of tags, each one a string
                    * **type** : type of scenario. Possible values are 'custom_python' and 'step_based'
                    * **active** : whether the scenario runs its automatic triggers
                    * **automationLocal** : on automation nodes, flag indicating that the scenario was created on the automation node, as opposed to having been imported via a bundle.
                    * **runAsUser** : login of the user that the scenario runs as. If empty, runs as the last user who modified the scenario
                    * **interest** : watches and stars on the scenario, as a dict
                    * **createdBy** : user who created the scenario, as a dict with fields **login** and **displayName**
                    * **createdOn** : timestamp of creation of the scenario, in milliseconds
                    * **lastModifiedBy** : user who last modified the scenario, as a dict with fields **login** and **displayName**
                    * **lastModifiedOn** : timestamp of last modification of the scenario, in milliseconds
                    * **triggerDigestItems** : list of summaries of the triggers, each one a dict:

                        * **name** : name of the trigger
                        * **description** : description of the trigger
                        * **active** : whether the trigger is active
                        * **nextRun** : for active time-based triggers, the expected timestamp of the next scenario run it will initiate

                    * **triggerDigest** : friendly display of the concatenation of the contents of **triggerDigestItems**
                    * **nextRun** : expected timestamp of the next scenario run that active time-based triggers will initiate
                    * **running** : whether the scenario is currently running
                    * **start** : if the scenario is running, the timestamp of the beginning of the run
                    * **futureId** : identifier of the thread running the scenario in the DSS backend. Can be used to instantiate a :class:`dataikuapi.dss.future.DSSFuture`
                    * **trigger** : if the scenario is running, the trigger fire that initiated it, as a dict (see :meth:DSSTriggerFire.get_raw()`)

        :rtype: dict
        """
        return self.data

    @property
    def running(self):
        """
        Whether the scenario is currently running

        :rtype: boolean
        """
        return self.data["running"]

    @property
    def next_run(self):
        """
        Time at which the scenario is expected to run next.

        This expected time is computed based on the only triggers for which forecasts
        are possible, that is, the active time-based triggers. May be None if there is 
        no such trigger.

        This is an approximate indication as scenario run may be delayed, especially in the case of 
        multiple triggers or high load.

        :rtype: :class:`datetime.datetime`
        """
        if not "nextRun" in self.data or self.data["nextRun"] == 0:
            return None
        return datetime.fromtimestamp(self.data["nextRun"] / 1000)


class DSSScenarioSettings(object):
    """
    Settings of a scenario. 

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.get_settings()`
    """
    def __init__(self, client, scenario, data):
        self.client = client
        self.scenario = scenario
        self.data = data

    def get_raw(self):
        """
        Get the raw definition of the scenario.

        This method returns a reference to the settings, not a copy. Modifying the settings then
        calling :meth:`save()` saves the changes made.

        :return: the scenario, as a dict with fields:

                    * **projectKey** and **id** : identifiers of the scenario
                    * **name** : name of the scenario, can be distinct from **id**
                    * **type** : type of scenario. Possible values are 'custom_python' and 'step_based'
                    * **shortDesc** : short description of the scenario
                    * **description** : longer description of the scenario, can use markdown
                    * **tags** : list of tags, each one a string
                    * **checklists** : definition of checklists on the scenario, as a dict
                    * **params** : type-specific parameters of the scenario, as dict
                    * **active** : whether the scenario runs its automatic triggers
                    * **automationLocal** : on automation nodes, flag indicating that the scenario was created on the automation node, as opposed to having been imported via a bundle.
                    * **runAsUser** : login of the user that the scenario runs as. If empty, runs as the last user who modified the scenario
                    * **delayedTriggersBehavior** : settings for the behavior of triggers firing while the scenario is running, as a dict of:

                        * **delayWhileRunning** : if True, run the scenario again after the current run is done. If False, dismiss the trigger fire
                        * **squashDelayedTriggers** : if True, when several triggers fire during a scenario run, run of the scenario only once afterwards. If False, run as many times as there were trigger fires.
                        * **suppressTriggersWhileRunning** : if True, triggers simply don't evaluate while the scenario runs

                    * **triggers** : list of the automatic triggers, see :meth:`raw_triggers()`
                    * **reporters** : list of reporters on the scenario, see :meth:`raw_reporters()`

        :rtype: dict
        """
        return self.data

    @property 
    def active(self):
        """
        Whether this scenario is currently active, i.e. its auto-triggers are executing.

        :rtype: boolean
        """
        return self.data["active"]
    @active.setter
    def active(self, active):
        self.data["active"] = active

    @property 
    def run_as(self):
        """
        Get the login of the user the scenario runs as.

        None means that the scenario runs as the last user who modified the scenario. Only 
        administrators may set a non-None value.

        :rtype: string
        """
        return self.data.get("runAsUser", None)
    @run_as.setter
    def run_as(self, run_as):
        self.data["runAsUser"] = run_as

    @property
    def effective_run_as(self):
        """
        Get the effective 'run as' of the scenario. 

        If the value returned by :meth:`run_as()` is not None, then that value. Otherwise, this
        will be the login of the last user who modified the scenario.

        .. note::

            If this method returns None, it means that it was not possible to identify who this
            scenario should run as. This scenario is probably not currently functioning.

        :rtype: string
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
        """
        Get the list of automatic triggers.

        This method returns a reference to the settings, not a copy. Modifying the settings then
        calling :meth:`save()` saves the changes made.

        :return: list of the automatic triggers, each one a dict of:

                        * **id** : identifier of the trigger within the scenario
                        * **type** : type of the trigger
                        * **name** : label of the trigger, distinct from **id** (which is often auto-generated)
                        * **description** : description of the trigger
                        * **active** : if False, the trigger is disabled
                        * **delay** : (deprecated) delay between the time when the trigger fires, and the time a scenario run is requested
                        * **graceDelaySettings** : additional settings for the delaying of the scenario run w.r.t. the trigger fire, as a dict of:

                            * **delay** : delay between the time when the trigger fires, and the time a scenario run is requested
                            * **checkAgainAfterGraceDelay** : if True, the trigger is evaluated again after the delay, and if the trigger fires again, the delay is reset

                        * **params** : type-specific parameters of the trigger
        :rtype: list[dict]
        """
        return self.data["triggers"]

    @property
    def raw_reporters(self):
        """
        Get the list of reporters.

        This method returns a reference to the settings, not a copy. Modifying the settings then
        calling :meth:`save()` saves the changes made.

        :return: list of reporters on the scenario, each one a dict of:

                        * **id** : identifier of the reporter
                        * **name** : label of the reporter
                        * **description** : description of the reporter
                        * **active** : if False, the reporter is disabled and will not send messages
                        * **runConditionEnabled** : if True, the reporter only runs if the **runCondition** evaluates to True
                        * **runCondition** : a condition to check to send the message
                        * **phase** : when the reporter is run. Possible values are START and END (of the scenario run)
                        * **messaging** : definition of how to send the message as a dict of:

                            * **type** : type of message to send, for example 'mail-scenario' or 'slack-scenario'
                            * **configuration** : type-specific parameters for how to produce and send the message, as a dict
        :rtype: list[dict]
        """
        return self.data["reporters"]

    def add_periodic_trigger(self, every_minutes=5):
        """
        Add a trigger that runs the scenario every X minutes.

        :param int every_minutes: interval between activations of the trigger, in minutes
        """
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Minutely", "repeatFrequency": every_minutes }}
        self.raw_triggers.append(trigger)

    def add_hourly_trigger(self, minute_of_hour=0, year=None, month=None, day=None, starting_hour=0, repeat_every=1, timezone="SERVER"):
        """
        Add a trigger that runs the scenario every X hours.

        :param int repeat_every: interval between activations of the trigger, in hours
        :param int minute_of_hour: minute in the hour when the trigger should run
        :param int year: year part of the date/time before which the trigger won't run
        :param int month: month part of the date/time before which the trigger won't run
        :param int day: day part of the date/time before which the trigger won't run
        :param int starting_hour: hour part of the date/time before which the trigger won't run
        :param string timezone: timezone in which the start date/time is expressed. Can be a time zone name like "Europe/Paris" or 
                                "SERVER" for the time zone of the DSS server
        """
        starting_date =self.__get_starting_date__(year=year, month=month, day=day)
        trigger = {"active": True, "type": "temporal", "params": { "frequency": "Hourly", "hour": starting_hour, "minute": minute_of_hour,
                                                                   "startingFrom": starting_date, "repeatFrequency": repeat_every, "timezone": timezone }}
        self.raw_triggers.append(trigger)

    def add_daily_trigger(self, hour=2, minute=0, days=None, year=None, month=None, day=None, repeat_every=1, timezone="SERVER"):
        """
        Add a trigger that runs the scenario every X days.

        :param int repeat_every: interval between activations of the trigger, in days
        :param list days: if None, the trigger runs every **repeat_every** other day. If set to a list of day names, the trigger
                          runs every **repeat_every** other week, on the designated days. The day names are Monday, Tuesday, 
                          Wednesday, Thursday, Friday, Saturday, Sunday
        :param int hour: hour in the day when the trigger should run
        :param int minute: minute in the hour when the trigger should run
        :param int year: year part of the date/time before which the trigger won't run
        :param int month: month part of the date/time before which the trigger won't run
        :param int day: day part of the date/time before which the trigger won't run
        :param string timezone: timezone in which the start date/time is expressed. Can be a time zone name like "Europe/Paris" or 
                                "SERVER" for the time zone of the DSS server
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
        """
        Add a trigger that runs the scenario every X months.

        :param int repeat_every: interval between activations of the trigger, in months
        :parma string run_on: when in the month the trigger should run. Possible values are ON_THE_DAY, LAST_DAY_OF_THE_MONTH, 
                              FIRST_WEEK, SECOND_WEEK, THIRD_WEEK, FOURTH_WEEK, LAST_WEEK.
        :param int day: day in the day when the trigger should run, when **run_on** is ON_THE_DAY or None
        :param int hour: hour in the day when the trigger should run, when **run_on** is ON_THE_DAY or None
        :param int minute: minute in the hour when the trigger should run, when **run_on** is ON_THE_DAY or None
        :param int minute_of_hour: position in the hour of the firing of the trigger
        :param int year: year part of the date/time before which the trigger won't run
        :param int month: month part of the date/time before which the trigger won't run
        :param string timezone: timezone in which the start date/time is expressed. Can be a time zone name like "Europe/Paris" or 
                                "SERVER" for the time zone of the DSS server
        """
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
        """
        Saves the settings to the scenario
        """
        self.client._perform_json("PUT",
            "/projects/%s/scenarios/%s" % (self.scenario.project_key, self.scenario.id), body = self.data)


class StepBasedScenarioSettings(DSSScenarioSettings):
    """
    Settings of a step-based scenario.

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.get_settings()`.
    """
    @property
    def raw_steps(self):
        """
        Returns raw definition of steps.

        This method returns a reference to the settings, not a copy. Modifying the settings then
        calling :meth:`save()` saves the changes made.

        :return: a list of scenario steps, each one a dict with fields:

                    * **id** : identifier of the step (unique in the scenario)
                    * **name** : label of the step
                    * **description** : description of the step
                    * **type** : type of the step. There are many types, commonly used ones are build_flowitem, custom_python or exec_sql
                    * **params** : type-specific parameters for the step, as a dict
                    * **runConditionType** : type of condition for the step to run. Possible values are:

                        * DISABLED : never run the step
                        * RUN_ALWAYS : always run the step, regardless of the current state of the scenario run (even FAILED)
                        * RUN_IF_STATUS_MATCH : run the step if the scenario run's current state is in **runConditionStatuses**
                        * RUN_CONDITIONALLY : run the step if **runConditionExpression** evaluates to True 

                    * **runConditionStatuses** : list of scenario run states. Possible states are SUCCESS, WARNING, FAILED, ABORTED
                    * **runConditionExpression** : a `GREL formula <https://doc.dataiku.com/dss/latest/formula/index.html>`_ . Can use variables, notably the current run state as '${outcome}'
                    * **maxRetriesOnFail** : how many times to retry the step if it ends in FAILED
                    * **delayBetweenRetries** : delay between retries, in seconds
                    * **resetScenarioStatus** : if True, the state of the scenario run before this step is ignored when computing the state post-step

        :rtype: list[dict]
        """
        return self.data["params"]["steps"]


class PythonScriptBasedScenarioSettings(DSSScenarioSettings):
    """
    Settings of a scenario defined by a Python script.

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.get_settings()`.
    """
    def __init__(self, client, scenario, data, script):
        super(PythonScriptBasedScenarioSettings, self).__init__(client, scenario, data)
        self.script = script

    @property
    def code(self):
        """
        Get the Python script of the scenario

        :rtype: string
        """
        return self.script

    @code.setter
    def code(self, script):
        self.script = script
    
    def save(self):
        """
        Saves the settings to the scenario.
        """
        super(PythonScriptBasedScenarioSettings, self).save()
        self.client._perform_json("PUT",
            "/projects/%s/scenarios/%s/payload" % (self.scenario.project_key, self.scenario.id), body = {'script' : self.script})

class DSSScenarioRun(object):
    """
    A handle containing basic info about a past run of a scenario.

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.get_run()`, :meth:`DSSScenario.get_current_run()`
        or :meth:`DSSScenario.get_last_runs()`

    This handle can also be used to fetch additional information about the run.
    """

    def __init__(self, client, run):
        self.client = client
        self.run = run

    @property
    def id(self):
        """
        Get the identifier of this run.

        :rtype: string
        """
        return self.run["runId"]

    def refresh(self):
        """
        Refresh the details of the run.

        For ongoing scenario runs, this updates the set of outcomes of the steps and 
        their results.

        .. note:: 

            This method performs another API call
        """
        updated_run_details = self.client._perform_json("GET", "/projects/%s/scenarios/%s/%s/" % \
                 (self.run["scenario"]["projectKey"], self.run["scenario"]["id"], self.run["runId"]))
        self.run = updated_run_details["scenarioRun"]

    def wait_for_completion(self, no_fail=False):
        """
        Wait for the scenario run to complete.

        If the scenario run is already finished, this method returns immediately.

        :param boolean no_fail: if False, raises an exception if scenario fails
        """
        while self.running:
            self.refresh()
            time.sleep(5)

        if self.outcome != 'SUCCESS' and no_fail == False:
            raise DataikuException("Scenario run returned status %s" % outcome)

    @property
    def running(self):
        """
        Whether this scenario run is currently running.

        :rtype: boolean
        """
        return not "result" in self.run

    @property
    def outcome(self):
        """
        The outcome of this scenario run, if available.

        :return: one of  SUCCESS, WARNING, FAILED, or ABORTED
        :rtype: string
        """
        if not "result" in self.run:
            raise ValueError("outcome not available for this scenario run. Maybe still running?")
        return self.run["result"]["outcome"]

    @property
    def trigger(self):
        """
        Get the trigger that triggered this scenario run.

        :return: the definition of a trigger, as in the :meth:`DSSScenarioSettings.raw_triggers()` list
        :rtype: dict
        """
        return self.run["trigger"]["trigger"]

    def get_info(self):
        """
        Get the raw information of the scenario run.

        :return: the scenario run, as a dict with fields:

                    * **scenario** : the scenario of this run, as a dict with the same fields as :meth:`DSSScenarioSettings.get_raw()`. In particular, the dict has fields:

                        * **projectKey** and **id** : identifiers of the scenario
                        * **name** : label of the scenario (can be distinct from **id**)
                        * **active** : whether the automatic triggers of this scenario run
                        * **runAsUser** : user that the scenario is configured to run as. If None, le last user that modified the scenario
                        * **type** : type of scenario (step_based or custom_python)

                    * **runId** : identifier of the run of the scenario
                    * **start** : timestamp of the scenario run beginning, in milliseconds
                    * **end** : timestamp of the scenario run end, in milliseconds. Will be 0 if the scenario run is still ongoing
                    * **trigger** : definition of the trigger fire that initiated the scenario run (see :meth:`DSSTriggerFire.get_raw()`)
                    * **result** : if the scenario run is finished, the detailed outcome of the run, as a dict of:

                        * **type** : type of result (should be SCENARIO_DONE in this context)
                        * **outcome** : one of  SUCCESS, WARNING, FAILED, or ABORTED
                        * **target** : definition of which object the result applies to, as a dict. A sub-field **type** indicates which kind of object the **target** is, and additional type-specific fields hold identifiers of the object
                        * **start** : timestamp of the beginning of the operation that produced the result, in milliseconds (the scenario run in this context)
                        * **end** : timestamp of the end of the operation that produced the result, in milliseconds (the scenario run in this context)
                        * **thrown** : if the **outcome** is FAILED, the error that caused the failure, as a dict (see :meth:`DSSStepRunDetails.first_error_details()`)
                        * **logTail** : if the **outcome** is FAILED, the last lines of the log of the operation that produced the result, as a dict of:

                            * **totalLines** : number of lines in the full log (not just in this log tail)
                            * **lines** : list of lines, each a string
                            * **status** : detected log level of each line, as a list of int

                    * **runAsUser** : information about the user that the scenario run effectively runs as, as a dict of:

                        * **authSource** : type of user in DSS. One of USER_FROM_UI, PERSONAL_API_KEY, CONFIGURABLE_API_KEY_GLOBAL, CONFIGURABLE_API_KEY_PROJECT
                        * **apiKey** : for API_KEY authentication sources, the API key as a dict, with at least a **key** field
                        * **realUserLogin** : when **authSource** is USER_FROM_UI, the login of the user

                    * **variables** : variables passed from parent scenario, in situations where a scenario A runs a sub-scenario B, as a dict
                    * **clustersUsed** : list of clusters created by start or attach cluster steps, as a list of dicts with **key** (for the cluster id) and **value** (for the name of the variable in which the cluster id is stored) fields
                    * **reportersStates** : the results of running the reporters of the scenario, as a list of dict. Only reporters that have completed are listed. Sub-fields are:

                        * **reporterName** : label of the reporter
                        * **messagingType** : type of reporter
                        * **activated** : if False, the reporter's run condition prevented it from executing
                        * **error** : if the reporter failed, a dict with the error details.
                        * **messages** : messages outputted while executing the reporter, as a dict with a **messages** field which is a list of messages
                        * **started** : when the reporter started executing, in milliseconds
                        * **ended** : when the reporter was done executing, in milliseconds

        :rtype: dict
        """
        return self.run

    def get_details(self):
        """
        Get the full details of the scenario run.

        This includes notably the individual step runs inside the scenario run.

        .. note:: 

            This method performs another API call

        :return: full details on a scenario run, as a dict with fields:

                    * **scenarioRun** : the run definition and base status, as a dict (see :meth:`get_info()`)
                    * **stepRuns** : details about each step that has executed so far, as a list of dicts (see :meth:`DSSScenarioRunDetails.steps()`)

        :rtype: dict
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
        Get the start time of the scenario run.

        :rtype: :class:`datetime.datetime`
        """
        return datetime.fromtimestamp(self.run['start'] / 1000)
    start_time = property(get_start_time)

    def get_end_time(self):
        """
        Get the end time of the scenario run, if it completed, else raises.

        :rtype: :class:`datetime.datetime`
        """
        if "end" in self.run and self.run["end"] > 0:
            return datetime.fromtimestamp(self.run['end'] / 1000)
        else:
            raise ValueError("Scenario run has not completed")
    end_time = property(get_end_time)

    def get_duration(self):
        """
        Get the duration of this run (in fractional seconds).

        If the run is still running, get the duration since it started.

        :rtype: float
        """
        end_time = datetime.now()
        if self.run['end'] > 0:
            end_time = datetime.fromtimestamp(self.run['end'] / 1000)
        duration = (end_time - self.get_start_time()).total_seconds()
        return duration

    duration = property(get_duration)

class DSSScenarioRunDetails(dict):
    """
    Details of a scenario run, notably the outcome of its steps.

    .. important::

        Do not instantiate directly, see :meth:`DSSScenarioRun.get_details()`
    """
    def __init__(self, data):
        super(DSSScenarioRunDetails, self).__init__(data)

    @property
    def steps(self):
        """
        Get the list of runs of the steps.

        Only completed or ongoing steps are included.

        .. note::

            When the instance of :class:`DSSScenarioRunDetails` was obtained via :meth:`DSSScenarioRun.get_details()`,
            then the returned list is made of instances of :class:`DSSStepRunDetails`.

        :return: a list of step runs, each as a dict with fields:

            * **scenarioRun** : the scenario run to which this step run belongs (see :meth:`DSSScenarioRun.get_info()`)
            * **step** : definition of the step that is running, as a dict (see :meth:`StepBasedScenarioSettings.raw_steps()`)
            * **runId** : unique identifier of the step run within the scenario run
            * **retryIndex** : how many times the step was retried before this step run
            * **start** : timestamp of the step run beginning, in milliseconds
            * **end** : timestamp of the step run end, in milliseconds. Will be 0 if the scenario run is still ongoing
            * **result** : result of the step itself, as a dict:

                * **type** : type of result (should be SCENARIO_DONE in this context)
                * **outcome** : one of  SUCCESS, WARNING, FAILED, or ABORTED
                * **target** : definition of which object the result applies to, as a dict. A sub-field **type** indicates which kind of object the **target** is, and additional type-specific fields hold identifiers of the object
                * **start** : timestamp of the beginning of the operation that produced the result, in milliseconds (the scenario run in this context)
                * **end** : timestamp of the end of the operation that produced the result, in milliseconds (the scenario run in this context)
                * **thrown** : if the **outcome** is FAILED, the error that caused the failure, as a dict (see :meth:`DSSStepRunDetails.first_error_details()`)
                * **logTail** : if the **outcome** is FAILED, the last lines of the log of the operation that produced the result, as a dict of:

                    * **totalLines** : number of lines in the full log (not just in this log tail)
                    * **lines** : list of lines, each a string
                    * **status** : detected log level of each line, as a list of int

            * **additionalReportItems** : additional results that the step can produce, as a list of dict with the structure of **result**. Can be datasets built, jobs runs, ...

        :rtype: list[dict]
        """
        return self["stepRuns"]

    @property
    def last_step(self):
        """
        Get the last step run.

        :return: a step run, as a dict. See :meth:`steps()`.
        :rtype: dict
        """
        return self["stepRuns"][len(self["stepRuns"]) - 1]

    @property
    def first_error_details(self):
        """
        Get the details of the first error if this run failed. 

        This will not always be able to find the error details (it returns None in that case)

        :return: a serialized exception, as in :meth:`DSSStepRunDetails.first_error_details()`
        :rtype: dict
        """
        for step in self.steps:
            step_error = step.first_error_details
            if step_error is not None:
                return step_error


class DSSStepRunDetails(dict):
    """
    Details of a run of a step in a scenario run.

    .. important::

        Do not instantiate directly, see :meth:`DSSScenarioRunDetails.steps()` on an instance
        of :class:`DSSScenarioRunDetails` obtained via :meth:`DSSScenarioRun.get_details()`
    """
    def __init__(self, data):
        super(DSSStepRunDetails, self).__init__(data)

    @property
    def outcome(self):
        """
        Get the outcome of the step run/

        :return: one of  SUCCESS, WARNING, FAILED, or ABORTED
        :rtype: string
        """
        return self["result"]["outcome"]

    @property
    def job_ids(self):
        """
        Get the list of DSS job ids that were run as part of this step.

        :return: a list of job ids, each one a string
        :rtype: list[string]
        """
        return [ri["jobId"] for ri in self["additionalReportItems"] if ri["type"] == "JOB_EXECUTED"]

    @property
    def first_error_details(self):
        """
        Try to get the details of the first error if this step failed. This will not always be able
        to find the error details (it returns None in that case)

        :return: a serialized exception, as a with fields:

            * **clazz** : class name of the exception
            * **title** : short message of the exception
            * **message** : message of the exception
            * **stack** : stacktrace of the exception, as a single string
            * **code** : well-known error code, as listed in `the doc <https://doc.dataiku.com/dss/latest/troubleshooting/errors/index.html>`_
            * **fixability** : type of action to take in order to remediate the issue, if possible. For example USER_CONFIG_DATASET, ADMIN_SETTINGS_SECURITY, ...
        
        :rtype: dict
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
    Helper to wait for a scenario to run to complete.
    """    
    def __init__(self, scenario_run, trigger_fire):
        self.trigger_fire = trigger_fire
        self.scenario_run = scenario_run

    def wait(self, no_fail=False):
        """
        Wait for the scenario run completion.

        :param boolean no_fail: if False, raises if the run doesn't end with a SUCCESS outcome

        :return: the final state of the scenario run (see :meth:`DSSScenarioRun.get_info()`)
        :rtype: dict
        """
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
    A handle representing the firing of a trigger on a scenario. 

    .. important::

        Do not instantiate directly, use :meth:`DSSScenario.run`
    """
    def __init__(self, scenario, trigger_fire):
        self.client = scenario.client
        self.project_key = scenario.project_key
        self.scenario_id = scenario.id
        self.trigger_id = trigger_fire['trigger']['id']
        self.run_id = trigger_fire['runId']
        self.trigger_fire = trigger_fire

    def get_raw(self):
        """
        Get the definition of the trigger fire event.

        :return: the trigger fire, as a dict of:

                    * **trigger** : definition of the trigger which fired, as a dict (see :meth:`DSSScenarioSettings.raw_triggers()`)
                    * **runId** : identifier of the trigger fire. Can be used with :meth:`get_trigger_fire()`
                    * **timestamp** : when the trigger fired (precedes the scenario run start)
                    * **triggerState** : current internal state of the trigger, as a string
                    * **params** : parameters passed by the trigger to the scenario (depend on trigger type), as a dict
                    * **triggerAuthCtx** : for manual runs, identity of the user who started the scenario, as a dict

        """


    def wait_for_scenario_run(self, no_fail=False):
        """
        Poll for the run of the scenario that the trigger fire should initiate.

        This methos waits for the run of the sceanrio that this trigger activation launched to be available, or 
        for the trigger fire to be cancelled (possibly cancelled by another trigger firing).

        :param boolean no_fail: if True, return None if the trigger fire is cancelled, else raise
        
        :return: a handle on a scenario run, or None
        :rtype: :class:`DSSScenarioRun`
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
        Get the run of the scenario that this trigger fire launched. 

        May return None if the scenario run started from this trigger has not yet been created.

        :return: a handle on a scenario run, or None
        :rtype: :class:`DSSScenarioRun`
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
    """
    An item in a list of scenarios. 

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.dss.project.DSSProject.list_scenarios()`
    """
    def __init__(self, client, data):
        super(DSSScenarioListItem, self).__init__(data)
        self.client = client

    def to_scenario(self):
        """
        Get a handle corresponding to this scenario.

        :rtype: :class:`DSSScenario`
        """
        return DSSScenario(self.client, self._data["projectKey"], self._data["id"])

    @property
    def id(self):
        """
        Get the identifier of the scenario.

        :rtype: string
        """
        return self._data["name"]

    @property
    def running(self):
        """
        Whether the scenario is currently running.

        :rtype: boolean
        """
        return self._data["running"]

    @property
    def start_time(self):
        """
        Get the start time of the scenario run.

        :return: timestap of the scenario run start, or None if it's not running at the moment.
        :rtype: :class:`datetime.datetime`
        """
        if self._data['start'] <= 0:
            return None
        else:
            return datetime.fromtimestamp(self._data['start'] / 1000)
