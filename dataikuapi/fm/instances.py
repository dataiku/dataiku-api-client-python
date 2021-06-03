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
