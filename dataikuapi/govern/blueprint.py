class GovernBlueprint(object):
    """
    A handle to read a blueprint on the Govern instance. If you wish to edit blueprints or the blueprint versions, use 
    the blueprint designer object :class:`~dataikuapi.admin_blueprint_designer.GovernAdminBlueprintDesigner`.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_blueprint`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Return the definition of the blueprint as an object.

        :returns: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintDefinition`
        """
        blueprint = self.client._perform_json("GET", "/blueprint/%s" % self.blueprint_id)
        return GovernBlueprintDefinition(self.client, self.blueprint_id, blueprint["blueprint"])

    def list_versions(self, as_objects=True):
        """
        Lists versions of this blueprint.

        :param boolean as_objects: (Optional) if True, returns a list of :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion`,
        else returns a list of dict. Each dict contains at least a field "blueprintVersion.id.versionId" indicating the identifier the version
        :return: the list of blueprint versions, each as a dict or an object. Each dict contains at least an "blueprintversion.id.versionId" field
        :rtype: list of :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion` or list of dict, see param as_objects
        """
        versions = self.client._perform_json("GET", "/blueprint/%s/versions" % self.id)
        if as_objects:
            return [GovernBlueprintVersion(self.client, self.blueprint_id, version["blueprintVersion"]["id"]["versionId"]) for version in versions]
        else:
            return versions

    def get_version(self, version_id):
        """
        Returns a handle to interact with a blueprint version

        :param str version_id: id of the version
        :rtype: :class:`~dataikuapi.govern.models.GovernBlueprintVersion`
        """
        return GovernBlueprintVersion(self.client, self.blueprint_id, version_id)


class GovernBlueprintDefinition(object):
    """
    A handle of the definition of a blueprint
    Do not create this class directly, instead use :meth:`~dataikuapi.govern.blueprint.GovernBlueprint.get_definition`
    """

    def __init__(self, client, blueprint_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of a blueprint

        :return: The raw definition of blueprint, as a dict.
        :rtype: dict
        """
        return self.definition


class GovernBlueprintVersion(object):
    """
    A handle to interact with a blueprint version on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern.blueprint.GovernBlueprint.get_version`
    """

    def __init__(self, client, blueprint_id, version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def get_trace(self):
        """
        Get the trace of this blueprint version (info about its status and origin blueprint version lineage).

        :return: The trace of this blueprint version.
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersionTrace`
        """
        version = self.client._perform_json("GET", "/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernBlueprintVersionTrace(self.client, self.blueprint_id, self.version_id, version["blueprintVersionTrace"])

    def get_definition(self):
        """
        Gets the definition of this blueprint version.

        :return: The definition of the blueprint version as an object.
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersionDefinition`

        """
        version = self.client._perform_json("GET", "/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id, version["blueprintVersion"])


class GovernBlueprintVersionTrace(object):
    """
    A handle to interfact with a blueprint version trace on the Govern instance
    Do not create this directly, use :meth:`~dataikuapi.govern.blueprint.GovernBlueprintVersion.get_trace`
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


class GovernBlueprintVersionDefinition(object):
    """
    A handle to interact with a blueprint version definition on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern.blueprint.GovernBlueprintVersion.get_definition`
    """

    def __init__(self, client, blueprint_id, version_id, definition):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id
        self.definition = definition

    def get_raw(self):
        """
        Get raw definition of the blueprint version.

        :return: The raw definition of blueprint version, as a dict.
        :rtype: dict
        """
        return self.definition


class GovernBlueprintVersionId(object):
    """
    A Blueprint Version ID definition builder
    """

    def __init__(self, blueprint_id, version_id):
        """
        :param str blueprint_id: the Blueprint ID
        :param str version_id: the Version ID
        """
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def build(self):
        """
        :returns: the built blueprint version ID definition
        :rtype: dict
        """
        return {"blueprintId": self.blueprint_id, "versionId": self.version_id}