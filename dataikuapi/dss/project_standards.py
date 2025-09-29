from .utils import DSSTaggableObjectListItem


class DSSProjectStandardsCheckSpecInfo(object):
    """
    Info about a Project Standards check spec.
    Project Standards check specs can be created or imported using DSS plugin components.
    """

    def __init__(self, data):
        self.data = data if data is not None else {}

    @property
    def element_type(self):
        """
        Element type can be considered as a unique identifier for a check spec.
        It's a concatenation of the plugin id and the plugin component id.

        :return: The element type of the check spec
        :rtype: str
        """
        return self.data.get("elementType") or ""

    @property
    def label(self):
        return self.data.get("label") or ""

    @property
    def description(self):
        return self.data.get("description") or ""

    @property
    def owner_plugin_id(self):
        return self.data.get("ownerPluginId") or ""


class DSSProjectStandardsCheckListItem(DSSTaggableObjectListItem):
    """
    An item in a list of checks.

    .. important::

        Do not instantiate directly, use :meth:`~DSSProjectStandards.list_checks`
    """

    def __init__(self, client, data):
        super(DSSProjectStandardsCheckListItem, self).__init__(data)
        self.client = client

    def to_check(self):
        """
        Gets a handle corresponding to this check.

        :rtype: :class:`.DSSProjectStandardsCheck`
        """
        return DSSProjectStandardsCheck(self.client, self._data)

    @property
    def id(self):
        return self._data.get("id") or ""

    @property
    def name(self):
        return self._data.get("name") or ""

    @property
    def description(self):
        return self._data.get("description") or ""

    @property
    def check_element_type(self):
        return self._data.get("checkElementType") or ""

    @property
    def check_params(self):
        return self._data.get("checkParams") or {}


class DSSProjectStandardsCheck(object):
    """
    A check for Project Standards

    .. important::
        Do not create this class directly, use :meth:`~.DSSProjectStandards.get_check`
    """

    def __init__(self, client, data):
        self.data = data if data is not None else {}
        self.client = client

    @property
    def id(self):
        return self.data.get("id") or ""

    @property
    def name(self):
        return self.data.get("name") or ""

    @name.setter
    def name(self, value):
        self.data["name"] = value

    @property
    def description(self):
        return self.data.get("description") or ""

    @description.setter
    def description(self, value):
        self.data["description"] = value

    @property
    def check_element_type(self):
        return self.data.get("checkElementType") or ""

    @property
    def check_params(self):
        return self.data.get("checkParams") or {}

    @check_params.setter
    def check_params(self, value):
        self.data["checkParams"] = value

    @property
    def tags(self):
        return self.data.get("tags") or []

    @tags.setter
    def tags(self, value):
        self.data["tags"] = value

    def get_raw(self):
        """
        Get the raw check

        :rtype: dict
        """
        return self.data

    def save(self):
        """
        Save the check

        :returns: The updated check returned by the backend
        :rtype: DSSProjectStandardsCheck
        """
        result_dict = self.client._perform_json("PUT", "/project-standards/checks/" + self.id, body=self.get_raw())
        return DSSProjectStandardsCheck(self.client, result_dict)

    def delete(self):
        """
        Delete the check
        """
        self.client._perform_empty("DELETE", "/project-standards/checks/" + self.id)

    def __eq__(self, other):
        if not isinstance(other, DSSProjectStandardsCheck):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.description == other.description
            and self.check_element_type == other.check_element_type
            and self.check_params == other.check_params
            and self.tags == other.tags
        )


