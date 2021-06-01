from enum import Enum

class FMInstance(object):
    def __init__(self, client, instance_data):
        self.client  = client
        self.instance_data = instance_data
        print(instance_data)
        self.id = instance_data['id']

    def reprovision(self):
        status = self.client._perform_tenant_json("GET", "/instances/%s/actions/reprovision" % self.id)
        print(status)

    def deprovision(self):
        status = self.client._perform_tenant_json("GET", "/instances/%s/actions/deprovision" % self.id)
        print(status)

    def status(self):
        status = self.client._perform_tenant_json("GET", "/instances/%s/status" % self.id)
        return status


class FMInstanceEncryptionMode(Enum):
    NONE = "NONE"
    DEFAULT_KEY = "DEFAULT_KEY"
    TENANT = "TENANT"
    CUSTOM = "CUSTOM"
