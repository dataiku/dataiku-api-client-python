class FMCloudCredentials(object):
    """
    A Tenant Cloud Credentials in the FM instance
    """
    def __init__(self, client, cloud_credentials):
        self.client = client
        self.cloud_credentials = cloud_credentials

    def set_cmk_key(self, cmk_key_id):
        self.cloud_credentials['awsCMKId'] = cmk_key_id

    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_tenant_empty("PUT", "/cloud-credentials",
                                   body = self.cloud_credentials)

