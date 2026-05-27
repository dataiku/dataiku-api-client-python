from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from .exceptions import (
    DataikuBadRequestException,
    DataikuClientException,
    DataikuResourceDoesNotExistException,
)
from .response import LaunchpadResponse

if TYPE_CHECKING:
    from ..launchpad_client import LaunchpadClient


Permissions = Dict[str, Union[bool, Dict[str, bool]]]


class LaunchpadGroup:
    """
    A group on the Cloud space

    .. important::
        Do not instantiate directly, use either
        :meth:`~dataikuapi.launchpad_client.LaunchpadClient.get_group` or :meth:`~dataikuapi.launchpad_client.LaunchpadClient.build_group`.

    Usage example:

    .. code-block:: python

        # Create a group
        group = client.build_group("Designers", "Designer group", ["user@example.com"])
        group.launchpad_permissions = {"mayTurnOnSpace": True}
        group.update_permissions({"mayCreateProjects": True}, node_type="dataiku")
        group.update_permissions({"isGovernArchitect": True}, node_type="govern")
        group.save()

        # Get a group
        group = client.get_group("my-group")

        # List groups
        groups = client.list_groups()

    """

    def __init__(
        self, client: "LaunchpadClient", name: str, id: Optional[str] = None, **kwargs
    ):
        self._client = client
        self._data = {"id": id, "name": name}
        self._data.update(kwargs)

        # Initializing mandatory collections
        if not self.launchpad_permissions:
            self._data["launchpadPermissions"] = {}
        if not self.dataiku_permissions:
            self._data["dataikuPermissions"] = {}
        if not self.govern_permissions:
            self._data["governPermissions"] = {}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self._data.get('name')}>"

    @staticmethod
    def _get_by(
        client: "LaunchpadClient",
        *,
        id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> "LaunchpadGroup":
        """
        Get the group from the specified keyword argument

        .. important::

            ``read_groups`` scope is required

        :return: the group object
        :rtype: LaunchpadGroup
        """
        # Optimization with ID
        if id is not None:
            group = client._perform_json("GET", f"/spaces/{client.space_id}/group/{id}")
            return LaunchpadGroup(client, **group)

        groups = client.list_groups(names=[name])
        if not groups:
            raise DataikuResourceDoesNotExistException(
                f"No group with name {name} found on space."
            )
        return groups[0]

    @property
    def id(self) -> str:
        """
        The group ID
        """
        if not self._data.get("id"):
            raise DataikuResourceDoesNotExistException(
                "You must create the group first."
            )
        return self._data["id"]

    @property
    def name(self) -> str:
        """
        The group name
        """
        if not self._data.get("name"):
            raise DataikuClientException(
                "Name must be specified for group.",
            )
        return self._data["name"]

    @property
    def description(self) -> str:
        """
        The group description
        """
        return self._data["description"]

    @description.setter
    def description(self, new_value: str) -> None:
        self._data["description"] = new_value

    @property
    def launchpad_permissions(self) -> Permissions:
        """
        The group's launchpad permissions
        """
        return self._data.get("launchpadPermissions", {})

    @launchpad_permissions.setter
    def launchpad_permissions(self, new_value: Permissions) -> None:
        self._data["launchpadPermissions"] = new_value

    @property
    def dataiku_permissions(self) -> Dict[str, Permissions]:
        """
        The group's dataiku permissions
        """
        return self._data.get("dataikuPermissions", {})

    @property
    def govern_permissions(self) -> Dict[str, Permissions]:
        """
        The group's govern permissions
        """
        return self._data.get("governPermissions", {})

    @property
    def accessible_nodes(self) -> Tuple[str, ...]:
        """
        The group's accessible nodes
        """
        return tuple(self.dataiku_permissions.keys()) + tuple(
            self.govern_permissions.keys()
        )

    @property
    def users(self) -> Tuple[str, ...]:
        """
        The users assigned to this group
        """
        return tuple(user["email"] for user in self._data.get("users", []))

    def grant_node_access(
        self,
        *,
        node_type: Optional[str] = None,
        node_name: Optional[str] = None,
        copy_permissions_from_node: Optional[str] = None,
    ) -> None:
        """
        Grant access to the specified node type or node name

        .. note::

            This grants node access to the group, without giving any permissions (all default to ``False`` on save).
            If the group already had access, this will not update the permissions.
            To update permissions once access is granted, see :meth:`~dataikuapi.launchpad.group.LaunchpadGroup.update_permissions`.

        Usage example:

        .. code-block:: python

            # Grant access and update permissions for a specific node
            group = client.get_group("my-group")
            print(group.accessible_nodes)
            group.grant_node_access(node_name="design-0")
            group.update_permissions(
                {"mayCreateProjects": True},
                node_name="design-0",
                grant_node_access=False,
            )
            group.save()

            # Copy the permissions from an existing node
            group = client.get_group("my-group")
            group.grant_node_access(node_name="automation-0", copy_permissions_from_node="design-0")
            group.save()


        :param node_type: the node_type to set. When provided, ``node_name`` should be ``None``
        :type node_type: Optional[str]
        :param node_name: the node_name to set. When provided, ``node_type`` should be ``None``
        :type node_name: Optional[str]
        :param copy_permissions_from_node: the node name to copy permissions from. Defaults to ``None``
        :type copy_permissions_from_node: Optional[str]
        """
        permissions_field, target_nodes = self._prepare_permission_edit(
            node_name, node_type
        )
        missing_nodes = [
            target_node
            for target_node in target_nodes
            if target_node not in self._data[permissions_field]
        ]
        default_permissions = self._data[permissions_field].get(
            copy_permissions_from_node, {}
        )
        for target_node in missing_nodes:
            self._data[permissions_field][target_node] = default_permissions

    def update_permissions(
        self,
        permissions: Permissions,
        *,
        node_type: Optional[str] = None,
        node_name: Optional[str] = None,
        grant_node_access: bool = True,
    ) -> None:
        """
        Update permissions for the specified node type or node name

        .. note::

            This will not grant access to new nodes.
            To do so, see :meth:`~dataikuapi.launchpad.group.LaunchpadGroup.grant_node_access`.

        Usage example:

        .. code-block:: python

            group = client.get_group("my-group")

            # Update permissions for all dataiku nodes
            group.update_permissions({"mayCreateProjects": True}, node_type="dataiku")

            # Update permissions for a specific node
            group.update_permissions({"mayCreateProjects": True}, node_name="design-0")

            # Update permissions for accessible dataiku nodes
            group.update_permissions(
                {"mayCreateProjects": True},
                node_type="dataiku",
                grant_node_access=False,
            )

            group.save()

        :param permissions: the permissions to update
        :type permissions: dict
        :param node_type: the node_type to set. When provided, ``node_name`` should be ``None``
        :type node_type: Optional[str]
        :param node_name: the node_name to set. When provided, ``node_type`` should be ``None``
        :type node_name: Optional[str]
        :param grant_node_access: whether to grant access and update permissions to nodes matching the criteria, or only update permissions for accessible nodes. Defaults to ``True`` (grant access)
        :type grant_node_access: bool
        """
        permissions_field, target_nodes = self._prepare_permission_edit(
            node_name, node_type
        )
        if grant_node_access:
            self.grant_node_access(node_type=node_type, node_name=node_name)
        accessible_nodes = [
            target_node
            for target_node in target_nodes
            if target_node in self._data[permissions_field]
        ]
        if not accessible_nodes:
            raise DataikuClientException("No node matches for permission update")
        for target_node in accessible_nodes:
            self._data[permissions_field][target_node].update(permissions)

    def revoke_node_access(
        self,
        *,
        node_type: Optional[str] = None,
        node_name: Optional[str] = None,
    ) -> None:
        """
        Revoke access to the specified node type or node name

        .. note::

            This revokes node access to the group.
            If the group was missing access, this will not update anything.

        Usage example:

        .. code-block:: python

            group = client.get_group("my-group")
            print(group.accessible_nodes)
            group.revoke_node_access(node_type="automation")
            group.save()

        :param node_type: the node_type to set. When provided, ``node_name`` should be ``None``
        :type node_type: Optional[str]
        :param node_name: the node_name to set. When provided, ``node_type`` should be ``None``
        :type node_name: Optional[str]
        """
        permissions_field, target_nodes = self._prepare_permission_edit(
            node_name, node_type
        )
        accessible_nodes = [
            target_node
            for target_node in target_nodes
            if target_node in self._data[permissions_field]
        ]
        for target_node in accessible_nodes:
            del self._data[permissions_field][target_node]

    def add_users(self, emails: List[str]) -> None:
        """
        Add the users to the group

        .. note::

            If you want to add a user to multiple groups, use :meth:`~dataikuapi.launchpad.user.LaunchpadUser.add_groups`.

        Usage example:

        .. code-block:: python

            group = client.get_group("my-group")
            group.add_users(["user@example.com"])
            group.save()

        :param emails: the emails of the users to add to the group
        :type emails: List[str]
        """
        emails_ = set(emails)
        users_to_add = self._client.list_users(list(emails_))
        if len(users_to_add) != len(emails_):
            existing_user_emails = {u.email for u in users_to_add}
            missing_users = emails_ - existing_user_emails
            raise DataikuClientException(
                f"The following users do not exist: {', '.join(missing_users)}"
            )
        self._data["users"] = self._data.get("users", []) + [
            {
                "id": user._data["id"],
                "email": user._data["email"],
            }
            for user in users_to_add
            if user.email not in self.users
        ]

    def remove_users(self, emails: List[str]) -> None:
        """
        Remove the users from the group

        Usage example:

        .. code-block:: python

            group = client.get_group(group_id)
            group.remove_users(["user@example.com"])
            group.save()

        :param emails: the emails of the users to remove from the group
        :type emails: List[str]
        """
        self._data["users"] = [
            user
            for user in self._data.get("users", [])
            if user["email"] not in set(emails)
        ]

    def get_raw(self) -> dict:
        """
        :return: A dictionary representation of the group
        :rtype: dict
        """
        return self._data

    def save(self, wait_for_propagation=False) -> None:
        """
        Saves the group

        :param wait_for_propagation: whether to wait for the changes to propagate to all Dataiku running nodes. Defaults to ``False``
        :type wait_for_propagation: bool
        """
        if self._data.get("id"):
            output = self._update()
        else:
            output = self._create()
        response = LaunchpadResponse(self._client, **output)
        if wait_for_propagation and response.has_task:
            response.task.wait_for_result()

    def delete(self, wait_for_propagation=False) -> None:
        """
        Delete the group referenced by this object

        :param wait_for_propagation: whether to wait for the changes to propagate to all Dataiku running nodes. Defaults to ``False``
        :type wait_for_propagation: bool
        """
        output = self._client._perform_json(
            method="DELETE",
            path=f"/spaces/{self._client.space_id}/group/{self.id}",
        )
        response = LaunchpadResponse(self._client, **output)
        if wait_for_propagation and response.has_task:
            response.task.wait_for_result()

    def _create(self) -> dict:
        output = self._client._perform_json(
            method="POST",
            path=f"/spaces/{self._client.space_id}/group",
            raw_body=self._data,
        )
        self._data = output["group"]
        return output

    def _update(self) -> dict:
        output = self._client._perform_json(
            method="PUT",
            path=f"/spaces/{self._client.space_id}/group/{self.id}",
            raw_body=self._data,
        )
        self._data = output["group"]
        return output

    def _prepare_permission_edit(
        self, node_name: Optional[str] = None, node_type: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        if bool(node_name) + bool(node_type) != 1:
            raise ValueError("node_name or node_type must be specified")
        if node_type:
            try:
                nodes = self._client.list_nodes(type=node_type)
            except DataikuBadRequestException as e:
                raise DataikuClientException(
                    f"Node type {node_type} does not exist on the space: {e}"
                )
            if not nodes:
                raise DataikuClientException(
                    f"Node type {node_type} does not exist on the space"
                )
        if node_name:
            nodes = [n for n in self._client.list_nodes() if n.name == node_name]
            if not nodes:
                raise DataikuClientException(
                    f"Node name {node_name} does not exist on the space"
                )
        return (
            (
                "governPermissions"
                if nodes[0].type == "govern"
                else "dataikuPermissions"
            ),
            [n.name for n in nodes],
        )
