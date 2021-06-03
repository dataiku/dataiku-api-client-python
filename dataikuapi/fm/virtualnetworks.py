from dataikuapi.fm.future import FMFuture

class FMVirtualNetwork(object):
    def __init__(self, client, vn_data):
        self.client  = client
        self.vn_data = vn_data
        self.id = self.vn_data['id']

    def save(self):
        """
        Update the Virtual Network.
        """
        self.client._perform_tenant_empty("PUT", "/virtual-networks/%s" % self.id, body=self.vn_data)
        self.vn_data = self.client._perform_tenant_json("GET", "/virtual-networks/%s" % self.id)

    def delete(self):
        """
        Delete the DSS Instance Settings Template.

        :return: A :class:`~dataikuapi.fm.future.FMFuture` representing the deletion process
        :rtype: :class:`~dataikuapi.fm.future.FMFuture`
        """
        future = self.client._perform_tenant_json("DELETE", "/virtual-networks/%s" % self.id)
        return FMFuture.from_resp(self.client, future)

    def set_fleet_management(self, enable, event_server=None, deployer_management="NO_MANAGED_DEPLOYER"):
        """
        When enabled, all instances in this virtual network know each other and can centrally manage deployer and logs centralization

        :param boolean enable: Enable or not the Fleet Management

        :param str event_server: Optional,  Node name of the node that should act as the centralized event server for logs concentration. Audit logs of all design, deployer and automation nodes will automatically be sent there.
        :param str deployer_management: Optional, Accepts:
            - "NO_MANAGED_DEPLOYER": Do not manage the the deployer. This is the default mode.
            - "CENTRAL_DEPLOYER": Central deployer. Recommanded if you have more than one design node or may have more than one design node in the future.
            - "EACH_DESIGN_NODE": Deployer from design. Recommanded if you have a single design node and want a simpler setup.
        """

        self.vn_data['managedNodesDirectory'] = enable
        self.vn_data['eventServerNodeLabel'] = event_server
        self.vn_data['nodesDirectoryDeployerMode'] = deployer_management
        self.save()

    def set_dns_strategy(self, assign_domain_name, aws_private_ip_zone53_id=None, aws_public_ip_zone53_id=None, azure_dns_zone_id=None):
        """
        Set the DNS strategy for this virtual network

        :param boolean assign_domain_name: If false, don't assign domain names, use ip_only
        :param str aws_private_ip_zone53_id: Optional, AWS Only, the ID of the AWS Route53 Zone to use for private ip
        :param str aws_public_ip_zone53_id: Optional, AWS Only, the ID of the AWS Route53 Zone to use for public ip
        :param str azure_dns_zone_id: Optional, Azure Only, the ID of the Azure DNS zone to use
        """

        if assign_domain_name:
            self.vn_data['dnsStrategy'] = "VN_SPECIFIC_CLOUD_DNS_SERVICE"
            self.vn_data['awsRoute53PrivateIPZoneId'] = aws_private_ip_zone53_id
            self.vn_data['awsRoute53PublicIPZoneId'] = aws_public_ip_zone53_id
            self.vn_data['azureDnsZoneId'] = azure_dns_zone_id
        else :
            self.vn_data['dnsStrategy'] = "NONE"

        self.save()

    def set_https_strategy(self, https_strategy):
        """
        Set the HTTPS strategy for this virtual network

        :param object: a :class:`dataikuapi.fm.virtualnetworks.FMHTTPSStrategy`
        """
        self.vn_data.update(https_strategy)
        self.save()

class FMHTTPSStrategy(dict):
    def __init__(self, data, https_strategy, http_redirect=False):
        """
        A class holding HTTPS Strategy for Virtual Network

        Do not create this directly, use:
            - :meth:`dataikuapi.fm.virtualnetwork.FMHTTPSStrategy.disable` to use HTTP only
            - :meth:`dataikuapi.fm.virtualnetwork.FMHTTPSStrategy.self_signed` to use self-signed certificates
            - :meth:`dataikuapi.fm.virtualnetwork.FMHTTPSStrategy.custom_cert` to use custom certificates
            - :meth:`dataikuapi.fm.virtualnetwork.FMHTTPSStrategy.lets_encrypt` to use Let's Encrypt
        """
        super(FMHTTPSStrategy, self).__init__(data)
        self['httpsStrategy'] = https_strategy
        if http_redirect:
            self['httpStrategy'] = "REDIRECT"
        else:
            self['httpStrategy'] = "DISABLE"

    @staticmethod
    def disable():
        """
        Use HTTP only
        """
        return FMHTTPSStrategy({}, "NONE", False)

    @staticmethod
    def self_signed(http_redirect):
        """
        Use self-signed certificates

        :param bool http_redirect: If true, HTTP is redirected to HTTPS. If false, HTTP is disabled. Defaults to false
        """
        return FMHTTPSStrategy({}, "SELF_SIGNED", http_redirect)

    @staticmethod
    def custom_cert(http_redirect):
        """
        Use a custom certificate for each instance

        :param bool http_redirect: If true, HTTP is redirected to HTTPS. If false, HTTP is disabled. Defaults to false
        """
        return FMHTTPSStrategy({}, "CUSTOM_CERTIFICATE", http_redirect)

    @staticmethod
    def lets_encrypt(contact_mail):
        """
        Use Let's Encrypt to generate https certificates

        :param str contact_mail: The contact email provided to Let's Encrypt
        """
        return FMHTTPSStrategy({"contactMail": contact_mail}, "LETSENCRYPT", True)
