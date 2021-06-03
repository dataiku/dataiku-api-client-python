from enum import Enum
from .future import FMFuture

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
