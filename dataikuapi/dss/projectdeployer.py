from .future import DSSFuture
from .scenario import DSSTestingStatus

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

    def generate_personal_api_key(self, label, description, for_user = None):
        """
        Generate a personal api key on all the nodes of the infrastructure. Only available for multi automation node infrastructures.

        :param string label: label of the key to create
        :param string description: description of the key to create
        :param string for_user: (Optional) the user for whom the key will be created. If not set, the key will be created for the current user.
                                Requires admin permission on the automation nodes to create a key for another user.

        :return: the key creation result, as a :class:`DSSPersonalAPIKeyCreationResult`
        :rtype: :class:`DSSPersonalAPIKeyCreationResult`
        """
        key_settings = {
            "label": label,
            "description": description,
            "forUser": for_user
        }
        key_creation_result = self.client._perform_json("POST", "/project-deployer/infras/%s/generate-personal-api-key" % self.infra_id, params=key_settings)
        return DSSPersonalAPIKeyCreationResult(key_creation_result)


class DSSPersonalAPIKeyCreationResult(object):
    """
    A handle on the result of the creation of a personal API key on the automation nodes of a Project Deployer multi automation nodes infrastructure

    .. warning::
        Do not instantiate directly, use :meth:`dataikuapi.dss.projectdeployer.DSSProjectDeployerInfra.generate_personal_api_key()`
    """

    def __init__(self, raw):
        self._raw = raw

    @property
    def created_on_all_nodes(self):
        """
        A boolean indicating that the personal API key has been created successfully on all the automation nodes

        :rtype: boolean
        """
        return self._raw["createdOnAllNodes"]

    @property
    def user(self):
        """
        The user for which the key has been created

        :rtype: str
        """
        return self._raw["user"]

    @property
    def secret(self):
        """
        The secret of the key created. If the key could not be created on any node, it will be set to None.

        :rtype: str
        """
        return self._raw.get("secret", None)

    @property
    def nodes_and_keys(self):
        """
        A list[dict] with information by node on the key created

        :rtype: list[dict]
        """
        return self._raw["nodesAndKeys"]

    @property
    def error(self):
        """
        If an error occurs while trying to create the key on any automation node, it will be reported in this field. Otherwise, it will be set to None.

        :rtype: str
        """
        return self._raw.get("error", None)

    @property
    def nodes_where_user_does_not_exist(self):
        """
        A list[dict] with information on the automation nodes where the user does not exist

        :rtype: list[dict]
        """
        return self._raw["nodesWhereUserDoesNotExist"]

    @property
    def nodes_where_user_is_disabled(self):
        """
        A list[dict] with information on the automation nodes where the user exists but is disabled

        :rtype: list[dict]
        """
        return self._raw["nodesWhereUserIsDisabled"]

    def get_raw(self):
        """
        Gets the raw personal API key creation result information.

        :rtype: dict
        """
        return self._raw


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
        Get the raw settings of this infrastructure.

        This returns a reference to the raw settings, not a copy, so changes made to the returned
        object will be reflected when saving.

        :return: the settings, as a dict.
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

        :return: the status, as a dict. The dict contains a list of the bundles currently deployed on the infrastructure
                 as a **deployments** field.
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

    def get_testing_status(self, bundle_id=None, automation_node_id=None):
        """
        Get the testing status of a project deployment.

        :param (optional) string bundle_id: filters the scenario runs done on a specific bundle
        :param (optional) automation_node_id: for multi-node deployments only, you need to specify the automation node id on which you want to retrieve
                                              the testing status
        :returns: A :class:`dataikuapi.dss.scenario.DSSTestingStatus` object handle
        """

        return DSSTestingStatus(self.client._perform_json("GET", "/project-deployer/deployments/%s/testing-status" % self.deployment_id, params={
            "bundleId": bundle_id,
            "automationNodeId": automation_node_id
        }))


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

        :return: the settings, as a dict. Notable fields are:

                    * **id** : identifier of the deployment
                    * **infraId** : identifier of the infrastructure on which the deployment is done
                    * **bundleId** : identifier of the bundle of the published project being deployed

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

        :returns: a summary, as a dict, with summary information on the deployment, the project from which the deployed
                  bundle originates, and the infrastructure on which it's deployed.
        :rtype: dict
        """
        return self.light_status

    def get_heavy(self):
        """
        Get the 'heavy' (full) status.

        This returns various information about the deployment, notably its health.

        :return: a status, as a dict. The overall status of the deployment is in a **health** field (possible values: UNKNOWN, ERROR,
                 WARNING, HEALTHY, UNHEALTHY, OUT_OF_SYNC).
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

    def get_bundle_stream(self, bundle_id):
        """
        Download a bundle from this published project, as a binary stream.

        .. warning::

            The stream must be closed after use. Use a **with** statement to handle closing the stream at the end of
            the block by default. For example:

        .. code-block:: python

                with project_deployer_project.get_bundle_stream('v1') as fp:
                    # use fp

                # or explicitly close the stream after use
                fp = project_deployer_project.get_bundle_stream('v1')
                # use fp, then close
                fp.close()

        :param str bundle_id: the identifier of the bundle

        """
        return self.client._perform_raw("GET",
                                        "/project-deployer/projects/%s/bundles/%s" % (self.project_key, bundle_id))

    def download_bundle_to_file(self, bundle_id, path):
        """
        Download a bundle from this published project into the given output file.

        :param str bundle_id: the identifier of the bundle
        :param str path: if "-", will write to /dev/stdout
        """
        if path == "-":
            path = "/dev/stdout"
        with self.get_bundle_stream(bundle_id) as stream:
            with open(path, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=10000):
                    if chunk:
                        f.write(chunk)
                        f.flush()

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

        :return: the settings, as a dict.
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

        :returns: a list of bundles, each one a dict. Each bundle has an **id** field holding its identifier.
        :rtype: list[dict]
        """
        return self.light_status["packages"]

    def get_infras(self):
        """
        Get the infrastructures that deployments of this project use.

        :returns: list of summaries of infrastructures, each a dict.
        :rtype: list[dict]
        """
        return self.light_status["infras"]

    def get_raw(self):
        """
        Gets the raw status information.

        :return: the status, as a dict. A  **deployments** sub-field contains a list of the deployments of bundles of this projects.
        :rtype: dict
        """
        return self.light_status
