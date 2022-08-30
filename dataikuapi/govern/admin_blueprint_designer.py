class GovernAdminBlueprintDesigner(object):
    """
    Handle to interact with the blueprint designer
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_blueprint_designer`
    """

    def __init__(self, client):
        self.client = client

    def list_blueprints(self, as_objects=True):
        """
        List blueprints

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`,
         else returns a list of dict. Each dict contains at least a field "blueprint.id".
        :returns: the list of blueprints
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint` or list of dict, see parameter as_objects
        """
        blueprints = self.client._perform_json("GET", "/admin/blueprints")

        if as_objects:
            return [GovernAdminBlueprint(self.client, blueprint["blueprint"]["id"]) for blueprint in blueprints]
        else:
            return blueprints

    def get_blueprint(self, blueprint_id):
        """
        Get a specific blueprint.

        :param str blueprint_id: the id of the blueprint
        :returns: an admin blueprint object
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """
        return GovernAdminBlueprint(self.client, blueprint_id)

    def create_blueprint(self, new_identifier, blueprint):
        """
        Create a new blueprint and returns a handle to interact with it.

        :param str new_identifier: the new identifier for the blueprint.
        :param dict blueprint: the blueprint definition
        :returns: The handle for the newly created blueprint
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """
        result = self.client._perform_json("POST", "/admin/blueprints", params={"newIdentifier": new_identifier}, body=blueprint)
        return GovernAdminBlueprint(self.client, result["blueprint"]["id"])


class GovernAdminBlueprint(object):
    """
    A handle to interact with a blueprint as an admin on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner.get_blueprint`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Get the definition of the blueprint as an object. To modify the definition, call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save`
        on the returned object.

        :returns: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition`
        """
        blueprint = self.client._perform_json("GET", "/admin/blueprint/%s" % self.blueprint_id)
        return GovernAdminBlueprintDefinition(self.client, self.blueprint_id, blueprint["blueprint"])

    def list_versions(self, as_objects=True):
        """
        Lists versions of this blueprint.

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`,
         else returns a list of dict. Each dict contains a field "blueprintVersion.id.versionId" indicating the identifier of this version
        :returns: The list of the versions of the blueprint
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion` or list of dict, see parameter as_objects
        """
        versions = self.client._perform_json("GET", "/admin/blueprint/%s/versions" % self.blueprint_id)
        if as_objects:
            return [GovernAdminBlueprintVersion(self.client, self.blueprint_id, version["blueprintVersion"]["id"]["versionId"]) for version in versions]
        else:
            return versions

    def create_version(self, new_identifier, blueprint_version_definition, origin_version_id=None):
        """
        Create a new blueprint version and returns a handle to interact with it.

        :param str new_identifier: The new identifier of the blueprint version.
        :param dict blueprint_version_definition: The definition of the blueprint version.
        :param str origin_version_id: (Optional) The blueprint version id of the origin version id if there is one.
        :returns: The handle of the newly created blueprint
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        params = {"newIdentifier": new_identifier}
        if origin_version_id is not None:
            params["originVersionId"] = origin_version_id

        version = self.client._perform_json("POST", "/admin/blueprint/%s/versions" % self.blueprint_id, params=params, body=blueprint_version_definition)

        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version["blueprintVersion"]["id"]["versionId"])

    def get_version(self, version_id):
        """
        Get a blueprint version and return a handle to interact with it.

        :param str version_id: id of the version
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version_id)

    def delete(self):
        """
        Delete the blueprint.
        To delete a blueprint, all related blueprint versions and artifacts must be deleted beforehand.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s" % self.blueprint_id)


class GovernAdminBlueprintDefinition(object):
    """
    A handle to interact with the definition of a blueprint
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected when saving
        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the blueprint.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s" % self.blueprint_id, body=self.definition)["blueprint"]


