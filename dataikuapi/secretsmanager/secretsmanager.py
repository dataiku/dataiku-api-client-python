import sys

from ..utils import _timestamp_ms_to_zoned_datetime

if sys.version_info >= (3, 0):
    import urllib.parse
    dku_quote_fn = urllib.parse.quote
else:
    import urllib
    dku_quote_fn = urllib.quote

if sys.version_info > (3, 4):
    from enum import Enum
else:
    class Enum(object):
        pass
class DSSSecretsManager(object):
    """
    Collection-level handle for DSS Secrets Manager operations.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_secrets_manager` instead

    """

    def __init__(self, client):
        self.client = client

    def list_secrets(self):
        """
        List secrets usable by the current authentication context.

        :returns: secret handles
        :rtype: list of DSSSecret
        """
        items = self.client._perform_json("GET", "/secrets-manager/secrets")
        return [DSSSecret._from_raw(self.client, item) for item in items]

    def get_secret(self, identifier):
        """
        Get a handle to a specific secret identifier.

        :param str identifier: identifier of the secret
        :returns: handle to the secret
        :rtype: DSSSecret
        """
        return DSSSecret(self.client, identifier)

    def create_local_secret(self, identifier, secret_value, permission_items=None, description=None):
        """
        Create a new local secret definition with its initial value.

        :param str identifier: identifier of the secret
        :param str secret_value: initial decrypted value to store for the local secret
        :param list permission_items: optional list of permission item dicts
        :param str description: optional description of the secret
        :returns: typed handle to the created local secret
        :rtype: DSSLocalSecret
        """
        self.client._perform_empty("POST", "/secrets-manager/secrets", body={
            "type": DSSSecretType.LOCAL.value,
            "format": "STRING",
            "ref": identifier,
            "permissionItems": permission_items or [],
            "description": description,
            "secret": secret_value,
        })
        return self.get_secret(identifier).get_as_local_secret()

    def create_vault_secret(self, identifier, vault_id, remote_secret_identifier, remote_secret_version=None, permission_items=None, description=None):
        """
        Create a new secret definition whose value is resolved from a vault.

        :param str identifier: identifier of the secret
        :param str vault_id: identifier of the configured vault provider to use
        :param str remote_secret_identifier: identifier of the secret in the remote vault
        :param str remote_secret_version: optional version of the remote secret to pin
        :param list permission_items: optional list of permission item dicts
        :param str description: optional description of the secret
        :returns: typed handle to the created vault secret
        :rtype: DSSVaultSecret
        """
        self.client._perform_empty("POST", "/secrets-manager/secrets", body={
            "type": DSSSecretType.VAULT.value,
            "format": "STRING",
            "ref": identifier,
            "permissionItems": permission_items or [],
            "description": description,
            "vaultId": vault_id,
            "remoteSecretRef": remote_secret_identifier,
            "remoteSecretVersion": remote_secret_version,
        })
        return self.get_secret(identifier).get_as_vault_secret()


