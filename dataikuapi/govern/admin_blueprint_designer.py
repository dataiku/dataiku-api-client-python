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
        :rtype: list of :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint` or list of dict
        """
        blueprints = self.client._perform_json("GET", "/admin/blueprints")

        if as_objects:
            return [GovernAdminBlueprint(self.client, blueprint.get["blueprint"]["id"]) for blueprint in
                    blueprints]
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

        :param str new_identifier: the new identifier for the blueprint
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
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s" % self.blueprint_id)["blueprint"]
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
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        params = {"newIdentifier": new_identifier}
        if origin_version_id is not None:
            params["originVersionId"] = origin_version_id

        if "id" not in blueprint_version_definition:
            blueprint_version_definition["id"] = {"blueprintId": self.blueprint_id}

        self.client._perform_json("POST", "/admin/blueprint/%s/versions" % self.blueprint_id, params=params,
                                  body=blueprint_version_definition)

        return self.get_version("bv" + new_identifier)

    def get_version(self, version_id):
        """
        Get a blueprint version and return a handle to interact with it.

        :param str version_id: id of the version
        :rtype: :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion`
        """
        return GovernAdminBlueprintVersion(self.client, self.blueprint_id, version_id)


class GovernAdminBlueprintDefinition(object):
    """
    A handle to interact with the definition of a blueprint
    Do not create this class directly, instead use :meth:`dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprint.get_definition`
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


    @property
    def name(self):
        """
        Return the blueprint name

        :return: the blueprint name
        :rtype: str
        """
        return self.definition.get("name")

    @property
    def icon(self):
        """
        Return the blueprint icon

        :return: the blueprint icon
        :rtype: str
        """
        return self.definition.get("icon")

    @property
    def color(self):
        """
        Return the blueprint color

        :return: the blueprint color
        :rtype: str
        """
        return self.definition.get("color")

    @property
    def background_color(self):
        """
        Return the blueprint background color

        :return: the blueprint background color
        :rtype: str
        """
        return self.definition.get("backgroundColor")

    @color.setter
    def color(self, color):
        """
        Set the icon color of the blueprint

        :param str color: the new color to set, has to be in hexadecimal format. Use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save`
        to save this new value back to the blueprint version
        :return: None
        """
        self.definition["color"] = color

    @name.setter
    def name(self, name):
        """
        Set the icon color of the blueprint

        :param str name: the new name to set. Use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save`
        to save this new value back to the blueprint version
        :return: None
        """
        self.definition["name"] = name

    @icon.setter
    def icon(self, icon):
        """
        Set the icon of the blueprint. Use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save`
        to save this new value back to the blueprint version

        :param str icon: the new icon to set
        :return: None
        """
        self.definition["icon"] = icon

    @background_color.setter
    def background_color(self, background_color):
        """
        Set the backgroundColor of the blueprint. Use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDefinition.save`
        to save this new value back to the blueprint version

        :param str background_color: the new background_color to set, has to be in hexadecimal format.
        :return: None
        """
        self.definition["backgroundColor"] = background_color

    def save(self):
        """
        Save this settings back to the blueprint.

        :return: None
        """
        self.definition = self.client._perform_json("PUT", "/admin/blueprint/%s" % self.id, body=self.definition)

    def delete(self):
        """
        Delete the blueprint, including all its versions and its artifacts.

        :return: None
        """
        self.client._perform_empty("DELETE", "/admin/blueprint/%s" % self.blueprint_id)


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
        definition = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernAdminBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id,
                                                     definition)

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
        self.client._perform_json("PUT", "/admin/blueprint/%s/version/%s/status" %
                                  (self.blueprint_id, self.version_id), body=status)

    def list_signoff_configurations(self):
        """
        Gets the blueprint sign-off configurations list of this blueprint version.

        :return: The list of configuration as a Python list of dict
        :rtype: List of dict
        """

        return self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s/signoffs" % (self.blueprint_id, self.version_id))

    def get_signoff_configuration(self, step_id):
        """
        Gets the sign off configurations for a specific step. If you want to modify the configurations, you need to call
        :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration.save` on the returned object

        :return: The signoff configuration as an object
        :rtype: a :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminSignOffConfiguration`
        """
        sign_off_config = self.client._perform_json(
            "GET", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" %
                   (self.blueprint_id, self.version_id, step_id))

        return GovernAdminSignOffConfiguration(self.client, self.blueprint_id, self.version_id, step_id,
                                               sign_off_config)

    def delete_signoff_configuration(self, step_id):
        """
        Delete the sign-off configuration of a specific step.
        :param str step_id: Identifier of the step of which the sign-off configuration will be deleted.
        :return: None
        """
        self.client._perform_empty(
            "DELETE", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id,
                                                                                   self.version_id, step_id))


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

        :return: the raw definition of blueprint, as a dict. Modifications made to the returned object are reflected
        when saving
        :rtype: dict
        """
        return self.definition

    def get_name(self):
        """
        Get the name of the version.

        :rtype: str
        """
        return self.definition.get("name")

    def get_instructions(self):
        """
        Get the instructions for this version.

        :rtype: str
        """
        return self.definition.get("instructions")

    def get_hierarchical_parent_field_id(self):
        """
        Get the parent field id.

        :rtype: str
        """
        return self.definition.get("hierarchicalParentFieldId")

    def get_field_definitions(self):
        """
        Get the field definitions of this version. This returns a dictionary with the field ids and the definitions.

        :rtype: dict
        """
        return self.definition.get("fieldDefinitions")

    def get_field_definition(self, field_id):
        """
        Get the definition of a specific field. This returns a dictionary with the definition of the field.

        :param str field_id: id of the desired field
        :rtype: dict
        """
        return self.definition.get("fieldDefinitions", {}).get(field_id)

    def get_workflow_definition(self):
        """
        Get the workflow definition for this version. This returns a dictionary with the step definitions.

        :rtype: dict
        """
        return self.definition.get("workflowDefinition")

    def get_logical_hook_list(self):
        """
        Get the list of the hooks for this version. This returns a list with the logical hooks.

        :rtype: list
        """
        return self.definition.get("logicalHookList")

    def get_ui_definition(self):
        """
        Get the UI definition of this version. Return a dict with the UI definition information.

        :rtype: dict
        """
        return self.definition.get("uiDefinition")

    def save(self, danger_zone_accepted=None):
        """
        Save this definition back to the blueprint version definition.

        :param boolean danger_zone_accepted: ignore the warning about existing artifacts. If there are existing artifacts using this blueprint version, modifying it may break them (ie. removing artifact field values). By default, the save call will fail in this case. If this parameter is set to true, the call will ignore the warning and be run anyway.
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
    Do not create this directly, use :meth:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintVersion.get_sign_off_configuration`
    """

    def __init__(self, client, blueprint_id, version_id, step_id, configuration):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.step_id = step_id
        self.configuration = configuration


    def get_raw(self):
        """
        Get raw definition of the signoff configuration

        :return: the raw configuration of the signoff, as a dict. Modifications made to the returned object are reflected
         when saving
        :rtype: dict
        """
        return self.configuration

    def save(self):
        """
        Save this settings back to the signoff configuration.

        :return: None
        """
        self.configuration = self.client._perform_json(
            "PUT", "/admin/blueprint/%s/version/%s/workflow/step/%s/signoff" % (self.blueprint_id, self.version_id,
                                                                                self.id), body=self.configuration)
