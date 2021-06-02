from enum import Enum
import json

class FMInstanceSettingsTemplate(object):
    def __init__(self, client, ist_data):
        self.client  = client
        self.id = ist_data['id']
        self.ist_data = ist_data

    def save(self):
        """
        Update the Instance Settings Template.
        """
        self.client._perform_tenant_empty("PUT", "/instance-settings-templates/%s" % self.id, body=self.ist_data)
        self.ist_data = self.client._perform_tenant_json("GET", "/instance-settings-templates/%s" % self.id)

class FMSetupAction(dict):
    def __init__(self, setupActionType, params=None):
        """
        param: object setupActionType: the type (`:class: FMSetupActionType`) of the SetupAction
        param: str params: the parameters of the SetupAction in a json-encoded string
        """
        data = {
            "type": setupActionType.value,
        }
        if params:
            data['params'] = params

        super(FMSetupAction, self).__init__(data)

class FMSetupActionAddAuthorizedKey(FMSetupAction):
    def __init__(self, ssh_key):
        super(FMSetupActionAddAuthorizedKey, self).__init__(FMSetupActionType.ADD_AUTHORIZED_KEY, {"sshKey": ssh_key })

class FMSetupActionType(Enum):
    RUN_ANSIBLE_TASKS="RUN_ANSIBLE_TASKS"
    INSTALL_SYSTEM_PACKAGES="INSTALL_SYSTEM_PACKAGES"
    INSTALL_DSS_PLUGINS_FROM_STORE="INSTALL_DSS_PLUGINS_FROM_STORE"
    SETUP_K8S_AND_SPARK="SETUP_K8S_AND_SPARK"
    SETUP_RUNTIME_DATABASE="SETUP_RUNTIME_DATABASE"
    SETUP_MUS_AUTOCREATE="SETUP_MUS_AUTOCREATE"
    SETUP_UI_CUSTOMIZATION="SETUP_UI_CUSTOMIZATION"
    SETUP_MEMORY_SETTINGS="SETUP_MEMORY_SETTINGS"
    SETUP_GRAPHICS_EXPORT="SETUP_GRAPHICS_EXPORT"
    ADD_AUTHORIZED_KEY="ADD_AUTHORIZED_KEY"
    INSTALL_JDBC_DRIVER="INSTALL_JDBC_DRIVER"
    SETUP_ADVANCED_SECURITY="SETUP_ADVANCED_SECURITY"
