import random
import re
import string

from .future import DSSFuture

from .utils import DSSTaggableObjectListItem


def random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

class DSSAppListItem(DSSTaggableObjectListItem):
    """
    An item in a list of apps. 

    .. important::

        Do not instantiate this class, use :meth:`dataikuapi.DSSClient.list_apps` instead
    """
    def __init__(self, client, data):
        super(DSSAppListItem, self).__init__(data)
        self.client = client

    def to_app(self):
        """
        Get a handle corresponding to this app.

        :return: a handle to interact with the app
        :rtype: :class:`dataikuapi.dss.app.DSSApp`
        """
        return DSSApp(self.client, self._data["appId"])

class DSSApp(object):
    """
    A handle to interact with an application on the DSS instance.

    .. important::
    
        Do not instantiate this class directly, instead use :meth:`dataikuapi.DSSClient.get_app`

    """
    def __init__(self, client, app_id):
        self.client = client
        self.app_id = app_id

    ########################################################
    # Instances
    ########################################################

    def create_instance(self, instance_key, instance_name, wait=True):
        """
        Create a new instance of this application. 

        Each instance must have a globally unique instance key, separate from any other project
        key across the whole DSS instance.

        :param string instance_key: project key for the new created app instance
        :param string instance_name: name for the new created app instance
        :param boolean wait: if False, the method returns immediately with a :class:`dataikuapi.dss.future.DSSFuture`
                             on which to wait for the app instance to be created

        :return: a handle to interact with the app instance
        :rtype: :class:`~DSSAppInstance`
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
        """
        Create a new project key based on this app name.

        This method suffixes the app's name with a random string to generate a 
        unique app instance key.

        :return: a project key
        :rtype: string
        """
        slugified_app_id = re.sub(r'[^A-Za-z_0-9]+', '_', self.app_id)
        return "%s_tmp_%s" % (slugified_app_id, random_string(10))

    def create_temporary_instance(self):
        """
        Create a new temporary instance of this application.

        The return value should be used as a Python context manager. Upon exit, the temporary app
        instance is deleted.
        
        :return: an app instance
        :rtype: :class:`TemporaryDSSAppInstance`
        """
        key = self.make_random_project_key()
        self.create_instance(key, key, True)
        return TemporaryDSSAppInstance(self.client, key)

    def list_instance_keys(self):
        """
        List the keys of the existing instances of this app.

        :return: a list of instance keys
        :rtype: list[string]
        """
        return [x["projectKey"] for x in self.list_instances()]

    def list_instances(self):
        """
        List the existing instances of this app.
        
        :return a list of instances, each as a dict containing at least a "projectKey" field
        :rtype: list
        """
        return self.client._perform_json(
            "GET", "/apps/%s/instances/" % self.app_id)

    def get_instance(self, instance_key):
        """
        Get a particular instance of this app.

        :return: an app instance
        :rtype: :class:`~DSSAppInstance`
        """
        return DSSAppInstance(self.client, instance_key)

    def get_manifest(self):
        """
        Get the manifest of this app.

        :return: an app manifest
        :rtype: :class:`~DSSAppManifest`
        """
        raw_data = self.client._perform_json("GET", "/apps/%s/" % self.app_id)
        project_key = self.app_id[8:] if self.app_id.startswith('PROJECT_') else None
        return DSSAppManifest(self.client, raw_data, project_key)


class DSSAppManifest(object):
    """
    Handle on the manifest of an app or an app instance.

    .. important::

        Do not instantiate this class directly, use :meth:`dataikuapi.dss.app.DSSApp.get_manifest()` or
        :meth:`dataikuapi.dss.app.DSSAppInstance.get_manifest()`

    """

    def __init__(self, client, raw_data, project_key=None):
        self.client = client
        self.raw_data = raw_data
        self.project_key = project_key

    def get_raw(self):
        """
        Get the raw definition of the manifest.

        Usage example:

        .. code-block:: python

            # list all app templates that anybody can instantiate
            for app in client.list_apps(as_type="objects"):
                manifest = app.get_manifest()
                if manifest.get_raw()["instantiationPermission"] == 'EVERYBODY':
                    print(app.app_id)            

        :return: the definition of the manifest, as a dict. The definitions of the tiles of the app are inside
                 the **homepageSections** field, which is a list of the sections displayed in the app. When the 
                 app is an app-as-recipe, the field **useAsRecipeSettings** is defined and contains the recipe-specific
                 settings.

        :rtype: dict
        """
        return self.raw_data

    def get_all_actions(self):
        """
        Get the flat list of all actions.

        :return: a list of action defintions, each one a dict. Each action has fields

                            * **type** : the type of the action
                            * **prompt** : label of the action in the form
                            * **help** and **helpTitle** : metadata for showing a help button on the action
                            * ... and additional fields depending on the type, to hold the action's setup

        :rtype: list
        """
        return [x for section in self.raw_data["homepageSections"] for x in section["tiles"]]

    def get_runnable_scenarios(self):
        """
        Get the scenario identifiers that are declared as actions for this app.

        :return: a list of scenario identifiers
        :rtype: list[string]
        """
        return [x["scenarioId"] for x in self.get_all_actions() if x["type"] == "SCENARIO_RUN"]

    def save(self):
        """
        Save the changes to this manifest object back to the template project.
        """
        if self.project_key is None:
            raise Exception("This manifest object wasn't created from a project, cannot be saved back")
        self.client._perform_empty("PUT", "/projects/%s/app-manifest" % self.project_key, body=self.raw_data)


class DSSAppInstance(object):
    """
    Handle on an instance of an app.

    .. important::

        Do not instantiate this class directly, use :meth:`dataikuapi.dss.app.DSSApp.get_instance()`
    """

    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def get_as_project(self):
        """
        Get a handle on the project corresponding to this application instance.

        :return: a handle on a DSS prohect
        :rtype: :class:`dataikuapi.dss.project.DSSProject`
        """
        return self.client.get_project(self.project_key)

    def get_manifest(self):
        """
        Get the manifest of this app instance.

        :return: an app manifest
        :rtype: :class:`~DSSAppManifest`
        """
        raw_data = self.client._perform_json("GET", "/projects/%s/app-manifest" % self.project_key)
        return DSSAppManifest(self.client, raw_data)


class TemporaryDSSAppInstance(DSSAppInstance):
    """
    Variant of :class:`~DSSAppInstance` that can be used as a Python context.

    .. important::

        Do not instantiate this class directly, use :meth:`dataikuapi.dss.app.DSSApp.create_temporary_instance()`
    """

    def __init__(self, client, project_key):
        DSSAppInstance.__init__(self, client,project_key)

    def close(self):
        """
        Delete the app instance.
        """
        self.get_as_project().delete(clear_managed_datasets=True)

    def __enter__(self,):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
