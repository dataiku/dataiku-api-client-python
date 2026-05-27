import copy

from .future import DSSFuture
from .utils import DSSTaggableObjectListItem


class DSSSemanticModelListItem(DSSTaggableObjectListItem):
    """
    An item in a list of semantic models

    .. important::
        Do not instantiate this class directly, instead use :meth:`dataikuapi.dss.project.DSSProject.list_semantic_models`.
    """

    def __init__(self, client, data):
        super(DSSSemanticModelListItem, self).__init__(data)
        self.client = client

    def to_semantic_model(self):
        """
        Convert the current item to a semantic model handle.

        :returns: A handle for the semantic model.
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModel`
        """
        return DSSSemanticModel(self.client, self._data["projectKey"], self._data["id"])

    @property
    def project_key(self):
        """
        :returns: The project key
        :rtype: string
        """
        return self._data["projectKey"]

    @property
    def id(self):
        """
        :returns: The id of the semantic model.
        :rtype: string
        """
        return self._data["id"]

    @property
    def name(self):
        """
        :returns: The name of the semantic model.
        :rtype: string
        """
        return self._data["name"]


class DSSSemanticModel(object):
    """
    A handle to interact with a semantic model.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.project.DSSProject.get_semantic_model` instead.
    """

    def __init__(self, client, project_key, semantic_model_id):
        self.client = client
        self.project_key = project_key
        self.semantic_model_id = semantic_model_id

    @property
    def id(self):
        return self.semantic_model_id

    def get_active_version_id(self):
        """
        Get the active version of this semantic model.

        :return: semantic model version handle
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModelVersion`
        """
        definition = self._get_definition()
        active_version_id = definition.get("activeVersionId")
        if active_version_id is None:
            raise Exception("No active version set for semantic model %s" % self.semantic_model_id)
        return active_version_id

    def set_active_version_id(self, version_id):
        """
        Set the active version of this semantic model.

        :param str version_id: identifier of the version to set as active
        """
        definition = self._get_definition()
        version_ids = [v.get("id") for v in definition.get("versions", [])]
        if version_id not in version_ids:
            raise Exception("Version %s not found in semantic model %s" % (version_id, self.semantic_model_id))

        definition["activeVersionId"] = version_id
        self._set_definition(definition)

    def delete(self):
        """
        Delete the semantic model.
        """
        return self.client._perform_empty(
            "DELETE", "/projects/%s/semantic-models/%s" % (self.project_key, self.semantic_model_id)
        )

    def list_versions_ids(self):
        """
        List versions of this semantic model.

        :return: list of versions
        :rtype: list[str]
        """
        return [v.get("id") for v in self._get_definition().get("versions", [])]

    def get_version(self, version_id):
        """
        Get a handle to a specific version of this semantic model.

        :param str version_id: identifier of the version
        :return: semantic model version handle
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModelVersion`
        """
        return DSSSemanticModelVersion(self, version_id)

    def new_version(self, version_id, duplicate_of=None):
        """
        Create settings for a new version of this semantic model.

        The returned settings must be saved using :meth:`DSSSemanticModelVersionSettings.save`.

        .. code-block:: python

            # Example usage of creating a new version

            sm = project.get_semantic_model("my_semantic_model")
            version_settings = sm.new_version("v2")
            version_settings.save()

            # Example usage of creating a new version as a duplicate of an existing version

            sm = project.get_semantic_model("my_semantic_model")
            version_settings = sm.new_version("v2", duplicate_of="v1")
            version_settings.save()

        :param str version_id: identifier for the new version
        :param str duplicate_of: optional version id to duplicate settings from
        :return: semantic model version settings
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModelVersionSettings`
        """
        if duplicate_of is None:
            settings = DSSSemanticModelVersionSettings.new_settings(version_id)
        else:
            settings = copy.deepcopy(self.get_version(duplicate_of).get_settings().get_raw())
            settings["id"] = version_id
        return DSSSemanticModelVersionSettings(
            self.client, self.project_key, self.semantic_model_id, version_id, settings
        )

    def _get_definition(self):
        return self.client._perform_json(
            "GET", "/projects/%s/semantic-models/%s" % (self.project_key, self.semantic_model_id)
        )

    def _set_definition(self, definition):
        return self.client._perform_empty(
            "PUT", "/projects/%s/semantic-models/%s" % (self.project_key, self.semantic_model_id), body=definition
        )


