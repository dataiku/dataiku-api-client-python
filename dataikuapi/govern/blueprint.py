class GovernBlueprintListItem(object):
    """
    An item in a list of blueprints.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.list_blueprints`
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
        Gets the :class:`~dataikuapi.govern.blueprint.GovernBlueprint` corresponding to this blueprint object

        :return: the blueprint object
        :rtype: a :class:`~dataikuapi.govern.blueprint.GovernBlueprint`
        """
        return GovernBlueprint(self.client, self._data["blueprint"]["id"])


class GovernBlueprint(object):
    """
    A handle to read a blueprint on the Govern instance. If you wish to edit blueprints or the blueprint versions, use 
    the blueprint designer object :class:`~dataikuapi.govern.admin_blueprint_designer.GovernAdminBlueprintDesigner`.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.get_blueprint`
    """

    def __init__(self, client, blueprint_id):
        self.client = client
        self.blueprint_id = blueprint_id

    def get_definition(self):
        """
        Return the definition of the blueprint as an object.

        :return: The blueprint definition as an object.
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintDefinition`
        """
        blueprint = self.client._perform_json("GET", "/blueprint/%s" % self.blueprint_id)
        return GovernBlueprintDefinition(self.client, self.blueprint_id, blueprint["blueprint"])

    def list_versions(self):
        """
        List versions of this blueprint.

        :return: the list of blueprint versions
        :rtype: list of :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersionListItem`
        """
        versions = self.client._perform_json("GET", "/blueprint/%s/versions" % self.blueprint_id)
        return [GovernBlueprintVersionListItem(self.client, self.blueprint_id, version) for version in versions]

    def get_version(self, version_id):
        """
        Return a handle to interact with a blueprint version

        :param str version_id: ID of the version
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion`
        """
        return GovernBlueprintVersion(self.client, self.blueprint_id, version_id)


class GovernBlueprintDefinition(object):
    """
    The definition of a blueprint.
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


class GovernBlueprintVersionListItem(object):
    """
    An item in a list of blueprint versions.
    Do not create this directly, use :meth:`~dataikuapi.govern.blueprint.GovernBlueprint.list_versions`
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
        Gets the :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion` corresponding to this blueprint version object

        :return: the blueprint object
        :rtype: a :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersion`
        """
        return GovernBlueprintVersion(self.client, self.blueprint_id, self._data["blueprintVersion"]["id"]["versionId"])


class GovernBlueprintVersion(object):
    """
    A handle to interact with a blueprint version on the Govern instance.
    Do not create this directly, use :meth:`~dataikuapi.govern.blueprint.GovernBlueprint.get_version`
    """

    def __init__(self, client, blueprint_id, version_id):
        self.client = client
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def get_blueprint(self):
        """
        Retrieve the blueprint handle of this blueprint version.

        :return: the corresponding blueprint handle
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprint`
        """
        return GovernBlueprint(self.client, self.blueprint_id)

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
        Get the definition of this blueprint version.

        :return: The definition of the blueprint version as an object.
        :rtype: :class:`~dataikuapi.govern.blueprint.GovernBlueprintVersionDefinition`

        """
        version = self.client._perform_json("GET", "/blueprint/%s/version/%s" % (self.blueprint_id, self.version_id))
        return GovernBlueprintVersionDefinition(self.client, self.blueprint_id, self.version_id, version["blueprintVersion"])


class GovernBlueprintVersionTrace(object):
    """
    The trace of a blueprint version containing information about its lineage and its status.
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


class GovernBlueprintVersionDefinition(object):
    """
    The definition of a blueprint version.
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
    A Blueprint Version ID builder

    :param str blueprint_id: the Blueprint ID
    :param str version_id: the Version ID
    """

    def __init__(self, blueprint_id, version_id):
        self.blueprint_id = blueprint_id
        self.version_id = version_id

    def build(self):
        """
        :return: the built blueprint version ID definition
        :rtype: dict
        """
        return {"blueprintId": self.blueprint_id, "versionId": self.version_id}
