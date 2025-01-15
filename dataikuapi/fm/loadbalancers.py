from .future import FMFuture

import sys

if sys.version_info > (3, 4):
    from enum import Enum
else:
    class Enum(object):
        pass


class FMLoadBalancerCreator(object):
    def __init__(self, client, name, virtual_network_id):
        """
        A builder class to create load balancer

        :param str name: The Name of the load balancer
        :param str virtual_network_id: The id of the virtual network
        """
        self.client = client
        self.lb_data = {}
        self.lb_data["name"] = name
        self.lb_data["virtualNetworkId"] = virtual_network_id
        self.lb_data["azureAssignPublicIP"] = False
        self.lb_data["nodes"] = []

    def with_description(self, description):
        """
        Set the load balancer description

        :param str description

        """
        self.lb_data["description"] = description
        return self

    def with_cloud_tags(self, cloud_tags):
        """
        Set the tags to be applied to the cloud resources created for this load balancer

        :param dict cloud_tags: a key value dictionary of tags to be applied on the cloud resources
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["cloudTags"] = cloud_tags
        return self

    def with_fm_tags(self, fm_tags):
        """
        A list of tags to add on the load balancer in Fleet Manager

        :param list fm_tags: Optional, list of tags to be applied on the load balancer in the Fleet Manager
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["fmTags"] = fm_tags
        return self
    
    def with_private_scheme(self):
        """
        Setup the load balancer private

        """
        self.lb_data["publicIpMode"] = 'NO_PUBLIC_IP'
        return self
    
    def add_node(self, hostname, instance):
        """
        The node mapping to add on the load balancer in Fleet Manager

        :param str hostname: the hostname for the instance
        :param :class:`dataikuapi.fm.instances.FMInstance` instance: the instance to assign to the load balancer
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["nodes"].append({
            "hostname": hostname,
            "instanceId": instance.id            
        })
        return self
        
    def remove_node(self, hostname):
        """
        The node mapping to remove on the load balancer in Fleet Manager

        :param str hostname: the hostname for the instance
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """

        self.lb_data["nodes"] = [x for x in self.lb_data["nodes"] if x["hostname"] != hostname]
        return self


class FMAWSLoadBalancerCreator(FMLoadBalancerCreator):
    def with_certificate_arn(self, aws_certificate_arn):
        """
        Setup the certificate ARN to be used by the load balancer

        :param str aws_certificate_arn: certificate ARN
        """
        self.lb_data["certificateMode"] = 'AWS_ARN'
        self.lb_data["awsCertificateARN"] = aws_certificate_arn
        return self

    def create(self):
        """
        Create a new load balancer

        :return: a newly created load balancer
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMAWSLoadBalancer`
        """
        lb = self.client._perform_tenant_json(
            "POST", "/load-balancers", body=self.lb_data
        )
        return FMAWSLoadBalancer(self.client, lb)


class FMAzureLoadBalancerCreator(FMLoadBalancerCreator):

    def with_tier(self, tier):
        """
        Setup the tier of the load balancer

        :param :class:`dataikuapi.fm.loadbalancers.FMAzureLoadBalancerTier` tier: lb tier
        """
        self.lb_data["tier"] = tier.value
        return self

    def with_certificate_secret_id(self, azure_certificate_secret_id):
        """
        Setup the certificate secret id to be used by the load balancer

        :param str azure_certificate_secret_id: certificate secret id
        """
        self.lb_data["certificateMode"] = 'AZURE_SECRET_ID'
        self.lb_data["azureCertificateSecretId"] = azure_certificate_secret_id
        return self
    
    def with_public_ip(self, azure_public_ip):
        """
        Setup the public IP to be used by the load balancer

        :param str azure_public_ip: public ip ID
        """
        self.lb_data["publicIpMode"] = 'STATIC_PUBLIC_IP'
        self.lb_data["azurePublicIPID"] = azure_public_ip
        return self
    

    def with_dynamic_public_ip(self):
        """
        Setup the public IP to be dynamic for the load balancer
        """
        self.lb_data["publicIpMode"] = 'DYNAMIC_PUBLIC_IP'
        return self

    def create(self):
        """
        Create a new load balancer

        :return: a newly created load balancer
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMAzureLoadBalancer`
        """
        lb = self.client._perform_tenant_json(
            "POST", "/load-balancers", body=self.lb_data
        )
        return FMAzureLoadBalancer(self.client, lb)
    
class FMLoadBalancer(object):
    def __init__(self, client, lb_data):
        self.client = client
        self.lb_data = lb_data
        self.id = self.lb_data["id"]

    def provision(self):
        """
        Provision the physical load balancer

        :return: the `Future` object representing the reprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "POST", "/load-balancers/%s/actions/provision" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def update(self):
        """
        Update the physical load balancer

        :return: the `Future` object representing the update process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "POST", "/load-balancers/%s/actions/update" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def reprovision(self):
        """
        Reprovision the physical load balancer

        :return: the `Future` object representing the reprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "POST", "/load-balancers/%s/actions/reprovision" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def deprovision(self):
        """
        Deprovision the physical load balancer

        :return: the `Future` object representing the deprovision process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "POST", "/load-balancers/%s/actions/deprovision" % self.id
        )
        return FMFuture.from_resp(self.client, future)

    def get_physical_status(self):
        """
        Get the physical load balancer's status

        :return: the load balancer status
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerPhysicalStatus`
        """
        status = self.client._perform_tenant_json(
            "GET", "/load-balancers/%s/physical/status" % self.id
        )
        return FMLoadBalancerPhysicalStatus(status)


    def set_description(self, description):
        """
        Set the load balancer description

        :param str description"

        """
        self.lb_data["description"] = description
        return self


    def set_cloud_tags(self, cloud_tags):
        """
        Set the tags to be applied to the cloud resources created for this load balancer

        :param dict cloud_tags: a key value dictionary of tags to be applied on the cloud resources
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["cloudTags"] = cloud_tags
        return self

    def set_fm_tags(self, fm_tags):
        """
        A list of tags to add on the load balancer in Fleet Manager

        :param list fm_tags: Optional, list of tags to be applied on the load balancer in the Fleet Manager
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["fmTags"] = fm_tags
        return self
    
    def set_private(self):
        """
        Setup the load balancer private

        """
        self.lb_data["publicIpMode"] = 'NO_PUBLIC_IP'
        return self
    
    def add_node(self, hostname, instance):
        """
        The node mapping to add on the load balancer in Fleet Manager

        :param str hostname: the hostname for the instance
        :param :class:`dataikuapi.fm.instances.FMInstance` instance: the instance to assign to the load balancer
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """
        self.lb_data["nodes"].append({
            "hostname": hostname,
            "instanceId": instance.id            
        })
        return self
        
    def remove_node(self, hostname):
        """
        The node mapping to remove on the load balancer in Fleet Manager

        :param str hostname: the hostname for the instance
        :rtype: :class:`dataikuapi.fm.loadbalancers.FMLoadBalancerCreator`
        """

        self.lb_data["nodes"] = [x for x in self.lb_data["nodes"] if x["hostname"] != hostname]
        return self

    def save(self):
        """
        Update this load balancers.
        """
        self.client._perform_tenant_empty(
            "PUT", "/load-balancers/%s" % self.id, body=self.lb_data
        )
        self.lb_data = self.client._perform_tenant_json(
            "GET", "/load-balancers/%s" % self.id
        )

    def delete(self):
        """
        Delete this load balancer.

        :return: the `Future` object representing the deletion process
        :rtype: :class:`dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json(
            "DELETE", "/load-balancers/%s" % self.id
        )
        return FMFuture.from_resp(self.client, future)


