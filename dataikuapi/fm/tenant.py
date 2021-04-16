class FMCloudCredentials(object):
    """
    A Tenant Cloud Credentials in the FM instance
    """
    def __init__(self, client, tenant_id, cloud_credentials):
        self.client = client
        self.tenant_id = tenant_id
        self.cloud_credentials = cloud_credentials

    def set_cmk_key(self, cmk_key_id):
        self.cloud_credentials['awsCMKId'] = cmk_key_id

    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_empty("PUT", "/tenants/%s/cloud-credentials" % (self.tenant_id),
                                   body = self.cloud_credentials)

