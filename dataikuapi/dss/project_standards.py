import re

from dataikuapi.dssclient import DSSFuture


class DSSProjectStandardsCheckSpecInfo(object):
    """
    Info about a Project Standards check spec.
    Project Standards check specs can be created or imported using DSS plugin components.
    """

    def __init__(self, data=None):
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


class DSSProjectStandardsCheck(object):
    """
    A check for Project Standards
    """

    def __init__(self, data=None):
        self.data = data if data is not None else {}

    @property
    def id(self):
        return self.data.get("id") or ""

    @id.setter
    def id(self, value):
        self.data["id"] = value

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

    @check_element_type.setter
    def check_element_type(self, value):
        self.data["checkElementType"] = value

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
    """

    def __init__(self, data=None):
        self.data = data if data is not None else {}

    @classmethod
    def by_project(cls, name, description="", projects=[], checks=[]):
        scope = DSSProjectStandardsScope()
        scope.name = name
        scope.description = description
        scope.selection_method = "BY_PROJECT"
        scope.selected_projects = projects
        scope.checks = checks
        return scope

    @classmethod
    def by_folder(cls, name, description="", folders=[], checks=[]):
        scope = DSSProjectStandardsScope()
        scope.name = name
        scope.description = description
        scope.selection_method = "BY_FOLDER"
        scope.selected_folders = folders
        scope.checks = checks
        return scope

    @classmethod
    def by_tag(cls, name, description="", tags=[], checks=[]):
        scope = DSSProjectStandardsScope()
        scope.name = name
        scope.description = description
        scope.selection_method = "BY_TAG"
        scope.selected_tags = tags
        scope.checks = checks
        return scope

    @property
    def name(self):
        return self.data.get("name") or ""

    @name.setter
    def name(self, value):
        DSSProjectStandardsScope._check_name_validity(value)
        self.data["name"] = value

    @property
    def description(self):
        return self.data.get("description") or ""

    @description.setter
    def description(self, value):
        self.data["description"] = value

    @property
    def selection_method(self):
        """
        :return: The selection method. Returns an empty string if this is the default scope.
        :rtype: str
        """
        return self.data.get("selectionMethod") or ""

    @selection_method.setter
    def selection_method(self, value):
        """
        :param value: The new selection method. Ignored if this is the default scope.
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

    @staticmethod
    def _check_name_validity(name):
        if not name:
            raise ValueError("Scope name cannot be empty")

        if not re.match(r"^[a-zA-Z0-9_-]+$", name):
            raise ValueError("Scope name is invalid: " + name)


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


class DSSProjectStandardsCheckRunInfo(object):
    """
    Contains info about the run of one check
    """

    def __init__(self, data):
        self.data = data if data is not None else {}

    @property
    def check(self):
        """
        :return: the original check configuration
        :rtype: DSSProjectStandardsCheck | None
        """
        check_dict = self.data.get("check")
        return DSSProjectStandardsCheck(check_dict) if check_dict is not None else None

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


class DSSProjectStandardsRunReport(object):
    """
    Report containing the result of all the checks run in the project
    """

    def __init__(self, data=None):
        self.data = data
        self.project_key = data.get("projectKey")
        self.scope = data.get("scope")
        self.requester = data.get("requester")
        self.start_time = data.get("startTime")
        self.total_duration_ms = data.get("totalDurationMs")
        self.raw_bundle_checks_run_info = data.get("bundleChecksRunInfo")

    @property
    def bundle_checks_run_info(self):
        """
        :return: A dict with the info of each run. The key is the check id.
        :rtype: Dict[str, DSSProjectStandardsCheckRunInfo]
        """
        return {k: DSSProjectStandardsCheckRunInfo(v) for (k, v) in self.raw_bundle_checks_run_info.items()}


