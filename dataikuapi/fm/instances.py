from enum import Enum
from .future import FMFuture

class FMInstanceCreator(object):
    def __init__(self, client, label, instance_settings_template_id, virtual_network_id, image_id):
        """
        Helper to create a DSS Instance

        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str label: The label of the instance
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)
        """
        self.client = client
        self.data = {}
        self.data["label"] = label
        self.data["instanceSettingsTemplateId"] = instance_settings_template_id
        self.data["virtualNetworkId"] = virtual_network_id
        self.data["imageId"] = image_id

        # Set the default value for dssNodeType
        self.data["dssNodeType"] = "design"

    def create(self):
        """
        Create the DSS instance

        :return: Instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstance`
        """
        instance = self.client._perform_tenant_json("POST", "/instances", body=self.data)
        return FMInstance(self.client, instance)

    def set_dss_node_type(self, dss_node_type):
        """
        Set the DSS Node type of the instance to create

        :param str dss_node_type: Optional , the type of the dss node to create. Supports "design", "automation ordeployer". Defaults to "design"
        """
        if dss_node_type not in ["design", "automation", "deployer"]:
            raise ValueError("Only \"design\", \"automation\" or \"deployer\" dss_node_type are supported")
        self.data["dssNodeType"] = dss_node_type

    def set_cloud_instance_type(self, cloud_instance_type):
        """
        Set the machine type for the DSS Instance
        """
        self.data["cloudInstanceType"] = cloud_instance_type

    def set_data_volume_options(self, data_volume_type=None, data_volume_size=None, data_volume_size_max=None, data_volume_IOPS=None, data_volume_encryption=None, data_volume_encryption_key=None):
        """
        Set the options of the data volume to use with the DSS Instance

        :param str data_volume_type: Optional, Data volume type
        :param int data_volume_size: Optional, Data volume initial size
        :param int data_volume_size_max: Optional, Data volume maximum size
        :param int data_volume_IOPS: Optional, Data volume IOPS
        :param object data_volume_encryption: Optional, a :class:`dataikuapi.fm.instances.FMInstanceEncryptionMode` setting the encryption mode of the data volume
        :param str data_volume_encryption_key: Optional, the encryption key to use when data_volume_encryption_key is FMInstanceEncryptionMode.CUSTOM
        """
        if type(data_volume_encryption) is not FMInstanceEncryptionMode:
            raise TypeError("data_volume encryption needs to be of type FMInstanceEncryptionMode")

        self.data["dataVolumeType"] = data_volume_type
        self.data["dataVolumeSizeGB"] = data_volume_size
        self.data["dataVolumeSizeMaxGB"] = data_volume_size_max
        self.data["dataVolumeIOPS"] = data_volume_IOPS
        self.data["dataVolumeEncryption"] = data_volume_encryption.value
        self.data["dataVolumeEncryptionKey"] = data_volume_encryption_key

    def set_aws_root_volume_options(self, aws_root_volume_size=None, aws_root_volume_type=None, aws_root_volume_IOPS=None):
        """
        AWS Only: Set the options of the root volume of the DSS Instance

        :param int aws_root_volume_size: Optional, the root volume size
        :param str aws_root_volume_type: Optional, the root volume type
        :param int aws_root_volume_IOPS: Optional, the root volume IOPS
        """
        if self.client.cloud != "AWS":
            raise BaseException("set_aws_root_volume_options is only usable on AWS tenants")
        self.data["awsRootVolumeSizeGB"] = aws_root_volume_size
        self.data["awsRootVolumeType"] = aws_root_volume_type
        self.data["awsRootVolumeIOPS"] = aws_root_volume_IOPS

    def set_cloud_tags(self, cloud_tags):
        """
        Set the tags to be applied to the cloud resources created for this DSS instance

        :param dict cloud_tags: a key value dictionary of tags to be applied on the cloud resources
        """
        self.data["cloudTags"] = cloud_tags

    def set_fm_tags(self, fm_tags):
        """
        A list of tags to add on the DSS Instance in Fleet Manager

        :param list fm_tags: Optional, list of tags to be applied on the instance in the Fleet Manager
        """
        self.data["fmTags"] = fm_tags


class FMInstance(object):
    """
    A handle to interact with a DSS instance.
    Do not create this directly, use :meth:`FMClient.get_instance` or :meth: `FMClient.create_instance`
    """
    def __init__(self, client, instance_data):
        self.client  = client
        self.instance_data = instance_data
        self.id = instance_data['id']

    def reprovision(self):
        """
        Reprovision the physical DSS instance

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the reprovision process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("GET", "/instances/%s/actions/reprovision" % self.id)
        return FMFuture.from_resp(self.client, future)

    def deprovision(self):
        """
        Deprovision the physical DSS instance

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the deprovision process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("GET", "/instances/%s/actions/deprovision" % self.id)
        return FMFuture.from_resp(self.client, future)

    def restart_dss(self):
        """
        Restart the DSS running on the physical instance

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the restart process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("GET", "/instances/%s/actions/restart-dss" % self.id)
        return FMFuture.from_resp(self.client, future)

    def save(self):
        """
        Update the Instance.
        """
        self.client._perform_tenant_empty("PUT", "/instances/%s" % self.id, body=self.instance_data)
        self.instance_data = self.client._perform_tenant_json("GET", "/instances/%s" % self.id)

    def get_status(self):
        """
        Get the physical DSS instance's status
        """
        status = self.client._perform_tenant_json("GET", "/instances/%s/status" % self.id)
        return FMInstanceStatus(status)

    def delete(self):
        """
        Delete the DSS instance

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the deletion process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("GET", "/instances/%s/actions/delete" % self.id)
        return FMFuture.from_resp(self.client, future)

    def set_automated_snapshots(self, enable, period, keep=0):
        """
        Set the automated snapshots policy for this instance

        :param boolean enable: Enable the automated snapshots
        :param int period: The time period between 2 snapshot in hours
        :param int keep: Optional, the number of snapshot to keep. Use 0 to keep all snapshots. Defaults to 0.
        """
        self.instance_data['enableAutomatedSnapshot'] = enable
        self.instance_data['automatedSnapshotPeriod'] = period
        self.instance_data['automatedSnapshotRetention'] = keep
        self.save()

    def set_elastic_ip(self, enable, elasticip_allocation_id):
        """
        Set a public elastic ip for this instance

        :param boolan enable: Enable the elastic ip allocation
        :param str elaticip_allocation_id: The AWS ElasticIP allocation ID or the Azure Public IP ID
        """
        self.instance_data['awsAssignElasticIP'] = enable
        self.instance_data['awsElasticIPAllocationId'] = elasticip_allocation_id
        self.instance_data['azureAssignElasticIP'] = enable
        self.instance_data['azurePublicIPId'] = elasticip_allocation_id
        self.save()

    def set_custom_certificate(self, pem_data):
        """
        Set the custom certificate for this instance

        Only needed when Virtual Network HTTPS Strategy is set to Custom Certificate

        param: str pem_data: The SSL certificate
        """
        self.instance_data['sslCertificatePEM'] = pem_data
        self.save()


class FMInstanceEncryptionMode(Enum):
    NONE = "NONE"
    DEFAULT_KEY = "DEFAULT_KEY"
    TENANT = "TENANT"
    CUSTOM = "CUSTOM"


class FMInstanceStatus(dict):
    """A class holding read-only information about an Instance.
    This class should not be created directly. Instead, use :meth:`FMInstance.get_info`
    """
    def __init__(self, data):
        """Do not call this directly, use :meth:`FMInstance.get_status`"""
        super(FMInstanceStatus, self).__init__(data)
