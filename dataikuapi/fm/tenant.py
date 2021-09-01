import json
class FMCloudCredentials(object):
    """
    A Tenant Cloud Credentials in the FM instance
    """
    def __init__(self, client, cloud_credentials):
        self.client = client
        self.cloud_credentials = cloud_credentials

    def set_cmk_key(self, cmk_key_id):
        self.cloud_credentials['awsCMKId'] = cmk_key_id

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
            license = json.load(license_string)
        else:
            raise ValueError("a valid license_file or license_string needs to be provided")
        self.cloud_credentials['licenseMode'] = 'STATIC'
        self.cloud_credentials['license'] = json.dumps(license, indent=2)

    def set_automatically_updated_license(self, license_token):
        """
        Set an automatically updated license for the DSS instances

        :param str license_token: License token
        """
        if license_token is None:
            raise ValueError("a valid license_token needs to be provided")
        self.cloud_credentials['licenseMode'] = 'AUTO_UPDATE'
        self.cloud_credentials['licenseToken'] = license_token

    def save(self):
        """Saves back the settings to the project"""

        self.client._perform_tenant_empty("PUT", "/cloud-credentials",
                                   body = self.cloud_credentials)

