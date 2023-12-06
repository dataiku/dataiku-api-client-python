from dataikuapi.govern.artifact import GovernArtifact
import copy

class GovernArtifactSearchRequest(object):
    """
    A search request object.
    Do not create this directly, use :meth:`~dataikuapi.govern_client.GovernClient.new_artifact_search_request` and then run the
    query using :meth:`~dataikuapi.govern.artifact_search.GovernArtifactSearchRequest.fetch_next_batch`
    """

    def __init__(self, client, artifact_search_query):
        self.client = client
        self.search_query = artifact_search_query.build()
        self.last_artifact_id = None

    def fetch_next_batch(self, page_size=20):
        """
        Run the search request fetching the next batch of results. Use page_size to specify the size of the result page.

        :param int page_size: (Optional) size of the result page, default value is set to 20.
        :return: The response of a single fetch of the search request
        :rtype: a :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchResponse`
        """
        body = copy.deepcopy(self.search_query)
        body["artifactSearchPagination"] = {
            "pageSize": page_size,
            "lastArtifactId": self.last_artifact_id
        }

        response = self.client._perform_json("POST", "/artifacts/search", body=body)

        artifact_list = response.get("uiArtifacts", [])
        # update local last_artifact_id for next requests
        if artifact_list:
            self.last_artifact_id = artifact_list[-1]["artifact"]["id"]

        return GovernArtifactSearchResponse(self.client, response)

class GovernArtifactSearchResponse(object):
    """
    A search request response for a single batch.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact_search.GovernArtifactSearchRequest.fetch_next_batch`.
    """

    def __init__(self, client, response):
        self.client = client
        self.response = response

    def get_raw(self):
        """
        Get the raw content of the search response
        
        :return: the raw content of the search response as a dict
        :rtype: dict
        """
        return self.response

    def get_response_hits(self):
        """
        Get the search response hits (artifacts)
        
        :return: list of the search response hits (artifacts)
        :rtype: list of :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchResponseHit`
        """
        return [GovernArtifactSearchResponseHit(self.client, hit) for hit in self.response.get("uiArtifacts", [])]


class GovernArtifactSearchResponseHit(object):
    """
    A search request response.
    Do not create this directly, use :meth:`~dataikuapi.govern.artifact_search.GovernArtifactSearchResponse.get_response_hits`.
    """

    def __init__(self, client, hit):
        self.client = client
        self.hit = hit

    def get_raw(self):
        """
        Get the raw content of the search response hit
        
        :return: the raw content of the search response hit as a dict
        :rtype: dict
        """
        return self.hit

    def to_artifact(self):
        """
        Gets the :class:`~dataikuapi.govern.artifact.GovernArtifact` corresponding to this search response hit

        :return: the custom page object
        :rtype: a :class:`~dataikuapi.govern.artifact.GovernArtifact`
        """
        return GovernArtifact(self.client, self.hit["artifact"]["id"])


class GovernArtifactSearchQuery(object):
    """
    A definition of an artifact query. Instantiate and interact with this object to customize the query.

    :param artifact_search_source: (Optional) The search source to target a subset of artifacts.
        For now, by default, the search will be executed on all artifacts using the
        :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSourceAll` search source.
    :type artifact_search_source: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSource`
    :param artifact_filters: A list of filters to apply on the query.
    :type artifact_filters: list of :class:`~dataikuapi.govern.artifact_search.GovernArtifactFilter`
    :param artifact_search_sort: The sort configuration to apply on the query
    :type artifact_search_sort: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSort`
    """

    def __init__(self, artifact_search_source=None, artifact_filters=None, artifact_search_sort=None):
        self.artifact_search_source = artifact_search_source if artifact_search_source is not None else GovernArtifactSearchSourceAll()
        self.artifact_filters = artifact_filters if artifact_filters is not None else []
        self.artifact_search_sort = artifact_search_sort

    def set_artifact_search_source(self, artifact_search_source):
        """
        Set a search source for this query

        :param artifact_search_source: (Optional) The search source to target a subset of artifacts.
            For now, by default, the search will be executed on all artifacts using the
            :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSourceAll` search source.
        :type artifact_search_source: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSource`
        :return: None
        """
        self.artifact_search_source = artifact_search_source

    def clear_artifact_filters(self):
        """
        Remove the filters set for this query

        :return: None
        """
        self.artifact_filters = []

    def add_artifact_filter(self, artifact_filter):
        """
        Add a new artifact filter to the filter list of the query.

        :param artifact_filter: A filter to add to the filter list.
        :type artifact_filter: :class:`~dataikuapi.govern.artifact_search.GovernArtifactFilter`
        :return: None
        """
        self.artifact_filters.append(artifact_filter)

    def clear_artifact_search_sort(self):
        """
        Remove the sort configuration of this query.

        :return: None
        """
        self.artifact_search_sort = None

    def set_artifact_search_sort(self, artifact_search_sort):
        """
        Set a new search sort configuration for this request.

        :param artifact_search_sort: The sort configuration to apply on the query
        :type artifact_search_sort: :class:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSort`
        :return: None
        """
        self.artifact_search_sort = artifact_search_sort

    def build(self):
        """
        :return: the search query definition
        :rtype: (dict, dict)
        """
        query = {
            "artifactSearchSource": self.artifact_search_source.build(),
            "artifactFilters": [artifact_filter.build() for artifact_filter in self.artifact_filters],
        }
        if self.artifact_search_sort is not None:
            query["artifactSearchSort"] = self.artifact_search_sort.build()
        return query


