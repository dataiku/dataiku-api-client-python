import json
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
from urllib3.util.retry import Retry

from .launchpad.exceptions import (
    DataikuBadRequestException,
    DataikuException,
    DataikuForbiddenException,
    DataikuResourceNotFoundException,
    DataikuResponseException,
    DataikuUnauthorizedException,
)
from .launchpad.group import LaunchpadGroup
from .launchpad.node import LaunchpadNode
from .launchpad.profile import LaunchpadProfile
from .launchpad.response import LaunchpadBulkResponse
from .launchpad.user import LaunchpadInvite, LaunchpadUser

API_VERSION = "v1"
DEFAULT_LAUNCHPAD_URL = f"https://api.launchpad-dku.app.dataiku.io/{API_VERSION}"


class LaunchpadClient:
    """Entry point for the Launchpad API client"""

    def __init__(
        self,
        space_id: str,
        api_key_id: str,
        api_key_secret: str,
        host=DEFAULT_LAUNCHPAD_URL,
        extra_headers: Optional[dict] = None,
    ):
        """
        Instantiate a new Launchpad API client

        .. note::
            Credentials are managed in the Launchpad
            The client credentials will define which operations are allowed
        """
        self.space_id = space_id
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.host = host
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(self.api_key_id, self.api_key_secret)
        retry_strategy = Retry(
            total=1,
            read=1,
            allowed_methods=None,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    ########################################################
    # Invites
    ########################################################

    def build_invite(
        self,
        email: str,
        profile: str,
        groups: Optional[List[str]] = None,
    ) -> LaunchpadInvite:
        """
        Get a handle for a new invite

        .. note::

            This does not create the invite on the Launchpad, it simply returns an object.
            See usage example to create the invite on the Launchpad.

        Usage example:

        .. code-block:: python

            # Invite a user
            invite = client.build_invite("user@example.com", "designer", ["designers"])
            client.create_invites([invite])

        :param email: the email of the invitee to create
        :type email: str
        :param profile: the profile of the invitee across Dataiku & Govern nodes
        :type profile: str
        :param groups: the groups of the invitee across Dataiku & Govern nodes. Defaults to ``[]``
        :type groups: Optional[List[str]]

        :return: An invite object
        :rtype: LaunchpadInvite
        """
        invite = LaunchpadInvite(self, email=email)
        invite.set_profile(profile)
        invite.add_groups(groups or [])
        return invite

    def get_invite(self, email: str) -> LaunchpadInvite:
        """
        Get a handle to interact with an existing invite on the Cloud space

        .. important::

            ``read_users`` scope is required

        :param email: the email of the desired invite
        :type email: str

        :return: An invite object
        :rtype: LaunchpadInvite
        """
        if not email:
            raise DataikuException("email_required: Email cannot be empty")
        return LaunchpadInvite._get_by(self, email=email)

    def list_invites(self, emails: Optional[List[str]] = None) -> List[LaunchpadInvite]:
        """
        List invites on the Cloud space

        .. important::

            ``read_users`` scope is required

        :param emails: the emails of the desired users. Defaults to ``None`` (no filter)
        :type emails: Optional[List[str]]

        :return: A list of invite objects
        :rtype: List[LaunchpadInvite]
        """
        invites = self._perform_json(
            "POST",
            f"/spaces/{self.space_id}/invites/search",
            raw_body={"emails": emails},
        )
        return [LaunchpadInvite(self, **invite) for invite in invites]

    def create_invites(
        self, invites: List[LaunchpadInvite], fail_all_on_error: bool = False
    ) -> Tuple[List[LaunchpadInvite], List[dict]]:
        """
        Create invites on the Cloud space

        .. important::

            ``write_users`` scope is required

        Usage example:

        .. code-block:: python

            # Create multiple invites
            invite_1 = client.build_invite(email_1, "reader")
            invite_2 = client.build_invite(email_2, "designer", ["designers"])
            successes, failures = client.create_invites([invite_1, invite_2])

        :param invites: the list of invite objects to create
        :type invites: List[LaunchpadInvite]
        :param fail_all_on_error: whether to perform the operation atomically, i.e. if one invite fails, all invites fail. Defaults to ``False``
        :type fail_all_on_error: bool

        :return: A Tuple of successes (invite objects) and errors (dicts) objects
        :rtype: Tuple[List[LaunchpadInvite], List[dict]]
        """
        multi_response = self._perform_json(
            "POST",
            f"/spaces/{self.space_id}/invites",
            raw_body=[invite._data for invite in invites],
            params={"failAllOnError": fail_all_on_error},
        )
        response = LaunchpadBulkResponse(self, **multi_response)
        email_to_invite = {invite.email: invite for invite in invites}
        successes = []
        for item in response.successes:
            invite = email_to_invite[item["email"]]
            invite._data["id"] = item["id"]
            successes.append(invite)
        return successes, response.errors

    def update_invites(
        self,
        invites: List[LaunchpadInvite],
        fail_all_on_error=False,
    ) -> Tuple[List[LaunchpadInvite], List[dict]]:
        """
        Update invites on the Cloud space

        .. important::

            ``write_users`` scope is required

        Usage example:

        .. code-block:: python

            # Update invites based on a group
            invites = client.list_invites()
            invites_to_update = [
                invite
                for invite in invites
                if "my-group" in invite.groups
            ]
            for invite in invites_to_update:
                invite.set_profile("designer")
            successes, failures = client.update_invites(invites_to_update)

        :param invites: the list of invite objects to update
        :type invites: List[LaunchpadInvite]
        :param fail_all_on_error: whether to perform the operation atomically, i.e. if one update fails, all updates fail. Defaults to ``False``
        :type fail_all_on_error: bool

        :return: A Tuple of successes (invite objects) and errors (dicts) objects
        :rtype: Tuple[List[LaunchpadInvite], List[dict]]
        """
        multi_response = self._perform_json(
            "PUT",
            f"/spaces/{self.space_id}/invites",
            raw_body=[invite._data for invite in invites],
            params={"failAllOnError": fail_all_on_error},
        )
        response = LaunchpadBulkResponse(self, **multi_response)
        id_to_invite = {invite.id: invite for invite in invites}
        successes = []
        for item in response.successes:
            invite = id_to_invite[item["id"]]
            invite._data.update(item)
            successes.append(invite)

        return successes, response.errors

    def delete_invites(
        self, emails: List[str], fail_all_on_error=False
    ) -> Tuple[List[dict], List[dict]]:
        """
        Delete invites on the Cloud space

        .. important::

            ``write_users`` scope is required

        Usage example:

        .. code-block:: python

            # Delete invites older than 7 days
            invites = client.list_invites()
            invites_to_delete = [
                invite.email
                for invite in invites
                if invite.created_on <= datetime.now(timezone.utc) - timedelta(days=7)
            ]
            successes, failures = client.delete_invites(invites_to_delete)

        :param emails: the list of emails to delete
        :type emails: List[str]
        :param fail_all_on_error: whether to perform the operation atomically, i.e. if one deletion fails, all deletions fail. Defaults to ``False``
        :type fail_all_on_error: bool

        :return: A Tuple of successes (dicts) and errors (dicts) objects
        :rtype: Tuple[List[dict], List[dict]]
        """
        multi_response = self._perform_json(
            "DELETE",
            f"/spaces/{self.space_id}/invites",
            raw_body={"emails": emails},
            params={"failAllOnError": fail_all_on_error},
        )
        response = LaunchpadBulkResponse(self, **multi_response)
        return response.successes, response.errors

    ########################################################
    # Users
    ########################################################

    def get_user(self, email: str) -> LaunchpadUser:
        """
        Get a handle to interact with an existing user on the Cloud space

        .. important::

            ``read_users`` scope is required

        :param str email: the email of the desired user

        :return: A user object
        :rtype: LaunchpadUser
        """
        if not email:
            raise DataikuException("email_required: Email cannot be empty")
        return LaunchpadUser._get_by(self, email=email)

    def list_users(self, emails: Optional[List[str]] = None) -> List[LaunchpadUser]:
        """
        List users on the Cloud space

        .. important::

            ``read_users`` scope is required

        :param emails: the emails of the desired users. Defaults to ``None`` (no filter)
        :type emails: Optional[List[str]]

        :return: A list of user objects
        :rtype: List[LaunchpadUser]
        """
        users = self._perform_json(
            "POST", f"/spaces/{self.space_id}/users/search", raw_body={"emails": emails}
        )
        return [LaunchpadUser(self, **user) for user in users]

    def update_users(
        self,
        users: List[LaunchpadUser],
        fail_all_on_error=False,
        wait_for_propagation=False,
    ) -> Tuple[List[LaunchpadUser], List[dict]]:
        """
        Update users on the Cloud space

        .. important::

            ``write_users`` scope is required

        Usage example:

        .. code-block:: python

            # Update users based on a group
            users = client.list_users()
            users_to_update = [
                user
                for user in users
                if "my-group" in user.groups
            ]
            for user in users_to_update:
                user.set_profile("designer")
            successes, failures = client.update_users(users_to_update)

        :param users: the list of user objects to update
        :type users: List[LaunchpadUser]
        :param fail_all_on_error: whether to perform the operation atomically, i.e. if one update fails, all updates fail. Defaults to ``False``
        :type fail_all_on_error: bool
        :param wait_for_propagation: whether to wait for the changes to propagate to all Dataiku & Govern running nodes. Defaults to ``False``
        :type wait_for_propagation: bool

        :return: A Tuple of successes (user objects) and errors (dicts) objects
        :rtype: Tuple[List[LaunchpadUser], List[dict]]
        """
        multi_response = self._perform_json(
            "PUT",
            f"/spaces/{self.space_id}/users",
            raw_body=[user._data for user in users],
            params={"failAllOnError": fail_all_on_error},
        )
        response = LaunchpadBulkResponse(self, **multi_response)
        id_to_user = {user.id: user for user in users}
        successes = []
        for item in response.successes:
            user = id_to_user[item["id"]]
            user._data.update(item)
            successes.append(user)

        if wait_for_propagation and response.has_task:
            response.task.wait_for_result()
        return successes, response.errors

    def delete_users(
        self,
        emails: List[str],
        fail_all_on_error=False,
        wait_for_propagation=False,
    ) -> Tuple[List[dict], List[dict]]:
        """
        Delete multiple users on the Cloud space

        .. important::

            ``write_users`` scope is required

        Usage example:

        .. code-block:: python

            # Delete users based on a group
            my_group = client.get_group("my-group")
            successes, failures = client.delete_users(my_group.users)

        :param emails: the list of user emails to delete
        :type emails: List[str]
        :param fail_all_on_error: whether to perform the operation atomically, i.e. if one deletion fails, all deletions fail. Defaults to ``False``
        :type fail_all_on_error: bool
        :param wait_for_propagation: whether to wait for the changes to propagate to all Dataiku & Govern running nodes. Defaults to ``False``
        :type wait_for_propagation: bool

        :return: A Tuple of successes (dicts) and errors (dicts) objects
        :rtype: Tuple[List[dict], List[dict]]
        """
        multi_response = self._perform_json(
            "DELETE",
            f"/spaces/{self.space_id}/users",
            raw_body={"emails": emails},
            params={"failAllOnError": fail_all_on_error},
        )
        response = LaunchpadBulkResponse(self, **multi_response)
        if wait_for_propagation and response.has_task:
            response.task.wait_for_result()
        return response.successes, response.errors

    ########################################################
    # Groups
    ########################################################

    def build_group(
        self,
        name: str,
        description: Optional[str] = None,
        emails: Optional[List[str]] = None,
        launchpad_permissions: Optional[Dict[str, bool]] = None,
        dataiku_permissions: Optional[Dict[str, Dict[str, Any]]] = None,
        govern_permissions: Optional[Dict[str, Dict[str, bool]]] = None,
    ) -> LaunchpadGroup:
        """
        Get a handle for a new group

        .. note::

            This does not create the group on the Launchpad, it simply returns an object.
            See usage example to create the group on the Launchpad.

        Usage example:

        .. code-block:: python

            # Create a group
            group = client.build_group("Designers", "Designer group", ["user@example.com"])
            group.launchpad_permissions = {"mayTurnOnSpace": True}
            group.update_permissions({"mayCreateProjects": True}, node_name="design-0")
            group.save()

        :param name: the name of the group to create
        :type name: str
        :param description: the description of the group to create. Defaults to ``None``
        :type description: Optional[str]
        :param emails: the emails of the group to create. Defaults to ``[]``
        :type emails: Optional[List[str]]
        :param launchpad_permissions: the launchpad permissions of the group. Defaults to ``{}``
        :type launchpad_permissions: Optional[Dict[str, bool]]
        :param dataiku_permissions: the permissions of the group across Dataiku nodes. Defaults to ``{}``
        :type dataiku_permissions: Optional[Dict[str, Dict[str, Any]]]
        :param govern_permissions: the govern permissions of the group across Govern nodes. Defaults to ``{}``
        :type govern_permissions: Optional[Dict[str, Dict[str, bool]]]

        :return: A group object
        :rtype: LaunchpadGroup
        """
        group = LaunchpadGroup(self, name=name)
        group.description = description
        if emails:
            group.add_users(emails)
        if launchpad_permissions:
            group.launchpad_permissions = deepcopy(launchpad_permissions)
        if dataiku_permissions:
            group._data["dataikuPermissions"] = deepcopy(dataiku_permissions)
        if govern_permissions:
            group._data["governPermissions"] = deepcopy(govern_permissions)
        return group

    def get_group(self, name: str) -> LaunchpadGroup:
        """
        Get a handle to interact with an existing group on the Cloud space

        .. important::

            ``read_groups`` scope is required

        :param name: the name of the desired group
        :type name: str

        :return: A group object
        :rtype: LaunchpadGroup
        """
        if not name:
            raise DataikuException("name_required: Name cannot be empty")
        return LaunchpadGroup._get_by(self, name=name)

    def list_groups(self, names: Optional[List[str]] = None) -> List[LaunchpadGroup]:
        """
        List groups setup on the Cloud space

        .. important::

            ``read_groups`` scope is required

        :param names: the names of the desired groups. Defaults to ``None`` (no filter)
        :type names: Optional[List[str]]

        :return: A list of group objects
        :rtype: List[LaunchpadGroup]
        """
        groups = self._perform_json(
            "POST", f"/spaces/{self.space_id}/groups/search", raw_body={"names": names}
        )
        return [LaunchpadGroup(self, **group) for group in groups]

    ########################################################
    # Profiles
    ########################################################

    def list_profiles(self) -> List[LaunchpadProfile]:
        """
        List profiles on the Cloud space

        .. important::

            ``read_users`` scope is required

        :return: A list of profile objects
        :rtype: List[LaunchpadProfile]
        """
        user_seats = self._perform_json("GET", f"/spaces/{self.space_id}/profiles")
        return [LaunchpadProfile(self, **profile) for profile in user_seats]

    ########################################################
    # Nodes
    ########################################################

    def list_nodes(self, type: Optional[str] = None) -> List[LaunchpadNode]:
        """
        List nodes on the Cloud space

        :param type: the type of nodes to list. Defaults to ``None`` (no filter)
        :type type: Optional[str]

        :return: A list of node objects
        :rtype: List[LaunchpadNode]
        """
        nodes = self._perform_json(
            "POST",
            f"/spaces/{self.space_id}/nodes/search",
            raw_body={"type": type},
        )
        return [LaunchpadNode(self, **node) for node in nodes]

    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(
        self,
        method,
        path,
        params=None,
        body=None,
        stream=False,
        files=None,
        raw_body=None,
        headers=None,
    ):
        if body is not None:
            body = json.dumps(body)
        elif raw_body is not None:
            body = raw_body

        return self._session.request(
            method,
            f"{self.host}{path}",
            params=params,
            json=body,
            files=files,
            stream=stream,
            headers=headers,
        )

    def _perform_json(
        self,
        method,
        path,
        params=None,
        body=None,
        files=None,
        raw_body=None,
        headers=None,
    ) -> dict:
        try:
            response = self._perform_http(
                method=method,
                path=path,
                params=params,
                body=body,
                files=files,
                stream=False,
                raw_body=raw_body,
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            exception_class_mapping = {
                401: DataikuUnauthorizedException,
                403: DataikuForbiddenException,
                404: DataikuResourceNotFoundException,
                422: DataikuBadRequestException,
            }
            exc = exception_class_mapping.get(
                err.response.status_code, DataikuResponseException
            )
            raise exc(err.response) from err
        if response.status_code == 204:
            return {}
        return response.json()