class DSSProjectStandards(object):
    """
    Handle to interact with Project Standards

    .. warning::
        Do not create this class directly, use :meth:`dataikuapi.dssclient.DSSClient.get_project_standards`
    """

    def __init__(self, client):
        self.client = client

    def list_bundle_check_specs(self, as_type="object"):
        """
        Get the list of the bundle check specs available in the DSS instance.

        :param as_type: How to return the check specs. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: A list of bundle check specs.
                If as_type=dict, each check spec is returned as a dict.
                If as_type=object, each check spec is returned as a :class:`DSSProjectStandardsCheckSpecInfo`.
        :rtype: List[DSSProjectStandardsCheckSpecInfo | dict]
        """
        specs = self.client._perform_json("GET", "/project-standards/bundle-check-specs")
        if specs is None:
            return []
        if as_type == "object":
            return [DSSProjectStandardsCheckSpecInfo(s) for s in specs]
        elif as_type == "dict":
            return specs
        else:
            raise ValueError("Unknown as_type")

    def import_bundle_checks(self, check_specs_element_types, as_type="object"):
        """
        Create new checks by importing check specs.

        :param check_specs_element_types: list of check spec element types to import
        :type check_specs_element_types: List[str]
        :param as_type: How to return the checks. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: A list of bundle checks.
                If as_type=dict, each check is returned as a dict.
                If as_type=object, each check is returned as a :class:`.DSSProjectStandardsCheck`.
        :rtype: List[DSSProjectStandardsCheck | dict]
        """
        checks = self.client._perform_json(
            "POST",
            "/project-standards/bundle-checks/actions/import",
            {"checkSpecElementTypes": check_specs_element_types},
        )
        if checks is None:
            return []
        if as_type == "object":
            return [DSSProjectStandardsCheck(check) for check in checks]
        elif as_type == "dict":
            return checks
        else:
            raise ValueError("Unknown as_type")

    def get_bundle_check(self, check_id, as_type="object"):
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
        check = self.client._perform_json("GET", "/project-standards/bundle-checks/" + check_id)
        if check is None:
            return {}
        if as_type == "object":
            return DSSProjectStandardsCheck(check)
        elif as_type == "dict":
            return check
        else:
            raise ValueError("Unknown as_type")

    def update_bundle_check(self, updated_check):
        """
        Update an existing bundle check

        :param updated_check: the check to update
        :type updated_check: DSSProjectStandardsCheck
        :returns: The updated check returned by the backend
        :rtype: DSSProjectStandardsCheck
        """
        check_dict = updated_check.get_raw()
        result_dict = self.client._perform_json(
            "PUT", "/project-standards/bundle-checks/" + updated_check.id, body=check_dict
        )
        return DSSProjectStandardsCheck(result_dict)

    def delete_bundle_check(self, check_id):
        """
        Delete a bundle check

        :param check_id: id of the check
        :type check_id: str
        """
        self.client._perform_empty("DELETE", "/project-standards/bundle-checks/" + check_id)

    def list_bundle_checks(self, as_type="object"):
        """
        Get the list of the bundle checks configured in the DSS instance.

        :param as_type: How to return the checks. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: A list of bundle checks.
                If as_type=dict, each check is returned as a dict.
                If as_type=object, each check is returned as a :class:`.DSSProjectStandardsCheck`.
        :rtype: List[DSSProjectStandardsCheck | dict]
        """
        checks = self.client._perform_json("GET", "/project-standards/bundle-checks")
        if checks is None:
            return []
        if as_type == "object":
            return [DSSProjectStandardsCheck(check) for check in checks]
        elif as_type == "dict":
            return checks
        else:
            raise ValueError("Unknown as_type")

    def get_bundle_scope(self, scope_name, as_type="object"):
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
        scope = self.client._perform_json("GET", "/project-standards/bundle-scopes/" + scope_name)
        if scope is None:
            return {}
        if as_type == "object":
            return DSSProjectStandardsScope(scope)
        elif as_type == "dict":
            return scope
        else:
            raise ValueError("Unknown as_type")

    def create_bundle_scope(self, new_scope):
        """
        Create a new bundle scope

        :param new_scope: the scope to create
        :type new_scope: DSSProjectStandardsScope
        :returns: The new scope returned by the backend
        :rtype: DSSProjectStandardsScope
        """
        scope_dict = new_scope.get_raw()
        result = self.client._perform_json(
            "POST", "/project-standards/bundle-scopes/" + new_scope.name, body=scope_dict
        )
        return DSSProjectStandardsScope(result)

    def update_bundle_scope(self, updated_scope):
        """
        Update an existing bundle scope

        :param updated_scope: the scope to update
        :type updated_scope: DSSProjectStandardsScope
        :returns: The updated scope returned by the backend
        :rtype: DSSProjectStandardsScope
        """
        scope_dict = updated_scope.get_raw()
        result = self.client._perform_json(
            "PUT", "/project-standards/bundle-scopes/" + updated_scope.name, body=scope_dict
        )
        return DSSProjectStandardsScope(result)

    def delete_bundle_scope(self, scope_name):
        """
        Delete a bundle scope

        :param scope_name: name of the scope
        :type scope_name: str
        """
        self.client._perform_empty("DELETE", "/project-standards/bundle-scopes/" + scope_name)

    def reorder_bundle_scope(self, scope_name, index):
        """
        Move an existing scope to a new index.
        The index should be specified on a list that does not include the scope.

        Ex: you want to move the scope 'foo' at the end of the list of scopes ['foo', 'bar'].
        The list without 'foo' is ['bar'] so the new index should be 1 (and not 2)

        :param scope_name: name of the scope
        :type scope_name: str
        :param index: the new index of the scope.
        :type index: int
        """
        self.client._perform_empty(
            "POST", "/project-standards/bundle-scopes/" + scope_name + "/actions/reorder", {"index": index}
        )

    def list_bundle_scopes(self, as_type="object"):
        """
        Get the list of the bundle scopes configured in the DSS instance.

        :param as_type: How to return the scopes. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: A list of bundle scopes.
                If as_type=dict, each check is returned as a dict.
                If as_type=object, each check is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: List[DSSProjectStandardsScope | dict]
        """
        scopes = self.client._perform_json("GET", "/project-standards/bundle-scopes")
        if scopes is None:
            return []
        if as_type == "object":
            return [DSSProjectStandardsScope(scope) for scope in scopes]
        elif as_type == "dict":
            return scopes
        else:
            raise ValueError("Unknown as_type")

    def get_default_bundle_scope(self, as_type="object"):
        """
        Get the default bundle scope.
        If no existing scope is associated with one project, the default scope will be used.

        :param as_type: How to return the default scope. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: The default bundle scope.
                If as_type=dict,it is returned as a dict.
                If as_type=object, it is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: (DSSProjectStandardsScope | dict)
        """
        scope = self.client._perform_json("GET", "/project-standards/default-bundle-scope")
        if scope is None:
            return {}
        if as_type == "object":
            return DSSProjectStandardsScope(scope)
        elif as_type == "dict":
            return scope
        else:
            raise ValueError("Unknown as_type")

    def set_default_bundle_scope(self, scope):
        """
        Set the default bundle scope.
        Name and description of the default bundle scope cannot be changed.

        :param scope: The new value of default scope
        :type scope: DSSProjectStandardsScope
        :returns: The updated default scope returned by the backend
        :rtype: DSSProjectStandardsScope
        """
        scope_dict = scope.get_raw()
        result = self.client._perform_json("PUT", "/project-standards/default-bundle-scope", body=scope_dict)
        return DSSProjectStandardsScope(result)

    def run_bundle_checks(self, project, check_ids=None, bundle_id=None):
        """
        Run the Project Standards checks on this project.

        :param project: The project or the project key
        :type project: (:class:`dataikuapi.dss.project.DSSProject` | str)
        :param check_ids: List of explicit checks to run. If None, the scope associated to the project will be used to fetch the check ids.
        :type check_ids: (List[str] | None)
        :param bundle_id: The id of the bundle to run the checks on. If None, a temporary bundle will be created with minimal content.
        :type bundle_id: (str | None)
        :return: a :class:`dataikuapi.dss.future.DSSFuture` tracking the progress of the checks. Call
                   :meth:`~dataikuapi.dss.future.DSSFuture.wait_for_result` on the returned object
                   to wait for completion (or failure). The completed object will be an instance of :class:`.DSSProjectStandardsRunReport`
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        project_key = project if isinstance(project, str) else project.project_key
        future_response = self.client._perform_json(
            "POST", "/project-standards/run", params={"projectKey": project_key, "checkIds": check_ids, "bundleId": bundle_id}
        )
        return DSSFuture(
            self.client,
            future_response.get("jobId", None),
            result_wrapper=lambda raw_result: DSSProjectStandardsRunReport(raw_result),
        )

    def get_scope_for_project(self, project, as_type="object"):
        """
        Get the scope details

        :param project: The project or the project key
        :type project: (:class:`dataikuapi.dss.project.DSSProject` | str)
        :param as_type: How to return the scope. Supported values are "dict" and "object" (defaults to **object**)
        :type as_type: str, optional
        :returns: The scope.
                If as_type=dict, scope is returned as a dict.
                If as_type=object, scope is returned as a :class:`.DSSProjectStandardsScope`.
        :rtype: (DSSProjectStandardsScope | dict)
        """
        project_key = project if isinstance(project, str) else project.project_key
        scope = self.client._perform_json(
            "GET", "/project-standards/bundle-scopes/actions/scope-for-project", params={"projectKey": project_key}
        )
        if scope is None:
            return {}
        if as_type == "object":
            return DSSProjectStandardsScope(scope)
        elif as_type == "dict":
            return scope
        else:
            raise ValueError("Unknown as_type")