########################################################
# Search Source
########################################################

class GovernArtifactSearchSource(object):
    """
    An abstract class to represent the different search source. Do not instantiate this class but one of its subclasses.
    """

    def __init__(self, search_source_type):
        self.search_source_type = search_source_type

    def build(self):
        raise NotImplementedError("Cannot build an abstract artifact search source")


class GovernArtifactSearchSourceAll(GovernArtifactSearchSource):
    """
    A generic search source definition.
    """

    def __init__(self):
        super(GovernArtifactSearchSourceAll, self).__init__(search_source_type="all")

    def build(self):
        """
        :return: the search source definition as a dict
        :rtype: dict
        """
        return {"type": self.search_source_type}


########################################################
# Search Sort
########################################################

class GovernArtifactSearchSort(object):
    """
    An abstract class to represent the different search sort. Do not instantiate this class but one of its subclasses.
    """

    def __init__(self, artifact_search_sort_type, direction):
        self.artifact_search_sort_type = artifact_search_sort_type
        self.direction = direction

    def build(self):
        raise NotImplementedError("Cannot build an abstract artifact search sort")


class GovernArtifactSearchSortName(GovernArtifactSearchSort):
    """
    An artifact sort definition based on their names.

    :param str direction: (Optional) The direction on which the artifacts will be sorted. Can be either "ASC" or "DESC"
    """

    def __init__(self, direction="ASC"):
        super(GovernArtifactSearchSortName, self).__init__(artifact_search_sort_type="name", direction=direction)

    def build(self):
        """
        :return: the search sort definition as a dict
        :rtype: dict
        """
        return {"direction": self.direction, "column": {"type": self.artifact_search_sort_type}}


class GovernArtifactSearchSortWorkflow(GovernArtifactSearchSort):
    """
    An artifact sort defintion based on their workflow.

    :param str direction: (Optional) The direction on which the artifacts will be sorted. Can be either "ASC" or "DESC"
    """

    def __init__(self, direction="ASC"):
        super(GovernArtifactSearchSortWorkflow, self).__init__(artifact_search_sort_type="workflow", direction=direction)

    def build(self):
        """
        :return: the search sort definition as a dict
        :rtype: dict
        """
        return {"direction": self.direction, "column": {"type": self.artifact_search_sort_type}}


class GovernArtifactSearchSortField(GovernArtifactSearchSort):
    """
    An artifact sort definition based on a list of fields.

    :param fields: (Optional) A list of fields on which the artifacts will be sorted.
        Use :meth:`~dataikuapi.govern.artifact_search.GovernArtifactSearchSortFieldDefinition.build` to build a field based sort definition.
    :type fields: list of dict
    :param str direction: (Optional) The direction on which the artifacts will be sorted. Can be either "ASC" or "DESC"
    """

    def __init__(self, fields=None, direction="ASC"):
        super(GovernArtifactSearchSortField, self).__init__(artifact_search_sort_type="field", direction=direction)
        self.fields = fields if fields is not None else []

    def build(self):
        """
        :return: the search sort definition as a dict
        :rtype: dict
        """
        return {"direction": self.direction, "column": {"type": self.artifact_search_sort_type, "fields": self.fields}}


class GovernArtifactSearchSortFieldDefinition(object):
    """
    A field sort definition builder to use in a search query in order to sort on a field of a blueprint.

    :param str blueprint_id: the Blueprint ID
    :param str field_id: the field ID
    """

    def __init__(self, blueprint_id, field_id):
        self.blueprint_id = blueprint_id
        self.field_id = field_id

    def build(self):
        """
        :return: the field search sort definition
        :rtype: dict
        """
        return {"blueprintId": self.blueprint_id, "fieldId": self.field_id}


########################################################
# Search Filters
########################################################

class GovernArtifactFilter(object):
    """
    An abstract class to represent artifact filters. Do not instance this class but one of its subclasses.
    """

    def __init__(self, filter_type):
        self.filter_type = filter_type

    def build(self):
        raise NotImplementedError("Cannot build an abstract artifact filter")

