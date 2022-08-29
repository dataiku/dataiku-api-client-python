class GovernAdminBlueprintDesigner(object):
    """
    Handle to interact with the blueprint designer
    Do not create this directly, use :meth:`~dataikuapi.GovernClient.get_admin_blueprint_designer()`
    """

    def __init__(self, client):
        self.client = client

    def list_blueprints(self, as_objects=True):
        """
        List blueprints

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`,
         else returns a list of dict. Each dict contains at least a field "blueprint.id".
        :returns: the list of blueprints
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint` or list of dict
        """
        blueprints = self.client._perform_json("GET", "/admin/blueprints")

        if as_objects:
            return [GovernAdminBlueprint(self.client, blueprint.get("blueprint")["id"]) for blueprint in blueprints]
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

    def create_blueprint(self, new_identifier, name, icon, color, background_color=""):
        """
        Create a new blueprint and returns a handle to interact with it.

        :param str new_identifier: the new identifier for the blueprint. This parameter should be made up of
        letters, digits or hyphen (-,_).
        :param str name: the name of the blueprint
        :param str icon: the icon of the blueprint
        :param str color: the color of the blueprint icon, to be specified in hexadecimal format
        :param str background_color: (Optional) the background color, to be specified in hexadecimal format
        :returns The handle for the newly created blueprint
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """

        result = self.client._perform_json(
            "POST", "/admin/blueprints", params={"newIdentifier": new_identifier},
            body={"name": name,
                  "icon": icon,
                  "color": color,
                  "backgroundColor": background_color})
        return GovernAdminBlueprint(self.client, result["blueprint"]["id"])


class GovernAdminBlueprint(object):
    """
    A handle to interact with a blueprint as an admin on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner.get_blueprint()`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Get the definition of the blueprint as an object. To modify the definition, call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save()`
        on the returned object.

        :returns: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint/%s" % self.blueprint_id)["blueprint"]
        return GovernAdminBlueprintDefinition(self.client, self.blueprint_id, definition)

    def list_versions(self, as_objects=True):
        """
        Lists versions of this blueprint.

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`,
         else returns a list of dict. Each dict contains a field "id.versionId" indicating the identifier of this version
        :returns: The list of the versions of the blueprint
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion` or list of dict
        """
        versions = self.client._perform_json(
            "GET", "/admin/blueprint/%s/versions" % self.blueprint_id)
        if as_objects:
            return [GovernAdminBlueprintVersion(self.client, self.blueprint_id, version["id"]["versionId"]) for version
                    in versions]
        else:
            return versions

    def create_version(self, new_identifier, blueprint_version_definition, origin_version_id=None):
        """
        Create a new blueprint version and returns a handle to interact with it.

        :param str new_identifier: The new identifier of the blueprint version. This parameter should be made up of
        letters, digits or hyphen (-,_).
        :param dict blueprint_version_definition: The definition of the blueprint version.
        :param str origin_version_id: (Optional) The blueprint version id of the origin version id if there is one.
        :returns The handle of the newly created blueprint
        :rtype: :class:`dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        params = {"newIdentifier": new_identifier}
        if origin_version_id is not None:
            params["originVersionId"] = origin_version_id

        blueprint_version_definition["id"] = {"blueprintId": self.blueprint_id}

        version = self.client._perform_json("POST", "/admin/blueprint/%s/versions" % self.blueprint_id, params=params,
                                            body=blueprint_version_definition)

        return self.get_version(version["id"]["versionId"])

    def get_version(self, version_id):
        """
        Get a blueprint version and return a handle to interact with it.

        :param str version_id: id of the version
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version_id)

    def delete(self):
        """
        Delete the blueprint. To delete a blueprint, all related blueprint versions and artifacts must be deleted
        beforehand.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s" % self.blueprint_id)


class GovernAdminBlueprintDefinition(object):
    """
    A handle to interact with the definition of a blueprint
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_definition()`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected
        when saving
        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the blueprint.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s" % self.blueprint_id,
                                                    body=self.definition)


class GovernAdminBlueprintVersion(object):
    """
    A handle to interact with a blueprint version
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_version()`
    """

    def __init__(self, client, blueprint_id, version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def get_definition(self):
        """
        Gets the definition of this blueprint version. To modify the definition, call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition.save()`
        on the returned object.

        :returns: The definition of the blueprint version as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition`.

        """
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id, definition)

    def get_status(self):
        """
        Gets the current status of the blueprint version.

        :return: the status of the blueprint versions. Can be "DRAFT", "ACTIVE", or "ARCHIVED"
        :rtype: str
        """
        return self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/status" %
                                         (self.blueprint_id, self.version_id))

    def update_status(self, status):
        """
        Directly update the status of the blueprint version.

        :param str status: DRAFT, ACTIVE, or ARCHIVED
        :return: None
        """
        self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s/status" % (self.blueprint_id, self.version_id),
                                  body=status)

    def list_sign_off_configurations(self, as_objects=True):
        """
        Gets the blueprint sign-off configurations list of this blueprint version.

        :param boolean as_objects: (Optional) If True, returns a list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`,
         else returns a list of dict. Each dict contains a field "stepId" indicating the identifier of the step.
        :return: The list of configuration as a Python list of dict
        :rtype: List of dict
        """

        configurations = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/signoffs" % (
            self.blueprint_id, self.version_id))

        if as_objects:
            return [GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id,
                                                    configuration["stepId"]) for configuration in configurations]
        else:
            return configurations

    def get_sign_off_configuration(self, step_id):
        """
        Gets the sign off configurations for a specific step. If you want to modify the configurations, you need to call
        :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration.save` on the returned object

        :return: The signoff configuration as an object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration`
        """

        return GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, step_id)

    def create_sign_off_configuration(self, step_id, sign_off_configuration):
        """
        Create a new signoff for a specific step of the workflow and return a handle to interact with it.

        :param str step_id: The step id of the workflow on which the signoff will be added.
        :param dict sign_off_configuration: The configuration of the signoff
        :returns The handle of the newly created signoff configuration
        :rtype: :class:`dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration`
        """

        self.client._perform_json("POST", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (
            self.blueprint_id, self.version_id, step_id), body=sign_off_configuration)

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
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_definition()`
    """

    def __init__(self, client, blueprint_id, version_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint version.

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected
        when saving
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
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s" % (
            self.blueprint_id, self.version_id), params=params, body=self.definition)


class GovernAdminSignoffConfiguration(object):
    """
    A handle to interact with the sign-off configuration of a specific step of a workflow.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_sign_off_configuration()`
    """

    def __init__(self, client, blueprint_id, version_id, step_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id

    def get_configuration_definition(self):
        """
        Get the definition of the configuration, to modify the configuration call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfigurationDefinition.save()`
        on the returned object.

        :returns: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition`
        """
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (
                self.blueprint_id, self.version_id, self.step_id))

        return GovernAdminSignOffConfigurationDefinition(self.client, self.blueprint_id, self.version_id, self.step_id,
                                                         definition)

    def delete(self):
        """
        Delete the sign-off configuration.

        :return: None
        """
        self.client._perform_empty(
            "DELETE", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id,
                                                                                   self.step_id))


class GovernAdminSignOffConfigurationDefinition(object):
    """
    A handle to interact with the definition of signoff configuration.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration.get_configuration_definition()`
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
            "PUT", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id,
                                                                                self.step_id), body=self.definition)
