class GovernBlueprint(object):
    """
    A handle to read a blueprint on the Govern instance. If you wish to edit blueprints or the blueprint versions, use
    :meth:`dataikuapi.govern_client.get_admin_blueprint_designer()`.
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_blueprint()`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    @property
    def id(self):
        """
        Return the blueprint id.

        :rtype: str
        """
        return self.blueprint_id

    def get_definition(self):
        """
        Return the definition of the blueprint as an object.

        :returns: the blueprint definition as an object.
        :rtype: :class:`dataikuapi.govern.models.GovernBlueprintDefinition`
        """
        definition = self.client._perform_json(
            "GET", "/blueprint/%s" % self.blueprint_id).get("definition")
        return GovernBlueprintDefinition(self.client, self.blueprint_id, definition)

    def list_versions(self, as_objects=True):
        """
        Lists versions of this blueprint.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`GovernAPIBlueprintDesignerBlueprintVersion`, else
         returns a list of dict. Each dict contains a field "id" indicating the identifier of this version
        :returns: a list - see as_objects for more information
        :rtype: list of :class: `dataikuapi.govern.models.GovernBlueprintVersion` or list of dict
        """
        versions = self.client._perform_json(
            "GET", "/blueprint/%s/versions" % self.id)
        if as_objects:
            return [GovernBlueprintVersion(self.client, self.blueprint_id, version["id"]["versionId"]) for version
                    in versions]
        else:
            return versions

    def get_version(self, version_id):
        """
        Returns a handle to interact with a blueprint version

        :param str version_id: id of the version
        :rtype: :class: `dataikuapi.govern.models.GovernBlueprintVersion`
        """
        return GovernBlueprintVersion(self.client, self.blueprint_id, version_id)


class GovernBlueprintDefinition(object):
    """
    A handle of the definition of a blueprint
    Do not create this class directly, instead use :meth:`dataikuapi.govern.models.GovernBlueprint.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of a blueprint

        :return: the raw definition of blueprint, as a dict.
        :rtype: dict
        """
        return self.definition

    @property
    def id(self):
        """
        Return the blueprint id.

        :return: the blueprint id
        :rtype: str
        """
        return self.blueprint_id

    @property
    def name(self):
        """
        Return the blueprint name.

        :return: the blueprint name
        :rtype: str
        """
        return self.definition.get("name")

    @property
    def icon(self):
        """
        Return the blueprint icon.

        :return: the blueprint icon
        :rtype: str
        """
        return self.definition.get("icon")

    @property
    def color(self):
        """
        Return the blueprint color.

        :return: the blueprint color
        :rtype: str
        """
        return self.definition.get("color")

    @property
    def background_color(self):
        """
        Return the blueprint background color.

        :return: the blueprint background color
        :rtype: str
        """
        return self.definition.get("backgroundColor")


class GovernBlueprintVersion(object):
    """
    A handle to interact with a blueprint version on the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.BlueprintDesigner.Blueprint.get_version`
    """

    def __init__(self, client, blueprint_id, blueprint_version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.blueprint_version_id = blueprint_version_id

    @property
    def id(self):
        """
        Return the blueprint version id.
        """
        return self.blueprint_version_id

    def get_definition(self):
        """
        Gets the definition of this blueprint version.

        :returns: The definition of the blueprint version as an object.
        :rtype: :class:`dataikuapi.govern.models.GovernBlueprintVersionDefinition`

        """
        definition = self.client._perform_json(
            "GET", "/blueprint/%s/version/%s" % (self.blueprint_id, self.blueprint_version_id))
        return GovernBlueprintVersionDefinition(self.client, self.blueprint_id, self.blueprint_version_id,
                                                definition)

    def get_status(self):
        """
        Get the blueprint version status.

        :returns: The status of this blueprint version. Can be either "DRAFT", "ACTIVE" or "ARCHIVED"
        :rtype: str
        """

        return self.client._perform_json("GET", "/blueprint/%s/version/%s/status" % (self.blueprint_id,
                                                                                     self.blueprint_version_id))


class GovernBlueprintVersionDefinition(object):
    """
    A handle to interact with a blueprint version definition on the Govern instance.
    Do not create this directly, use :meth:`dataikuapi.govern.models.GovernBlueprintVersion.get_definition`
    """

    def __init__(self, client, blueprint_id, blueprint_version_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.blueprint_version_id = blueprint_version_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint version.

        :return: the raw definition of blueprint, as a dict.
        :rtype: dict
        """
        return self.definition

    def get_name(self):
        """
        Gets the name of the version.

        :rtype: str
        """
        return self.definition.get("name")

    def get_instructions(self):
        """
        Gets the instructions for this version.

        :rtype: str
        """
        return self.definition.get("instructions")

    def get_hierarchical_parent_field_id(self):
        """
        Gets the parent field id.

        :rtype: str
        """
        return self.definition.get("hierarchicalParentFieldId")

    def get_field_definitions(self):
        """
        Gets the field definitions of this version. This returns a dictionary with the field ids of as the keys,
        the values are the definition of the fields.

        :rtype: dict
        """
        return self.definition.get("fieldDefinitions")

    def get_field_definition(self, field_definition_id):
        """
        Gets the definition of a specific field. This returns a dictionary with the definition of the field.

        :param str field_definition_id: id of the desired field
        :rtype: dict
        """
        return self.definition.get("fieldDefinitions").get(field_definition_id)

    def get_workflow_definition(self):
        """
        Gets the workflow definition for this version. This returns a dictionary with the step definitions.

        :rtype: dict
        """
        return self.definition.get("workflowDefinition")

    def get_logical_hook_list(self):
        """
        Gets the list of the hooks for this version. This returns a list with the logical hooks.

        :rtype: list
        """
        return self.definition.get("logicalHookList")

    def get_ui_definition(self):
        """
        Gets the UI definition of this version. Returns a dict with the UI definition information.

        :rtype: dict
        """
        return self.definition.get("uiDefinition")