class GovernArtifactFilterBlueprints(GovernArtifactFilter):
    """
    An artifact filter definition based on a list of specific blueprints.

    :param blueprint_ids: (Optional) the list of blueprint IDs to use to filter the artifacts
    :param blueprint_ids: lsit of str
    """
    def __init__(self, blueprint_ids=None):
        super(GovernArtifactFilterBlueprints, self).__init__(filter_type="blueprints")
        self.blueprint_ids = blueprint_ids if blueprint_ids is not None else []

    def build(self):
        """
        :return: the artifact filter definition as a dict
        :rtype: dict
        """
        return {"type": self.filter_type, "blueprintIds": self.blueprint_ids}

class GovernArtifactFilterBlueprintVersions(GovernArtifactFilter):
    """
    An artifact filter definition based on a list of specific blueprint versions.

    :param blueprint_version_ids: (Optional) the list of blueprint version IDs to use to filter the artifacts.
        A blueprint version ID definition is a dict composed of the blueprint ID and the version ID like the following dict:
        `{"blueprintId": "bp.my_blueprint", "versionId": "bv.my_version"}`.
        You can use :meth:`~dataikuapi.govern.blueprint.GovernBlueprintVersionId.build` to build a blueprint version ID definition directly.
        At the end, the `blueprint_version_ids` parameter expects a value looking like this:
        `[{"blueprintId": "bp.my_blueprint", "versionId": "bv.my_version"}, {"blueprintId": "bp.my_blueprint", "versionId": "bv.my_version2"}`.
    :type blueprint_version_ids: list of dict
    """

    def __init__(self, blueprint_version_ids=None):
        super(GovernArtifactFilterBlueprintVersions, self).__init__(filter_type="blueprintVersions")
        self.blueprint_version_ids = blueprint_version_ids if blueprint_version_ids is not None else []

    def build(self):
        """
        :return: the artifact filter definition as a dict
        :rtype: dict
        """
        return {"type": self.filter_type, "blueprintVersionIds": self.blueprint_version_ids}

class GovernArtifactFilterArtifacts(GovernArtifactFilter):
    """
    An artifact filter definition based on a list of specific artifacts.

    :param artifact_ids: (Optional) the list of artifacts IDs to use to filter the artifacts.
    :type artifact_ids: list of str
    """

    def __init__(self, artifact_ids=None):
        super(GovernArtifactFilterArtifacts, self).__init__(filter_type="artifacts")
        self.artifact_ids = artifact_ids if artifact_ids is not None else []

    def build(self):
        """
        :return: the artifact filter definition as a dict
        :rtype: dict
        """
        return {"type": self.filter_type, "artifactIds": self.artifact_ids}

class GovernArtifactFilterFieldValue(GovernArtifactFilter):
    """
    An artifact filter definition based on specific fields value.

    :param str condition_type: the condition type of the filter. Has to be chosen from EQUALS, CONTAINS, START_WITH, END_WITH.
    :param str condition: (Optional) The value on which the condition will be applied.
    :param str field_id: (Optional) The ID of the field on which the condition will be applied. If not specified the filter will apply on the name.
    :param boolean negate_condition: (Optional) A boolean to negate the condition. By default, the condition is not negated.
    :param str case_sensitive: (Optional) Can be used to activate case-sensitive filtering. By default, filters will not be case-sensitive.
    """

    def __init__(self, condition_type, condition=None, field_id=None, negate_condition=None, case_sensitive=None):
        super(GovernArtifactFilterFieldValue, self).__init__(filter_type="field")
        self.condition_type = condition_type
        self.condition = condition
        self.field_id = field_id
        self.negate_condition = negate_condition
        self.case_sensitive = case_sensitive

    def build(self):
        """
        :return: the artifact filter definition as a dict
        :rtype: dict
        """
        field_filter = {"type": self.filter_type, "conditionType": self.condition_type}
        if self.condition is not None:
            field_filter["condition"] = self.condition
        if self.field_id is not None:
            field_filter["fieldId"] = self.field_id
        if self.negate_condition is not None:
            field_filter["negateCondition"] = self.negate_condition
        if self.case_sensitive is not None:
            field_filter["caseSensitive"] = self.case_sensitive
        return field_filter


class GovernArtifactFilterArchivedStatus(GovernArtifactFilter):
    """
    An artifact filter definition based on the archived status.

    :param boolean is_archived: the value for filtering. If is_archived is set to True, all artifacts including archived ones will be part of the search result
    """

    def __init__(self, is_archived):
        super(GovernArtifactFilterArchivedStatus, self).__init__(filter_type="archived")
        self.is_archived = is_archived

    def build(self):
        """
        :return: the artifact filter definition as a dict
        :rtype: dict
        """
        return {"type": self.filter_type, "isArchived": self.is_archived}

