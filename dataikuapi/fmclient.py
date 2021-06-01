import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth

import os.path as osp
from .utils import DataikuException

from .fm.tenant import FMCloudCredentials
from .fm.virtualnetworks import FMVirtualNetwork
from .fm.instances import FMInstance, FMInstanceEncryptionMode
from .fm.instancesettingstemplates import FMInstanceSettingsTemplate

class FMClient(object):
    """Entry point for the FM API client"""

    def __init__(self, host, api_key_id, api_key_secret, tenant_id, extra_headers = None):
        """
        Instantiate a new FM API client on the given host with the given API key.

        API keys can be managed in FM on the project page or in the global settings.

        The API key will define which operations are allowed for the client.
        """
        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.host = host
        self.__tenant_id = tenant_id
        self._session = Session()

        if self.api_key_id is not None and self.api_key_secret is not None:
            self._session.auth = HTTPBasicAuth(self.api_key_id, self.api_key_secret)
        else:
            raise ValueError("API Key ID and API Key secret are required")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)


    ########################################################
    # Tenant
    ########################################################

    def get_cloud_credentials(self):
        """
        Get Cloud Credential

        :return: Cloud credentials
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudCredentials`
        """
        creds = self._perform_tenant_json("GET", "/cloud-credentials")
        return FMCloudCredentials(self, creds)


    ########################################################
    # VirtualNetwork
    ########################################################

    def get_virtual_networks(self):
        """
        Get Virtual Networks

        :return: list of virtual networks
        :rtype: list of :class:`dataikuapi.fm.tenant.FMVirtualNetwork`
        """
        vns = self._perform_tenant_json("GET", "/virtual-networks")
        return [ FMVirtualNetwork(self, x) for x in vns]

    def get_virtual_network(self, virtual_network_id):
        """
        Get a Virtual Network

        :param str virtual_network_id

        :return: requested virtual network
        :rtype: :class:`dataikuapi.fm.tenant.FMVirtualNetwork`
        """
        template = self._perform_tenant_json("GET", "/virtual-networks/%s" % virtual_network_id)
        return FMVirtualNetwork(self, template)


    ########################################################
    # Instance settings template
    ########################################################

    def get_instance_templates(self):
        """
        Get Instance Settings Templates

        :return: list of instance settings template
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstanceSettingsTemplate`
        """
        templates = self._perform_tenant_json("GET", "/instance-settings-templates")
        return [ FMInstanceSettingsTemplate(self, x) for x in templates]

    def get_instance_template(self, template_id):
        """
        Get an Instance

        :param str template_id

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.tenant.FMInstance`
        """
        template = self._perform_tenant_json("GET", "/instance-settings-templates/%s" % template_id)
        return FMInstanceSettingsTemplate(self, template)


    ########################################################
    # Instance
    ########################################################

    def get_instances(self):
        """
        Get Instances

        :return: list of instances
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstance`
        """
        instances = self._perform_tenant_json("GET", "/instances")
        return [ FMInstance(self, **x) for x in instances]

    def get_instance(self, instance_id):
        """
        Get an Instance

        :param str instance_id

        :return: Instance
        :rtype: :class:`dataikuapi.fm.tenant.FMInstance`
        """
        instance = self._perform_tenant_json("GET", "/instances/%s" % instance_id)
        return FMInstance(self, instance)

    def create_instance(self, instance_settings_template, virtual_network, label,
                        dss_node_type="design", image_id=None,
                        cloud_instance_type=None, data_volume_type=None, data_volume_size=None,
                        data_volume_size_max=None, data_volume_IOPS=None, data_volume_encryption=FMInstanceEncryptionMode.NONE,
                        data_volume_encryption_key=None, aws_root_volume_size=None, aws_root_volume_type=None, aws_root_volume_IOPS=None,
                        cloud_tags=None, fm_tags=None):
        """
        Create an Instance

        :param str instance_id

        :return: Instance
        :rtype: :class:`dataikuapi.fm.tenant.FMInstance`
        """
        data = {
            "virtualNetworkId": virtual_network.id,
            "instanceSettingsTemplateId": instance_settings_template.id,
            "label": label,
            "dssNodeType": dss_node_type,
            "imageId": image_id,
            "cloudInstanceType": cloud_instance_type,
            "dataVolumeType": data_volume_type,
            "dataVolumeSizeGB": data_volume_size,
            "dataVolumeSizeMaxGB": data_volume_size_max,
            "dataVolumeIOPS": data_volume_IOPS,
            "dataVolumeEncryption": data_volume_encryption.value,
            "dataVolumeEncryptionKey": data_volume_encryption_key,
            "awsRootVolumeSizeGB": aws_root_volume_size,
            "awsRootVolumeType": aws_root_volume_type,
            "awsRootVolumeIOPS": aws_root_volume_IOPS,
            "cloudTags": cloud_tags,
            "fmTags": fm_tags
        }
        instance = self._perform_tenant_json("POST", "/instances", body=data)
        return FMInstance(self, instance)


    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(self, method, path, params=None, body=None, stream=False, files=None, raw_body=None):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body

        try:
            http_res = self._session.request(
                    method, "%s/api/public%s" % (self.host, path),
                    params=params, data=body,
                    files = files,
                    stream = stream)
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException("%s: %s" % (ex.get("errorType", "Unknown error"), ex.get("message", "No message")))

    def _perform_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_http(method, path, params=params, body=body, files=files, stream=False, raw_body=raw_body)

    def _perform_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_http(method, path,  params=params, body=body, files=files, stream=False, raw_body=raw_body).json()

    def _perform_tenant_json(self, method, path, params=None, body=None,files=None, raw_body=None):
        return self._perform_json(method, "/tenants/%s%s" % ( self.__tenant_id, path ), params=params, body=body, files=files, raw_body=raw_body)

    def _perform_tenant_empty(self, method, path, params=None, body=None, files = None, raw_body=None):
        self._perform_empty(method, "/tenants/%s%s" % ( self.__tenant_id, path ), params=params, body=body, files=files, raw_body=raw_body)