class DSSSecret(object):
    """
    Handle for a specific DSS secret.

    .. important::

        Do not instantiate directly, use :meth:`DSSSecretsManager.list_secrets` or :meth:`DSSSecretsManager.get_secret` instead

    """

    def __init__(self, client, identifier, metadata=None, capabilities=None):
        self.client = client
        self.identifier = identifier
        self._metadata = metadata
        self._capabilities = capabilities

    def refresh(self):
        """
        Refresh this secret's metadata and capabilities from DSS.

        :returns: self
        :rtype: DSSSecret
        """
        self._get_metadata(refresh=True)
        self._get_capabilities(refresh=True)
        return self

    def _get_metadata_value(self, name):
        return self._get_metadata().get(name)

    def _get_metadata(self, refresh=False):
        if self._metadata is None or refresh:
            self._metadata = self.client._perform_json(
                "GET", "/secrets-manager/secrets/%s" % dku_quote_fn(self.identifier)
            )
        return self._metadata

    def _metadata_payload(self):
        metadata = self._get_metadata()
        return {
            "type": metadata.get("type"),
            "format": metadata.get("format"),
            "ref": self.identifier,
            "permissionItems": metadata.get("permissionItems", []),
            "description": metadata.get("description"),
            "createdBy": metadata.get("createdBy"),
            "createdOn": metadata.get("createdOn"),
            "lastUpdatedBy": metadata.get("lastUpdatedBy"),
            "lastUpdatedOn": metadata.get("lastUpdatedOn"),
            "vaultId": metadata.get("vaultId"),
            "remoteSecretRef": metadata.get("remoteSecretRef"),
            "remoteSecretVersion": metadata.get("remoteSecretVersion"),
        }

    @property
    def type(self):
        """The secret type, such as :attr:`DSSSecretType.LOCAL`."""
        secret_type = self._get_metadata_value("type")
        return DSSSecretType(secret_type) if secret_type is not None else None

    @property
    def description(self):
        """The secret description."""
        return self._get_metadata_value("description")

    @description.setter
    def description(self, value):
        self._get_metadata()["description"] = value

    @property
    def permission_items(self):
        """The permission items visible to the current caller."""
        return self._get_metadata().setdefault("permissionItems", [])

    @permission_items.setter
    def permission_items(self, value):
        self._get_metadata()["permissionItems"] = value

    @property
    def created_by(self):
        """The user that created the secret."""
        return self._get_metadata_value("createdBy")

    @property
    def created_on(self):
        """The date and time when the secret was created."""
        return _timestamp_ms_to_zoned_datetime(self._get_metadata_value("createdOn"))

    @property
    def last_updated_by(self):
        """The user who last updated the secret metadata."""
        return self._get_metadata_value("lastUpdatedBy")

    @property
    def last_updated_on(self):
        """The date and time of the latest secret metadata update."""
        return _timestamp_ms_to_zoned_datetime(self._get_metadata_value("lastUpdatedOn"))

    @staticmethod
    def _from_raw(client, raw):
        """
        Internal helper that builds the appropriate secret handle from a metadata payload.

        Returns a :class:`DSSLocalSecret` or :class:`DSSVaultSecret` for the
        corresponding secret type, otherwise a generic :class:`DSSSecret`.
        """
        if raw is None:
            return None
        if raw.get("type") == DSSSecretType.LOCAL.value:
            return DSSLocalSecret(client, raw["ref"], metadata=raw)
        if raw.get("type") == DSSSecretType.VAULT.value:
            return DSSVaultSecret(client, raw["ref"], metadata=raw)
        return DSSSecret(client, raw["ref"], metadata=raw)

    def save(self, confirm_losing_admin_access=False):
        """
        Persist updates made to this secret handle and refresh it from DSS.

        :param bool confirm_losing_admin_access: allow this update to remove
            the caller's ability to administer the secret. Defaults to ``False``.
        :returns: self
        :rtype: DSSSecret
        """
        self.client._perform_empty(
            "PUT",
            "/secrets-manager/secrets/%s/metadata" % dku_quote_fn(self.identifier),
            body={
                "secretMetadata": self._metadata_payload(),
                "confirmLosingAdminAccess": confirm_losing_admin_access,
            },
        )
        self._metadata = None
        self._capabilities = None
        return self

    def _get_capabilities(self, refresh=False):
        if self._capabilities is None or refresh:
            data = self.client._perform_json("GET", "/secrets-manager/secrets/%s/capabilities" % dku_quote_fn(self.identifier))
            self._capabilities = DSSSecretCapabilities.from_dict(data)
        return self._capabilities

    @property
    def can_use(self):
        """Return whether the current caller can use this secret indirectly."""
        return self._get_capabilities().can_use

    @property
    def can_read(self):
        """Return whether the current caller can read this secret value or metadata."""
        return self._get_capabilities().can_read

    @property
    def can_write(self):
        """Return whether the current caller can rotate this secret value."""
        return self._get_capabilities().can_write

    @property
    def can_admin(self):
        """Return whether the current caller can administer this secret metadata and ACLs."""
        return self._get_capabilities().can_admin

    def delete(self):
        """
        Delete this secret.

        :returns: self
        :rtype: DSSSecret
        """
        self.client._perform_empty("DELETE", "/secrets-manager/secrets/%s" % dku_quote_fn(self.identifier))
        self._metadata = None
        return self

    def share_with_user(self, user, can_use=True, can_read=False, can_write=False, is_admin=False):
        """
        Add or replace a user permission on this secret handle.

        Call :meth:`save` to persist the change.

        :param str user: DSS login to share with
        :param bool can_use: grant use permission
        :param bool can_read: grant read permission
        :param bool can_write: grant write permission
        :param bool is_admin: grant admin permission
        :returns: self
        :rtype: DSSSecret
        """
        permission_items = [p for p in self.permission_items if p.get("user") != user]
        permission_items.append({
            "user": user,
            "group": None,
            "use": can_use,
            "read": can_read,
            "write": can_write,
            "admin": is_admin
        })
        self.permission_items = permission_items
        return self

    def revoke_share_with_user(self, user):
        """
        Remove a user permission from this secret handle.

        Call :meth:`save` to persist the change.

        .. caution::

            If the user still gets access through one of their groups, they will keep that access.

        :param str user: DSS login to revoke
        :returns: self
        :rtype: DSSSecret
        """
        self.permission_items = [p for p in self.permission_items if p.get("user") != user]
        return self

    def share_with_group(self, group, can_use=True, can_read=True, can_write=False, is_admin=False):
        """
        Add or replace a group permission on this secret handle.

        Call :meth:`save` to persist the change.

        :param str group: DSS group name to share with
        :param bool can_use: grant use permission
        :param bool can_read: grant read permission
        :param bool can_write: grant write permission
        :param bool is_admin: grant admin permission
        :returns: self
        :rtype: DSSSecret
        """
        permission_items = [p for p in self.permission_items if p.get("group") != group]
        permission_items.append({
            "user": None,
            "group": group,
            "use": can_use,
            "read": can_read,
            "write": can_write,
            "admin": is_admin
        })
        self.permission_items = permission_items
        return self

    def revoke_share_with_group(self, group):
        """
        Remove a group permission from this secret handle.

        Call :meth:`save` to persist the change.

        Direct user permissions are unaffected.

        :param str group: DSS group name to revoke
        :returns: self
        :rtype: DSSSecret
        """
        self.permission_items = [p for p in self.permission_items if p.get("group") != group]
        return self

    def get_as_local_secret(self):
        """
        Get a typed local-secret handle for this secret.

        :returns: a local secret handle
        :rtype: DSSLocalSecret
        """
        return DSSLocalSecret(self.client, self.identifier, metadata=self._metadata, capabilities=self._capabilities)

    def get_as_vault_secret(self):
        """
        Get a typed vault-secret handle for this secret.

        :returns: a vault secret handle
        :rtype: DSSVaultSecret
        """
        return DSSVaultSecret(self.client, self.identifier, metadata=self._metadata, capabilities=self._capabilities)

    def get_value(self, context=None):
        """
        Read the current value of this secret through DSS.

        :param dict context: optional caller-provided context attached to audit usage
        :returns: decrypted or resolved secret value
        :rtype: str
        """
        body = None
        if context is not None:
            body = {"context": context}
        data = self.client._perform_json(
            "POST",
            "/secrets-manager/secrets/%s/actions/read" % dku_quote_fn(self.identifier),
            body=body,
        )
        return data.get("value")

    def __repr__(self):
        return "<DSSSecret identifier=%s>" % self.identifier


