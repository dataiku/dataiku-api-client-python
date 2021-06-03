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
        List all Virtual Networks

        :return: list of virtual networks
        :rtype: list of :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vns = self._perform_tenant_json("GET", "/virtual-networks")
        return [ FMVirtualNetwork(self, x) for x in vns]

    def get_virtual_network(self, virtual_network_id):
        """
        Get a Virtual Network

        :param str virtual_network_id

        :return: requested virtual network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vn = self._perform_tenant_json("GET", "/virtual-networks/%s" % virtual_network_id)
        return FMVirtualNetwork(self, vn)

    def create_virtual_network(self,
                               label,
                               awsVpcId=None,
                               awsSubnetId=None,
                               awsAutoCreateSecurityGroups=False,
                               awsSecurityGroups=None,
                               azureVnId=None,
                               azureSubnetId=None,
                               azureAutoUpdateSecurityGroups=None,
                               internetAccessMode = "YES"):
        """
        Create a Virtual Network

        :param str label: The label of the Virtual Network

        :param str awsVpcId: AWS Only, ID of the VPC to use
        :param str awsSubnetId: AWS Only, ID of the subnet to use
        :param boolean awsAutoCreateSecurityGroups: Optional, AWS Only, If false, do not create security groups automatically. Defaults to false
        :param list awsSecurityGroups: Optional, AWS Only, A list of up to 5 security group ids to assign to the instances created in this virtual network. Ignored if awsAutoCreateSecurityGroups is true

        :param str azureVnId: Azure Only, ID of the Azure Virtual Network to use
        :param str azureSubnetId: Azure Only, ID of the subnet to use
        :param boolean azureAutoUpdateSecurityGroups: Azure Only, Auto update the subnet security group

        :param str internetAccessMode: Optional, The internet access mode of the instances created in this virtual network. Accepts "YES", "NO", "EGRESS_ONLY". Defaults to "YES"

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """

        data = {
            "label": label,
            "awsVpcId": awsVpcId,
            "awsSubnetId": awsSubnetId,
            "awsAutoCreateSecurityGroups": awsAutoCreateSecurityGroups,
            "awsSecurityGroups": awsSecurityGroups,
            "azureVnId": azureVnId,
            "azureSubnetId": azureSubnetId,
            "azureAutoUpdateSecurityGroups": azureAutoUpdateSecurityGroups,
            "internetAccessMode": internetAccessMode,
            "mode": "EXISTING_MONOTENANT"
        }

        vn = self._perform_tenant_json("POST", "/virtual-networks", body=data)
        return FMVirtualNetwork(self, vn)


    ########################################################
    # Instance settings template
    ########################################################

    def get_instance_templates(self):
        """
        List all Instance Settings Templates

        :return: list of instance settings template
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstanceSettingsTemplate`
        """
        templates = self._perform_tenant_json("GET", "/instance-settings-templates")
        return [ FMInstanceSettingsTemplate(self, x) for x in templates]

    def get_instance_template(self, template_id):
        """
        Get an Instance Template

        :param str template_id

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """
        template = self._perform_tenant_json("GET", "/instance-settings-templates/%s" % template_id)
        return FMInstanceSettingsTemplate(self, template)


    def create_instance_template(self, label,
                                 setupActions=None, license=None,
                                 awsKeyPairName=None, startupInstanceProfileArn=None, runtimeInstanceProfileArn=None,
                                 restrictAwsMetadataServerAccess=True, dataikuAwsAPIAccessMode="NONE", dataikuAwsKeypairStorageMode=None,
                                 dataikuAwsAccessKeyId=None, dataikuAwsSecretAccessKey=None,
                                 dataikuAwsSecretAccessKeyAwsSecretName=None, awsSecretsManagerRegion=None,
                                 azureSshKey=None, startupManagedIdentity=None, runtimeManagedIdentity=None):
        """
        Create an Instance Template

        :param str label: The label of the Instance Settings Template

        :param list setupActions: Optional, a list of :class:`dataikuapi.fm.instancesettingstemplates.FMSetupAction` to be played on an instance
        :param str license: Optional, overrides the license set in Cloud Setup

        :param str awsKeyPairName: Optional, AWS Only, the name of an AWS key pair to add to the instance. Needed to get SSH access to the DSS instance, using the centos user.
        :param str startupInstanceProfileArn: Optional, AWS Only, the ARN of the Instance profile assigned to the DSS instance at startup time
        :param str runtimeInstanceProfileArn: Optional, AWS Only, the ARN of the Instance profile assigned to the DSS instance at runtime
        :param boolean restrictAwsMetadataServerAccess: Optional, AWS Only, If true, restrict the access to the metadata server access. Defaults to true
        :param str dataikuAwsAPIAccessMode: Optional, AWS Only, the access mode DSS is using to connect to the AWS API. If "NONE" DSS will use the Instance Profile, If "KEYPAIR", an AWS access key id and secret will be securely given to the dataiku account.
        :param str dataikuAwsKeypairStorageMode: Optional, AWS Only, the storage mode of the AWS api key. Accepts "NONE", "INLINE_ENCRYPTED" or "AWS_SECRETS_MANAGER"
        :param str dataikuAwsAccessKeyId: Optional, AWS Only, AWS Access Key ID. Only needed if dataikuAwsAPIAccessMode is "KEYPAIR"
        :param str dataikuAwsSecretAccessKey: Optional, AWS Only, AWS Access Key Secret. Only needed if dataikuAwsAPIAccessMode is "KEYPAIR" and dataikuAwsKeypairStorageMode is "INLINE_ENCRYPTED"
        :param str dataikuAwsSecretAccessKeyAwsSecretName: Optional, AWS Only, ASM secret name. Only needed if dataikuAwsAPIAccessMode is "KEYPAIR" and dataikuAwsKeypairStorageMode is "AWS_SECRET_MANAGER"
        :param str awsSecretsManagerRegion: Optional, AWS Only

        :param str azureSshKey: Optional, Azure Only, the ssh public key to add to the instance. Needed to get SSH access to the DSS instance, using the centos user.
        :param str startupManagedIdentity: Optional, Azure Only, the managed identity assigned to the DSS instance at startup time
        :param str runtimeManagedIdentity: Optional, Azure Only, the managed identity assigned to the DSS instance at runtime

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """

        data = {
            "label": label,
            "setupActions": setupActions,
            "license": license,
            "awsKeyPairName": awsKeyPairName,
            "startupInstanceProfileArn": startupInstanceProfileArn,
            "runtimeInstanceProfileArn": runtimeInstanceProfileArn,
            "restrictAwsMetadataServerAccess": restrictAwsMetadataServerAccess,
            "dataikuAwsAPIAccessMode": "dataikuAwsAPIAccessMode",
            "dataikuAwsKeypairStorageMode": dataikuAwsKeypairStorageMode,
            "dataikuAwsAccessKeyId": dataikuAwsAccessKeyId,
            "dataikuAwsSecretAccessKey": dataikuAwsSecretAccessKey,
            "dataikuAwsSecretAccessKeyAwsSecretName": dataikuAwsSecretAccessKeyAwsSecretName,
            "awsSecretsManagerRegion": awsSecretsManagerRegion,
            "azureSshKey": azureSshKey,
            "startupManagedIdentity": startupManagedIdentity,
            "runtimeManagedIdentity": runtimeManagedIdentity
        }

        template = self._perform_tenant_json("POST", "/instance-settings-templates", body=data)
        return FMInstanceSettingsTemplate(self, template)


    ########################################################
    # Instance
    ########################################################

    def get_instances(self):
        """
        List all DSS Instances

        :return: list of instances
        :rtype: list of :class:`dataikuapi.fm.instances.FMInstance`
        """
        instances = self._perform_tenant_json("GET", "/instances")
        return [ FMInstance(self, **x) for x in instances]

    def get_instance(self, instance_id):
        """
        Get a DSS Instance

        :param str instance_id

        :return: Instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstance`
        """
        instance = self._perform_tenant_json("GET", "/instances/%s" % instance_id)
        return FMInstance(self, instance)

    def create_instance(self, instance_settings_template, virtual_network, label, image_id,
                        dss_node_type="design",
                        cloud_instance_type=None, data_volume_type=None, data_volume_size=None,
                        data_volume_size_max=None, data_volume_IOPS=None, data_volume_encryption=FMInstanceEncryptionMode.NONE,
                        data_volume_encryption_key=None, aws_root_volume_size=None, aws_root_volume_type=None, aws_root_volume_IOPS=None,
                        cloud_tags=None, fm_tags=None):
        """
        Create a DSS Instance

        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str label: The label of the instance
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)

        :param str dss_node_type: Optional , the type of the dss node to create. Defaults to "design"
        :param str cloud_instance_type: Optional, Machine type
        :param str data_volume_type: Optional, Data volume type
        :param int data_volume_size: Optional, Data volume initial size
        :param int data_volume_size_max: Optional, Data volume maximum size
        :param int data_volume_IOPS: Optional, Data volume IOPS
        :param object data_volume_encryption: Optional, a :class:`dataikuapi.fm.instances.FMInstanceEncryptionMode` setting the encryption mode of the data volume
        :param str data_volume_encryption_key: Optional, the encryption key to use when data_volume_encryption_key is FMInstanceEncryptionMode.CUSTOM
        :param int aws_root_volume_size: Optional, the root volume size
        :param str aws_root_volume_type: Optional, the root volume type
        :param int aws_root_volume_IOPS: Optional, the root volume IOPS
        :param dict cloud_tags: Optional, a key value dictionary of tags to be applied on the cloud resources
        :param list fm_tags: Optional, list of tags to be applied on the instance in the Fleet Manager

        :return: Instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstance`
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