class DSSSemanticModelVersion(object):
    """
    A handle to a semantic model version.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.semantic_model.DSSSemanticModel.get_version` instead.
    """

    def __init__(self, semantic_model, version_id):
        self.semantic_model = semantic_model
        self.client = semantic_model.client
        self.project_key = semantic_model.project_key
        self.semantic_model_id = semantic_model.semantic_model_id
        self._version_id = version_id

    @property
    def version_id(self):
        return self._version_id

    def get_settings(self):
        """
        Get the settings of this semantic model version.

        :return: semantic model version settings
        :rtype: :class:`dataikuapi.dss.semantic_model.DSSSemanticModelVersionSettings`
        """

        semantic_model = self.semantic_model._get_definition()
        version_settings = None
        for version in semantic_model.get("versions", []):
            if version.get("id") == self._version_id:
                version_settings = version
                break
        if version_settings is None:
            raise Exception("Version %s not found" % self._version_id)
        return DSSSemanticModelVersionSettings(
            self.client, self.project_key, self.semantic_model_id, self._version_id, version_settings
        )

    def get_basic_distinct_values_for_attribute(self, entity, attribute, max_values=1000):
        """
        Get distinct values for an attribute of this semantic model version.

        :param str entity: entity name
        :param str attribute: attribute name
        :param int max_values: maximum number of values to return
        :return: distinct values for the attribute
        :rtype: dict
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/semantic-models/%s/versions/%s/distinct-values/forAttribute"
            % (self.project_key, self.semantic_model_id, self.version_id),
            params={"entity": entity, "attribute": attribute, "maxValues": max_values},
        )

    def get_basic_distinct_values_for_model(self, max_values=1000):
        """
        Get distinct values for all attributes of this semantic model version.

        :param int max_values: maximum number of values per attribute
        :return: distinct values for the semantic model
        :rtype: dict
        """
        return self.client._perform_json(
            "GET",
            "/projects/%s/semantic-models/%s/versions/%s/distinct-values/global"
            % (self.project_key, self.semantic_model_id, self.version_id),
            params={"maxValues": max_values},
        )

    def start_update_distinct_values(self):
        """
        Start updating the distinct values index for this semantic model version.

        :return: a future tracking the update
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        future_resp = self.client._perform_json(
            "POST",
            "/projects/%s/semantic-models/%s/versions/%s/distinct-values/actions/startUpdate"
            % (self.project_key, self.semantic_model_id, self.version_id),
        )
        return DSSFuture.from_resp(self.client, future_resp)


class DSSSemanticModelVersionSettings(object):
    """
    Settings of a semantic model version

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.semanticmodel.DSSSemanticModelVersion.get_settings` instead.
    """

    def __init__(self, client, project_key, semantic_model_id, version_id, settings):
        self.client = client
        self.project_key = project_key
        self.semantic_model_id = semantic_model_id
        self.version_id = version_id
        self._settings = settings

    @staticmethod
    def new_settings(version_id):
        return {
            "id": version_id,
            "description": "",
            "created": {},
            "entities": [],
            "relationships": [],
            "goldenQueries": [],
            "crossEntityMetrics": [],
            "glossaryTerms": [],
            "glossaryBindings": [],
            "indexingSettings": {
                "maxDistinctValuesPerAttribute": 1000,
                "maxScannedRowsForSQLDatasets": -1,
                "maxScannedRowsForNonSQLDatasets": 1000000,
            },
            "privateEditorData": {},
            "sqlGenerationConfig": {},
        }

    @property
    def id(self):
        return self._settings.get("id")

    def get_raw(self):
        """
        Returns the raw settings of the semantic model version.

        :return: raw settings
        :rtype: dict
        """
        return self._settings

    def save(self):
        """
        Save the semantic model version settings.
        """
        if "id" not in self._settings:
            self._settings["id"] = self.version_id
        self.client._perform_empty(
            "PUT",
            "/projects/%s/semantic-models/%s/versions/%s" % (self.project_key, self.semantic_model_id, self.version_id),
            body=self._settings,
        )
