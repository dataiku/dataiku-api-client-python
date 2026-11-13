from ..utils import DataikuException, _ExponentialBackoff
from ._utils import dku_quote_fn, _format_list


class OperationSearchResult(object):
    """
    A bounded operation search result.

    Use :attr:`has_more` to determine whether more operations matched and narrower filters are needed.
    Do not create this directly; use :meth:`dataikuapi.AgentManagementClient.list_operations`, :meth:`dataikuapi.agentmanagement.platform.Platform.list_operations`
    or :meth:`dataikuapi.agentmanagement.agent.Agent.list_operations`.
    """
    def __init__(self, client, response, as_type="listitems"):
        operations = response["operations"]
        self.operations = _format_list([OperationListItem(client, operation) for operation in operations], as_type)
        self.has_more = response["hasMore"]


class Operation(object):
    """
    An Agent Management asynchronous operation.

    Do not create this directly. Start an asynchronous Agent Management action or use
    :meth:`dataikuapi.agentmanagement.platform.Platform.get_operation` or :meth:`dataikuapi.agentmanagement.agent.Agent.get_operation`.
    """
    def __init__(self, client, platform_id, operation_id, agent_id=None):
        self.client = client
        self.platform_id = platform_id
        self.operation_id = operation_id
        self.agent_id = agent_id

    @property
    def id(self):
        return self.operation_id

    def __repr__(self):
        return "<Operation platform_id=%r agent_id=%r id=%r>" % (self.platform_id, self.agent_id, self.operation_id)

    def get_status(self):
        """
        Returns status information about this operation.

        :rtype: :class:`dataikuapi.agentmanagement.operations.OperationStatus`
        """
        status = self.client._perform_json("GET", self._path())
        return OperationStatus(self.client, self.platform_id, self.operation_id, status)

    def get_result(self):
        """
        Returns the completed operation result, or None for operations without a result.

        :rtype: dict or None
        """
        return self.client._perform_json("GET", self._path("result")).get("result")

    def wait_for_completion(self, no_fail=False):
        """
        Waits for this operation to reach a terminal state.

        :param boolean no_fail: if False, raises an exception when the operation fails or is aborted
        :returns: the terminal operation status
        :rtype: :class:`dataikuapi.agentmanagement.operations.OperationStatus`
        """
        successful_statuses = ["FINISHED", "FINISHED_WITH_WARNINGS"]
        terminal_statuses = successful_statuses + ["FAILED", "ABORTED"]
        backoff = _ExponentialBackoff()
        status = self.get_status()
        status_name = status.get_raw().get("status")
        while status_name not in terminal_statuses:
            backoff.sleep_next()
            status = self.get_status()
            status_name = status.get_raw().get("status")

        if no_fail or status_name in successful_statuses:
            return status

        error_message = status.get_raw().get("errorMessage")
        details = ": %s" % error_message if error_message else ""
        raise DataikuException("Agent Management operation %s returned status %s%s" % (self.operation_id, status_name, details))

    def wait_for_result(self):
        """
        Waits for this operation to complete successfully and returns its result.

        :returns: the completed operation result, or None for operations without a result
        :rtype: dict or None
        """
        self.wait_for_completion()
        return self.get_result()

    def abort(self):
        """Requests cancellation of the operation."""
        self.client._perform_empty("POST", self._path("actions/abort"))

    def _path(self, suffix=None):
        if self.agent_id is None:
            path = "/agent-management/platforms/%s/operations/%s" % (
                dku_quote_fn(self.platform_id, safe=""),
                dku_quote_fn(self.operation_id, safe=""))
        else:
            path = "/agent-management/platforms/%s/agents/%s/operations/%s" % (
                dku_quote_fn(self.platform_id, safe=""),
                dku_quote_fn(self.agent_id, safe=""),
                dku_quote_fn(self.operation_id, safe=""))
        if suffix is not None:
            path += "/" + suffix
        return path


class OperationStatus(object):
    """
    The status of an Agent Management asynchronous operation.

    Do not create this directly, use :meth:`dataikuapi.agentmanagement.operations.Operation.get_status`.
    """
    def __init__(self, client, platform_id, operation_id, status):
        self.client = client
        self.platform_id = platform_id
        self.operation_id = operation_id
        self.status = status

    def get_raw(self):
        """
        Returns the raw status of this operation.

        :rtype: dict
        """
        return self.status


class OperationListItem(dict):
    """A Operation listing entry with local accessors and conversion to a resource handle."""

    def __init__(self, client, data):
        super(OperationListItem, self).__init__(data)
        self.client = client

    @property
    def id(self):
        """The listing entry's id."""
        return self["id"]

    @property
    def platform_id(self):
        """The listing entry's platform id."""
        return self.get("infraId")

    @property
    def agent_id(self):
        """The listing entry's agent id."""
        return self.get("agentId")

    @property
    def status(self):
        """The listing entry's status."""
        return self.get("status")

    @property
    def type(self):
        """The listing entry's type."""
        return self.get("type")

    def to_operation(self):
        """Return a :class:`Operation` handle without making an API call."""
        return Operation(self.client, self.platform_id, self.id, self.agent_id)

    def _to_object(self):
        return self.to_operation()
