class GovernArtifactSearchHandler(object):
    """
    Handle to perform search queries on artifacts.
    Do not create this directly, use :meth:`dataikuapi.govern_client.GovernClient.get_artifact_search_handler()`
    """

    def __init__(self, client):
        self.client = client

    @staticmethod
    def build_field_artifact_filter(condition_type, condition=None, field_id=None, negate_condition=None,
                                    case_sensitive=None):
        """
        Create a new artifact field filter and return an object to interact with it.

        :param str condition_type: the condition type of the filter. Has to be chosen from EQUALS, CONTAINS, START_WITH,
        END_WITH.
        :param str condition: (Optional) The value on which the condition will be applied.
        :param str field_id: (Optional) The id of the field on which the condition will be applied. If not specified the
        filter will apply on the name.
        :param boolean negate_condition: (Optional) A boolean to negate the condition. By default, the condition is not
        negated.
        :param str case_sensitive: (Optional) Can be used to activate case-sensitive filtering. By default, filters will
        not be case-sensitive.
        :returns The created filter that will be useful to perform the search.
        :rtype: :class:`dataikuapi.govern.artifact_search_handler.GovernFieldValueArtifactFilter`
        """

        return GovernFieldValueArtifactFilter(condition_type, condition, field_id, negate_condition, case_sensitive)

    @staticmethod
    def build_archived_status_artifact_filter(is_archived):
        """
        Create a new artifact archived status filter and return an object to interact with it.

        :param boolean is_archived: the value for filtering. If is_archived is set to True, all artifacts including
        archived ones will be part of the search result
        :returns The created filter that will be useful to filter the search result.
        :rtype: :class:`dataikuapi.govern.artifact_search_handler.GovernFieldValueArtifactFilter`
        """

        return GovernArchivedStatusArtifactFilter(is_archived)

    def build_query(self, artifact_search_source_type, ids_list=None, artifact_filters_list=None, sort_direction=None,
                    sort_column=None, page_size=20, last_artifact_id=None):
        """
        Create a new blueprint and returns a handle to interact with it.

        :param str artifact_search_source_type: a python str that represents the source type of the artifacts. The
        artifact_search_source value must be chosen from: "all", "blueprint", "blueprintVersions" or "artifacts".
        :param list of str ids_list: a list of ids of the parent objects to filter. If only artifacts related to some
         blueprints are wanted, specify the list of blueprint ids that are needed. TODO: what about bp versions ids ?
        :param list artifact_filters_list: A list of :class: `dataikuapi.govern.artifact_search_handler.GovernFieldValueArtifactFilter`
         or :class: `dataikuapi.govern.artifact_search_handler.GovernArchivedStatusArtifactFilter`.

        :param str sort_column: the column on which the results will be sorted. This parameter must be chosen between:
        "name", "workflow", "field".
        :param str sort_direction: the direction on which the results will be sorted. The sort direction must be either
        "ASC" or "DESC".
        :param int page_size: the size of the pagination. Default page size is 20.
        :param str last_artifact_id: the last artifact id to paginate
        :return: the created :class:`govern.models.Blueprint`
        :returns The query object that will perform the search.
        :rtype: :class:`dataikuapi.govern.artifact_search_handler.GovernArtifactSearchRequest`
        """

        if ids_list is None:
            ids_list = []

        if artifact_search_source_type not in ["all", "blueprints", "blueprintVersions", "artifacts"]:
            raise ValueError(""""Parameter artifact_search_source must be chosen from "all", "blueprints", 
            "blueprintVersions", or "artifacts".""")

        artifact_search_source = {"type": artifact_search_source_type}
        if artifact_search_source_type == "blueprints":
            artifact_search_source["blueprintIds"] = ids_list
        if artifact_search_source_type == "blueprintVersions":
            artifact_search_source["blueprintVersionIds"] = ids_list
        if artifact_search_source_type == "artifacts":
            artifact_search_source["artifactIds"] = ids_list

        if artifact_filters_list is None:
            artifact_filters_list = []
        query = {"artifactFilters": [artifact_filter.build() for artifact_filter in artifact_filters_list]}
        if sort_direction is not None or sort_column is not None:
            query["artifactSearchSort"] = {"direction": sort_direction, "column": {"type": sort_column}}

        artifact_search_pagination = {}
        if page_size != 20:
            artifact_search_pagination["pageSize"] = page_size
        if last_artifact_id is not None:
            artifact_search_pagination["lastArtifactId"] = last_artifact_id

        return GovernArtifactSearchRequest(self.client, artifact_search_source, query, artifact_search_pagination)


class GovernArtifactSearchRequest(object):
    """
    A search query object.
    Do not create this directly, use :meth:`dataikuapi.govern.artifact_search_handler.build_query()` and then run the
    query using :meth:`dataikuapi.govern.artifact_search_handler.GovernArtifactSearchRequest.perform_search()`
    """

    def __init__(self, client, artifact_search_source, query, artifact_search_pagination):
        self.client = client
        self.artifact_search_source = artifact_search_source
        self.query = query
        self.artifact_search_pagination = artifact_search_pagination

    def perform_search(self):
        """
        Run the search request.

        :returns The result of the search request.
        :rtype: python dict. This dict contains a key "hasNextPage" and another one "uiArtifacts" which is the list of
        artifacts.
        """
        return self.client._perform_json("POST", "/artifacts/search",
                                         body=self.__build())

    def __build(self):
        return {"artifactSearchSource": self.artifact_search_source,
                "query": self.query,
                "artifactSearchPagination": self.artifact_search_pagination}


class GovernFieldValueArtifactFilter(object):
    """
    A handle to apply filters on specific fields on a search request.
    Do not create this directly, use :meth:`dataikuapi.govern.artifact_search_handler.build_field_artifact_filter()`
    """

    def __init__(self, condition_type, condition, field_id, negate_condition, case_sensitive):
        self.filter_type = "field"
        self.condition_type = condition_type
        self.condition = condition
        self.field_id = field_id
        self.negate_condition = negate_condition
        self.case_sensitive = case_sensitive

    def build(self):
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


class GovernArchivedStatusArtifactFilter(object):
    """
    A handle to apply filters on the archived status of artifacts. Do not create this directly,
    use :meth:`dataikuapi.govern.artifact_search_handler.build_archived_status_artifact_filter()`
    """

    def __init__(self, is_archived):
        self.filter_type = "archived"
        self.is_archived = is_archived

    def build(self):
        return {"type": self.filter_type, "isArchived": self.is_archived}
