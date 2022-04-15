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

    def create_deployment(self, deployment_id, project_key, infra_id, bundle_id,
                          deployed_project_key=None, project_folder_id=None, ignore_warnings=False):
        """
        Creates a deployment and returns the handle to interact with it. The returned deployment
        is not yet started and you need to call :meth:`~DSSProjectDeployerDeployment.start_update`

        :param str deployment_id: Identifier of the deployment to create
        :param str project_key: The source published project key
        :param str infra_id: Identifier of the deployment infrastructure to use
        :param str bundle_id: Identifier of the bundle to deploy
        :param str deployed_project_key: The project key to use when deploying this project to the automation node. If
                                         not set, the project will be created with the same project key as the source
                                         published project
        :param str project_folder_id: The automation node project folder id to deploy this project into. If not set,
                                      the project will be created in the root folder
        :param boolean ignore_warnings: ignore warnings concerning the governance status of the bundle to deploy
        :rtype: :class:`DSSProjectDeployerDeployment`
        """
        settings = {
            "deploymentId": deployment_id,
            "publishedProjectKey": project_key,
            "infraId": infra_id,
            "bundleId": bundle_id
        }
        if deployed_project_key:
            settings["deployedProjectKey"] = deployed_project_key
        if project_folder_id:
            settings["projectFolderId"] = project_folder_id
        self.client._perform_json("POST", "/project-deployer/deployments", params={"ignoreWarnings": ignore_warnings}, body=settings)
        return self.get_deployment(deployment_id)

    def list_stages(self):
        """
        Lists infrastructure stages of the Project Deployer

        :rtype: list of dict. Each dict contains a field "id" for the stage identifier and "desc" for its description.
        :rtype: list
        """
        return self.client._perform_json("GET", "/project-deployer/stages")

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

    def create_infra(self, infra_id, stage, govern_check_policy="NO_CHECK"):
        """
        Creates a new infrastructure on the Project Deployer and returns the handle to interact with it.

        :param str infra_id: Unique Identifier of the infra to create
        :param str stage: Infrastructure stage
        :param str govern_check_policy: PREVENT, WARN, or NO_CHECK depending if the deployer will check wether the bundle deployed on this infrastructure has to be managed and approved in Dataiku Govern
        :rtype: :class:`DSSProjectDeployerInfra`
        """
        settings = {
            "id": infra_id,
            "stage": stage, 
            "governCheckPolicy": govern_check_policy,
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
            "publishedProjectKey": project_key
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

    def upload_bundle(self, fp, project_key=None):
        """
        Uploads a new version for a project from a file-like object pointing
        to a bundle Zip file.

        :param string fp: A file-like object pointing to a bundle Zip file
        :param string project_key: The key of the published project where the bundle will be uploaded. If the project does not exist, it is created.
        If not set, the key of the bundle's source project is used.

        """
        if project_key is None:
            params = None
        else:
            params = {
                "projectKey": project_key,
            }
        return self.client._perform_empty("POST",
                "/project-deployer/projects/bundles", params=params, files={"file":fp})

###############################################
# Infrastructures
###############################################


class DSSProjectDeployerInfra(object):
    """
    An Automation infrastructure on the Project Deployer

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployer.get_infra`
    """
    def __init__(self, client, infra_id):
        self.client = client
        self.infra_id = infra_id

    @property
    def id(self):
        return self.infra_id

    def get_status(self):
        """
        Returns status information about this infrastructure

        :rtype: :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerInfraStatus`
        """
        light = self.client._perform_json("GET", "/project-deployer/infras/%s" % (self.infra_id))

        return DSSProjectDeployerInfraStatus(self.client, self.infra_id, light)

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
    """
    The settings of an Automation infrastructure.

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
        """
        Saves back these settings to the infra
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/infras/%s/settings" % (self.infra_id),
                body = self.settings)


