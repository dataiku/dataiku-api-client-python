import time
from typing import TYPE_CHECKING, Optional

from .exceptions import (
    DataikuMissingTaskException,
    DataikuTaskException,
    DataikuTaskTimeoutException,
)

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient
    from .response import _BaseResponse


class LaunchpadTask:
    """
    A long-running task on the Launchpad

    It allows you to track the state of the task and retrieve its result when it is ready

    Usage example:

    .. code-block:: python

        # In this example, create a group, which triggers a task
        group = client.build_group(...)
        group.save(wait_for_propagation=True)  # This will wait for the task to complete before returning

    .. note::
        This class does not need to be instantiated directly.

        A :class:`~dataikuapi.launchpad.task.LaunchpadTask` is usually returned by
        the API calls that are initiating long-running tasks.
    """

    def __init__(
        self,
        client: "LaunchpadClient",
        task_id: str,
    ):
        self._client = client
        self.task_id = task_id

    @staticmethod
    def from_resp(
        client: "LaunchpadClient",
        resp: "_BaseResponse",
    ) -> Optional["LaunchpadTask"]:
        """
        Create a :class:`~dataikuapi.launchpad.task.LaunchpadTask` from the response of
        an endpoint that initiated a long-running task

        :param client: An api client to connect to the Launchpad
        :type client: :class:`~dataikuapi.launchpad_client.LaunchpadClient`
        :param resp: The response of the API call that initiated a long-running task.
        :type resp: :class:`~dataikuapi.launchpad.response._BaseResponse`

        :return: the Launchpad task, if any
        :rtype: Optional[LaunchpadTask]
        """
        if not resp.task_id:
            raise DataikuMissingTaskException("Response does not have a task id")
        return LaunchpadTask(client, resp.task_id)

    @classmethod
    def get_result_wait_if_needed(
        cls,
        client: "LaunchpadClient",
        response: "_BaseResponse",
    ) -> dict:
        """
        :meta private:
        """
        if response.task_id:
            task = LaunchpadTask(client, response.task_id)
            result = task.wait_for_result()
        else:
            result = response.get_raw()
        return result

    def wait_for_result(self, timeout=0) -> Optional[dict]:
        """
        Wait for the completion of the long-running task, and return its result

        :param timeout: A timeout in seconds. Default value (0) means no timeout
        :type timeout: int
        :return: the result of the task
        :rtype: Optional[dict]
        :raises DataikuTaskException:
            if the task failed to complete
        :raises DataikuTaskTimeoutException:
            if the task failed to complete before the specified timeout
        """
        t_0 = time.monotonic()
        while timeout == 0 or time.monotonic() - t_0 < timeout:
            status = self._client._perform_json(
                "GET",
                f"/spaces/{self._client.space_id}/task/{self.task_id}",
            )
            if not status.get("ready"):
                time.sleep(5)
                continue
            if not status.get("successful"):
                raise DataikuTaskException
            return status.get("result")
        raise DataikuTaskTimeoutException(
            f"Timed out waiting for task {self.task_id} ({timeout}s)"
        )
