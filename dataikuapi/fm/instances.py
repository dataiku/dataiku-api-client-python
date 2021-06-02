from enum import Enum

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
        Reprovision the DSS physical instance
        """
        self.client._perform_tenant_json("GET", "/instances/%s/actions/reprovision" % self.id)

    def deprovision(self):
        """
        Deprovision the DSS physical instance
        """
        self.client._perform_tenant_json("GET", "/instances/%s/actions/deprovision" % self.id)

    def restart_dss(self):
        """
        Restart the DSS running on the physical instance
        """
        self.client._perform_tenant_json("GET", "/instances/%s/actions/restart-dss" % self.id)

    def save(self):
        """
        Update the DSS Instance.
        """
        self.client._perform_tenant_empty("PUT", "/instances/%s" % self.id, body=self.instance_data)
        self.instance_data = self.client._perform_tenant_json("GET", "/instances/%s" % self.id)



    def get_status(self):
        status = self.client._perform_tenant_json("GET", "/instances/%s/status" % self.id)
        return FMInstanceStatus(status)


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