class DSSProjectDeployerInfraStatus(object):
    """
    The status of an Automation infrastructure.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerInfra.get_status`
    """
    def __init__(self, client, infra_id, light_status):
        self.client = client
        self.infra_id = infra_id
        self.light_status = light_status

    def get_deployments(self):
        """
        Returns the deployments that are deployed on this infrastructure

        :returns: a list of deployments
        :rtype: list of :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerDeployment`
        """
        return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]

    def get_raw(self):
        """
        Gets the raw status information. This returns a dictionary with various information about the infrastructure

        :rtype: dict
        """
        return self.light_status

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

    @property
    def id(self):
        return self.deployment_id

    def get_status(self):
        """
        Returns status information about this deployment

        :rtype: dataikuapi.dss.apideployer.DSSProjectDeployerDeploymentStatus
        """
        light = self.client._perform_json("GET", "/project-deployer/deployments/%s" % (self.deployment_id))
        heavy = self.client._perform_json("GET", "/project-deployer/deployments/%s/status" % (self.deployment_id))

        return DSSProjectDeployerDeploymentStatus(self.client, self.deployment_id, light, heavy)

    def get_governance_status(self, bundle_id=""):
        """
        Returns the governance status about this deployment if applicable

        :param str bundle_id: (Optional) The ID of a specific bundle of the published project to get status from. If empty, consider the bundle currently used in the deployment.
        :rtype: dict InforMessages containing the governance status
        """
        return self.client._perform_json("GET", "/project-deployer/deployments/%s/governance-status" % (self.deployment_id), params={ "bundleId": bundle_id })

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

    @property
    def bundle_id(self):
        """
        Gets or sets the bundle id currently used by this deployment. When setting, you need to call
        :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerDeploymentSettings.save` afterward for the change to be
        effective.
        """
        return self.settings["bundleId"]

    @bundle_id.setter
    def bundle_id(self, new_bundle_id):
        self.settings["bundleId"] = new_bundle_id

    def save(self, ignore_warnings=False):
        """
        Saves back these settings to the deployment

        :param boolean ignore_warnings: ignore warnings concerning the governance status of the bundle to deploy
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/deployments/%s/settings" % (self.deployment_id),
                params = { "ignoreWarnings" : ignore_warnings },
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
        """
        Returns the health of this deployment as a string

        :returns: HEALTHY if the deployment is working properly, various other status otherwise
        :rtype: string
        """
        return self.heavy_status["health"]

    def get_health_messages(self):
        """
        Returns messages about the health of this deployment
        """
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

    @property
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

    def delete_bundle(self, bundle_id):
        """
        Deletes a bundle from this project

        :param string bundle_id: The identifier of the bundle to delete
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/projects/%s/bundles/%s" % (self.project_key, bundle_id))

    def delete(self):
        """
        Deletes this project

        You may only delete a project if it has no deployments on it anymore.
        """
        return self.client._perform_empty(
            "DELETE", "/project-deployer/projects/%s" % (self.project_key))


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
        """
        Saves back these settings to the project
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/projects/%s/settings" % (self.project_key),
                body = self.settings)


class DSSProjectDeployerProjectStatus(object):
    """
    The status of a published project.

    Do not create this directly, use :meth:`~dataikuapi.dss.projectdeployer.DSSProjectDeployerProject.get_status`
    """
    def __init__(self, client, project_key, light_status):
        self.client = client
        self.project_key = project_key
        self.light_status = light_status

    def get_deployments(self, infra_id=None):
        """
        Returns the deployments that have been created from this published project

        :param str infra_id: Identifier of an infra, allows to only keep in the returned list the deployments on this infra.
        If not set, the list contains all the deployments using this published project, across every infra of the Project Deployer.

        :returns: a list of deployments
        :rtype: list of :class:`dataikuapi.dss.projectdeployer.DSSProjectDeployerDeployment`
        """
        if infra_id is None:
            return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]
        return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"] if infra_id == deployment["infraId"]]

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
