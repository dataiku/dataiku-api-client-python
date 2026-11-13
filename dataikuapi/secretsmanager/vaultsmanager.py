from ..utils import _timestamp_ms_to_zoned_datetime
from .secretsmanager import Enum, dku_quote_fn


class DSSVaultType(Enum):
    """Enumeration of vault provider types supported by DSS."""

    AWS_SECRETS_MANAGER = "AWS_SECRETS_MANAGER"
    AZURE_KEY_VAULT = "AZURE_KEY_VAULT"
    GCP_SECRET_MANAGER = "GCP_SECRET_MANAGER"


class AWSSecretsManagerAuthMode(Enum):
    """Enumeration of authentication modes supported for AWS Secrets Manager vaults."""

    ENVIRONMENT = "ENVIRONMENT"
    IAM_ROLE = "IAM_ROLE"
    KEYPAIR = "KEYPAIR"


class AWSSecretsManagerAuthConfigBase(object):
    """
    Base class for AWS Secrets Manager vault authentication configurations.

    Do not instantiate this class directly. Use one of the concrete subclasses
    to describe how DSS should authenticate against the remote AWS Secrets Manager service.
    """

    @staticmethod
    def from_raw(raw):
        """
        Build the appropriate authentication config object from a raw DSS payload.

        :param dict raw: raw authentication configuration as returned by DSS
        :returns: typed authentication configuration
        :rtype: AWSSecretsManagerAuthConfigBase
        """
        if raw is None:
            return None

        auth_type = raw.get("type")
        if auth_type == AWSSecretsManagerAuthMode.ENVIRONMENT.value:
            return AWSEnvironmentAuthConfig()
        if auth_type == AWSSecretsManagerAuthMode.IAM_ROLE.value:
            return AWSIAMRoleAuthConfig(
                role_arn=raw.get("roleArn"),
                external_id=raw.get("externalId"),
                duration_seconds=raw.get("durationSeconds"),
                sts_endpoint=raw.get("stsEndpoint"),
            )
        if auth_type == AWSSecretsManagerAuthMode.KEYPAIR.value:
            return AWSKeypairAuthConfig(
                access_key=raw.get("accessKey"),
                secret_key=raw.get("secretKey"),
                session_token=raw.get("sessionToken"),
            )

        raise ValueError("Unsupported AWS auth config type '%s'" % auth_type)

    def get_raw(self):
        """
        Serialize this authentication configuration to the DSS payload format.

        :returns: raw authentication configuration
        :rtype: dict
        """
        raise NotImplementedError()


class AWSEnvironmentAuthConfig(AWSSecretsManagerAuthConfigBase):
    """Use environment-provided AWS credentials when accessing the remote vault."""

    def get_raw(self):
        return {"type": AWSSecretsManagerAuthMode.ENVIRONMENT.value}


class AWSIAMRoleAuthConfig(AWSSecretsManagerAuthConfigBase):
    """Use an AWS IAM role assumption flow when accessing the remote vault."""

    def __init__(self, role_arn, external_id=None, duration_seconds=None, sts_endpoint=None):
        """
        Create an IAM role-based authentication configuration.

        :param str role_arn: ARN of the IAM role to assume
        :param str external_id: optional external ID to use during role assumption
        :param int duration_seconds: optional STS session duration in seconds
        :param str sts_endpoint: optional AWS region or custom endpoint URL for STS
        """
        self.role_arn = role_arn
        self.external_id = external_id
        self.duration_seconds = duration_seconds
        self.sts_endpoint = sts_endpoint

    def get_raw(self):
        return {
            "type": AWSSecretsManagerAuthMode.IAM_ROLE.value,
            "roleArn": self.role_arn,
            "externalId": self.external_id,
            "durationSeconds": self.duration_seconds,
            "stsEndpoint": self.sts_endpoint,
        }


