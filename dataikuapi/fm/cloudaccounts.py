from .future import FMFuture


class FMCloudAccountCreator(object):
    def __init__(self, client, label):
        """
        A builder class to create cloud accounts

        :param str label: The label of the cloud account
        """
        self.client = client
        self.data = {"label": label}

    def with_description(self, description):
        """
        Set the description of this cloud account

        :param str description: the description of the cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMCloudAccountCreator`
        """
        self.data["description"] = description
        return self


class FMAWSCloudAccountCreator(FMCloudAccountCreator):
    def same_as_fm(self):
        """
        Use the same authentication as Fleet Manager
        """
        self.data["awsAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"
        return self

    def with_iam_role(self, role_arn):
        """
        Use an IAM Role

        :param str role_arn: ARN of the IAM Role
        """
        self.data["awsAuthenticationMode"] = "IAM_ROLE"
        self.data["awsIAMRoleARN"] = role_arn
        return self

    def with_keypair(self, access_key_id, secret_access_key):
        """
        Use an AWS Access Key

        :param str access_key_id: AWS Access Key ID
        :param str secret_access_key: AWS Secret Access Key
        """
        self.data["awsAuthenticationMode"] = "KEYPAIR"
        self.data["awsAccessKeyId"] = access_key_id
        self.data["awsSecretAccessKey"] = secret_access_key
        return self

    def create(self):
        """
        Create a new cloud account

        :return: a newly created cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMAWSCloudAccount`
        """
        account = self.client._perform_tenant_json(
            "POST", "/cloud-accounts", body=self.data
        )
        return FMAWSCloudAccount(self.client, account)


class FMAzureCloudAccountCreator(FMCloudAccountCreator):
    def same_as_fm(self, subscription, tenant_id, image_resource_group):
        """
        Use the same authentication as Fleet Manager
        
        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str image_resource_group: Azure image cached resource group
        """
        self.data["azureAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"
        self.data["azureSubscription"] = subscription
        self.data["azureTenantId"] = tenant_id
        self.data["azureImageResourceGroup"] = image_resource_group
        return self

    def with_secret(self, subscription, tenant_id, environment, image_resource_group, client_id, secret):
        """
        Use a Secret based authentication

        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str environment: Azure Environment
        :param str client_id: Azure Client Id
        :param str image_resource_group: Azure image cached resource group
        :param str secret: Azure Secret
        """

        self.data["azureAuthenticationMode"] = "OAUTH2_AUTHENTICATION_METHOD_CLIENT_SECRET"
        self.data["azureSubscription"] = subscription
        self.data["azureTenantId"] = tenant_id
        self.data["azureEnvironment"] = environment
        self.data["azureClientId"] = client_id
        self.data["azureSecret"] = secret
        self.data["azureImageResourceGroup"] = image_resource_group
        return self
    
    def with_certificate(self, subscription, tenant_id, environment, client_id, image_resource_group, certificate_path, certificate_password):
        """
        Use a Secret based authentication

        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str environment: Azure Environment
        :param str client_id: Azure Client Id
        :param str image_resource_group: Azure image cached resource group
        :param str certificate_path: Azure certificate path
        :param str certificate_password: Azure certificate password
        """

        self.data["azureAuthenticationMode"] = "OAUTH2_AUTHENTICATION_METHOD_CERTIFICATE"
        self.data["azureSubscription"] = subscription
        self.data["azureTenantId"] = tenant_id
        self.data["azureEnvironment"] = environment
        self.data["azureClientId"] = client_id
        self.data["azureImageResourceGroup"] = image_resource_group
        self.data["azureCertificatePath"] = certificate_path
        self.data["azureCertificatePassword"] = certificate_password
        return self

    def with_managed_identity(self, tenant_id, environment, image_resource_group, managed_identity):
        """
        Use a Managed Identity based authentication

        :param str tenant_id: Azure Tenant identifier
        :param str environment: Azure Environment
        :param str image_resource_group: Azure image cached resource group
        :param str managed_identity: Azure Managed Identity
        """

        self.data["azureAuthenticationMode"] = "MANAGED_IDENTITY"
        self.data["azureTenantId"] = tenant_id
        self.data["azureEnvironment"] = environment
        self.data["azureManagedIdentityId"] = managed_identity
        self.data["azureImageResourceGroup"] = image_resource_group
        return self

    def create(self):
        """
        Create a new cloud account

        :return: a newly created cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMAzureCloudAccount`
        """
        account = self.client._perform_tenant_json(
            "POST", "/cloud-accounts", body=self.data
        )
        return FMAzureCloudAccount(self.client, account)


class FMGCPCloudAccountCreator(FMCloudAccountCreator):
    def same_as_fm(self):
        """
        Use the same authentication as Fleet Manager
        """
        self.data["gcpAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"
        return self

    def with_service_account_key(self, project_id, service_account_key):
        """
        Use a Service Account JSON key based authentication

        :param str project_id: GCP project
        :param str service_account_key: Optional, service account key (JSON)
        """
        self.data["gcpAuthenticationMode"] = "JSON_KEY"
        self.data["gcpProjectId"] = project_id
        self.data["gcpServiceAccountKey"] = service_account_key
        return self

    def create(self):
        """
        Create a new cloud account

        :return: a newly created cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMGCPCloudAccount`
        """
        account = self.client._perform_tenant_json(
            "POST", "/cloud-accounts", body=self.data
        )
        return FMGCPCloudAccount(self.client, account)


class FMCloudAccount(object):

    def __init__(self, client, account_data):
        self.client = client
        self.account_data = account_data
        self.id = self.account_data["id"]

    def delete(self):
        """
        Delete this cloud account.

        :return: the `Future` object representing the deletion process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        if (self.account_data["nbNetworks"] > 0):
            raise Exception("This account is in use by some networks, you cannot delete it")

        future = self.client._perform_tenant_json(
            "DELETE", "/cloud-accounts/%s" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def save(self):
        """
        Save this cloud account.
        """
        self.client._perform_tenant_empty(
            "PUT", "/cloud-accounts/%s" % self.id, body=self.account_data
        )


class FMAWSCloudAccount(FMCloudAccount):
    def set_same_as_fm(self):
        """
        Use the same authentication as Fleet Manager
        """
        self.account_data["awsAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"

    def set_iam_role(self, role_arn):
        """
        Use an IAM Role

        :param str role_arn: ARN of the IAM Role
         """
        self.account_data["awsAuthenticationMode"] = "IAM_ROLE"
        self.account_data["awsIAMRoleARN"] = role_arn

    def set_keypair(self, access_key_id, secret_access_key):
        """
        Use an AWS Access Key

        :param str access_key_id: AWS Access Key ID
        :param str secret_access_key: AWS Secret Access Key
        """
        self.account_data["awsAuthenticationMode"] = "KEYPAIR"
        self.account_data["awsAccessKeyId"] = access_key_id
        self.account_data["awsSecretAccessKey"] = secret_access_key


class FMAzureCloudAccount(FMCloudAccount):
    def set_same_as_fm(self, tenant_id, image_resource_group):
        """
        Use the same authentication as Fleet Manager

        :param str tenant_id: Azure Tenant Id
        :param str image_resource_group: Azure image cached resource group
        """
        self.account_data["azureAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"
        self.account_data["azureTenantId"] = tenant_id
        self.account_data["azureImageResourceGroup"] = image_resource_group

    def set_secret(self, subscription, tenant_id, environment, client_id, image_resource_group, secret):
        """
        Use a Secret based authentication

        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str environment: Azure Environment
        :param str client_id: Azure Client Id
        :param str image_resource_group: Azure image cached resource group
        :param str secret: Azure Secret
        """

        self.account_data["azureAuthenticationMode"] = "OAUTH2_AUTHENTICATION_METHOD_CLIENT_SECRET"
        self.account_data["azureSubscription"] = subscription
        self.account_data["azureTenantId"] = tenant_id
        self.account_data["azureEnvironment"] = environment
        self.account_data["azureClientId"] = client_id
        self.account_data["azureSecret"] = secret
        self.account_data["azureImageResourceGroup"] = image_resource_group
        return self
    
    def set_certificate(self, subscription, tenant_id, environment, client_id, image_resource_group, certificate_path, certificate_password):
        """
        Use a Secret based authentication

        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str environment: Azure Environment
        :param str client_id: Azure Client Id
        :param str image_resource_group: Azure image cached resource group
        :param str certificate_path: Azure certificate path
        :param str certificate_password: Azure certificate password
        """

        self.account_data["azureAuthenticationMode"] = "OAUTH2_AUTHENTICATION_METHOD_CLIENT_SECRET"
        self.account_data["azureSubscription"] = subscription
        self.account_data["azureTenantId"] = tenant_id
        self.account_data["azureEnvironment"] = environment
        self.account_data["azureClientId"] = client_id
        self.account_data["azureCertificatePath"] = certificate_path
        self.account_data["azureCertificatePassword"] = certificate_password
        self.account_data["azureImageResourceGroup"] = image_resource_group
        return self

    def set_managed_identity(self, tenant_id, environment, managed_identity, image_resource_group):
        """
        Use a Managed Identity based authentication

        :param str tenant_id: Azure Tenant identifier
        :param str environment: Azure Environment
        :param str image_resource_group: Azure image cached resource group
        :param str managed_identity: Azure Managed Identity
        """

        self.account_data["azureAuthenticationMode"] = "MANAGED_IDENTITY"
        self.account_data["azureTenantId"] = tenant_id
        self.account_data["azureEnvironment"] = environment
        self.account_data["azureManagedIdentityId"] = managed_identity
        self.account_data["azureImageResourceGroup"] = image_resource_group
        return self


class FMGCPCloudAccount(FMCloudAccount):
    def set_same_as_fm(self):
        """
        Use the same authentication as Fleet Manager
        """
        self.account_data["gcpAuthenticationMode"] = "DEFAULT_INSTANCE_CREDENTIALS"

    def set_service_account_key(self, project_id, service_account_key):
        """
        Use a Service Account JSON key based authentication

        :param str project_id: GCP project
        :param str service_account_key: Optional, service account key (JSON)
        """
        self.account_data["gcpAuthenticationMode"] = "JSON_KEY"
        self.account_data["gcpProjectId"] = project_id
        self.account_data["gcpServiceAccountKey"] = service_account_key

