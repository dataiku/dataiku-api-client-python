from .future import DSSFuture


class DSSProjectDeployer(object):
    """
    Handle to interact with the Project Deployer.

    Do not create this directly, use :meth:`dataikuapi.dss.DSSClient.get_projectdeployer`
    """
    def __init__(self, client):
        self.client = client

    def list_deployments(self, as_objects=True):
        """
        Lists deployments on the Project Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerDeployment`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this deployment

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/deployments")
        if as_objects:
            return [DSSProjectDeployerDeployment(self.client, x["deploymentBasicInfo"]["id"]) for x in l]
        else:
            return l

    def get_deployment(self, deployment_id):
        """
        Returns a handle to interact with a single deployment, as a :class:`DSSProjectDeployerDeployment`

        :param str deployment_id: Identifier of the deployment to get
        :rtype: :class:`DSSProjectDeployerDeployment`
        """
        return DSSProjectDeployerDeployment(self.client, deployment_id)

    def create_deployment(self, deployment_id, project_key, infra_id, bundle_id):
        """
        Creates a deployment and returns the handle to interact with it. The returned deployment
        is not yet started and you need to call :meth:`~DSSProjectDeployerDeployment.start_update`

        :param str deployment_id: Identifier of the deployment to create
        :param str project_key: Identifier of the published project target
        :param str infra_id: Identifier of the deployment infrastructure to use
        :param str bundle_id: Identifier of the bundle to deploy
        :rtype: :class:`DSSProjectDeployerDeployment`
        """
        settings = {
            "deploymentId" : deployment_id,
            "publishedProjectKey" : project_key,
            "infraId" : infra_id,
            "bundleId" : bundle_id
        }
        self.client._perform_json("POST", "/project-deployer/deployments", body=settings)
        return self.get_deployment(deployment_id)

    def list_infras(self, as_objects=True):
        """
        Lists deployment infrastructures on the Project Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerInfra`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this infra

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/infras")
        if as_objects:
            return [DSSProjectDeployerInfra(self.client, x["infraBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_infra(self, infra_id, stage):
        """
        Creates a new infrastructure on the Project Deployer and returns the handle to interact with it.

        :param str infra_id: Unique Identifier of the infra to create
        :param str stage: Infrastructure stage
        :rtype: :class:`DSSProjectDeployerInfra`
        """
        settings = {
            "id": infra_id,
            "stage": stage
        }
        self.client._perform_json("POST", "/project-deployer/infras", body=settings)
        return self.get_infra(infra_id)

    def get_infra(self, infra_id):
        """
        Returns a handle to interact with a single deployment infra, as a :class:`DSSProjectDeployerInfra`

        :param str infra_id: Identifier of the infra to get
        :rtype: :class:`DSSProjectDeployerInfra`
        """
        return DSSProjectDeployerInfra(self.client, infra_id)

    def list_projects(self, as_objects=True):
        """
        Lists published projects on the Project Deployer

        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerProject`, else returns a list of dict.
                Each dict contains at least a field "id" indicating the identifier of this project

        :returns: a list - see as_objects for more information
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/projects")
        if as_objects:
            return [DSSProjectDeployerProject(self.client, x["projectBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_project(self, project_key):
        """
        Creates a new project on the Project Deployer and returns the handle to interact with it.

        :param str project_key: Identifier of the project to create
        :rtype: :class:`DSSProjectDeployerProject`
        """
        settings = {
            "projectKey" : project_key
        }
        self.client._perform_json("POST", "/project-deployer/projects", body=settings)
        return self.get_project(project_key)

    def get_project(self, project_key):
        """
        Returns a handle to interact with a single project, as a :class:`DSSProjectDeployerProject`

        :param str project_key: Identifier of the project to get
        :rtype: :class:`DSSProjectDeployerProject`
        """
        return DSSProjectDeployerProject(self.client, project_key)


###############################################
# Infrastructures
###############################################


class DSSProjectDeployerInfra(object):
    """
    A Deployment infrastructure on the Project Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployer.get_infra`
    """
    def __init__(self, client, infra_id):
        self.client = client
        self.infra_id = infra_id

    def id(self):
        return self.infra_id

    def get_settings(self):
        """
        Gets the settings of this infra. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerInfraSettings.save` on the returned
        object

        :returns: a :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerInfraSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/infras/%s/settings" % (self.infra_id))

        return DSSProjectDeployerInfraSettings(self.client, self.infra_id, settings)

    def delete(self):
        """
        Deletes this infra
        You may only delete an infra if it has no deployments on it anymore.
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/infras/%s" % (self.infra_id))


class DSSProjectDeployerInfraSettings(object):
    """The settings of a Project Deployer Infra.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerInfra.get_settings`
    """
    def __init__(self, client, infra_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this infra. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """Saves back these settings to the infra"""
        self.client._perform_empty(
                "PUT", "/project-deployer/infras/%s/settings" % (self.infra_id),
                body = self.settings)


###############################################
# Deployments
###############################################


class DSSProjectDeployerDeployment(object):
    """
    A Deployment on the Project Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployer.get_deployment`
    """
    def __init__(self, client, deployment_id):
        self.client = client
        self.deployment_id = deployment_id

    def id(self):
        return self.deployment_id

    def get_status(self):
        """Returns status information about this deployment

        :rtype: dataikuapi.dss.apideployer.DSSProjectDeployerDeploymentStatus
        """
        light = self.client._perform_json("GET", "/project-deployer/deployments/%s" % (self.deployment_id))
        heavy = self.client._perform_json("GET", "/project-deployer/deployments/%s/status" % (self.deployment_id))

        return DSSProjectDeployerDeploymentStatus(self.client, self.deployment_id, light, heavy)

    def get_settings(self):
        """
        Gets the settings of this deployment. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerDeploymentSettings.save` on the returned
        object

        :returns: a :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerDeploymentSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/deployments/%s/settings" % (self.deployment_id))

        return DSSProjectDeployerDeploymentSettings(self.client, self.deployment_id, settings)

    def start_update(self):
        """
        Starts an asynchronous update of this deployment to try to match the actual state to the current settings

        :returns: a :class:`dataikuapi.dss.future.DSSFuture` tracking the progress of the update. Call
                   :meth:`~dataikuapi.dss.future.DSSFuture.wait_for_result` on the returned object
                   to wait for completion (or failure)
        """
        future_response = self.client._perform_json(
            "POST", "/project-deployer/deployments/%s/actions/update" % (self.deployment_id))

        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

    def delete(self):
        """
        Deletes this deployment

        You may only delete a deployment if it is disabled and has been updated after disabling it.
        """
        return self.client._perform_empty(
            "DELETE", "/project-deployer/deployments/%s" % (self.deployment_id))


class DSSProjectDeployerDeploymentSettings(object):
    """The settings of a Project Deployer deployment.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerDeployment.get_settings`
    """
    def __init__(self, client, deployment_id, settings):
        self.client = client
        self.deployment_id = deployment_id
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this deployment. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def set_enabled(self, enabled):
        """Enables or disables this deployment"""
        self.settings["enabled"] = enabled

    def save(self):
        """Saves back these settings to the deployment"""
        self.client._perform_empty(
                "PUT", "/project-deployer/deployments/%s/settings" % (self.deployment_id),
                body = self.settings)


class DSSProjectDeployerDeploymentStatus(object):
    """The status of a Project Deployer deployment.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerDeployment.get_status`
    """
    def __init__(self, client, deployment_id, light_status, heavy_status):
        self.client = client
        self.deployment_id = deployment_id
        self.light_status = light_status
        self.heavy_status = heavy_status

    def get_light(self):
        """
        Gets the 'light' (summary) status. This returns a dictionary with various information about the deployment,
        but not the actual health of the deployment

        :rtype: dict
        """
        return self.light_status

    def get_heavy(self):
        """
        Gets the 'heavy' (full) status. This returns a dictionary with various information about the deployment
        :rtype: dict
        """
        return self.heavy_status

    def get_health(self):
        """Returns the health of this deployment as a string

        :returns: HEALTHY if the deployment is working properly, various other status otherwise
        :rtype: string
        """
        return self.heavy_status["health"]

    def get_health_messages(self):
        """Returns messages about the health of this deployment"""
        return self.heavy_status["healthMessages"]

###############################################
# Published Project
###############################################

class DSSProjectDeployerProject(object):
    """
    A project on the Project Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployer.get_project`
    """
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def id(self):
        return self.project_key

    def get_status(self):
        """
        Returns status information about this project. This is used mostly to get information about
        which versions are available and which deployments are exposing this project

        :rtype: dataikuapi.dss.projectdeployer.DSSProjectDeployerProjectStatus
        """
        light = self.client._perform_json("GET", "/project-deployer/projects/%s" % (self.project_key))
        return DSSProjectDeployerProjectStatus(self.client, self.project_key, light)

    def import_bundle(self, fp, design_node_url=None, design_node_id=None):
        """
        Imports a new version for a project from a file-like object pointing
        to a bundle Zip file.
        :param string fp: A file-like object pointing to a bundle Zip file
        :param string design_node_url: The URL of the Design node where the bundle was created
        :param design_node_id: The identifier of the Design node where the bundle was created
        """
        if design_node_url is None and design_node_id is None:
            params = None
        else:
            params = {
                "nodeId": design_node_id,
                "nodeUrl": design_node_url
            }
        return self.client._perform_empty("POST",
                "/project-deployer/projects/%s/bundles" % (self.project_key), params=params, files={"file":fp})

    def get_settings(self):
        """
        Gets the settings of this project. If you want to modify the settings, you need to
        call :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerProjectSettings.save` on the returned
        object.

        The main things that can be modified in a project settings are permissions

        :returns: a :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerProjectSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/projects/%s/settings" % (self.project_key))

        return DSSProjectDeployerProjectSettings(self.client, self.project_key, settings)


class DSSProjectDeployerProjectSettings(object):
    """The settings of a published project.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerProject.get_settings`
    """
    def __init__(self, client, project_key, settings):
        self.client = client
        self.project_key = project_key
        self.settings = settings

    def get_raw(self):
        """
        Gets the raw settings of this deployment. This returns a reference to the raw settings, not a copy,
        so changes made to the returned object will be reflected when saving.

        :rtype: dict
        """
        return self.settings

    def save(self):
        """Saves back these settings to the project"""
        self.client._perform_empty(
                "PUT", "/project-deployer/projects/%s/settings" % (self.project_key),
                body = self.settings)


class DSSProjectDeployerProjectStatus(object):
    """The status of a published project.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerProject.get_status`
    """
    def __init__(self, client, project_key, light_status):
        self.client = client
        self.project_key = project_key
        self.light_status = light_status

    def get_bundles(self):
        """
        Returns the bundles that have been published on this project

        Each bundle is a dict that contains at least a "id" field, which is the version identifier

        :returns: a list of bundles, each as a dict containing a "id" field
        :rtype: list of dicts
        """
        return self.light_status["packages"]

    def get_raw(self):
        """
        Gets the raw status information. This returns a dictionary with various information about the project
        :rtype: dict
        """
        return self.light_status