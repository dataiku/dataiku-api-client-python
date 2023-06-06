from .future import FMFuture

from ..dssclient import DSSClient
from ..govern_client import GovernClient

import sys

if sys.version_info > (3, 4):
    from enum import Enum
else:

    class Enum(object):
        pass


class FMInstanceCreator(object):
    def __init__(
        self, client, label, instance_settings_template_id, virtual_network_id, image_id
    ):
        """
        Helper to create a DSS instance.

        :param client: The FM client
        :type client: :class:`dataikuapi.fm.fmclient`
        :param str label: The label of the instance
        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
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

    def with_dss_node_type(self, dss_node_type):
        """
        Set the DSS node type of the instance to create. The default node type is `DESIGN`.

        :param dss_node_type: the type of the dss node to create.
        :type dss_node_type: :class:`dataikuapi.fm.instances.FMNodeType`
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        # backward compatibility, was a string before . be sure the value falls into the enum
        value = dss_node_type
        # python2 does not support enum, keep string
        if sys.version_info > (3, 4):
            if isinstance(dss_node_type, str):
                value = FMNodeType[dss_node_type.upper()]
            self.data["dssNodeType"] = value.value
        else:
            value = FMNodeType.get_from_string(dss_node_type.upper())
            self.data["dssNodeType"] = value;
        return self

    def with_cloud_instance_type(self, cloud_instance_type):
        """
        Set the machine type for the DSS Instance

        :param str cloud_instance_type: the machine type to be used for the instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        self.data["cloudInstanceType"] = cloud_instance_type
        return self

    def with_data_volume_options(
        self,
        data_volume_type=None,
        data_volume_size=None,
        data_volume_size_max=None,
        data_volume_IOPS=None,
        data_volume_encryption=None,
        data_volume_encryption_key=None,
    ):
        """
        Set the options of the data volume to use with the DSS Instance

        :param str data_volume_type: Optional, data volume type
        :param int data_volume_size: Optional, data volume initial size
        :param int data_volume_size_max: Optional, data volume maximum size
        :param int data_volume_IOPS: Optional, data volume IOPS
        :param  data_volume_encryption: Optional, encryption mode of the data volume
        :type data_volume_encryption: :class:`dataikuapi.fm.instances.FMInstanceEncryptionMode`
        :param str data_volume_encryption_key: Optional, the encryption key to use when data_volume_encryption_key is FMInstanceEncryptionMode.CUSTOM
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        if type(data_volume_encryption) is not FMInstanceEncryptionMode:
            raise TypeError(
                "data_volume encryption needs to be of type FMInstanceEncryptionMode"
            )

        self.data["dataVolumeType"] = data_volume_type
        self.data["dataVolumeSizeGB"] = data_volume_size
        self.data["dataVolumeSizeMaxGB"] = data_volume_size_max
        self.data["dataVolumeIOPS"] = data_volume_IOPS
        self.data["volumesEncryption"] = data_volume_encryption.value
        self.data["volumesEncryptionKey"] = data_volume_encryption_key
        return self

    def with_cloud_tags(self, cloud_tags):
        """
        Set the tags to be applied to the cloud resources created for this DSS instance

        :param dict cloud_tags: a key value dictionary of tags to be applied on the cloud resources
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        self.data["cloudTags"] = cloud_tags
        return self

    def with_fm_tags(self, fm_tags):
        """
        A list of tags to add on the DSS Instance in Fleet Manager

        :param list fm_tags: Optional, list of tags to be applied on the instance in the Fleet Manager
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceCreator`
        """
        self.data["fmTags"] = fm_tags
        return self


class FMAWSInstanceCreator(FMInstanceCreator):
    def with_aws_root_volume_options(
        self,
        aws_root_volume_size=None,
        aws_root_volume_type=None,
        aws_root_volume_IOPS=None,
    ):
        """
        Set the options of the root volume of the DSS Instance

        :param int aws_root_volume_size: Optional, the root volume size
        :param str aws_root_volume_type: Optional, the root volume type
        :param int aws_root_volume_IOPS: Optional, the root volume IOPS
        :rtype: :class:`dataikuapi.fm.instances.FMAWSInstanceCreator`
        """
        self.data["awsRootVolumeSizeGB"] = aws_root_volume_size
        self.data["awsRootVolumeType"] = aws_root_volume_type
        self.data["awsRootVolumeIOPS"] = aws_root_volume_IOPS
        return self

    def create(self):
        """
        Create the DSS instance

        :return: a newly created DSS instance
        :rtype: :class:`dataikuapi.fm.instances.FMAWSInstance`
        """
        instance = self.client._perform_tenant_json(
            "POST", "/instances", body=self.data
        )
        return FMAWSInstance(self.client, instance)


class FMAzureInstanceCreator(FMInstanceCreator):
    def create(self):
        """
        Create the DSS instance

        :return: a newly created DSS instance
        :rtype: :class:`dataikuapi.fm.instances.FMAzureInstance`
        """
        instance = self.client._perform_tenant_json(
            "POST", "/instances", body=self.data
        )
        return FMAzureInstance(self.client, instance)


class FMGCPInstanceCreator(FMInstanceCreator):
    def create(self):
        """
        Create the DSS instance

        :return: a newly created DSS instance
        :rtype: :class:`dataikuapi.fm.instances.FMGCPInstance`
        """
        instance = self.client._perform_tenant_json(
            "POST", "/instances", body=self.data
        )
        return FMGCPInstance(self.client, instance)


class FMInstance(object):
    """
    A handle to interact with a DSS instance.
    Do not create this directly, use :meth:`dataikuapi.fmclient.FMClient.get_instance` or

    * :meth:`dataikuapi.fmclient.FMClientAWS.new_instance_creator`
    * :meth:`dataikuapi.fmclient.FMClientAzure.new_instance_creator`
    * :meth:`dataikuapi.fmclient.FMClientGCP.new_instance_creator`

    """

    def __init__(self, client, instance_data):
        self.client = client
        self.instance_data = instance_data
        self.id = instance_data["id"]

    def get_client(self):
        """
        Get a Python client to communicate with a DSS instance
        :return: a Python client to communicate with the target instance
        :rtype: :class:`dataikuapi.dssclient.DSSClient`
        """
        instance_status = self.get_status()
        external_url = instance_status.get("publicURL")

        admin_api_key_resp = self.client._perform_tenant_json(
            "GET", "/instances/%s/admin-api-key" % self.id
        )
        api_key = admin_api_key_resp["adminAPIKey"]

        if not external_url:
            raise ValueError("No external URL available for node %s. This node may not be provisioned yet" % self.id)

        if self.instance_data.get("dssNodeType") == "govern":
            return GovernClient(external_url, api_key)
        else:
            return DSSClient(external_url, api_key)

    def reprovision(self):
        """
        Reprovision the physical DSS instance

        :return: the `Future` object representing the reprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/reprovision" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def deprovision(self):
        """
        Deprovision the physical DSS instance

        :return: the `Future` object representing the deprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/deprovision" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def restart_dss(self):
        """
        Restart the DSS running on the physical instance

        :return: the `Future` object representing the restart process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/restart-dss" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def save(self):
        """
        Update the instance
        """
        self.client._perform_tenant_empty(
            "PUT", "/instances/%s" % self.id, body=self.instance_data
        )
        self.instance_data = self.client._perform_tenant_json(
            "GET", "/instances/%s" % self.id
        )

    def get_status(self):
        """
        Get the physical DSS instance's status

        :return: the instance status
        :rtype: :class:`dataikuapi.fm.instances.FMInstanceStatus`
        """
        status = self.client._perform_tenant_json(
            "GET", "/instances/%s/status" % self.id
        )
        return FMInstanceStatus(status)

    def delete(self):
        """
        Delete the DSS instance

        :return: the `Future` object representing the deletion process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/delete" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def get_initial_password(self):
        """
        Get the initial DSS admin password.

        Can only be called once

        :return: a password for the 'admin' user.
        """
        return self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/get-initial-password" % self.id
        )

    def reset_user_password(self, username, password):
        """
        Reset the password for a user on the DSS instance

        :param string username: login
        :param string password: new password
        :return: the `Future` object representing the password reset process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future =  self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/reset-user-password" % self.id, params={ 'userName':username, 'password':password }
        )
        return FMFuture.from_resp(self.client, future)

    def replay_setup_actions(self):
        """
        Replay the setup actions on the DSS instance

        :return: the `Future` object representing the replay process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future =  self.client._perform_tenant_json(
            "GET", "/instances/%s/actions/replay-setup-actions" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def set_automated_snapshots(self, enable, period, keep=0):
        """
        Set the automated snapshot policy for this instance

        :param boolean enable: Enable the automated snapshots
        :param int period: The time period between 2 snapshot in hours
        :param int keep: Optional, the number of snapshot to keep. Use 0 to keep all snapshots. Defaults to 0.
        """
        self.instance_data["enableAutomatedSnapshot"] = enable
        self.instance_data["automatedSnapshotPeriod"] = period
        self.instance_data["automatedSnapshotRetention"] = keep
        return self

    def set_custom_certificate(self, pem_data):
        """
        Set the custom certificate for this instance

        Only needed when Virtual Network HTTPS Strategy is set to Custom Certificate

        :param str pem_data: The SSL certificate
        """
        self.instance_data["sslCertificatePEM"] = pem_data
        return self


    ########################################################
    # Snapshots
    ########################################################

    def list_snapshots(self):
        """
        List all the snapshots of this instance

        :return: list of snapshots
        :rtype: list of :class:`dataikuapi.fm.instances.FMSnapshot`
        """
        snapshots = self.client._perform_tenant_json("GET", "/instances/%s/snapshots" % self.id)
        return [FMSnapshot(self.client, self.id, x["id"], x) for x in snapshots]

    def get_snapshot(self, snapshot_id):
        """
        Get a snapshot of this instance

        :param str snapshot_id: identifier of the snapshot

        :return: Snapshot
        :rtype: :class:`dataikuapi.fm.instances.FMSnapshot`
        """
        return FMSnapshot(self.client, self.id, snapshot_id)

    def snapshot(self, reason_for_snapshot=None):
        """
        Create a snapshot of the instance

        :return: Snapshot
        :rtype: :class:`dataikuapi.fm.instances.FMSnapshot`
        """
        snapshot = self.client._perform_tenant_json(
            "POST", "/instances/%s/snapshots" % self.id, params={ "reasonForSnapshot":reason_for_snapshot }
        )
        return FMSnapshot(self.client, self.id, snapshot["id"], snapshot)

class FMAWSInstance(FMInstance):
    def set_elastic_ip(self, enable, elasticip_allocation_id):
        """
        Set a public elastic ip for this instance

        :param boolan enable: Enable the elastic ip allocation
        :param str elasticip_allocation_id: AWS ElasticIP allocation ID
        """
        self.instance_data["awsAssignElasticIP"] = enable
        self.instance_data["awsElasticIPAllocationId"] = elasticip_allocation_id
        return self


class FMAzureInstance(FMInstance):
    def set_elastic_ip(self, enable, public_ip_id):
        """
        Set a public elastic ip for this instance

        :param boolan enable: Enable the elastic ip allocation
        :param str public_ip_id: Azure Public IP ID
        """
        self.instance_data["azureAssignElasticIP"] = enable
        self.instance_data["azurePublicIPId"] = public_ip_id
        return self


class FMGCPInstance(FMInstance):
    def set_public_ip(self, enable, public_ip_id):
        """
        Set a public ip for this instance

        :param boolan enable: Enable the public ip allocation
        :param str public_ip_id: GCP Public IP ID
        """
        self.instance_data["gcpAssignPublicIP"] = enable
        self.instance_data["gcpPublicIPId"] = public_ip_id
        return self


class FMNodeType(Enum):
    DESIGN = "design"
    DEPLOYER = "deployer"
    AUTOMATION = "automation"
    GOVERN = "govern"

    # Python2 emulated enum. to be removed on Python2 support removal
    @staticmethod
    def get_from_string(s):
        if s == "DESIGN": return FMNodeType.DESIGN
        if s == "DEPLOYER": return FMNodeType.DEPLOYER
        if s == "AUTOMATION": return FMNodeType.AUTOMATION
        if s == "GOVERN": return FMNodeType.GOVERN
        raise Exception("Invalid Node Type " + s)


class FMInstanceEncryptionMode(Enum):
    NONE = "NONE"
    DEFAULT_KEY = "DEFAULT_KEY"
    TENANT = "TENANT"
    CUSTOM = "CUSTOM"


class FMInstanceStatus(dict):
    """A class holding read-only information about an Instance.
    This class should not be created directly. Instead, use :meth:`FMInstance.get_status`
    """

    def __init__(self, data):
        """Do not call this directly, use :meth:`FMInstance.get_status`"""
        super(FMInstanceStatus, self).__init__(data)


class FMSnapshot(object):
    """
    A handle to interact with a snapshot of a DSS instance.
    Do not create this directly, use :meth:`FMInstance.snapshot`
    """

    def __init__(self, client, instance_id, snapshot_id, snapshot_data=None):
        self.client = client
        self.instance_id = instance_id
        self.snapshot_id = snapshot_id
        self.snapshot_data = snapshot_data

    def get_info(self):
        """
        Get the information about this snapshot

        :return: a dict
        """
        if self.snapshot_data is None:
            self.snapshot_data = self.client._perform_tenant_json(
                "GET", "/instances/%s/snapshots/%s" % (self.instance_id, self.snapshot_id)
            )
        return self.snapshot_data

    def reprovision(self):
        """
        Reprovision the physical DSS instance from this snapshot

        :return: the `Future` object representing the reprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "POST", "/instances/%s/snapshots/%s/reprovision" % (self.instance_id, self.snapshot_id)
        )
        return FMFuture.from_resp(self.client, future)

    def delete(self):
        """
        Delete the snapshot

        :return: the `Future` object representing the deletion process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "DELETE", "/instances/%s/snapshots/%s" % (self.instance_id, self.snapshot_id)
        )
        return FMFuture.from_resp(self.client, future)
