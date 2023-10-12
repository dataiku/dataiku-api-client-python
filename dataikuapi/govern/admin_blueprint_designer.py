class GovernAdminBlueprintDesigner(object):
    """
    Handle to interact with the blueprint designer
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_blueprint_designer`
    """

    def __init__(self, client):
        self.client = client

    def list_blueprints(self):
        """
        List blueprints

        :return: the list of blueprints
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintListItem`
        """
        blueprints = self.client._perform_json("GET", "/admin/blueprints")
        return [GovernAdminBlueprintListItem(self.client, blueprint) for blueprint in blueprints]

    def get_blueprint(self, blueprint_id):
        """
        Get a specific blueprint.

        :param str blueprint_id: the ID of the blueprint
        :return: a blueprint object
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """
        return GovernAdminBlueprint(self.client, blueprint_id)

    def create_blueprint(self, new_identifier, blueprint):
        """
        Create a new blueprint and returns a handle to interact with it.

        :param str new_identifier: the new identifier for the blueprint. Allowed characters are letters, digits, hyphen, and underscore.
        :param dict blueprint: the blueprint definition
        :return: The handle for the newly created blueprint
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """
        result = self.client._perform_json("POST", "/admin/blueprints", params={"newIdentifier": new_identifier}, body=blueprint)
        return GovernAdminBlueprint(self.client, result["blueprint"]["id"])


class GovernAdminBlueprintListItem(object):
    """
    An item in a list of blueprints.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner.list_blueprints`
    """

    def __init__(self, client, data):
        self.client = client
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the blueprint list item

        :return: the raw content of the blueprint list item as a dict
        :rtype: dict
        """
        return self._data

    def to_blueprint(self):
        """
        Gets the :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint` corresponding to this blueprint object

        :return: the blueprint object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint`
        """
        return GovernAdminBlueprint(self.client, self._data["blueprint"]["id"])


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

        :return: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition`
        """
        blueprint = self.client._perform_json("GET", "/admin/blueprint/%s" % self.blueprint_id)
        return GovernAdminBlueprintDefinition(self.client, self.blueprint_id, blueprint["blueprint"])

    def list_versions(self):
        """
        List versions of this blueprint.

        :return: The list of the versions of the blueprint
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionListItem`
        """
        versions = self.client._perform_json("GET", "/admin/blueprint/%s/versions" % self.blueprint_id)
        return [GovernAdminBlueprintVersionListItem(self.client, self.blueprint_id, version) for version in versions]

    def create_version(self, new_identifier, name=None, origin_version_id=None):
        """
        Create a new blueprint version and returns a handle to interact with it.

        :param str new_identifier: The new identifier of the blueprint version. Allowed characters are letters, digits, hyphen, and underscore.
        :param str name: (Optional) The name of the blueprint version.
        :param str origin_version_id: (Optional) The blueprint version ID of the origin version ID if there is one.
        :return: The handle of the newly created blueprint
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        params = {"newIdentifier": new_identifier}
        if name is not None:
            params["name"] = name
        if origin_version_id is not None:
            params["originVersionId"] = origin_version_id

        version = self.client._perform_json("POST", "/admin/blueprint/%s/versions" % self.blueprint_id, params=params)

        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version["blueprintVersion"]["id"]["versionId"])

    def get_version(self, version_id):
        """
        Get a blueprint version and return a handle to interact with it.

        :param str version_id: ID of the version
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
    The definition of a blueprint.
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