class GovernAdminBlueprintVersion(object):
    """
    A handle to interact with a blueprint version
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_version`
    """

    def __init__(self, client, blueprint_id, version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def get_definition(self):
        """
        Gets the definition of this blueprint version. To modify the definition, call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition.save`
        on the returned object.

        :returns: The definition of the blueprint version as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition`.

        """
        definition = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id, definition["blueprintVersion"])

    def get_trace(self):
        """
        Gets the trace of the blueprint version.

        :return: the trace of the blueprint versions.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionTrace`.
        """
        definition = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionTrace(self.client, self.blueprint_id, self.version_id, definition["blueprintVersionTrace"])

    def list_signoff_configurations(self, as_objects=True):
        """
        Gets the blueprint sign-off configurations of this blueprint version.

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration`,
         else returns a list of dict. Each dict contains a field "stepId" indicating the identifier of the step.
        :return: The list of sign-off configurations
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration` or list of dict, see parameter as_objects
        """
        configurations = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/signoffs" % (self.blueprint_id, self.version_id))

        if as_objects:
            return [GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, configuration["stepId"]) for configuration in configurations]
        else:
            return configurations

    def get_sign_off_configuration(self, step_id):
        """
        Gets the sign-off configurations for a specific step

        :return: The signoff configuration as an object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration`
        """

        return GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, step_id)

    def create_sign_off_configuration(self, step_id, signoff_configuration):
        """
        Create a new sign-off for a specific step of the workflow and return a handle to interact with it.

        :param str step_id: The step id of the workflow on which the sign-off will be added.
        :param dict signoff_configuration: The configuration of the sign-off
        :returns: The handle of the newly created sign-off configuration
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration`
        """
        self.client._perform_json("POST", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, step_id),
            body=signoff_configuration)
        return GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, step_id)

    def delete(self):
        """
        Delete the blueprint version. To delete a blueprint, all related artifacts must be deleted beforehand.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))


class GovernAdminBlueprintVersionDefinition(object):
    """
    A handle to interact with a blueprint version definition
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_definition`
    """

    def __init__(self, client, blueprint_id, version_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint version.

        :return: the raw definition of blueprint version, as a dict. Modifications made to the returned object are reflected when saving
        :rtype: dict
        """
        return self.definition

    def save(self, danger_zone_accepted=None):
        """
        Save this definition back to the blueprint version definition.

        :param boolean danger_zone_accepted: ignore the warning about existing artifacts. If there are existing artifact
        s using this blueprint version, modifying it may break them (ie. removing artifact field values). By default,
        the save call will fail in this case. If this parameter is set to true, the call will ignore the warning
        and be run anyway.
        :return: None
        """
        params = {}
        if danger_zone_accepted is not None:
            params["dangerZoneAccepted"] = danger_zone_accepted
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id),
            params=params, body=self.definition)


class GovernAdminBlueprintVersionTrace(object):
    """
    A handle to interact with a blueprint version trace
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_trace`
    """

    def __init__(self, client, blueprint_id, version_id, trace):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.trace = trace

    def get_raw(self):
        """
        Get raw definition of the blueprint version trace.

        :return: the raw definition of blueprint version trace, as a dict.
        :rtype: dict
        """
        return self.trace

    def update_status(self, status):
        """
        Directly update the status of the blueprint version.

        :param str status: DRAFT, ACTIVE, or ARCHIVED
        :return: None
        """
        self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s/status" % (self.blueprint_id, self.version_id), body=status)


class GovernAdminSignoffConfiguration(object):
    """
    A handle to interact with the sign-off configuration of a specific step of a workflow.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_sign_off_configuration`
    """

    def __init__(self, client, blueprint_id, version_id, step_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id

    def get_configuration_definition(self):
        """
        Get the definition of the configuration, to modify the configuration call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfigurationDefinition.save`
        on the returned object.

        :returns: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfigurationDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id))
        return GovernAdminSignOffConfigurationDefinition(self.client, self.blueprint_id, self.version_id, self.step_id, definition)

    def delete(self):
        """
        Delete the sign-off configuration.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id))


class GovernAdminSignOffConfigurationDefinition(object):
    """
    A handle to interact with the definition of signoff configuration.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration.get_configuration_definition`
    """

    def __init__(self, client, blueprint_id, version_id, step_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the signoff configuration

        :return: the raw configuration of the signoff, as a dict. Modifications made to the returned object are reflected
         when saving
        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the signoff configuration.

        :return: None
        """
        self.definition = self.client._perform_json(
            "PUT", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id),
            body=self.definition)