class FMAWSLoadBalancer(FMLoadBalancer):
    def set_certificate_arn(
        self,
        certificate_arn
    ):
        """
        Set the certificate ARN for this load balancer

        :param str certificate_arn: the certificate ARN
        """

        self.lb_data["awsCertificateARN"] = certificate_arn
        return self

class FMAzureLoadBalancer(FMLoadBalancer):
    def set_tier(self, tier):
        """
        Setup the tier of the load balancer

        :param :class:`dataikuapi.fm.loadbalancers.FMAzureLoadBalancerTier` tier: lb tier
        """
        self.lb_data["tier"] = tier.value
        return self

    def set_certificate_secret_id(
        self,
        certificate_secret_id
    ):
        """
        Set the certificate secret id for this load balancer

        :param str certificate_secret_id: the certificate secret ID
        """

        self.lb_data["azureCertificateSecretId"] = certificate_secret_id
        return self

    def set_public_ip(self, azure_public_ip):
        """
        Setup the public IP to be used by the load balancer

        :param str azure_public_ip: public ip ID
        """
        self.lb_data["publicIpMode"] = 'STATIC_PUBLIC_IP'
        self.lb_data["azurePublicIPID"] = azure_public_ip
        return self

    def set_dynamic_public_ip(self):
        """
        Setup the public IP to be dynamic for the load balancer
        """
        self.lb_data["publicIpMode"] = 'DYNAMIC_PUBLIC_IP'
        return self


class FMLoadBalancerPhysicalStatus(dict):
    """
    A class holding read-only information about an load balancer.
    This class should not be created directly. Instead, use :meth:`FMLoadBalancer.get_physical_status`
    """

    def __init__(self, data):
        """
        Do not call this directly, use :meth:`FMLoadBalancer.get_physical_status`
        """
        super(FMLoadBalancerPhysicalStatus, self).__init__(data)


class FMAzureLoadBalancerTier(Enum):
    WAF_V2 = "WAF_V2"
    STANDARD_V2 = "STANDARD_V2"

    # Python2 emulated enum. to be removed on Python2 support removal
    @staticmethod
    def get_from_string(s):
        if s == "WAF_V2": return FMAzureLoadBalancerTier.WAF_V2
        if s == "STANDARD_V2": return FMAzureLoadBalancerTier.STANDARD_V2
        raise Exception("Invalid load balancer tier " + s)