class AWSKeypairAuthConfig(AWSSecretsManagerAuthConfigBase):
    """Use an explicit AWS access key / secret key pair when accessing the remote vault."""

    def __init__(self, access_key, secret_key, session_token=None):
        """
        Create a keypair-based authentication configuration.

        :param str access_key: AWS access key ID
        :param str secret_key: AWS secret access key
        :param str session_token: optional AWS session token
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.session_token = session_token

    def get_raw(self):
        return {
            "type": AWSSecretsManagerAuthMode.KEYPAIR.value,
            "accessKey": self.access_key,
            "secretKey": self.secret_key,
            "sessionToken": self.session_token,
        }


class AzureKeyVaultAuthMode(Enum):
    """Enumeration of authentication modes supported for Azure Key Vault vaults."""

    ENVIRONMENT = "ENVIRONMENT"
    MANAGED_IDENTITY = "MANAGED_IDENTITY"
    CLIENT_SECRET = "CLIENT_SECRET"
    CLIENT_CERTIFICATE = "CLIENT_CERTIFICATE"


class AzureKeyVaultAuthConfigBase(object):
    """
    Base class for Azure Key Vault authentication configurations.

    Do not instantiate this class directly. Use one of the concrete subclasses
    to describe how DSS should authenticate against the remote Azure Key Vault service.
    """

    @staticmethod
    def from_raw(raw):
        """
        Build the appropriate authentication config object from a raw DSS payload.

        :param dict raw: raw authentication configuration as returned by DSS
        :returns: typed authentication configuration
        :rtype: AzureKeyVaultAuthConfigBase
        """
        if raw is None:
            return None

        auth_type = raw.get("type")
        if auth_type == AzureKeyVaultAuthMode.ENVIRONMENT.value:
            return AzureEnvironmentAuthConfig(
                authority_host=raw.get("authorityHost"),
            )
        if auth_type == AzureKeyVaultAuthMode.MANAGED_IDENTITY.value:
            return AzureManagedIdentityAuthConfig(
                managed_identity_resource_id=raw.get("managedIdentityResourceId"),
            )
        if auth_type == AzureKeyVaultAuthMode.CLIENT_SECRET.value:
            return AzureClientSecretAuthConfig(
                tenant_id=raw.get("tenantId"),
                client_id=raw.get("clientId"),
                client_secret=raw.get("clientSecret"),
                authority_host=raw.get("authorityHost"),
            )
        if auth_type == AzureKeyVaultAuthMode.CLIENT_CERTIFICATE.value:
            return AzureClientCertificateAuthConfig(
                tenant_id=raw.get("tenantId"),
                client_id=raw.get("clientId"),
                certificate_path=raw.get("certificatePath"),
                password=raw.get("password"),
                authority_host=raw.get("authorityHost"),
            )

        raise ValueError("Unsupported Azure auth config type '%s'" % auth_type)

    def get_raw(self):
        """
        Serialize this authentication configuration to the DSS payload format.

        :returns: raw authentication configuration
        :rtype: dict
        """
        raise NotImplementedError()


class AzureEnvironmentAuthConfig(AzureKeyVaultAuthConfigBase):
    """Use environment-provided Azure credentials when accessing the remote vault."""

    def __init__(self, authority_host=None):
        """
        Create an environment-based authentication configuration.

        :param str authority_host: optional Azure Active Directory authority host
        """
        self.authority_host = authority_host

    def get_raw(self):
        return {
            "type": AzureKeyVaultAuthMode.ENVIRONMENT.value,
            "authorityHost": self.authority_host,
        }


class AzureManagedIdentityAuthConfig(AzureKeyVaultAuthConfigBase):
    """Use Azure managed identity when accessing the remote vault."""

    def __init__(self, managed_identity_resource_id=None):
        """
        Create a managed identity-based authentication configuration.

        :param str managed_identity_resource_id: optional Azure managed identity resource ID
        """
        self.managed_identity_resource_id = managed_identity_resource_id

    def get_raw(self):
        return {
            "type": AzureKeyVaultAuthMode.MANAGED_IDENTITY.value,
            "managedIdentityResourceId": self.managed_identity_resource_id,
        }


class AzureClientSecretAuthConfig(AzureKeyVaultAuthConfigBase):
    """Use an explicit Azure application client secret when accessing the remote vault."""

    def __init__(self, tenant_id, client_id, client_secret, authority_host=None):
        """
        Create a client secret-based authentication configuration.

        :param str tenant_id: Azure tenant identifier
        :param str client_id: Azure application client identifier
        :param str client_secret: Azure application client secret
        :param str authority_host: optional Azure Active Directory authority host
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority_host = authority_host

    def get_raw(self):
        return {
            "type": AzureKeyVaultAuthMode.CLIENT_SECRET.value,
            "tenantId": self.tenant_id,
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
            "authorityHost": self.authority_host,
        }


