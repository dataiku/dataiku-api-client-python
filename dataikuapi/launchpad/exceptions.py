import json
from typing import TYPE_CHECKING

from ..utils import DataikuException

if TYPE_CHECKING:
    import requests


class DataikuLaunchpadException(DataikuException):
    """
    Exception launched by the Launchpad when a failure occurred
    """


class DataikuClientException(DataikuLaunchpadException):
    """
    Exception launched by the client when a usage error occurred
    """


class DataikuResponseException(DataikuLaunchpadException):
    """
    Base class for exceptions that wraps a response from the server
    """

    def __init__(self, response: "requests.Response"):
        self.response = response
        try:
            self._error = response.json()
        except ValueError:
            self._error = {"message": response.text}
        super().__init__(self.message)

    @property
    def error(self) -> dict:
        """
        The error as a dictionary
        """
        return self._error

    @property
    def message(self) -> str:
        """
        The error message
        """
        return self._error.get("message", "Unknown error")


class DataikuTaskException(DataikuLaunchpadException):
    """
    Exception launched when a task related failure occurred
    """


class DataikuMissingTaskException(DataikuTaskException):
    """
    Exception launched when attempting to create a task object from a response lacking one
    """


class DataikuTaskTimeoutException(DataikuTaskException):
    """
    Exception launched when timing out awaiting a task completion
    """


class DataikuBadRequestException(DataikuResponseException):
    """
    Exception launched when the request is malformed
    """

    @property
    def error(self) -> dict:
        """
        The error as a dictionary
        """
        return self._error.get("errors", {}).get("json", self._error)

    @property
    def message(self) -> str:
        """
        The error message
        """
        return json.dumps(self.error)


class DataikuResourceDoesNotExistException(DataikuClientException):
    """
    Exception launched when attempting to access an object that does not exist
    """


class DataikuResourceNotFoundException(
    DataikuResponseException, DataikuResourceDoesNotExistException
):
    """
    Exception launched when the resource is not found
    """


class DataikuUnauthorizedException(DataikuResponseException):
    """
    Exception launched when trying to access a resource without proper authorization
    """


class DataikuForbiddenException(DataikuResponseException):
    """
    Exception launched when trying to access a resource without proper scope
    """
