from typing import TYPE_CHECKING

from .exceptions import DataikuClientException

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient


class LaunchpadNode:
    """
    A node on the Cloud space

    .. important::
        Do not instantiate directly, use
        :meth:`~dataikuapi.launchpad_client.LaunchpadClient.list_nodes()`
    """

    def __init__(self, client: "LaunchpadClient", name: str, type: str):
        self.client = client
        self._data = {"name": name, "type": type}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.type})>"

    @property
    def name(self) -> str:
        """
        The node name
        """
        if not self._data.get("name"):
            raise DataikuClientException(
                "Name must be specified for node.",
            )
        return self._data["name"]

    @property
    def type(self) -> str:
        """
        The node type
        """
        if not self._data.get("type"):
            raise DataikuClientException(
                "Type must be specified for node.",
            )
        return self._data["type"]