class AzureClientCertificateAuthConfig(AzureKeyVaultAuthConfigBase):
    """Use an Azure application client certificate when accessing the remote vault."""

    def __init__(self, tenant_id, client_id, certificate_path, password=None, authority_host=None):
        """
        Create a client certificate-based authentication configuration.

        :param str tenant_id: Azure tenant identifier
        :param str client_id: Azure application client identifier
        :param str certificate_path: path to the client certificate PFX file on the DSS host
        :param str password: optional client certificate password
        :param str authority_host: optional Azure Active Directory authority host
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.certificate_path = certificate_path
        self.password = password
        self.authority_host = authority_host

    def get_raw(self):
        return {
            "type": AzureKeyVaultAuthMode.CLIENT_CERTIFICATE.value,
            "tenantId": self.tenant_id,
            "clientId": self.client_id,
            "certificatePath": self.certificate_path,
            "password": self.password,
            "authorityHost": self.authority_host,
        }


class GCPSecretManagerAuthMode(Enum):
    """Enumeration of authentication modes supported for GCP Secret Manager vaults."""

    ENVIRONMENT = "ENVIRONMENT"
    KEYPAIR = "KEYPAIR"


class GCPSecretManagerAuthConfigBase(object):
    """Base class for GCP Secret Manager vault authentication configurations. Do not instantiate directly."""

    @staticmethod
    def from_raw(raw):
        """
        Build the appropriate authentication config object from a raw DSS payload.

        :param dict raw: raw authentication configuration as returned by DSS
        :returns: typed authentication configuration
        :rtype: GCPSecretManagerAuthConfigBase
        """
        if raw is None:
            return None

        common_args = {
            "universe_domain": raw.get("universeDomain"),
            "impersonate_service_account_after_initial_auth": raw.get("impersonateServiceAccountAfterInitialAuth", False),
            "service_account_to_impersonate_after_initial_auth": raw.get("serviceAccountToImpersonateAfterInitialAuth"),
            "perform_wif_token_exchange": raw.get("performWIFTokenExchange", False),
            "wif_pool_provider_incoming_audience": raw.get("wifPoolProviderIncomingAudience"),
            "wif_token_audience": raw.get("wifTokenAudience"),
            "wif_token_endpoint": raw.get("wifTokenEndpoint"),
        }
        auth_type = raw.get("type")
        if auth_type == GCPSecretManagerAuthMode.ENVIRONMENT.value:
            return GCPEnvironmentAuthConfig(**common_args)
        if auth_type == GCPSecretManagerAuthMode.KEYPAIR.value:
            return GCPKeypairAuthConfig(
                app_secret_content=raw.get("appSecretContent"),
                service_account_email=raw.get("serviceAccountEmail"),
                **common_args
            )

        raise ValueError("Unsupported GCP auth config type '%s'" % auth_type)

    def __init__(
        self,
        universe_domain=None,
        impersonate_service_account_after_initial_auth=False,
        service_account_to_impersonate_after_initial_auth=None,
        perform_wif_token_exchange=False,
        wif_pool_provider_incoming_audience=None,
        wif_token_audience=None,
        wif_token_endpoint=None,
    ):
        self.universe_domain = universe_domain
        self.impersonate_service_account_after_initial_auth = impersonate_service_account_after_initial_auth
        self.service_account_to_impersonate_after_initial_auth = service_account_to_impersonate_after_initial_auth
        self.perform_wif_token_exchange = perform_wif_token_exchange
        self.wif_pool_provider_incoming_audience = wif_pool_provider_incoming_audience
        self.wif_token_audience = wif_token_audience
        self.wif_token_endpoint = wif_token_endpoint

    def _get_common_raw(self):
        return {
            "universeDomain": self.universe_domain,
            "impersonateServiceAccountAfterInitialAuth": self.impersonate_service_account_after_initial_auth,
            "serviceAccountToImpersonateAfterInitialAuth": self.service_account_to_impersonate_after_initial_auth,
            "performWIFTokenExchange": self.perform_wif_token_exchange,
            "wifPoolProviderIncomingAudience": self.wif_pool_provider_incoming_audience,
            "wifTokenAudience": self.wif_token_audience,
            "wifTokenEndpoint": self.wif_token_endpoint,
        }

    def get_raw(self):
        """Serialize this authentication configuration to the DSS payload format."""
        raise NotImplementedError()


class GCPEnvironmentAuthConfig(GCPSecretManagerAuthConfigBase):
    """Use Google Application Default Credentials when accessing the remote vault."""

    def get_raw(self):
        return dict(self._get_common_raw(), type=GCPSecretManagerAuthMode.ENVIRONMENT.value)


class GCPKeypairAuthConfig(GCPSecretManagerAuthConfigBase):
    """Use a GCP service account key or path when accessing the remote vault."""

    def __init__(
        self,
        app_secret_content,
        service_account_email=None,
        universe_domain=None,
        impersonate_service_account_after_initial_auth=False,
        service_account_to_impersonate_after_initial_auth=None,
        perform_wif_token_exchange=False,
        wif_pool_provider_incoming_audience=None,
        wif_token_audience=None,
        wif_token_endpoint=None,
    ):
        """
        :param str app_secret_content: service account JSON content or a path to a JSON or P12 key file on the DSS host
        :param str service_account_email: service account e-mail, required when using a P12 key file
        :param str universe_domain: optional custom Google universe domain
        :param bool impersonate_service_account_after_initial_auth: whether to impersonate a service account after initial authentication
        :param str service_account_to_impersonate_after_initial_auth: optional service account e-mail to impersonate
        :param bool perform_wif_token_exchange: whether to perform a Workload Identity Federation token exchange
        :param str wif_pool_provider_incoming_audience: optional incoming audience for the WIF pool provider
        :param str wif_token_audience: optional audience for the generated WIF token
        :param str wif_token_endpoint: optional WIF token endpoint URL
        """
        super(GCPKeypairAuthConfig, self).__init__(
            universe_domain=universe_domain,
            impersonate_service_account_after_initial_auth=impersonate_service_account_after_initial_auth,
            service_account_to_impersonate_after_initial_auth=service_account_to_impersonate_after_initial_auth,
            perform_wif_token_exchange=perform_wif_token_exchange,
            wif_pool_provider_incoming_audience=wif_pool_provider_incoming_audience,
            wif_token_audience=wif_token_audience,
            wif_token_endpoint=wif_token_endpoint,
        )
        self.app_secret_content = app_secret_content
        self.service_account_email = service_account_email

    def get_raw(self):
        return dict(
            self._get_common_raw(),
            type=GCPSecretManagerAuthMode.KEYPAIR.value,
            appSecretContent=self.app_secret_content,
            serviceAccountEmail=self.service_account_email,
        )


class DSSVaultCacheSettings(object):
    """Cache settings attached to a DSS vault definition."""

    def __init__(self, max_caching_minutes=5):
        self.max_caching_minutes = max_caching_minutes

    @staticmethod
    def from_raw(raw):
        if raw is None:
            return DSSVaultCacheSettings()
        return DSSVaultCacheSettings(
            max_caching_minutes=raw.get("maxCachingMinutes", 5),
        )

    def get_raw(self):
        return {
            "maxCachingMinutes": self.max_caching_minutes,
        }


class DSSVaultsManager(object):
    """
    Collection-level handle for DSS vault administration operations.

    .. important::

        Do not instantiate directly, use :meth:`dataikuapi.DSSClient.get_vaults_manager` instead

    """

    def __init__(self, client):
        self.client = client

    def list_vaults(self):
        """
        List vaults visible to the current authentication context.

        :returns: vault handles
        :rtype: list of DSSVault
        """
        items = self.client._perform_json("GET", "/secrets-manager/vaults")
        return [DSSVault.from_raw(self.client, item) for item in items]

    def get_vault(self, vault_id):
        """
        Get a handle to a specific vault.

        :param str vault_id: identifier of the vault
        :returns: handle to the vault
        :rtype: DSSVault
        """
        raw = self.client._perform_json("GET", "/secrets-manager/vaults/%s" % dku_quote_fn(vault_id))
        return DSSVault.from_raw(self.client, raw)

    def create_aws_secrets_manager_vault(
        self,
        id,
        region_or_endpoint,
        auth_config=None,
        permission_items=None,
        description=None,
        allowed_remote_secret_identifier_regex=None,
        cache_settings=None,
    ):
        """
        Create a new AWS Secrets Manager vault definition.

        :param str id: identifier of the vault in DSS
        :param str region_or_endpoint: AWS region or custom endpoint for the remote vault
        :param AWSSecretsManagerAuthConfigBase auth_config: optional authentication configuration, defaults to environment-based auth
        :param DSSVaultCacheSettings cache_settings: optional cache settings for remote secret resolution
        :param list permission_items: optional list of permission item dicts
        :param str description: optional description of the vault
        :param str allowed_remote_secret_identifier_regex: optional regex restricting remote secret identifiers allowed through this vault
        :returns: handle to the created vault
        :rtype: DSSVault
        """
        payload = {
            "id": id,
            "type": DSSVaultType.AWS_SECRETS_MANAGER.value,
            "description": description,
            "permissionItems": permission_items or [],
            "allowedRemoteSecretRefRegex": allowed_remote_secret_identifier_regex,
            "cacheSettings": (cache_settings or DSSVaultCacheSettings()).get_raw(),
            "regionOrEndpoint": region_or_endpoint,
            "authConfig": (auth_config or AWSEnvironmentAuthConfig()).get_raw(),
        }
        raw = self.client._perform_json("POST", "/secrets-manager/vaults", body=payload)
        return DSSVault.from_raw(self.client, raw)

    def create_azure_key_vault_vault(
        self,
        id,
        vault_url,
        auth_config=None,
        permission_items=None,
        description=None,
        allowed_remote_secret_identifier_regex=None,
        cache_settings=None,
    ):
        """
        Create a new Azure Key Vault definition.

        :param str id: identifier of the vault in DSS
        :param str vault_url: Azure Key Vault URL for the remote vault
        :param AzureKeyVaultAuthConfigBase auth_config: optional authentication configuration, defaults to environment-based auth
        :param DSSVaultCacheSettings cache_settings: optional cache settings for remote secret resolution
        :param list permission_items: optional list of permission item dicts
        :param str description: optional description of the vault
        :param str allowed_remote_secret_identifier_regex: optional regex restricting remote secret identifiers allowed through this vault
        :returns: handle to the created vault
        :rtype: DSSVault
        """
        payload = {
            "id": id,
            "type": DSSVaultType.AZURE_KEY_VAULT.value,
            "description": description,
            "permissionItems": permission_items or [],
            "allowedRemoteSecretRefRegex": allowed_remote_secret_identifier_regex,
            "cacheSettings": (cache_settings or DSSVaultCacheSettings()).get_raw(),
            "vaultUrl": vault_url,
            "authConfig": (auth_config or AzureEnvironmentAuthConfig()).get_raw(),
        }
        raw = self.client._perform_json("POST", "/secrets-manager/vaults", body=payload)
        return DSSVault.from_raw(self.client, raw)

    def create_gcp_secret_manager_vault(
        self,
        id,
        project_id,
        psc_endpoint_id=None,
        endpoint=None,
        auth_config=None,
        permission_items=None,
        description=None,
        allowed_remote_secret_identifier_regex=None,
        cache_settings=None,
    ):
        """
        Create a new Google Cloud Secret Manager vault definition.

        :param str id: identifier of the vault in DSS
        :param str project_id: GCP project ID containing the remote secrets
        :param str psc_endpoint_id: optional Private Service Connect endpoint ID
        :param str endpoint: optional custom GCP Secret Manager endpoint
        :param GCPSecretManagerAuthConfigBase auth_config: optional authentication configuration, defaults to environment-based auth
        :param DSSVaultCacheSettings cache_settings: optional cache settings for remote secret resolution
        :param list permission_items: optional list of permission item dicts
        :param str description: optional description of the vault
        :param str allowed_remote_secret_identifier_regex: optional regex restricting remote secret identifiers allowed through this vault
        :returns: handle to the created vault
        :rtype: DSSVault
        """
        payload = {
            "id": id,
            "type": DSSVaultType.GCP_SECRET_MANAGER.value,
            "description": description,
            "permissionItems": permission_items or [],
            "allowedRemoteSecretRefRegex": allowed_remote_secret_identifier_regex,
            "cacheSettings": (cache_settings or DSSVaultCacheSettings()).get_raw(),
            "projectId": project_id,
            "pscEndpointId": psc_endpoint_id,
            "endpoint": endpoint,
            "authConfig": (auth_config or GCPEnvironmentAuthConfig()).get_raw(),
        }
        raw = self.client._perform_json("POST", "/secrets-manager/vaults", body=payload)
        return DSSVault.from_raw(self.client, raw)


class DSSVault(object):
    """
    Handle for a specific DSS vault.

    .. important::

        Do not instantiate directly, use :meth:`DSSVaultsManager.list_vaults` or :meth:`DSSVaultsManager.get_vault` instead

    """

    def __init__(
        self,
        client,
        vault_id,
        vault_type=None,
        description=None,
        permission_items=None,
        allowed_remote_secret_identifier_regex=None,
        cache_settings=None,
        region_or_endpoint=None,
        vault_url=None,
        project_id=None,
        psc_endpoint_id=None,
        endpoint=None,
        auth_config=None,
    ):
        self.client = client
        self.id = vault_id
        self.type = vault_type
        self.description = description
        self.permission_items = permission_items or []
        self.allowed_remote_secret_identifier_regex = allowed_remote_secret_identifier_regex
        self.cache_settings = cache_settings or DSSVaultCacheSettings()
        self.region_or_endpoint = region_or_endpoint
        self.vault_url = vault_url
        self.project_id = project_id
        self.psc_endpoint_id = psc_endpoint_id
        self.endpoint = endpoint
        self.auth_config = auth_config
        self._created_by = None
        self._created_on = None
        self._last_updated_by = None
        self._last_updated_on = None

    @classmethod
    def from_raw(cls, client, raw):
        vault = cls(client, raw.get("id"))
        vault._load_from_raw(raw)
        return vault

    def _load_from_raw(self, raw):
        self.id = raw.get("id")
        self.type = raw.get("type")
        self.description = raw.get("description")
        self.permission_items = list(raw.get("permissionItems", []))
        self.allowed_remote_secret_identifier_regex = raw.get("allowedRemoteSecretRefRegex")
        self.cache_settings = DSSVaultCacheSettings.from_raw(raw.get("cacheSettings"))
        if self.type == DSSVaultType.AZURE_KEY_VAULT.value:
            self.region_or_endpoint = None
            self.vault_url = raw.get("vaultUrl")
            self.project_id = None
            self.psc_endpoint_id = None
            self.endpoint = None
            self.auth_config = AzureKeyVaultAuthConfigBase.from_raw(raw.get("authConfig"))
        elif self.type == DSSVaultType.GCP_SECRET_MANAGER.value:
            self.region_or_endpoint = None
            self.vault_url = None
            self.project_id = raw.get("projectId")
            self.psc_endpoint_id = raw.get("pscEndpointId")
            self.endpoint = raw.get("endpoint")
            self.auth_config = GCPSecretManagerAuthConfigBase.from_raw(raw.get("authConfig"))
        else:
            self.region_or_endpoint = raw.get("regionOrEndpoint")
            self.vault_url = None
            self.project_id = None
            self.psc_endpoint_id = None
            self.endpoint = None
            self.auth_config = AWSSecretsManagerAuthConfigBase.from_raw(raw.get("authConfig"))
        self._created_by = raw.get("createdBy")
        self._last_updated_by = raw.get("lastUpdatedBy")
        self._created_on = raw.get("createdOn")
        self._last_updated_on = raw.get("lastUpdatedOn")

    @property
    def created_by(self):
        """Get the user that created the vault."""
        return self._created_by

    @property
    def last_updated_by(self):
        """Get the user who last updated the vault."""
        return self._last_updated_by

    @property
    def created_on(self):
        """
        Get the date and time when the vault was created.

        :rtype: :class:`datetime.datetime`
        """
        return _timestamp_ms_to_zoned_datetime(self._created_on)

    @property
    def last_updated_on(self):
        """
        Get the date and time of the latest vault update.

        :rtype: :class:`datetime.datetime`
        """
        return _timestamp_ms_to_zoned_datetime(self._last_updated_on)

    def _to_raw(self):
        payload = {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, DSSVaultType) else self.type,
            "description": self.description,
            "permissionItems": self.permission_items,
            "allowedRemoteSecretRefRegex": self.allowed_remote_secret_identifier_regex,
            "cacheSettings": self.cache_settings.get_raw() if self.cache_settings is not None else None,
            "authConfig": self.auth_config.get_raw() if self.auth_config is not None else None,
            "createdBy": self._created_by,
            "createdOn": self._created_on,
            "lastUpdatedBy": self._last_updated_by,
            "lastUpdatedOn": self._last_updated_on,
        }
        if payload["type"] == DSSVaultType.AZURE_KEY_VAULT.value:
            payload["vaultUrl"] = self.vault_url
        elif payload["type"] == DSSVaultType.GCP_SECRET_MANAGER.value:
            payload["projectId"] = self.project_id
            payload["pscEndpointId"] = self.psc_endpoint_id
            payload["endpoint"] = self.endpoint
        else:
            payload["regionOrEndpoint"] = self.region_or_endpoint
        return payload

    def save(self):
        """
        Persist updates made to this vault handle.

        The local object fields are sent back to DSS, then refreshed from the
        server response.

        :returns: self
        :rtype: DSSVault
        """
        if self.type is None:
            raise ValueError("No vault definition loaded")
        self.client._perform_empty("PUT", "/secrets-manager/vaults/%s" % dku_quote_fn(self.id), body=self._to_raw())
        self._load_from_raw(self.client._perform_json("GET", "/secrets-manager/vaults/%s" % dku_quote_fn(self.id)))
        return self

    def list_referencing_secret_identifiers(self):
        """
        List DSS secret identifiers currently backed by this vault.

        :returns: list of secret identifier strings
        :rtype: list
        """
        return self.client._perform_json(
            "GET",
            "/secrets-manager/vaults/%s/referencing-secret-refs" % dku_quote_fn(self.id),
        )

    def delete(self):
        """
        Delete this vault definition from DSS.

        :returns: self
        :rtype: DSSVault
        """
        self.client._perform_empty("DELETE", "/secrets-manager/vaults/%s" % dku_quote_fn(self.id))
        self.type = None
        self.description = None
        self.permission_items = []
        self.allowed_remote_secret_identifier_regex = None
        self.cache_settings = DSSVaultCacheSettings()
        self.region_or_endpoint = None
        self.vault_url = None
        self.project_id = None
        self.psc_endpoint_id = None
        self.endpoint = None
        self.auth_config = None
        self._created_by = None
        self._last_updated_by = None
        self._created_on = None
        self._last_updated_on = None
        return self

    def __repr__(self):
        return "<DSSVault id=%s>" % self.id


__all__ = [
    "AWSEnvironmentAuthConfig",
    "AWSIAMRoleAuthConfig",
    "AWSKeypairAuthConfig",
    "AzureClientCertificateAuthConfig",
    "AzureClientSecretAuthConfig",
    "AzureEnvironmentAuthConfig",
    "AzureManagedIdentityAuthConfig",
    "GCPEnvironmentAuthConfig",
    "GCPKeypairAuthConfig",
    "DSSVaultCacheSettings",
    "DSSVault",
    "DSSVaultType",
    "DSSVaultsManager",
]