class DSSProjectStandardsScope(object):
    """
    A scope for Project Standards.
    Use scopes to select which checks a project should run.

    .. important::
        Do not create this class directly, use :meth:`~.DSSProjectStandards.get_scope` or :meth:`~.DSSProjectStandards.get_default_scope`
    """

    def __init__(self, client, data):
        self.client = client
        self.data = data if data is not None else {}

    @property
    def is_default(self):
        return self.selection_method == "ALL"

    @property
    def id(self):
        return self.name

    @property
    def name(self):
        return self.data.get("name") or ""

    @property
    def description(self):
        return self.data.get("description") or ""

    @description.setter
    def description(self, value):
        self.data["description"] = value

    @property
    def selection_method(self):
        """
        :return: The selection method.
        :rtype: str
        """
        return self.data.get("selectionMethod") or ""

    @selection_method.setter
    def selection_method(self, value):
        """
        :param value: The new selection method.
        :type value: str
        """
        self.data["selectionMethod"] = value

    @property
    def selected_projects(self):
        return self.data.get("selectedProjects") or []

    @selected_projects.setter
    def selected_projects(self, value):
        self.data["selectedProjects"] = value

    @property
    def selected_folders(self):
        return self.data.get("selectedFolders") or []

    @selected_folders.setter
    def selected_folders(self, value):
        self.data["selectedFolders"] = value

    @property
    def selected_tags(self):
        return self.data.get("selectedTags") or []

    @selected_tags.setter
    def selected_tags(self, value):
        self.data["selectedTags"] = value

    @property
    def checks(self):
        return self.data.get("checks") or []

    @checks.setter
    def checks(self, value):
        self.data["checks"] = value

    def get_raw(self):
        """
        Get the raw scope

        :rtype: dict
        """
        return self.data

    def reorder(self, index):
        """
        Move the scope to a new index.
        The index should be specified on a list that does not include the scope.

        Ex: you want to move the scope 'foo' at the end of the list of scopes ['foo', 'bar'].
        The list without 'foo' is ['bar'] so the new index should be 1 (and not 2)

        .. note::
            Default scope will always be the last scope, you can't move it or put another scope after it.

        :param index: the new index of the scope.
        :type index: int
        """
        if self.is_default:
            raise Exception("Default scope cannot be reordered")

        self.client._perform_empty(
            "POST", "/project-standards/scopes/" + self.name + "/actions/reorder", {"index": index}
        )

    def save(self):
        """
        Update the scope.

        .. note::
            Description of the default scope cannot be changed.

        :returns: The updated scope returned by the backend
        :rtype: DSSProjectStandardsScope
        """
        path = "/project-standards/scopes/" + self.name
        result = self.client._perform_json("PUT", path, body=self.get_raw())
        return DSSProjectStandardsScope(self.client, result)

    def delete(self):
        """
        Delete the scope
        """
        if self.is_default:
            raise Exception("Default scope cannot be deleted")

        self.client._perform_empty("DELETE", "/project-standards/scopes/" + self.name)

    def __eq__(self, other):
        if not isinstance(other, DSSProjectStandardsScope):
            return NotImplemented
        return (
            self.name == other.name
            and self.description == other.description
            and self.selection_method == other.selection_method
            and self.selected_projects == other.selected_projects
            and self.selected_folders == other.selected_folders
            and self.selected_tags == other.selected_tags
            and self.checks == other.checks
        )


