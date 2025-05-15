import json
from requests import Session
from requests import exceptions
from requests.auth import HTTPBasicAuth
import os.path as osp
import warnings

from .utils import handle_http_exception

from .iam.settings import FMSSOSettings, FMLDAPSettings, FMAzureADSettings

from .fm.tenant import FMCloudCredentials, FMCloudTags
from .fm.cloudaccounts import (
    FMCloudAccount,
    FMAWSCloudAccountCreator,
    FMAzureCloudAccountCreator,
    FMGCPCloudAccountCreator,
    FMAWSCloudAccount,
    FMAzureCloudAccount,
    FMGCPCloudAccount
)
from .fm.virtualnetworks import (
    FMVirtualNetwork,
    FMAWSVirtualNetworkCreator,
    FMAzureVirtualNetworkCreator,
    FMGCPVirtualNetworkCreator,
    FMAWSVirtualNetwork,
    FMAzureVirtualNetwork,
    FMGCPVirtualNetwork
)
from .fm.loadbalancers import (
    FMAWSLoadBalancerCreator,
    FMAzureLoadBalancerCreator,
    FMAWSLoadBalancer,
    FMAzureLoadBalancer
)
from .fm.instances import (
    FMInstance,
    FMInstanceEncryptionMode,
    FMAWSInstanceCreator,
    FMAzureInstanceCreator,
    FMGCPInstanceCreator,
    FMAWSInstance,
    FMAzureInstance,
    FMGCPInstance
)
from .fm.instancesettingstemplates import (
    FMInstanceSettingsTemplate,
    FMAWSInstanceSettingsTemplateCreator,
    FMAzureInstanceSettingsTemplateCreator,
    FMGCPInstanceSettingsTemplateCreator
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
        no_check_certificate=False,
        client_certificate=None,
        **kwargs
    ):
        """Initialize a new FM (Fleet Management) API client.

        This client provides access to Dataiku's Fleet Management capabilities, allowing interaction
        with feature stores, feature sets, and related functionality.

        Args:
            host (str): The URL of the DSS instance (e.g., "http://localhost:11200")
            api_key_id (str): The API key ID for authentication
            api_key_secret (str): The API key secret for authentication
            tenant_id (str, optional): The tenant ID. Defaults to "main"
            extra_headers (dict, optional): Additional HTTP headers to include in all requests
            no_check_certificate (bool, optional): If True, disables SSL certificate verification.
                Defaults to False.
            client_certificate (str or tuple, optional): Path to client certificate file or tuple of 
                (cert, key) paths for client certificate authentication
            **kwargs: Additional keyword arguments

        Note:
            - API key ID and secret are required for authentication
            - When using HTTPS, certificate verification is enabled by default for security
            - Use no_check_certificate=True only in development or when using self-signed certificates
        """
        if self.cloud == None:
            raise NotImplementedError(
                "Do not use FMClient directly, instead use FMClientAWS, FMClientAzure or FMClientGCP"
            )
        
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate

        self.api_key_id = api_key_id
        self.api_key_secret = api_key_secret
        self.host = host
        self.__tenant_id = tenant_id
        self._session = Session()
        if no_check_certificate:
            self._session.verify = False
        if client_certificate:
            self._session.cert = client_certificate

        if self.api_key_id is not None and self.api_key_secret is not None:
            self._session.auth = HTTPBasicAuth(self.api_key_id, self.api_key_secret)
        else:
            raise ValueError("API Key ID and API Key secret are required")

        if extra_headers is not None:
            self._session.headers.update(extra_headers)

    ########################################################
    # Tenant
    ########################################################

    def get_tenant_id(self):
        return self.__tenant_id

    def get_cloud_credentials(self):
        """
        Get the cloud credentials
        :return: cloud credentials
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudCredentials`
        """
        creds = self._perform_tenant_json("GET", "/cloud-credentials")
        return FMCloudCredentials(self, creds)

    def get_sso_settings(self):
        """
        Get the Single Sign-On (SSO) settings

        :return: SSO settings
        :rtype: :class:`dataikuapi.iam.settings.SSOSettings`
        """
        sso = self._perform_tenant_json("GET", "/iam/sso-settings")
        return FMSSOSettings(self, sso)

    def get_ldap_settings(self):
        """
        Get the LDAP settings

        :return: LDAP settings
        :rtype: :class:`dataikuapi.iam.settings.LDAPSettings`
        """
        ldap = self._perform_tenant_json("GET", "/iam/ldap-settings")
        return FMLDAPSettings(self, ldap)

    def get_azure_ad_settings(self):
        """
        Get the Azure Active Directory (aka Microsoft Entra ID) settings

        :return: Azure AD settings
        :rtype: :class:`dataikuapi.iam.settings.AzureADSettings`
        """
        ldap = self._perform_tenant_json("GET", "/iam/azure-ad-settings")
        return FMAzureADSettings(self, ldap)

    def get_cloud_tags(self):
        """
        Get the tenant's cloud tags

        :return: tenant's cloud tags
        :rtype: :class:`dataikuapi.fm.tenant.FMCloudTags`
        """
        tags = self._perform_tenant_json("GET", "/cloud-tags")
        return FMCloudTags(self, tags)

    ########################################################
    # CloudAccount
    ########################################################

    def _make_cloud_account(self, account):
        if self.cloud == "AWS":
            return FMAWSCloudAccount(self, account)
        elif self.cloud == "Azure":
            return FMAzureCloudAccount(self, account)
        elif self.cloud == "GCP":
            return FMGCPCloudAccount(self, account)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_cloud_accounts(self):
        """
        List all cloud accounts

        :return: list of cloud accounts
        :rtype: list of :class:`dataikuapi.fm.cloudaccounts.FMCloudAccount`
        """
        vns = self._perform_tenant_json("GET", "/cloud-accounts")
        return [self._make_cloud_account(x) for x in vns]

    def get_cloud_account(self, cloud_account_id):
        """
        Get a cloud account by its id

        :param str cloud_account_id: the id of the cloud account to retrieve

        :return: the requested cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMCloudAccount`
        """
        vn = self._perform_tenant_json(
            "GET", "/cloud-accounts/%s" % cloud_account_id
        )
        return self._make_cloud_account(vn)

    ########################################################
    # VirtualNetwork
    ########################################################

    def _make_virtual_network(self, vn):
        if self.cloud == "AWS":
            return FMAWSVirtualNetwork(self, vn)
        elif self.cloud == "Azure":
            return FMAzureVirtualNetwork(self, vn)
        elif self.cloud == "GCP":
            return FMGCPVirtualNetwork(self, vn)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_virtual_networks(self):
        """
        List all virtual networks

        :return: list of virtual networks
        :rtype: list of :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vns = self._perform_tenant_json("GET", "/virtual-networks")
        return [self._make_virtual_network(x) for x in vns]

    def get_virtual_network(self, virtual_network_id):
        """
        Get a virtual network by its id

        :param str virtual_network_id: the id of the network to retrieve

        :return: the requested virtual network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMVirtualNetwork`
        """
        vn = self._perform_tenant_json(
            "GET", "/virtual-networks/%s" % virtual_network_id
        )
        return self._make_virtual_network(vn)

    ########################################################
    # Load balancers
    ########################################################

    def _make_load_balancer(self, vn):
        if self.cloud == "AWS":
            return FMAWSLoadBalancer(self, vn)
        elif self.cloud == "Azure":
            return FMAzureLoadBalancer(self, vn)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_load_balancers(self):
        """
        List all load balancers

        :return: list of load balancers
        :rtype: list of :class:`dataikuapi.fm.loadbalancers.FMLoadBalancer`
        """
        vns = self._perform_tenant_json("GET", "/load-balancers")
        return [self._make_load_balancer(x) for x in vns]

    def get_load_balancer(self, load_balancer_id):
        """
        Get a load balancer by its id

        :param str load_balancer_id: the id of the load balancer to retrieve

        :return: the requested load balancer
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancer`
        """
        vn = self._perform_tenant_json(
            "GET", "/load-balancers/%s" % load_balancer_id
        )
        return self._make_load_balancer(vn)

    ########################################################
    # Instance settings template
    ########################################################

    def list_instance_templates(self):
        """
        List all instance settings templates

        :return: list of instance settings template
        :rtype: list of :class:`dataikuapi.fm.tenant.FMInstanceSettingsTemplate`
        """
        templates = self._perform_tenant_json("GET", "/instance-settings-templates")
        return [FMInstanceSettingsTemplate(self, x) for x in templates]

    def get_instance_template(self, template_id):
        """
        Get an instance setting template template by its id

        :param str template_id: the id of the template to retrieve

        :return: the requested instance settings template
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
        elif self.cloud == "GCP":
            return FMGCPInstance(self, i)
        else:
            raise Exception("Unknown cloud type %s" % self.cloud)

    def list_instances(self):
        """
        List all DSS instances

        :return: list of instances
        :rtype: list of :class:`dataikuapi.fm.instances.FMInstance`
        """
        instances = self._perform_tenant_json("GET", "/instances")
        return [self._make_instance(x) for x in instances]

    def get_instance(self, instance_id):
        """
        Get a DSS instance by its id

        :param str instance_id: the id of the instance to retrieve

        :return: the requested instance if any
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


        http_res = self._session.request(
                method,
                "%s/api/public%s" % (self.host, path),
                params=params,
                data=body,
                files=files,
                stream=stream,
            )
        handle_http_exception(http_res)
        return http_res

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
        no_check_certificate=False,
        **kwargs
    ):
        """
        AWS Only - Instantiate a new FM API client on the given host with the given API key.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM

        """
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate

        self.cloud = "AWS"
        super(FMClientAWS, self).__init__(
            host, api_key_id, api_key_secret, tenant_id, extra_headers, no_check_certificate=no_check_certificate
        )

    def new_cloud_account_creator(self, label):
        """
        Instantiate a new cloud account creator

        :param str label: The label of the cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMAWSCloudAccountCreator`
        """
        return FMAWSCloudAccountCreator(self, label)

    def new_virtual_network_creator(self, label):
        """
        Instantiate a new virtual network creator

        :param str label: The label of the network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMAWSVirtualNetworkCreator`
        """
        return FMAWSVirtualNetworkCreator(self, label)

    def new_load_balancer_creator(self, name, virtual_network_id):
        """
        Instantiate a new load balancer creator

        :param str name: The name of the load balancer
        :param str virtual_network_id: The id of the virtual network
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMAWSLoadBalancerCreator`
        """
        return FMAWSLoadBalancerCreator(self, name, virtual_network_id)

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
        no_check_certificate=False,
        **kwargs
    ):
        """
        Azure Only - Instantiate a new FM API client on the given host with the given API key.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM
        """
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate

        self.cloud = "Azure"
        super(FMClientAzure, self).__init__(
            host, api_key_id, api_key_secret, tenant_id, extra_headers, no_check_certificate=no_check_certificate
        )

    def new_cloud_account_creator(self, label):
        """
        Instantiate a new cloud account creator

        :param str label: The label of the cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMAzureCloudAccountCreator`
        """
        return FMAzureCloudAccountCreator(self, label)

    def new_virtual_network_creator(self, label):
        """
        Instantiate a new virtual network creator

        :param str label: The label of the network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMAzureVirtualNetworkCreator`
        """
        return FMAzureVirtualNetworkCreator(self, label)

    def new_load_balancer_creator(self, name, virtual_network_id):
        """
        Instantiate a new Load balancer creator

        :param str name: The name of the load balancer
        :param str virtual_network_id: The id of the virtual network
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMAzureLoadBalancerCreator`
        """
        return FMAzureLoadBalancerCreator(self, name, virtual_network_id)

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

class FMClientGCP(FMClient):
    def __init__(
        self,
        host,
        api_key_id,
        api_key_secret,
        tenant_id="main",
        extra_headers=None,
        no_check_certificate=False,
        **kwargs
    ):
        """
        GCP Only - Instantiate a new FM API client on the given host with the given API key.

        The API key will define which operations are allowed for the client.

        :param str host: Full url of the FM
        """
        if "insecure_tls" in kwargs:
            # Backward compatibility before removing insecure_tls option
            warnings.warn("insecure_tls field is now deprecated. It has been replaced by no_check_certificate.", DeprecationWarning)
            no_check_certificate = kwargs.get("insecure_tls") or no_check_certificate
        
        self.cloud = "GCP"
        super(FMClientGCP, self).__init__(
            host, api_key_id, api_key_secret, tenant_id, extra_headers, no_check_certificate=no_check_certificate
        )

    def new_cloud_account_creator(self, label):
        """
        Instantiate a new cloud account creator

        :param str label: The label of the cloud account
        :rtype: :class:`dataikuapi.fm.cloudaccounts.FMGCPCloudAccountCreator`
        """
        return FMGCPCloudAccountCreator(self, label)

    def new_virtual_network_creator(self, label):
        """
        Instantiate a new virtual network creator

        :param str label: The label of the network
        :rtype: :class:`dataikuapi.fm.virtualnetworks.FMGCPVirtualNetworkCreator`
        """
        return FMGCPVirtualNetworkCreator(self, label)

    def new_instance_template_creator(self, label):
        """
        Instantiate a new instance template creator

        :param str label: The label of the instance
        :rtype: :class:`dataikuapi.fm.instancesettingstemplates.FMGCPInstanceSettingsTemplateCreator`
        """
        return FMGCPInstanceSettingsTemplateCreator(self, label)

    def new_instance_creator(
        self, label, instance_settings_template_id, virtual_network_id, image_id
    ):
        """
        Instantiate a new instance creator

        :param str label: The label of the instance
        :param str instance_settings_template: The instance settings template id this instance should be based on
        :param str virtual_network: The virtual network where the instance should be spawned
        :param str image_id: The ID of the DSS runtime image (ex: dss-9.0.3-default)
        :rtype: :class:`dataikuapi.fm.instances.FMGCPInstanceCreator`
        """
        return FMGCPInstanceCreator(
            self, label, instance_settings_template_id, virtual_network_id, image_id
        )
