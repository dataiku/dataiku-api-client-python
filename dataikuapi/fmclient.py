import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
import os.path as osp

from .utils import DataikuException

from .fm.tenant import FMCloudCredentials, FMCloudTags
from .fm.virtualnetworks import (
    FMVirtualNetwork,
    FMAWSVirtualNetworkCreator,
    FMAzureVirtualNetworkCreator,
    FMAWSVirtualNetwork,
    FMAzureVirtualNetwork,
)
from .fm.instances import (
    FMInstance,
    FMInstanceEncryptionMode,
    FMAWSInstanceCreator,
    FMAzureInstanceCreator,
    FMAWSInstance,
    FMAzureInstance,
)
from .fm.instancesettingstemplates import (
    FMInstanceSettingsTemplate,
    FMAWSInstanceSettingsTemplateCreator,
    FMAzureInstanceSettingsTemplateCreator,
)

import sys

if sys.version_info > (3, 4):
    from enum import Enum
else:

    class Enum(object):
        pass


class FMClient(object):
    def __init__(
        self,
        host,
        api_key_id,
        api_key_secret,
        tenant_id="main",
        extra_headers=None,
    ):
        """
        Base class for the different FM Clients
        Do not create this class, instead use :class:`dataikuapi.FMClientAWS` or :class:`dataikuapi.FMClientAzure`
        """
        if self.cloud == None:
            raise NotImplementedError(
                "Do not use FMClient directly, instead use FMClientAWS or FMClientAzure"
            )
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
        Get Cloud Credentials

        :return: Cloud credentials
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudCredentials`
        """
        creds = self._perform_tenant_json("GET", "/cloud-credentials")
        return FMCloudCredentials(self, creds)

    def get_cloud_tags(self):
        """
        Get Tenant's Cloud Tags

        :param string tenant_id

        :return: tenant's cloud tags
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudTags`
        """
        tags = self._perform_tenant_json("GET", "/cloud-tags")
        return FMCloudTags(self, tags)

    ########################################################
    # VirtualNetwork
    ########################################################

    def _make_virtual_network(self, vn):
        if self.cloud == "AWS":
            return FMAWSVirtualNetwork(self, vn)
        elif self.cloud == "Azure":
            return FMAzureVirtualNetwork(self, vn)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_virtual_networks(self):
        """
        List all Virtual Networks

        :return: list of virtual networks
        :rtype: list of :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vns = self._perform_tenant_json("GET", "/virtual-networks")
        return [self._make_virtual_network(x) for x in vns]

    def get_virtual_network(self, virtual_network_id):
        """
        Get a Virtual Network

        :param str virtual_network_id

        :return: requested virtual network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vn = self._perform_tenant_json(
            "GET", "/virtual-networks/%s" % virtual_network_id
        )
        return self._make_virtual_network(vn)

    ########################################################
    # Instance settings template
    ########################################################

    def list_instance_templates(self):
        """
        List all Instance Settings Templates

        :return: list of instance settings template
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstanceSettingsTemplate`
        """
        templates = self._perform_tenant_json("GET", "/instance-settings-templates")
        return [FMInstanceSettingsTemplate(self, x) for x in templates]

    def get_instance_template(self, template_id):
        """
        Get an Instance Template

        :param str template_id

        :return: requested instance settings template
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMInstanceSettingsTemplate`
        """
        template = self._perform_tenant_json(
            "GET", "/instance-settings-templates/%s" % template_id
        )
        return FMInstanceSettingsTemplate(self, template)

    ########################################################
    # Instance
    ########################################################

    def _make_instance(self, i):
        if self.cloud == "AWS":
            return FMAWSInstance(self, i)
        elif self.cloud == "Azure":
            return FMAzureInstance(self, i)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_instances(self):
        """
        List all DSS Instances

        :return: list of instances
        :rtype: list of :class:`dataikuapi.fm.instances.FMInstance`
        """
        instances = self._perform_tenant_json("GET", "/instances")
        return [self._make_instance(x) for x in instances]

    def get_instance(self, instance_id):
        """
        Get a DSS Instance

        :param str instance_id

        :return: Instance
        :rtype: :class:`dataikuapi.fm.instances.FMInstance`
        """
        instance = self._perform_tenant_json("GET", "/instances/%s" % instance_id)
        return self._make_instance(instance)

    def list_instance_images(self):
        """
        List all available images to create new instances

        :return: list of images, as a pair of id and label
        """
        return self._perform_tenant_json("GET", "/images")

    ########################################################
    # Internal Request handling
    ########################################################

    def _perform_http(
        self,
        method,
        path,
        params=None,
        body=None,
        stream=False,
        files=None,
        raw_body=None,
    ):
        if body is not None:
            body = json.dumps(body)
        if raw_body is not None:
            body = raw_body
        try:
            http_res = self._session.request(
                method,
                "%s/api/public%s" % (self.host, path),
                params=params,
                data=body,
                files=files,
                stream=stream,
            )
            http_res.raise_for_status()
            return http_res
        except exceptions.HTTPError:
            try:
                ex = http_res.json()
            except ValueError:
                ex = {"message": http_res.text}
            raise DataikuException(
                "%s: %s"
                % (
                    ex.get("errorType", "Unknown error"),
                    ex.get("message", "No message"),
                )
            )

    def _perform_empty(
        self, method, path, params=None, body=None, files=None, raw_body=None
    ):
        self._perform_http(
            method,
            path,
            params=params,
            body=body,
            files=files,
            stream=False,
            raw_body=raw_body,
        )

    def _perform_json(
        self, method, path, params=None, body=None, files=None, raw_body=None
    ):
        return self._perform_http(
            method,
            path,
            params=params,
            body=body,
            files=files,
            stream=False,
            raw_body=raw_body,
        ).json()

    def _perform_tenant_json(
        self, method, path, params=None, body=None, files=None, raw_body=None
    ):
        return self._perform_json(
            method,
            "/tenants/%s%s" % (self.__tenant_id, path),
            params=params,
            body=body,
            files=files,
            raw_body=raw_body,
        )

    def _perform_tenant_empty(
        self, method, path, params=None, body=None, files=None, raw_body=None
    ):
        self._perform_empty(
            method,
            "/tenants/%s%s" % (self.__tenant_id, path),
            params=params,
            body=body,
            files=files,
            raw_body=raw_body,
        )


class FMClientAWS(FMClient):
    def __init__(
        self,
        host,
        api_key_id,
        api_key_secret,
        tenant_id="main",
        extra_headers=None,
    ):
        """
        AWS Only - Instantiate a new FM API client on the given host with the given API key.

        API keys can be managed in FM on the project page or in the global settings.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM

        """
        self.cloud = "AWS"
        super(FMClientAWS, self).__init__(
            host, api_key_id, api_key_secret, tenant_id, extra_headers
        )

    def new_virtual_network_creator(self, label):
        """
        Instantiate a new virtual network creator

        :param str label: The label of the
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMAWSVirtualNetworkCreator`
        """
        return FMAWSVirtualNetworkCreator(self, label)

    def new_instance_template_creator(self, label):
        """
        Instantiate a new instance template creator

        :param str label: The label of the instance
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMAWSInstanceSettingsTemplateCreator`
        """
        return FMAWSInstanceSettingsTemplateCreator(self, label)

    def new_instance_creator(
        self, label, instance_settings_template_id, virtual_network_id, image_id
    ):
        """
        Instantiate a new instance creator

        :param str label: The label of the instance
        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)
        :rtype: :class:`dataikuapi.fm.instances.FMAWSInstanceCreator`
        """
        return FMAWSInstanceCreator(
            self, label, instance_settings_template_id, virtual_network_id, image_id
        )


class FMClientAzure(FMClient):
    def __init__(
        self,
        host,
        api_key_id,
        api_key_secret,
        tenant_id="main",
        extra_headers=None,
    ):
        """
        Azure Only - Instantiate a new FM API client on the given host with the given API key.

        API keys can be managed in FM on the project page or in the global settings.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM
        """
        self.cloud = "Azure"
        super(FMClientAzure, self).__init__(
            host, api_key_id, api_key_secret, tenant_id, extra_headers
        )

    def new_virtual_network_creator(self, label):
        """
        Instantiate a new virtual network creator

        :param str label: The label of the
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMAzureVirtualNetworkCreator`
        """
        return FMAzureVirtualNetworkCreator(self, label)

    def new_instance_template_creator(self, label):
        """
        Instantiate a new instance template creator

        :param str label: The label of the instance
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMAzureInstanceSettingsTemplateCreator`
        """
        return FMAzureInstanceSettingsTemplateCreator(self, label)

    def new_instance_creator(
        self, label, instance_settings_template_id, virtual_network_id, image_id
    ):
        """
        Instantiate a new instance creator

        :param str label: The label of the instance
        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)
        :rtype: :class:`dataikuapi.fm.instances.FMAzureInstanceCreator`
        """
        return FMAzureInstanceCreator(
            self, label, instance_settings_template_id, virtual_network_id, image_id
        )