class DSSProjectStandardsCheckRunResult(object):
    """
    The result of the check run
    """

    def __init__(self, data):
        self.data = data if data is not None else {}

    @property
    def status(self):
        """
        The status of the run

        :return: Possible values: RUN_SUCCESS, RUN_ERROR or NOT_APPLICABLE
        :rtype: str
        """
        return self.data.get("status") or ""

    @property
    def severity(self):
        """
        Severity of a potential issue.

        :return: the severity, between 0 and 5. 0 means no issue, 5 means critical issue. None if the run is not a success.
        :rtype: int | None
        """
        return self.data.get("severity")

    @property
    def severity_category(self):
        """
        String representation of the severity.
        None if there is no detected issue or if the run is not a success.

        :return: the severity name. Possible values: LOWEST, LOW, MEDIUM, HIGH, CRITICAL. None if the severity is not between 1 and 5.
        :rtype: str | None
        """
        if not self.severity or self.severity <= 0 or self.severity > 5:
            return None
        severities = ["SUCCESS", "LOWEST", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        return severities[self.severity]

    @property
    def success(self):
        """
        Whether the run was successful and no issue was found.

        :return: True if the run was successful and no issue was found, False otherwise.
        :rtype: bool
        """
        return self.status == "RUN_SUCCESS" and self.severity == 0

    @property
    def message(self):
        """
        :return: A message related to the run result.
        :rtype: str
        """
        return self.data.get("message") or ""

    @property
    def details(self):
        """
        :return: Additional metadata about the run
        :rtype: dict
        """
        return self.data.get("details") or {}

    def __repr__(self):
        return "<CheckRunResult status={} severity={}>".format(self.status, self.severity)


class DSSProjectStandardsCheckRunInfo(object):
    """
    Contains info about the run of one check
    """

    def __init__(self, client, data):
        self.client = client
        self.data = data if data is not None else {}

    @property
    def check(self):
        """
        :return: the original check configuration
        :rtype: DSSProjectStandardsCheckListItem | None
        """
        check_dict = self.data.get("check")
        return DSSProjectStandardsCheckListItem(self.client, check_dict) if check_dict is not None else None

    @property
    def result(self):
        """
        :return: the result of the run
        :rtype: DSSProjectStandardsCheckRunResult | None
        """
        result_dict = self.data.get("result")
        return DSSProjectStandardsCheckRunResult(result_dict) if result_dict is not None else None

    @property
    def duration_ms(self):
        """
        :return: the duration of the check run
        :rtype: int
        """
        return self.data.get("durationMs") or 0

    @property
    def expanded_check_params(self):
        """
        :return: the parameters that have been used when running the check
        :rtype: dict
        """
        return self.data.get("expandedCheckParams") or {}

    def __repr__(self):
        return "<CheckRunInfo check={} result={}>".format(self.check.id if self.check else None, repr(self.result))


class DSSProjectStandardsRunReport(object):
    """
    Report containing the result of all the checks run in the project
    """

    def __init__(self, client, data):
        self.client = client
        data = data if data else {}
        self.data = data
        self.project_key = data.get("projectKey")
        self.scope = data.get("scope")
        self.requester = data.get("requester")
        self.start_time = data.get("startTime")
        self.total_duration_ms = data.get("totalDurationMs")
        self.raw_checks_run_info = data.get("bundleChecksRunInfo")

    @property
    def checks_run_info(self):
        """
        :return: A dict with the info of each run. The key is the check id.
        :rtype: Dict[str, DSSProjectStandardsCheckRunInfo]
        """
        if not self.raw_checks_run_info:
            return {}
        return {k: DSSProjectStandardsCheckRunInfo(self.client, v) for (k, v) in self.raw_checks_run_info.items()}


class DSSProjectStandards(object):
    """
    Handle to interact with Project Standards

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.DSSClient.get_project_standards`
    """

    def __init__(self, client):
        self.client = client

    def list_check_specs(self, as_type="listitems"):
        """
        Get the list of the check specs available in the DSS instance.

        :param as_type: How to return the check specs. Supported values are "listitems" and "objects" (defaults to **objects**)
        :type as_type: str, optional
        :returns: A list of check specs.
                If as_type=listitems, each check spec is returned as a dict.
                If as_type=objects, each check spec is returned as a :class:`.DSSProjectStandardsCheckSpecInfo`.
        :rtype: List[DSSProjectStandardsCheckSpecInfo | dict]
        """
        specs = self.client._perform_json("GET", "/project-standards/check-specs")
        if specs is None:
            return []
        if as_type == "objects" or as_type == "object":
            return [DSSProjectStandardsCheckSpecInfo(s) for s in specs]
        elif as_type == "listitems" or as_type == "listitem":
            return specs
        else:
            raise ValueError("Unknown as_type")

    def create_checks(self, check_specs_element_types, as_type="listitems"):
        """
        Create new checks from check specs.

        :param check_specs_element_types: list of check spec element types to import
        :type check_specs_element_types: List[str]
        :param as_type: How to return the checks. Supported values are "listitems" and "objects" (defaults to **listitems**)
        :type as_type: str, optional
        :returns: A list of checks.
                If as_type=listitems, each check is returned as a :class:`.DSSProjectStandardsCheckListItem`.
                If as_type=objects, each check is returned as a :class:`.DSSProjectStandardsCheck`.
        :rtype: List[DSSProjectStandardsCheck | DSSProjectStandardsCheckListItem]
        """
        checks = self.client._perform_json(
            "POST",
            "/project-standards/checks/actions/import",
            {"checkSpecElementTypes": check_specs_element_types},
        )
        if checks is None:
            return []
        if as_type == "listitems" or as_type == "listitem":
            return [DSSProjectStandardsCheckListItem(self.client, check) for check in checks]
        elif as_type == "objects" or as_type == "object":
            return [DSSProjectStandardsCheck(self.client, check) for check in checks]
        else:
            raise ValueError("Unknown as_type")

    def get_check(self, check_id, as_type="object"):
        """
        Get the check details

        :param check_id: id of the check
        :type check_id: str
        :param as_type: How to return the check. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: The check.
                If as_type=dict, check is returned as a dict.
                If as_type=object, check is returned as a :class:`.DSSProjectStandardsCheck`.
        :rtype: (DSSProjectStandardsCheck | dict)
        """
        check = self.client._perform_json("GET", "/project-standards/checks/" + check_id)
        if as_type == "object":
            return DSSProjectStandardsCheck(self.client, check)
        elif as_type == "dict":
            return check if check else {}
        else:
            raise ValueError("Unknown as_type")

    def list_checks(self, as_type="listitems"):
        """
        Get the list of the checks configured in the DSS instance.

        :param as_type: How to return the checks. Supported values are "listitems" and "objects" (defaults to **listitems**)
        :type as_type: str, optional
        :returns: A list of checks.
                If as_type=listitems, each check is returned as a :class:`.DSSProjectStandardsCheckListItem`.
                If as_type=objects, each check is returned as a :class:`.DSSProjectStandardsCheck`.
        :rtype: List[DSSProjectStandardsCheck | DSSProjectStandardsCheckListItem]
        """
        checks = self.client._perform_json("GET", "/project-standards/checks")
        if checks is None:
            return []
        if as_type == "listitems" or as_type == "listitem":
            return [DSSProjectStandardsCheckListItem(self.client, check) for check in checks]
        elif as_type == "objects" or as_type == "object":
            return [DSSProjectStandardsCheck(self.client, check) for check in checks]
        else:
            raise ValueError("Unknown as_type")

    def get_scope(self, scope_name, as_type="object"):
        """
        Get the scope details

        :param scope_name: name of the scope
        :type scope_name: str
        :param as_type: How to return the scope. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: The scope.
                If as_type=dict, scope is returned as a dict.
                If as_type=object, scope is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: (DSSProjectStandardsScope | dict)
        """
        scope = self.client._perform_json("GET", "/project-standards/scopes/" + scope_name)
        if as_type == "object":
            return DSSProjectStandardsScope(self.client, scope)
        elif as_type == "dict":
            return scope if scope else {}
        else:
            raise ValueError("Unknown as_type")

    def create_scope(self, name, description="", checks=[], selection_method="BY_PROJECT", items=[]):
        """
        Create a new scope

        :param name: name of the scope, it cannot be changed later
        :type name: str
        :param description: description of the scope
        :type description: str, optional
        :param checks: list of checks associated to the scope
        :type checks: List[str], optional
        :param selection_method: the kind of objects the scope will select. Supported values are "BY_PROJECT", "BY_FOLDER", and "BY_TAG" (defaults to "BY_PROJECT")
        :type selection_method: str, optional
        :param items: list of object ids selected by the scope. The kind of the objects depends on `selection_method`. `BY_PROJECT` -> project keys. `BY_FOLDER` -> folder ids. `BY_TAG` -> tags.
        :type items: List[str], optional
        :returns: The new scope returned by the backend
        :rtype: DSSProjectStandardsScope
        """
        scope = {
            "name": name,
            "description": description,
            "checks": checks,
            "selectionMethod": selection_method,
        }
        if selection_method == "BY_PROJECT":
            scope["selectedProjects"] = items
        elif selection_method == "BY_FOLDER":
            scope["selectedFolders"] = items
        elif selection_method == "BY_TAG":
            scope["selectedTags"] = items

        result = self.client._perform_json("POST", "/project-standards/scopes/" + name, body=scope)
        return DSSProjectStandardsScope(self.client, result)

    def list_scopes(self, as_type="listitems"):
        """
        Get the list of the scopes configured in the DSS instance.

        :param as_type: How to return the scopes. Supported values are "listitems" and "objects" (defaults to **listitems**)
        :type as_type: str, optional
        :returns: A list of scopes.
                If as_type=listitems, each check is returned as a dict.
                If as_type=objects, each check is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: List[DSSProjectStandardsScope | dict]
        """
        scopes = self.client._perform_json("GET", "/project-standards/scopes")
        if scopes is None:
            return []
        if as_type == "objects" or as_type == "object":
            return [DSSProjectStandardsScope(self.client, scope) for scope in scopes]
        elif as_type == "listitems" or as_type == "listitem":
            return scopes
        else:
            raise ValueError("Unknown as_type")

    def get_default_scope(self, as_type="object"):
        """
        Get the default scope.
        If no existing scope is associated with one project, the default scope will be used.

        :param as_type: How to return the default scope. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: The default scope.
                If as_type=dict,it is returned as a dict.
                If as_type=object, it is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: (DSSProjectStandardsScope | dict)
        """
        scope = self.client._perform_json("GET", "/project-standards/default-scope")
        if as_type == "object":
            return DSSProjectStandardsScope(self.client, scope)
        elif as_type == "dict":
            return scope if scope else {}
        else:
            raise ValueError("Unknown as_type")
