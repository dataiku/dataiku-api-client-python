import random
import re
import string

from .future import DSSFuture


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


class DSSApp(object):
    """
    A handle to interact with an application on the DSS instance.
    Do not create this class directly, instead use :meth:`dataikuapi.DSSClient.get_app`
    """
    def __init__(self, client, app_id):
        self.client = client
        self.app_id = app_id

    ########################################################
    # Instances
    ########################################################

    def create_instance(self, instance_key, instance_name, wait=True):
        """
        Creates a new instance of this application. Each instance. must have a globally unique
        instance key, separate from any project key across the whole DSS instance

        :return: 
        """
        future_resp = self.client._perform_json(
            "POST", "/apps/%s/instances" % self.app_id, body={
                "targetProjectKey": instance_key,
                "targetProjectName": instance_name
            })
        future = DSSFuture(self.client, future_resp.get("jobId", None), future_resp)
        if wait:
            future.wait_for_result()
            return DSSAppInstance(self.client, instance_key)
        else:
            return future

    def make_random_project_key(self):
        slugified_app_id = re.sub(r'[^A-Za-z_0-9]+', '_', self.app_id)
        return "%s_tmp_%s" % (slugified_app_id, random_string(10))

    def create_temporary_instance(self):
        """
        Creates a new temporary instance of this application.
        The return value should be used as a Python context manager. Upon exit, the temporary app
        instance is deleted
        :return a :class:`TemporaryDSSAppInstance`
        """
        key = self.make_random_project_key()
        self.create_instance(key, key, True)
        return TemporaryDSSAppInstance(self.client, key)

    def list_instance_keys(self):
        """
        List the existing instances of this app

        :return a list of instance keys, each as a string
        """
        return [x["projectKey"] for x in self.list_instances()]

    def list_instances(self):
        """
        List the existing instances of this app
        
        :return a list of instances, each as a dict containing at least a "projectKey" field
        :rtype: list of dicts
        """
        return self.client._perform_json(
            "GET", "/apps/%s/instances/" % self.app_id)

    def get_instance(self, instance_key):
        return DSSAppInstance(self.client, instance_key)

    def get_manifest(self):
        raw_data = self.client._perform_json("GET", "/apps/%s/" % self.app_id)
        project_key = self.app_id[8:] if self.app_id.startswith('PROJECT_') else None
        return DSSAppManifest(self.client, raw_data, project_key)


class DSSAppManifest(object):

    def __init__(self, client, raw_data, project_key=None):
        """The manifest for an application. Do not create this class directly"""
        self.client = client
        self.raw_data = raw_data
        self.project_key = project_key

    def get_raw(self):
        return self.raw_data

    def get_all_actions(self):
        return [x for section in self.raw_data["homepageSections"] for x in section["tiles"]]

    def get_runnable_scenarios(self):
        """Return the scenario identifiers that are declared as actions for this app"""
        return [x["scenarioId"] for x in self.get_all_actions() if x["type"] == "SCENARIO_RUN"]

    def save(self):
        """Saves the changes to this manifest object back to the template project"""
        if self.project_key is None:
            raise Exception("This manifest object wasn't created from a project, cannot be saved back")
        self.client._perform_empty("PUT", "/projects/%s/app-manifest" % self.project_key, body=self.raw_data)


class DSSAppInstance(object):

    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def get_as_project(self):
        """
        Get the :class:`dataikuapi.dss.project DSSProject` corresponding to this application instance
        """
        return self.client.get_project(self.project_key)

    def get_manifest(self):
        """
        Get the application manifest for this instance, as a :class:`DSSAppManifest`
        """
        raw_data = self.client._perform_json("GET", "/projects/%s/app-manifest" % self.project_key)
        return DSSAppManifest(self.client, raw_data)


class TemporaryDSSAppInstance(DSSAppInstance):
    """internal class"""

    def __init__(self, client, project_key):
        DSSAppInstance.__init__(self, client,project_key)

    def close(self):
        self.get_as_project().delete(clear_managed_datasets=True)

    def __enter__(self,):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