class DSSLocalSecret(DSSSecret):
    """
    Typed handle for a local DSS secret.

    .. important::

        Do not instantiate directly, use :meth:`DSSSecret.get_as_local_secret` instead

    """

    def update_value(self, value, context=None):
        """
        Update the value of this local secret.

        :param str value: new decrypted secret value
        :param dict context: optional caller-provided context attached to audit usage
        :returns: self
        :rtype: DSSLocalSecret
        """
        body = {"value": value}
        if context is not None:
            body["context"] = context
        self.client._perform_empty(
            "POST",
            "/secrets-manager/secrets/%s/actions/update-value" % dku_quote_fn(self.identifier),
            body=body,
        )
        self._metadata = None
        return self

    def __repr__(self):
        return "<DSSLocalSecret identifier=%s>" % self.identifier


class DSSVaultSecret(DSSSecret):
    """
    Typed handle for a DSS secret whose value is resolved from a vault.

    .. important::

        Do not instantiate directly, use :meth:`DSSSecret.get_as_vault_secret` instead

    """

    @property
    def vault_id(self):
        """The identifier of the vault backing this secret."""
        return self._get_metadata_value("vaultId")

    @vault_id.setter
    def vault_id(self, value):
        self._get_metadata()["vaultId"] = value

    @property
    def remote_secret_identifier(self):
        """The identifier of the secret in the remote vault."""
        return self._get_metadata_value("remoteSecretRef")

    @remote_secret_identifier.setter
    def remote_secret_identifier(self, value):
        self._get_metadata()["remoteSecretRef"] = value

    @property
    def remote_secret_version(self):
        """The optional version of the remote secret pinned by this secret."""
        return self._get_metadata_value("remoteSecretVersion")

    @remote_secret_version.setter
    def remote_secret_version(self, value):
        self._get_metadata()["remoteSecretVersion"] = value

    def __repr__(self):
        return "<DSSVaultSecret identifier=%s>" % self.identifier


class DSSSecretType(Enum):
    """Enumeration of DSS secret types."""

    LOCAL = "LOCAL"
    VAULT = "VAULT"


class DSSSecretCapabilities(object):
    """
    Client-side capabilities payload for DSS secrets.

    This object exposes what the current authentication context can do on a
    secret.
    """

    def __init__(self, secret_type, can_use, can_read, can_write, can_admin):
        self.type = DSSSecretType(secret_type) if isinstance(secret_type, str) else secret_type
        self.can_use = can_use
        self.can_read = can_read
        self.can_write = can_write
        self.can_admin = can_admin

    @staticmethod
    def from_dict(d):
        """
        Build a capabilities object from a raw DSS payload.

        :param dict d: raw capabilities payload
        :returns: parsed capabilities object
        :rtype: DSSSecretCapabilities
        """
        if d is None:
            return None
        return DSSSecretCapabilities(
            secret_type=d.get("type"),
            can_use=d.get("canUse", False),
            can_read=d.get("canRead", False),
            can_write=d.get("canWrite", False),
            can_admin=d.get("canAdmin", False),
        )

    def __repr__(self):
        return "<DSSSecretCapabilities type=%s can_use=%s can_read=%s can_write=%s can_admin=%s>" % (
            self.type.value if self.type is not None else None,
            self.can_use,
            self.can_read,
            self.can_write,
            self.can_admin,
        )


__all__ = [
    "DSSLocalSecret",
    "DSSSecret",
    "DSSSecretsManager",
    "DSSVaultSecret",
    "DSSSecretType",
]
