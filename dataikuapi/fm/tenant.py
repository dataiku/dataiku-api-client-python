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
        self.save()

    def set_static_license(self, license_file=None, license_string=None):
        """
        Set a default static license for the DSS instances

        Requires either a license_file or a license_string

        :param str license_file: Optional, load the license from a json file
        :param str license_string: Optional, load the license from a json string
        """
        if license_file is not None:
            with open(license_file) as json_file:
                license = json.load(json_file)
        elif license_string is not None:
            license = json.loads(license_string)
        else:
            raise ValueError(
                "a valid license_file or license_string needs to be provided"
            )
        self.cloud_credentials["licenseMode"] = "STATIC"
        self.cloud_credentials["license"] = json.dumps(license, indent=2)
        self.save()

    def set_automatically_updated_license(self, license_token):
        """
        Set an automatically updated license for the DSS instances

        :param str license_token: License token
        """
        if license_token is None:
            raise ValueError("a valid license_token needs to be provided")
        self.cloud_credentials["licenseMode"] = "AUTO_UPDATE"
        self.cloud_credentials["licenseToken"] = license_token
        self.save()

    def set_authentication(self, authentication):
        """
        Set the authentication for the tenant

        :param object: a :class:`dataikuapi.fm.tenant.FMCloudAuthentication`
        """
        self.cloud_credentials.update(authentication)
        self.save()

    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_tenant_empty(
            "PUT", "/cloud-credentials", body=self.cloud_credentials
        )


class FMCloudTags(object):
    """
    A Tenant Cloud Tags in the FM instance
    """

    def __init__(self, client, tenant_id, cloud_tags):
        self.client = client
        self.tenant_id = tenant_id
        self.cloud_tags = json.loads(cloud_tags["msg"])

    def add_tag(self, key, value):
        """
        Add a tag to the tenant


        :param str key: Tag key
        :param str value: Tag value
        """
        if key in self.cloud_tags:
            raise Exception("Key already exists")
        self.cloud_tags[key] = value

    def update_tag(self, key, new_key=None, new_value=None):
        """
        Update a tag key or value


        :param str key: Key of the tag to update
        :param str new_key: Optional, new key for the tag
        :param str new_value: Optional, new value for the tag
        """
        if key not in self.cloud_tags:
            raise Exception("Key does not exists")
        if new_value:
            self.cloud_tags[key] = new_value
        if new_key:
            self.cloud_tags[new_key] = self.cloud_tags[key]
            del self.cloud_tags[key]

    def delete_tag(self, key):
        """
        Delete a tag


        :param str key: Key of the tag to delete
        """
        if key not in self.cloud_tags:
            raise Exception("Key does not exists")
        del self.cloud_tags[key]

    def save(self):
        """Saves the tags on FM"""

        self.client._perform_empty(
            "PUT", "/tenants/%s/cloud-tags" % (self.tenant_id), body=self.cloud_tags
        )


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
        AWS Only: Use the same authentication as Fleet Manager
        """
        return FMCloudAuthentication({"awsAuthenticationMode": "SAME_AS_FM"})

    @staticmethod
    def aws_iam_role(role_arn):
        """
        AWS Only: Use an IAM Role

        params: str role_arn: ARN of the IAM Role
        """
        return FMCloudAuthentication(
            {"awsAuthenticationMode": "IAM_ROLE", "awsIAMRoleARN": role_arn}
        )

    @staticmethod
    def aws_keypair(access_key_id, secret_access_key):
        """
        AWS Only: Use an AWS Access Key

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