class GovernAdminBlueprintVersionListItem(object):
    """
    An item in a list of blueprint versions.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.list_versions`
    """

    def __init__(self, client, blueprint_id, data):
        self.client = client
        self.blueprint_id = blueprint_id
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the blueprint version list item

        :return: the raw content of the blueprint version list item as a dict
        :rtype: dict
        """
        return self._data

    def to_blueprint_version(self):
        """
        Gets the :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion` corresponding to this blueprint version object

        :return: the blueprint object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, self._data["blueprintVersion"]["id"]["versionId"])


class GovernAdminBlueprintVersion(object):
    """
    A handle to interact with a blueprint version.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_version`
    """

    def __init__(self, client, blueprint_id, version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def get_definition(self):
        """
        Get the definition of this blueprint version. To modify the definition, call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition.save`
        on the returned object.

        :return: The definition of the blueprint version as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionDefinition`.

        """
        version = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id, version["blueprintVersion"])

    def get_trace(self):
        """
        Get a handle of the blueprint version trace containing information about its lineage and its status.

        :return: the trace of the blueprint version.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersionTrace`.
        """
        version = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionTrace(self.client, self.blueprint_id, self.version_id, version["blueprintVersionTrace"])

    def list_signoff_configurations(self):
        """
        Get the blueprint sign-off configurations of this blueprint version.

        :return: The list of sign-off configurations
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfigurationListItem`
        """
        configurations = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/signoffs" % (self.blueprint_id, self.version_id))
        return [GovernAdminSignoffConfigurationListItem(self.client, self.blueprint_id, self.version_id, configuration) for configuration in configurations]

    def get_signoff_configuration(self, step_id):
        """
        Get the sign-off configurations for a specific step

        :param str step_id: The step ID of the sign-off
        :return: The sign-off configuration as an object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration`
        """

        return GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, step_id)

    def create_signoff_configuration(self, step_id, signoff_configuration):
        """
        Create a new sign-off for a specific step of the workflow and return a handle to interact with it.

        :param str step_id: The step ID of the workflow on which the sign-off will be added.
        :param dict signoff_configuration: The configuration of the sign-off
        :return: The newly created sign-off configuration as an object
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration`
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
    The blueprint version definition.
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

        :param boolean danger_zone_accepted: ignore the warning about existing artifacts.
            If there are existing artifacts using this blueprint version,
            modifying it may break them (ie. removing artifact field values).
            By default, the save call will fail in this case.
            If this parameter is set to true, the call will ignore the warning and be run anyway.
        :return: None
        """
        params = {}
        if danger_zone_accepted is not None:
            params["dangerZoneAccepted"] = danger_zone_accepted
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id),
            params=params, body=self.definition)["blueprintVersion"]


class GovernAdminBlueprintVersionTrace(object):
    """
    The trace of a blueprint version containing information about its lineage and its status.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_trace`
    """

    def __init__(self, client, blueprint_id, version_id, trace):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.trace = trace

    def get_raw(self):
        """
        Get raw trace of the blueprint version.

        :return: The raw trace of blueprint version, as a dict.
        :rtype: dict
        """
        return self.trace

    @property
    def status(self):
        """
        Get the status of the blueprint version among (DRAFT, ACTIVE, or ARCHIVED)

        :rtype: str
        """
        return self.trace.get("status")

    @property
    def origin_version_id(self):
        """
        Get the origin version ID of this blueprint version

        :rtype: str
        """
        return self.trace.get("originVersionId")

    def set_status(self, status):
        """
        Directly update the status of the blueprint version.

        :param str status: DRAFT, ACTIVE, or ARCHIVED
        :return: None
        """
        version = self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s/status" % (self.blueprint_id, self.version_id), body=status)
        self.trace = version["blueprintVersionTrace"]


class GovernAdminSignoffConfigurationListItem(object):
    """
    An item in a list of sign-off configurations.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.list_signoff_configurations`
    """

    def __init__(self, client, blueprint_id, version_id, data):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self._data = data

    def get_raw(self):
        """
        Get the raw content of the sign-off configuration list item

        :return: the raw content of the sign-off configuration list item as a dict
        :rtype: dict
        """
        return self._data

    def to_signoff_configuration(self):
        """
        Gets the :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration` corresponding to this sign-off configuration object

        :return: the sign-off configuration object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration`
        """
        return GovernAdminSignoffConfiguration(self.client, self.blueprint_id, self.version_id, self._data["id"]["stepId"])


class GovernAdminSignoffConfiguration(object):
    """
    A handle to interact with the sign-off configuration of a specific step of a workflow.
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_signoff_configuration`
    """

    def __init__(self, client, blueprint_id, version_id, step_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id

    def get_definition(self):
        """
        Get the definition of the configuration, to modify the configuration call :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfigurationDefinition.save`
        on the returned object.

        :return: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfigurationDefinition`
        """
        definition = self.client._perform_json("GET", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id))
        return GovernAdminSignoffConfigurationDefinition(self.client, self.blueprint_id, self.version_id, self.step_id, definition)

    def delete(self):
        """
        Delete the sign-off configuration.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id))


class GovernAdminSignoffConfigurationDefinition(object):
    """
    The definition of sign-off configuration.
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignoffConfiguration.get_definition`
    """

    def __init__(self, client, blueprint_id, version_id, step_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the sign-off configuration

        :return: the raw configuration of the sign-off, as a dict. Modifications made to the returned object are reflected
         when saving
        :rtype: dict
        """
        return self.definition

    def save(self):
        """
        Save this settings back to the sign-off configuration.

        :return: None
        """
        self.definition = self.client._perform_json(
            "PUT", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id, self.step_id),
            body=self.definition)
