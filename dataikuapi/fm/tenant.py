import json


class FMCloudCredentials(object):
    """
    A Tenant Cloud Credentials in the FM instance
    """

    def __init__(self, client, cloud_credentials):
        self.client = client
        self.cloud_credentials = cloud_credentials

    def set_cmk_key(self, cmk_key_id):
        self.cloud_credentials["awsCMKId"] = cmk_key_id
        return self

    def set_static_license(self, license_file_path=None, license_string=None):
        """
        Set a default static license for the DSS instances

        :param str license_file_path: Optional, load the license from a json file
        :param str license_string: Optional, load the license from a json string
        """
        if license_file_path is not None:
            with open(license_file_path) as json_file:
                license = json.load(json_file)
        elif license_string is not None:
            license = json.loads(license_string)
        else:
            raise ValueError(
                "a valid license_file_path or license_string needs to be provided"
            )
        self.cloud_credentials["licenseMode"] = "STATIC"
        self.cloud_credentials["license"] = json.dumps(license, indent=2)
        return self

    def set_automatically_updated_license(self, license_token):
        """
        Set an automatically updated license for the DSS instances

        :param str license_token: License token
        """
        if license_token is None:
            raise ValueError("a valid license_token needs to be provided")
        self.cloud_credentials["licenseMode"] = "AUTO_UPDATE"
        self.cloud_credentials["licenseToken"] = license_token
        return self

    def set_authentication(self, authentication):
        """
        Set the authentication for the tenant

        :param authentication: the authentication to be used
        :type authentication: :class:`dataikuapi.fm.tenant.FMCloudAuthentication`
        """
        self.cloud_credentials.update(authentication)
        return self

    def save(self):
        """
        Saves back the settings to the project
        """

        self.client._perform_tenant_empty(
            "PUT", "/cloud-credentials", body=self.cloud_credentials
        )


class FMCloudTags(object):
    """
    A Tenant Cloud Tags in the FM instance
    """

    def __init__(self, client, cloud_tags):
        self.client = client
        self.cloud_tags = json.loads(cloud_tags["msg"])

    @property
    def tags(self):
        return self.cloud_tags

    def save(self):
        """
        Saves the tags on FM
        """

        self.client._perform_tenant_empty("PUT", "/cloud-tags", body=self.cloud_tags)


class FMCloudAuthentication(dict):
    def __init__(self, data):
        """
        A class holding the Cloud Authentication information

        Do not create this directly, use:
            - :meth:`dataikuapi.fm.tenant.FMCloudAuthentication.aws_same_as_fm` to use the same authentication as Fleet Manager
            - :meth:`dataikuapi.fm.tenant.FMCloudAuthentication.aws_iam_role` to use a custom IAM Role
            - :meth:`dataikuapi.fm.tenant.FMCloudAuthentication.aws_keypair` to use a AWS Access key ID and AWS Secret Access Key pair
        """
        super(FMCloudAuthentication, self).__init__(data)

    @staticmethod
    def aws_same_as_fm():
        """
        AWS Only: use the same authentication as Fleet Manager
        """
        return FMCloudAuthentication({"awsAuthenticationMode": "SAME_AS_FM"})

    @staticmethod
    def aws_iam_role(role_arn):
        """
        AWS Only: use an IAM Role

        :param str role_arn: ARN of the IAM Role
        """
        return FMCloudAuthentication(
            {"awsAuthenticationMode": "IAM_ROLE", "awsIAMRoleARN": role_arn}
        )

    @staticmethod
    def aws_keypair(access_key_id, secret_access_key):
        """
        AWS Only: use an AWS Access Key

        :param str access_key_id: AWS Access Key ID
        :param str secret_access_key: AWS Secret Access Key
        """
        return FMCloudAuthentication(
            {
                "awsAuthenticationMode": "KEYPAIR",
                "awsAccessKeyId": access_key_id,
                "awsSecretAccessKey": secret_access_key,
            }
        )

    @staticmethod
    def azure(subscription, tenant_id, environment, client_id):
        """
        Azure Only

        :param str subscription: Azure Subscription
        :param str tenant_id: Azure Tenant Id
        :param str environment: Azure Environment
        :param str client_id: Azure Client Id
        """
        data = {
            "azureSubscription": subscription,
            "azureTenantId": tenant_id,
            "azureEnvironment": environment,
            "azureFMAppClientId": client_id,
        }

        return FMCloudAuthentication(data)

    @staticmethod
    def gcp(project_id, service_account_key):
        """
        GCP Only

        :param str project_id: GCP project
        :param str service_account_key: Optional, service account key (JSON)
        """
        data = {
            "gcpProjectId": project_id,
            "gcpServiceAccountKey": service_account_key
        }

        return FMCloudAuthentication(data)
