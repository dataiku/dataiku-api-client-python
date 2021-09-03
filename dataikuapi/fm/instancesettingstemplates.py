from enum import Enum
import json
from dataikuapi.fm.future import FMFuture

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

    def delete(self):
        """
        Delete the DSS Instance Settings Template.

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the deletion process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("DELETE", "/instance-settings-templates/%s" % self.id)
        return FMFuture.from_resp(self.client, future)

    def add_setup_action(self, setup_action):
        """
        Add a setup_action

        :param object setup_action: a :class:`dataikuapi.fm.instancesettingstemplates.FMSetupAction`
        """
        self.ist_data['setupActions'].append(setup_action)
        self.save()


class FMSetupAction(dict):
    def __init__(self, setupActionType, params=None):
        """
        A class representing a SetupAction

        Do not create this directly, use:
            - :meth:`dataikuapi.fm.instancesettingstemplates.FMSetupAction.add_authorized_key`

        """
        data = {
            "type": setupActionType.value,
        }
        if params:
            data['params'] = params

        super(FMSetupAction, self).__init__(data)

    @staticmethod
    def add_authorized_key(ssh_key):
        """
        Return a ADD_AUTHORIZED_KEY SetupAction
        """
        return FMSetupAction(FMSetupActionType.ADD_AUTHORIZED_KEY, {"sshKey": ssh_key })

    @staticmethod
    def run_ansible_task(stage, yaml_string):
        """
        Return a RUN_ANSIBLE_TASK SetupAction

        :params object stage: a :class:`dataikuapi.fm.instancesettingstemplates.FMSetupActionStage`
        :params str yaml_string: a yaml encoded string defining the ansibles tasks to run
        """
        return FMSetupAction(FMSetupActionType.RUN_ANSIBLE_TASKS, {"stage": stage.value, "ansibleTasks": yaml_string })

    @staticmethod
    def install_system_packages(packages):
        """
        Return an INSTALL_SYSTEM_PACKAGES SetupAction

        :params list packages: List of packages to install
        """
        return FMSetupAction(FMSetupActionType.INSTALL_SYSTEM_PACKAGES, {"packages": packages })

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

class FMSetupActionStage(Enum):
    after_dss_startup="after_dss_startup"
    after_install="after_install"
    before_install="before_install"
