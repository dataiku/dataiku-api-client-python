from .future import DSSFuture


class DSSProjectDeployer(object):
    """
    Handle to interact with the Project Deployer.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_projectdeployer()`
    """
    def __init__(self, client):
        self.client = client

    def list_deployments(self, as_objects=True):
        """
        List deployments on the Project Deployer.

        Usage example:

        .. code-block:: python

            # list all deployments with their current state
            for deployment in deployer.list_deployments():
                status = deployment.get_status()
                print("Deployment %s is %s" % (deployment.id, status.get_health()))            

        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerDeployment`, else returns a list of dict.

        :returns: list of deployments, either as :class:`DSSProjectDeployerDeployment` or as dict (with fields 
                  as in :meth:`DSSProjectDeployerDeploymentStatus.get_light()`)
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/deployments")
        if as_objects:
            return [DSSProjectDeployerDeployment(self.client, x["deploymentBasicInfo"]["id"]) for x in l]
        else:
            return l

    def get_deployment(self, deployment_id):
        """
        Get a handle to interact with a deployment.

        :param string deployment_id: identifier of a deployment

        :rtype: :class:`DSSProjectDeployerDeployment`
        """
        return DSSProjectDeployerDeployment(self.client, deployment_id)

    def create_deployment(self, deployment_id, project_key, infra_id, bundle_id,
                          deployed_project_key=None, project_folder_id=None, ignore_warnings=False):
        """
        Create a deployment and return the handle to interact with it. 

        The returned deployment is not yet started and you need to call :meth:`~DSSProjectDeployerDeployment.start_update`

        Usage example:

        .. code-block:: python

            # create and deploy a bundle
            project = 'my-project'
            infra = 'my-infra'
            bundle = 'my-bundle'
            deployment_id = '%s-%s-on-%s' % (project, bundle, infra)
            deployment = deployer.create_deployment(deployment_id, project, infra, bundle)
            update = deployment.start_update()
            update.wait_for_result()

        :param string deployment_id: identifier of the deployment to create
        :param string project_key: key of the published project
        :param string bundle_id: identifier of the bundle to deploy
        :param string infra_id: identifier of the infrastructure to use
        :param string deployed_project_key: The project key to use when deploying this project to the automation node. If
                                            not set, the project will be created with the same project key as the published project
        :param string project_folder_id: The automation node project folder id to deploy this project into. If not set,
                                         the project will be created in the root folder
        :param boolean ignore_warnings: ignore warnings concerning the governance status of the bundle to deploy

        :return: a new deployment
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
        List the possible stages for infrastructures.

        :return: list of stages. Each stage is returned as a dict with fields:

                    * **id** : identifier of the stage
                    * **desc** : description of the stage

        :rtype: list[dict]
        """
        return self.client._perform_json("GET", "/project-deployer/stages")

    def list_infras(self, as_objects=True):
        """
        List the infrastructures on the Project Deployer.

        Usage example:

        .. code-block:: python

            # list infrastructures that the user can deploy to
            for infrastructure in deployer.list_infras(as_objects=False):
                if infrastructure.get("canDeploy", False):
                    print("User can deploy to %s" % infrastructure["infraBasicInfo"]["id"])            

        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerInfra`, else returns a list of dict.

        :return: list of infrastructures, either as :class:`DSSProjectDeployerInfra` or as dict (with fields 
                 as in :meth:`DSSProjectDeployerInfraStatus.get_raw()`)
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/infras")
        if as_objects:
            return [DSSProjectDeployerInfra(self.client, x["infraBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_infra(self, infra_id, stage, govern_check_policy="NO_CHECK"):
        """
        Create a new infrastructure and returns the handle to interact with it.

        :param string infra_id: unique identifier of the infrastructure to create
        :param string stage: stage of the infrastructure to create
        :param string govern_check_policy: what actions with Govern the the deployer will take whe bundles are deployed on this infrastructure. Possible values: PREVENT, WARN, or NO_CHECK

        :return: a new infrastructure
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
        Get a handle to interact with an infrastructure.

        :param string infra_id: identifier of the infrastructure to get

        :rtype: :class:`DSSProjectDeployerInfra`
        """
        return DSSProjectDeployerInfra(self.client, infra_id)

    def list_projects(self, as_objects=True):
        """
        List published projects on the Project Deployer.

        Usage example:

        .. code-block:: python

            # list project that the user can deploy bundles from
            for project in deployer.list_projects(as_objects=False):
                if project.get("canDeploy", False):
                    print("User can deploy to %s" % project["projectBasicInfo"]["id"])            


        :param boolean as_objects: if True, returns a list of :class:`DSSProjectDeployerProject`, else returns a list of dict.

        :return: list of published projects, either as :class:`DSSProjectDeployerProject` or as dict (with fields 
                 as in :meth:`DSSProjectDeployerProjectStatus.get_raw()`)
        :rtype: list
        """
        l = self.client._perform_json("GET", "/project-deployer/projects")
        if as_objects:
            return [DSSProjectDeployerProject(self.client, x["projectBasicInfo"]["id"]) for x in l]
        else:
            return l

    def create_project(self, project_key):
        """
        Create a new published project on the Project Deployer and return the handle to interact with it.

        :param string project_key: key of the project to create

        :rtype: :class:`DSSProjectDeployerProject`
        """
        settings = {
            "publishedProjectKey": project_key
        }
        self.client._perform_json("POST", "/project-deployer/projects", body=settings)
        return self.get_project(project_key)

    def get_project(self, project_key):
        """
        Get a handle to interact with a published project.

        :param string project_key: key of the project to get

        :rtype: :class:`DSSProjectDeployerProject`
        """
        return DSSProjectDeployerProject(self.client, project_key)

    def upload_bundle(self, fp, project_key=None):
        """
        Upload a bundle archive for a project.

        :param file-like fp: a bundle archive (should be a zip)
        :param string project_key: key of the published project where the bundle will be uploaded. If the project does not 
                                   exist, it is created. If not set, the key of the bundle's source project is used.
        """
        if project_key is None:
            params = None
        else:
            params = {
                "projectKey": project_key,
            }
        self.client._perform_empty("POST",
                "/project-deployer/projects/bundles", params=params, files={"file":fp})


###############################################
# Infrastructures
###############################################

class DSSProjectDeployerInfra(object):
    """
    An Automation infrastructure on the Project Deployer.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployer.get_infra`.
    """
    def __init__(self, client, infra_id):
        self.client = client
        self.infra_id = infra_id

    @property
    def id(self):
        """
        Get the unique identifier of the infrastructure.

        :rtype: string
        """
        return self.infra_id

    def get_status(self):
        """
        Get status information about this infrastructure.

        :return: the current status
        :rtype: :class:`DSSProjectDeployerInfraStatus`
        """
        light = self.client._perform_json("GET", "/project-deployer/infras/%s" % (self.infra_id))

        return DSSProjectDeployerInfraStatus(self.client, self.infra_id, light)

    def get_settings(self):
        """
        Get the settings of this infrastructure. 

        :rtype: :class:`DSSProjectDeployerInfraSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/infras/%s/settings" % (self.infra_id))

        return DSSProjectDeployerInfraSettings(self.client, self.infra_id, settings)

    def delete(self):
        """
        Delete this infra.
        
        .. note::

            You may only delete an infra if there are no deployments using it.
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/infras/%s" % (self.infra_id))


class DSSProjectDeployerInfraSettings(object):
    """
    The settings of an Automation infrastructure.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployerInfra.get_settings`

    To modify the settings, modify them in the dict returned by :meth:`get_raw()` then call :meth:`save()`.
    """
    def __init__(self, client, infra_id, settings):
        self.client = client
        self.infra_id = infra_id
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of this infrastracture. 

        This returns a reference to the raw settings, not a copy, so changes made to the returned 
        object will be reflected when saving.

        :return: the settings, as a dict with fields:

                    * **id** : unique identifier of the infrastructure
                    * **stage** : name of the stage of the infrastructure
                    * **governCheckPolicy** : what actions with Govern the deployer will take when bundles are deployed on this infrastructure. Possible values: PREVENT, WARN, or NO_CHECK
                    * **autoconfigureFromNodesDirectory** : whether this infrastructure is automatically setup according to what's in the fleet
                    * **nodeId** : when configured from a fleet, the name of the automation node in the fleet
                    * **automationNodeUrl** : URL of the automation node that this infrastructure points to
                    * **automationNodeExternalUrl** : externally-accessible URL of the automation node that this infrastructure points to
                    * **adminApiKey** : API key used to communicate with the automation node
                    * **trustAllSSLCertificates** : whether to verify SSL certificates when communicating with the automation node
                    * **permissions** : list of permissions per group, each as a dict of:

                        * **group** : name of the group being granted the permissions
                        * **admin** : whether the group can administer the infrastructure
                        * **read** : whether the group can see the deployments running on the infrastructure                        
                        * **deploy** : whether the group can create deployments on the infrastructure

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Save back these settings to the infrastracture.
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/infras/%s/settings" % (self.infra_id),
                body = self.settings)


class DSSProjectDeployerInfraStatus(object):
    """
    The status of an Automation infrastructure.

    .. important::

        Do not instantiage directly, use :meth:`DSSProjectDeployerInfra.get_status`
    """
    def __init__(self, client, infra_id, light_status):
        self.client = client
        self.infra_id = infra_id
        self.light_status = light_status

    def get_deployments(self):
        """
        Get the deployments that are deployed on this infrastructure.

        :return: a list of deployments
        :rtype: list of :class:`DSSProjectDeployerDeployment`
        """
        return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]

    def get_raw(self):
        """
        Get the raw status information. 

        :return: the status, as a dict with fields:

                    * **isAdmin** : whether the user can administer the infrastructure
                    * **canDeploy** : whether the user can deploy bundles on the infrastructure
                    * **infraBasicInfo** : summary of the infrastructure, as a dict with fields:

                        * **id** : unique identifier of the infrastructure
                        * **stage** : name of the stage of the infrastructure
                        * **governCheckPolicy** : what actions with Govern the deployer will take when bundles are deployed on this infrastructure. Possible values: PREVENT, WARN, or NO_CHECK
                        * **automationNodeUrl** : URL of the automation node that this infrastructure points to
                        * **automationNodeExternalUrl** : externally-accessible URL of the automation node that this infrastructure points to

                    * **deployments** : list of summaries of the deployments on the infrastructure, as a list of dict with fields:

                        * **id** : identifier of the deployment
                        * **infraId** : identifier of the infrastructure
                        * **tags** : list of tags, each a string
                        * **createdByDisplayName** : login of the user who created the deployment
                        * **lastModifiedByDisplayName** : login of the user who last modified the deployment
                        * **publishedProjectKey** : key of the published project of the deployment
                        * **bundleId** : identifier of the bundle of the published project that the deployment pushes onto the automation node
                        * **deployedProjectKey** : key of the remote project that this deployment is pushed to

        :rtype: dict
        """
        return self.light_status

###############################################
# Deployments
###############################################


class DSSProjectDeployerDeployment(object):
    """
    A deployment on the Project Deployer.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployer.get_deployment`
    """
    def __init__(self, client, deployment_id):
        self.client = client
        self.deployment_id = deployment_id

    @property
    def id(self):
        """
        Get the identifier of the deployment.

        :rtype: string
        """
        return self.deployment_id

    def get_status(self):
        """
        Get status information about this deployment.

        :rtype: dataikuapi.dss.apideployer.DSSProjectDeployerDeploymentStatus
        """
        light = self.client._perform_json("GET", "/project-deployer/deployments/%s" % (self.deployment_id))
        heavy = self.client._perform_json("GET", "/project-deployer/deployments/%s/status" % (self.deployment_id))

        return DSSProjectDeployerDeploymentStatus(self.client, self.deployment_id, light, heavy)

    def get_governance_status(self, bundle_id=""):
        """
        Get the governance status about this deployment.

        The infrastructure on which this deployment is running needs to have a Govern check policy of
        PREVENT or WARN.

        :param string bundle_id: (Optional) The ID of a specific bundle of the published project to get status from. If empty, the bundle currently used in the deployment.

        :return: messages about the governance status, as a dict with a **messages** field, itself a list of meassage 
                 information, each one a dict of:

                    * **severity** : severity of the error in the message. Possible values are SUCCESS, INFO, WARNING, ERROR
                    * **isFatal** : for ERROR **severity**, whether the error is considered fatal to the operation
                    * **code** : a string with a well-known code documented in `DSS doc <https://doc.dataiku.com/dss/latest/troubleshooting/errors/index.html>`_
                    * **title** : short message
                    * **message** : the error message
                    * **details** : a more detailed error description

        :rtype: dict 
        """
        return self.client._perform_json("GET", "/project-deployer/deployments/%s/governance-status" % (self.deployment_id), params={ "bundleId": bundle_id })

    def get_settings(self):
        """
        Get the settings of this deployment. 

        :rtype: :class:`DSSProjectDeployerDeploymentSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/deployments/%s/settings" % (self.deployment_id))

        return DSSProjectDeployerDeploymentSettings(self.client, self.deployment_id, settings)

    def start_update(self):
        """
        Start an asynchronous update of this deployment.

        After the update, the deployment should be matching the actual state to the current settings.

        :returns: a handle on the update operation
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_response = self.client._perform_json(
            "POST", "/project-deployer/deployments/%s/actions/update" % (self.deployment_id))

        return DSSFuture(self.client, future_response.get('jobId', None), future_response)

    def delete(self):
        """
        Deletes this deployment

        .. note::

            You may only delete a deployment if it is disabled and has been updated after disabling it.
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/deployments/%s" % (self.deployment_id))


class DSSProjectDeployerDeploymentSettings(object):
    """
    The settings of a Project Deployer deployment.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployerDeployment.get_settings`

    To modify the settings, modify them in the dict returned by :meth:`get_raw()`, or change the value of
    :meth:`bundle_id()`, then call :meth:`save()`.
    """
    def __init__(self, client, deployment_id, settings):
        self.client = client
        self.deployment_id = deployment_id
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of this deployment. 

        This returns a reference to the raw settings, not a copy, so changes made to the returned 
        object will be reflected when saving.

        :return: the settings, as a dict of: 

                    * **id** : identifier of the deployment
                    * **infraId** : identifier of the infrastructure on which the deployment is done
                    * **tags** : list of tags, each one a string
                    * **publishedProjectKey** : key of the published project on the Project Deployer
                    * **bundleId** : identifier of the bundle of the published project being deployed 
                    * **deployedProjectKey** : key of the project the deployment is deployed to on the automation node
                    * **projectFolderId** : identifier of the project folder on the automation node
                    * **bundleContainerSettings** : bundle settings on the automation node, as a dict of:

                        * **remapping** : remapping settings for connections and code envs for the bundle on the automation node, as a dict with fields:

                            * **connections** : list of remappings, each a dict of **source** and **target** fields holding connection names
                            * **codeEnvs** : list of remappings, each a dict of **source** and **target** fields holding code env names

                        * **codeEnvsBehavior** : defines the behavior w.r.t. code envs used by the bundle, as a dict of:

                            * **importTimeMode** : one of INSTALL_IF_MISS, FAIL_IF_MISS or DO_NOTHING
                            * **envImportSpecificationMode** : one of SPECIFIED or ACTUAL

                    * **localVariables** : override to the project local variables on the automation node, as a dict
                    * **scenariosToActivate** : dict of scenario name to boolean, controlling which scenarios of the bundle are (de)activated upon deployment
                    * **disableAutomaticTriggers** : whether the automatic triggers in the scenario should be all deactivated after the deployment

        :rtype: dict
        """
        return self.settings

    @property
    def bundle_id(self):
        """
        Get or set the identifier of the bundle currently used by this deployment. 

        If setting the value, you need to call :meth:`save()` afterward for the change to be effective.
        """
        return self.settings["bundleId"]

    @bundle_id.setter
    def bundle_id(self, new_bundle_id):
        self.settings["bundleId"] = new_bundle_id

    def save(self, ignore_warnings=False):
        """
        Save back these settings to the deployment.

        :param boolean ignore_warnings: whether to ignore warnings concerning the governance status of the bundle to deploy
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/deployments/%s/settings" % (self.deployment_id),
                params = { "ignoreWarnings" : ignore_warnings },
                body = self.settings)


class DSSProjectDeployerDeploymentStatus(object):
    """
    The status of a deployment on the Project Deployer.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployerDeployment.get_status`
    """
    def __init__(self, client, deployment_id, light_status, heavy_status):
        self.client = client
        self.deployment_id = deployment_id
        self.light_status = light_status
        self.heavy_status = heavy_status

    def get_light(self):
        """
        Get the 'light' (summary) status. 

        This returns a dictionary with various information about the deployment, but not the actual health of the deployment

        :returns: a summary, as a dict with fields:

                    * **deploymentBasicInfo** : summary of the definition of the deployment, as a dict of:

                        * **id** : identifier of the deployment
                        * **infraId** : identifier of the infrastructure
                        * **tags** : list of tags, each a string
                        * **createdByDisplayName** : login of the user who created the deployment
                        * **lastModifiedByDisplayName** : login of the user who last modified the deployment
                        * **publishedProjectKey** : key of the published project of the deployment
                        * **bundleId** : identifier of the bundle of the published project that the deployment pushes onto the automation node
                        * **deployedProjectKey** : key of the remote project that this deployment is pushed to

                    * **infraBasicInfo** : summary of the infrastructure on which the deployment is made, as a dict of:

                        * **id** : unique identifier of the infrastructure
                        * **stage** : name of the stage of the infrastructure
                        * **governCheckPolicy** : what actions with Govern the deployer will take when bundles are deployed on this infrastructure. Possible values: PREVENT, WARN, or NO_CHECK
                        * **automationNodeUrl** : URL of the automation node that this infrastructure points to
                        * **automationNodeExternalUrl** : externally-accessible URL of the automation node that this infrastructure points to

                    * **projectBasicInfo** : summary of the published project from where the bundle of this deployment originates, as a dict of:

                        * **id** : key of the project
                        * **name** : name of the project

                    * **packages** : list of bundles in the published project of this deployment (see :meth:`DSSProjectDeployerProjectStatus.get_bundles()`)
                    * **neverEverDeployed** : True if the deployment hasn't yet been deployed

        :rtype: dict
        """
        return self.light_status

    def get_heavy(self):
        """
        Get the 'heavy' (full) status. 

        This returns various information about the deployment, notably its health.

        :return: a status, as a dict with fields:

                    * **deploymentId** : identifier of the deployment
                    * **health** : the current health of the deployment. Possible values: UNKNOWN, ERROR, WARNING, HEALTHY, UNHEALTHY, OUT_OF_SYNC
                    * **healthMessages** : detailed messages of errors or warnings that occurred while checking the health
                    * **monitoring** : information about the scenarios in the project on the automation node, as a dict of:

                        * **hasScenarios** : whether there are scenarios in the project
                        * **hasActiveScenarios** : whether there are active scenarios in the project
                        * **failed** : list of names of the scenarios whose last run ended in failed state
                        * **warning** : list of names of the scenarios whose last run ended in warning state
                        * **successful** : list of names of the scenarios whose last run ended in success state
                        * **aborted** : list of names of the scenarios whose last run was aborted
                        * **running** : list of names of the scenarios currently running

        :rtype: dict
        """
        return self.heavy_status

    def get_health(self):
        """
        Get the health of this deployment.

        :returns: possible values are UNKNOWN, ERROR, WARNING, HEALTHY, UNHEALTHY, OUT_OF_SYNC
        :rtype: string
        """
        return self.heavy_status["health"]

    def get_health_messages(self):
        """
        Get messages about the health of this deployment

        :return: a dict with a **messages** field, which is a list of meassage information, each one a dict of:

                    * **severity** : severity of the error in the message. Possible values are SUCCESS, INFO, WARNING, ERROR
                    * **isFatal** : for ERROR **severity**, whether the error is considered fatal to the operation
                    * **code** : a string with a well-known code documented in `DSS doc <https://doc.dataiku.com/dss/latest/troubleshooting/errors/index.html>`_
                    * **title** : short message
                    * **message** : the error message
                    * **details** : a more detailed error description

        :rtype: dict
        """
        return self.heavy_status["healthMessages"]

###############################################
# Published Project
###############################################

class DSSProjectDeployerProject(object):
    """
    A published project on the Project Deployer.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployer.get_project`
    """
    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    @property
    def id(self):
        """
        Get the key of the published project.

        :rtype: string
        """
        return self.project_key

    def get_status(self):
        """
        Get status information about this published project. 

        This is used mostly to get information about which versions are available and which 
        deployments are exposing this project

        :rtype: :class:`DSSProjectDeployerProjectStatus`
        """
        light = self.client._perform_json("GET", "/project-deployer/projects/%s" % (self.project_key))
        return DSSProjectDeployerProjectStatus(self.client, self.project_key, light)

    def get_settings(self):
        """
        Get the settings of this published project. 

        The main things that can be modified in a project settings are permissions

        :rtype: :class:`DSSProjectDeployerProjectSettings`
        """
        settings = self.client._perform_json(
            "GET", "/project-deployer/projects/%s/settings" % (self.project_key))

        return DSSProjectDeployerProjectSettings(self.client, self.project_key, settings)

    def delete_bundle(self, bundle_id):
        """
        Delete a bundle from this published project.

        :param string bundle_id: identifier of the bundle to delete
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/projects/%s/bundles/%s" % (self.project_key, bundle_id))

    def delete(self):
        """
        Delete this published project.

        .. note::

            You may only delete a published project if there are no deployments using it.
        """
        self.client._perform_empty(
            "DELETE", "/project-deployer/projects/%s" % (self.project_key))


class DSSProjectDeployerProjectSettings(object):
    """
    The settings of a published project.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployerProject.get_settings`

    To modify the settings, modify them in the dict returned by :meth:`get_raw()` then call :meth:`save()`.
    """
    def __init__(self, client, project_key, settings):
        self.client = client
        self.project_key = project_key
        self.settings = settings

    def get_raw(self):
        """
        Get the raw settings of this published project. 

        This returns a reference to the raw settings, not a copy, so changes made to the returned 
        object will be reflected when saving.

        :return: the settings, as a dict with fields:

                        * **id** : key of the project
                        * **name** : name of the project
                        * **owner** : owner of the published project (independent of the owner of the project on the design node)
                        * **permissions** : list of permissions per group, each as a dict of:

                            * **group** : name of the group being granted the permissions
                            * **admin** : whether the group can administer the project
                            * **read** : whether the group can see the published project and deployments of bundles of this project                        
                            * **write** : whether the group can upload new bundles in this published project      
                            * **deploy** : whether the group can create deployments from bundles of this project

                        * **basicImageInfo** : information about the image associated to the project (in project lists, on the project's home, etc...)

        :rtype: dict
        """
        return self.settings

    def save(self):
        """
        Save back these settings to the published project.
        """
        self.client._perform_empty(
                "PUT", "/project-deployer/projects/%s/settings" % (self.project_key),
                body = self.settings)


class DSSProjectDeployerProjectStatus(object):
    """
    The status of a published project.

    .. important::

        Do not instantiate directly, use :meth:`DSSProjectDeployerProject.get_status`
    """
    def __init__(self, client, project_key, light_status):
        self.client = client
        self.project_key = project_key
        self.light_status = light_status

    def get_deployments(self, infra_id=None):
        """
        Get the deployments that have been created from this published project.

        :param string infra_id: (optional) identifier of an infrastructure. When set, only get the deployments deployed on 
                                this infrastructure. When not set, the list contains all the deployments using this published project, 
                                across every infrastructure of the Project Deployer.

        :returns: a list of deployments, each a :class:`DSSProjectDeployerDeployment`
        :rtype: list
        """
        if infra_id is None:
            return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"]]
        return [DSSProjectDeployerDeployment(self.client, deployment["id"]) for deployment in self.light_status["deployments"] if infra_id == deployment["infraId"]]

    def get_bundles(self):
        """
        Get the bundles that have been published on this project.

        Each bundle is a dict that contains at least a "id" field, which is the version identifier

        :returns: a list of bundles, each one a dict of:

                    * **id** : the bundle id
                    * **publishedOn** : timestamp of when the bundle was added to the published project
                    * **publishedBy** : login of the user who added the bundle to the published project
                    * **designNodeInfo** : extra information on the node from which the bundle came, as a dict of

                        * **projectKey** : the key of the project on the source node
                        * **nodeId** : node name in the fleet (if the design node is part of a fleet)
                        * **url** : node url in the fleet (if the design node is part of a fleet)

        :rtype: list[dict]
        """
        return self.light_status["packages"]

    def get_infras(self):
        """
        Get the infrastructures that deployments of this project use.

        :returns: list of summaries of infrastructures, each a dict of:

                    * **id** : unique identifier of the infrastructure
                    * **stage** : name of the stage of the infrastructure
                    * **governCheckPolicy** : what actions with Govern the deployer will take when bundles are deployed on this infrastructure. Possible values: PREVENT, WARN, or NO_CHECK
                    * **automationNodeUrl** : URL of the automation node that this infrastructure points to
                    * **automationNodeExternalUrl** : externally-accessible URL of the automation node that this infrastructure points to

        :rtype: list[dict]
        """
        return self.light_status["infras"]

    def get_raw(self):
        """
        Gets the raw status information. 

        :return: the status, as a dict with fields:

                    * **projectBasicInfo** : summary of the published project, as a dict of:

                        * **id** : key of the project
                        * **name** : name of the project

                    * **isAdmin** : whether the user can administer the published project
                    * **canDeploy** : whether the user can deploy the published project
                    * **canWrite** : whether the user can upload bundles to the published project
                    * **packages** : list of bundles in the published project (see :meth:`get_bundles()`)
                    * **deployments** : list of summaries of the deployments of bundles of the published project, as a list of dict with fields:

                        * **id** : identifier of the deployment
                        * **infraId** : identifier of the infrastructure
                        * **tags** : list of tags, each a string
                        * **createdByDisplayName** : login of the user who created the deployment
                        * **lastModifiedByDisplayName** : login of the user who last modified the deployment
                        * **publishedProjectKey** : key of the published project of the deployment
                        * **bundleId** : identifier of the bundle of the published project that the deployment pushes onto the automation node
                        * **deployedProjectKey** : key of the remote project that this deployment is pushed to

                    * **infras** : list of summaries of infrastructures, for infrastructures appearing in **deployments** (see :meth:`get_infras()`)

        :rtype: dict
        """
        return self.light_status
