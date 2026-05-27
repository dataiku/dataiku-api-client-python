from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .exceptions import DataikuClientException, DataikuResourceDoesNotExistException

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient


class BaseLaunchpadUser:
    """
    A base Launchpad user

    .. important:: Do not instantiate directly
    """

    def __init__(
        self, client: "LaunchpadClient", email: str, id: Optional[str] = None, **kwargs
    ):
        self._client = client
        self._data = {"id": id, "email": email}
        self._data.update(kwargs)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._data.get('email')}>"

    @classmethod
    def _get_by_id(cls, client: "LaunchpadClient", id: str):
        raise NotImplementedError

    @classmethod
    def _list(
        cls, client: "LaunchpadClient", emails: Optional[List[str]] = None
    ) -> List["BaseLaunchpadUser"]:
        raise NotImplementedError

    @classmethod
    def _get_by(
        cls,
        client: "LaunchpadClient",
        *,
        id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> "BaseLaunchpadUser":
        if id is not None:
            return cls._get_by_id(client, id)

        objs = cls._list(client, emails=[email])
        if not objs:
            raise DataikuResourceDoesNotExistException(
                f"No match found for email {email} on space."
            )
        return objs[0]

    @property
    def id(self) -> str:
        """
        The user ID
        """
        if not self._data.get("id"):
            raise DataikuResourceDoesNotExistException(
                "You must invite the user first."
            )
        return self._data["id"]

    @property
    def email(self) -> str:
        """
        The user email
        """
        if not self._data.get("email"):
            raise DataikuClientException(
                "Email must be specified for user.",
            )
        return self._data["email"]

    @property
    def profile(self) -> dict:
        """
        The user profile
        """
        return self._data.get("profile", {})

    @property
    def groups(self) -> Tuple[str, ...]:
        """
        Groups the user belongs to
        """
        return tuple(group["name"] for group in self._data.get("groups", []))

    @property
    def created_on(self) -> datetime:
        """
        The creation date
        """
        if "createdOn" not in self._data:
            raise DataikuResourceDoesNotExistException(
                "You must create the invite first."
            )
        return datetime.strptime(
            self._data["createdOn"][:-6], "%Y-%m-%dT%H:%M:%S.%f"
        ).replace(tzinfo=timezone.utc)

    def set_profile(self, name: str, **kwargs) -> None:
        self._data["profile"] = {
            "name": name,
            **kwargs,
        }

    def add_groups(self, groups: List[str]) -> None:
        groups_ = set(groups)
        groups_to_add = self._client.list_groups(list(groups_))
        if len(groups_to_add) != len(groups_):
            existing_group_names = {g.name for g in groups_to_add}
            missing_groups = groups_ - existing_group_names
            raise DataikuResourceDoesNotExistException(
                f"The following groups do not exist: {', '.join(missing_groups)}"
            )
        self._data["groups"] = self._data.get("groups", []) + [
            {
                "id": group._data["id"],
                "name": group._data["name"],
            }
            for group in groups_to_add
            if group.name not in self.groups
        ]

    def remove_groups(self, groups: List[str]) -> None:
        self._data["groups"] = [
            g for g in self._data.get("groups", []) if g["name"] not in set(groups)
        ]

    def get_raw(self) -> dict:
        """
        :return: A dictionary representation of the object
        :rtype: dict
        """
        return self._data


class LaunchpadUser(BaseLaunchpadUser):
    """
    A user on the Cloud space

    .. important::
        Do not instantiate directly, use
        :meth:`~dataikuapi.launchpad_client.LaunchpadClient.get_user`.

    Usage example:

    .. code-block:: python

        # Get a user
        user = client.get_user("user@example.com")

        # List users
        users = client.list_users()

    """

    @classmethod
    def _get_by_id(cls, client: "LaunchpadClient", id: str) -> Dict:
        user = client._perform_json(
            "GET",
            f"/spaces/{client.space_id}/user/{id}",
        )
        return LaunchpadUser(client, **user)

    @classmethod
    def _list(
        cls, client: "LaunchpadClient", emails: Optional[List[str]] = None
    ) -> List["LaunchpadUser"]:
        return client.list_users(emails=emails)

    @property
    def is_owner(self) -> bool:
        """
        Whether the user is the owner of the space
        """
        return self._data["isOwner"]

    @property
    def admin_properties(self) -> Dict[str, Any]:
        """
        The user's admin properties
        """
        return self._data.setdefault("adminProperties", {})

    @admin_properties.setter
    def admin_properties(self, new_value: Dict[str, Any]) -> None:
        self._data["adminProperties"] = dict(new_value)

    def set_profile(
        self,
        name: str,
        is_trial: bool = False,
        **kwargs,
    ) -> None:
        """
        Set the user's profile

        Usage example:

        .. code-block:: python

            # Update user profile
            user = client.get_user("user@example.com")
            user.set_profile("designer")
            client.update_users([user])

            # Start a trial seat
            user = client.get_user("user@example.com")
            user.set_profile("designer", is_trial=True)
            client.update_users([user])

        :param name: name of the user profile to set
        :type name: str
        :param is_trial: whether the user is a trial user. Defaults to ``False``
        :type is_trial: Optional[bool]
        :param kwargs: additional keyword arguments
        :type kwargs: Any
        """
        super().set_profile(name, isTrial=is_trial, **kwargs)

    def add_groups(self, groups: List[str]) -> None:
        """
        Add the user to the specified groups

        .. note::

            If you want to add multiple users to a group, use :meth:`~dataikuapi.launchpad.group.LaunchpadGroup.add_users`.

        Usage example:

        .. code-block:: python

            user = client.get_user("user@example.com")
            user.add_groups(["designers"])
            client.update_users([user])

        :param groups: the groups to add the user to
        :type groups: List[str]
        """
        super().add_groups(groups)

    def remove_groups(self, groups: List[str]) -> None:
        """
        Remove the user from the specified groups

        Usage example:

        .. code-block:: python

            user = client.get_user("user@example.com")
            user.remove_groups(["designers"])
            client.update_users([user])

        :param groups: the groups to remove the user from
        :type groups: List[str]
        """
        super().remove_groups(groups)

    def set_admin_property(self, key: str, value: Any) -> None:
        """
        Set a single admin property on the user

        Usage example:

        .. code-block:: python

            user = client.get_user("user@example.com")
            user.set_admin_property("key", "value")
            client.update_users([user])

        :param key: the admin property key to set
        :type key: str
        :param value: the admin property value to set
        :type value: Any
        """
        self.admin_properties[key] = value

    def remove_admin_property(self, key: str) -> None:
        """
        Remove a single admin property on the user

        Usage example:

        .. code-block:: python

            user = client.get_user("user@example.com")
            user.remove_admin_property("key")
            client.update_users([user])

        :param key: the admin property key to set
        :type key: str
        """
        self.admin_properties.pop(key, None)


class LaunchpadInvite(BaseLaunchpadUser):
    """
    An invite on the Cloud space

    .. important::
        Do not instantiate directly, use either
        :meth:`~dataikuapi.launchpad_client.LaunchpadClient.get_invite` or :meth:`~dataikuapi.launchpad_client.LaunchpadClient.create_invites`.

    Usage example:

    .. code-block:: python

        # Create an invite
        invite = client.build_invite("user@example.com", "designer")
        client.create_invites([invite])

        # Get an invite
        invite = client.get_invite("user@example.com")

        # List invites
        invites = client.list_invites()

    """

    @classmethod
    def _get_by_id(cls, client: "LaunchpadClient", id: str) -> Dict:
        invite = client._perform_json("GET", f"/spaces/{client.space_id}/invite/{id}")
        return LaunchpadInvite(client, **invite)

    @classmethod
    def _list(
        cls, client: "LaunchpadClient", emails: Optional[List[str]] = None
    ) -> List["LaunchpadInvite"]:
        return client.list_invites(emails=emails)

    def set_profile(
        self,
        name: str,
        **kwargs,
    ) -> None:
        """
        Set the user's profile

        Usage example:

        .. code-block:: python

            # Update user profile
            invite = client.get_invite("user@example.com")
            invite.set_profile("designer")
            client.update_invites([invite])

        :param name: name of the user profile to set
        :type name: str
        :param kwargs: additional keyword arguments
        :type kwargs: Any
        """
        super().set_profile(name, **kwargs)

    def add_groups(self, groups: List[str]) -> None:
        """
        Add the user to the specified groups

        Usage example:

        .. code-block:: python

            invite = client.get_invite("user@example.com")
            invite.add_groups(["designers"])
            client.update_invites([invite])

        :param groups: the groups to add the user to
        :type groups: List[str]
        """
        super().add_groups(groups)

    def remove_groups(self, groups: List[str]) -> None:
        """
        Remove the user from the specified groups

        Usage example:

        .. code-block:: python

            invite = client.get_invite("user@example.com")
            invite.remove_groups(["designers"])
            client.update_invites([invite])

        :param groups: the groups to remove the user from
        :type groups: List[str]
        """
        super().remove_groups(groups)
