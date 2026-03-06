from typing import TYPE_CHECKING, List, Optional

from .task import LaunchpadTask

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient


class _BaseResponse:
    """
    A Launchpad response

    .. important:: Do not instantiate directly
    """

    def __init__(self, client: "LaunchpadClient", **kwargs):
        self._client = client
        self._data = kwargs

    @property
    def task_id(self) -> Optional[str]:
        """ID of the task associated with this response, if any"""
        return self._data.get("taskId")

    @property
    def has_task(self) -> bool:
        """Whether this response has an associated task"""
        return bool(self.task_id)

    @property
    def task(self) -> Optional[LaunchpadTask]:
        """The task associated with this response, if any"""
        return LaunchpadTask.from_resp(self._client, self) if self.has_task else None

    def get_raw(self) -> dict:
        """
        :return: A dictionary representation of the response
        :rtype: dict
        """
        return self._data


class LaunchpadResponse(_BaseResponse):
    """
    A Launchpad response

    .. important:: Do not instantiate directly
    """


class LaunchpadBulkResponse(_BaseResponse):
    """
    A Launchpad bulk response

    .. important:: Do not instantiate directly
    """

    @property
    def successes(self) -> List[dict]:
        """
        The list of successful items in the bulk response
        """
        return self._data.get("successes", [])

    @property
    def errors(self) -> List[dict]:
        """
        The list of error items in the bulk response
        """
        return self._data.get("errors", [])
