from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient


class LaunchpadProfile:
    """
    A profile on the Cloud space

    .. important::
        Do not instantiate directly, use
        :meth:`~dataikuapi.launchpad_client.LaunchpadClient.list_profiles`.

    Usage example:

    .. code-block:: python

        # Get profiles
        profiles = client.list_profiles()

    """

    def __init__(self, client: "LaunchpadClient", **kwargs):
        self._client = client
        self._data = kwargs

    def __repr__(self) -> str:
        if self.is_trial:
            return f"<LaunchpadProfile {self.name} (trial)>"
        return f"<LaunchpadProfile {self.name}>"

    @property
    def name(self) -> str:
        """
        The profile name
        """
        return self._data["name"]

    @property
    def total_seats(self) -> int:
        """
        The total number of seats allowed for this profile.
        Returns -1 if unlimited (infinity).
        """
        return self._data["totalSeats"]

    @property
    def used_seats(self) -> int:
        """
        The number of seats currently used for this profile
        """
        return self._data["usedSeats"]

    @property
    def free_seats(self) -> int:
        """
        The number of seats available for this profile.
        Returns -1 if unlimited (infinity).
        """
        if self.total_seats == -1:
            return -1
        return self.total_seats - self.used_seats

    @property
    def is_trial(self) -> bool:
        """
        Whether the profile is a trial seat or not
        """
        return self._data["isTrial"]

    def get_raw(self) -> dict:
        """
        :return: A dictionary representation of the profile
        :rtype: dict
        """
        return self._data
