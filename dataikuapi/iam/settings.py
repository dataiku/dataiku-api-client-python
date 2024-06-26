import sys

if sys.version_info > (3, 4):
    from enum import Enum
else:

    class Enum(object):
        pass


class UserRemappingRule(object):
    def __init__(self, rule_from=None, rule_to=None):
        """
        A class representing a User Remapping Rule

        :param str rule_from: Rule From
        :param str rule_to: Rule To
        """
        self.rule_from = rule_from
        self.rule_to = rule_to


class SSOProtocol(Enum):
    SAML = "SAML"
    SPNEGO = "SPNEGO"
    OPENID = "OPENID"


class TokenEndpointAuthMethod(Enum):
    CLIENT_SECRET_BASIC = "CLIENT_SECRET_BASIC"
    CLIENT_SECRET_POST = "CLIENT_SECRET_POST"


class OpenIDParams(dict):
    def __init__(self, data):
        """
        A class holding OpenID parameters for SSO settings

        Do not create this directly.

        :param dict data: Initial OpenID parameters
        """
        super(OpenIDParams, self).__init__(data)

    def set_client_id(self, client_id):
        """
        Set the OpenID client ID.

        :param str client_id: OpenID client ID
        :return: self
        :rtype: OpenIDParams
        """
        self["clientId"] = client_id
        return self

    def set_client_secret(self, client_secret):
        """
        Set the OpenID client secret.

        :param str client_secret: OpenID client secret
        :return: self
        :rtype: OpenIDParams
        """
        self["clientSecret"] = client_secret
        return self

    def set_scope(self, scope):
        """
        Set the OpenID scope.

        :param str scope: OpenID scope
        :return: self
        :rtype: OpenIDParams
        """
        self["scope"] = scope
        return self

    def set_issuer(self, issuer):
        """
        Set the OpenID issuer.

        :param str issuer: OpenID issuer
        :return: self
        :rtype: OpenIDParams
        """
        self["issuer"] = issuer
        return self

    def set_authorization_endpoint(self, authorization_endpoint):
        """
        Set the OpenID authorization endpoint.

        :param str authorization_endpoint: OpenID authorization endpoint
        :return: self
        :rtype: OpenIDParams
        """
        self["authorizationEndpoint"] = authorization_endpoint
        return self

    def set_token_endpoint(self, token_endpoint):
        """
        Set the OpenID token endpoint.

        :param str token_endpoint: OpenID token endpoint
        :return: self
        :rtype: OpenIDParams
        """
        self["tokenEndpoint"] = token_endpoint
        return self

    def set_jwks_uri(self, jwks_uri):
        """
        Set the OpenID JWKS URI.

        :param str jwks_uri: OpenID JWKS URI
        :return: self
        :rtype: OpenIDParams
        """
        self["jwksUri"] = jwks_uri
        return self

    def set_claim_key_identifier(self, claim_key_identifier):
        """
        Set the OpenID claim key for identifier.

        :param str claim_key_identifier: OpenID claim key for identifier
        :return: self
        :rtype: OpenIDParams
        """
        self["claimKeyIdentifier"] = claim_key_identifier
        return self

    def set_claim_key_display_name(self, claim_key_display_name):
        """
        Set the OpenID claim key for display name.

        :param str claim_key_display_name: OpenID claim key for display name
        :return: self
        :rtype: OpenIDParams
        """
        self["claimKeyDisplayName"] = claim_key_display_name
        return self

    def set_claim_key_email(self, claim_key_email):
        """
        Set the OpenID claim key for email.

        :param str claim_key_email: OpenID claim key for email
        :return: self
        :rtype: OpenIDParams
        """
        self["claimKeyEmail"] = claim_key_email
        return self

    def set_enable_groups(self, enable_groups):
        """
        Set whether groups are enabled in OpenID.

        :param bool enable_groups: True to enable groups, False otherwise
        :return: self
        :rtype: OpenIDParams
        """
        self["enableGroups"] = enable_groups
        return self

    def set_claim_key_groups(self, claim_key_groups):
        """
        Set the OpenID claim key for groups.

        :param str claim_key_groups: OpenID claim key for groups
        :return: self
        :rtype: OpenIDParams
        """
        self["claimKeyGroups"] = claim_key_groups
        return self

    def set_use_global_proxy(self, use_global_proxy):
        """
        Set whether to use the global proxy in OpenID.

        :param bool use_global_proxy: True to use the global proxy, False otherwise
        :return: self
        :rtype: OpenIDParams
        """
        self["useGlobalProxy"] = use_global_proxy
        return self

    def set_use_pkce(self, use_pkce):
        """
        Set whether to use PKCE in OpenID.

        :param bool use_pkce: True to use PKCE, False otherwise
        :return: self
        :rtype: OpenIDParams
        """
        self["usePKCE"] = use_pkce
        return self

    def set_token_endpoint_auth_method(self, token_endpoint_auth_method):
        """
        Set the token endpoint authentication method.

        :param TokenEndpointAuthMethod token_endpoint_auth_method: Token endpoint authentication method
        :return: self
        :rtype: OpenIDParams
        """
        if not isinstance(token_endpoint_auth_method, TokenEndpointAuthMethod):
            raise ValueError("Invalid value for token_endpoint_auth_method. Must be one of: CLIENT_SECRET_BASIC, CLIENT_SECRET_POST")
        
        self["tokenEndpointAuthMethod"] = token_endpoint_auth_method.value
        return self

    def get_client_id(self):
        """
        Get the OpenID client ID.

        :return: OpenID client ID
        :rtype: str
        """
        return self.get("clientId")

    def get_client_secret(self):
        """
        Get the OpenID client secret.

        :return: OpenID client secret
        :rtype: str
        """
        return self.get("clientSecret")

    def get_scope(self):
        """
        Get the OpenID scope.

        :return: OpenID scope
        :rtype: str
        """
        return self.get("scope")

    def get_issuer(self):
        """
        Get the OpenID issuer.

        :return: OpenID issuer
        :rtype: str
        """
        return self.get("issuer")

    def get_authorization_endpoint(self):
        """
        Get the OpenID authorization endpoint.

        :return: OpenID authorization endpoint
        :rtype: str
        """
        return self.get("authorizationEndpoint")

    def get_token_endpoint(self):
        """
        Get the OpenID token endpoint.

        :return: OpenID token endpoint
        :rtype: str
        """
        return self.get("tokenEndpoint")

    def get_jwks_uri(self):
        """
        Get the OpenID JWKS URI.

        :return: OpenID JWKS URI
        :rtype: str
        """
        return self.get("jwksUri")

    def get_claim_key_identifier(self):
        """
        Get the OpenID claim key for identifier.

        :return: OpenID claim key for identifier
        :rtype: str
        """
        return self.get("claimKeyIdentifier")

    def get_claim_key_display_name(self):
        """
        Get the OpenID claim key for display name.

        :return: OpenID claim key for display name
        :rtype: str
        """
        return self.get("claimKeyDisplayName")

    def get_claim_key_email(self):
        """
        Get the OpenID claim key for email.

        :return: OpenID claim key for email
        :rtype: str
        """
        return self.get("claimKeyEmail")

    def get_enable_groups(self):
        """
        Get whether groups are enabled in OpenID.

        :return: True if groups are enabled, False otherwise
        :rtype: bool
        """
        return self.get("enableGroups")

    def get_claim_key_groups(self):
        """
        Get the OpenID claim key for groups.

        :return: OpenID claim key for groups
        :rtype: str
        """
        return self.get("claimKeyGroups")

    def get_use_global_proxy(self):
        """
        Get whether to use the global proxy in OpenID.

        :return: True if using the global proxy, False otherwise
        :rtype: bool
        """
        return self.get("useGlobalProxy")

    def get_use_pkce(self):
        """
        Get whether to use PKCE in OpenID.

        :return: True if using PKCE, False otherwise
        :rtype: bool
        """
        return self.get("usePKCE")

    def get_token_endpoint_auth_method(self):
        """
        Get the token endpoint authentication method.

        :return: Token endpoint authentication method
        :rtype: TokenEndpointAuthMethod
        """
        return TokenEndpointAuthMethod(self.get("tokenEndpointAuthMethod"))


class SAMLSPParams(dict):
    def __init__(self, data):
        """
        A class holding SAML Service Provider parameters for SSO settings
        Do not create this directly.

        :param dict data: Initial SAML SP parameters
        """
        super(SAMLSPParams, self).__init__(data)

    def set_sign_requests(self, sign_requests):
        """
        Set whether to sign requests in SAML.

        :param bool sign_requests: True to sign requests, False otherwise
        :return: self
        :rtype: SAMLSPParams
        """
        self["signRequests"] = sign_requests
        return self

    def set_display_name_attribute(self, display_name_attribute):
        """
        Set the display name attribute in SAML.

        :param str display_name_attribute: Display name attribute
        :return: self
        :rtype: SAMLSPParams
        """
        self["displayNameAttribute"] = display_name_attribute
        return self

    def set_email_attribute(self, email_attribute):
        """
        Set the email attribute in SAML.

        :param str email_attribute: Email attribute
        :return: self
        :rtype: SAMLSPParams
        """
        self["emailAttribute"] = email_attribute
        return self

    def set_enable_groups(self, enable_groups):
        """
        Set whether groups are enabled in SAML.

        :param bool enable_groups: True to enable groups, False otherwise
        :return: self
        :rtype: SAMLSPParams
        """
        self["enableGroups"] = enable_groups
        return self

    def set_groups_attribute(self, groups_attribute):
        """
        Set the groups attribute in SAML.

        :param str groups_attribute: Groups attribute
        :return: self
        :rtype: SAMLSPParams
        """
        self["groupsAttribute"] = groups_attribute
        return self

    def get_sign_requests(self):
        """
        Get whether to sign requests in SAML.

        :return: True if signing requests, False otherwise
        :rtype: bool
        """
        return self.get("signRequests")

    def get_display_name_attribute(self):
        """
        Get the display name attribute in SAML.

        :return: Display name attribute
        :rtype: str
        """
        return self.get("displayNameAttribute")

    def get_email_attribute(self):
        """
        Get the email attribute in SAML.

        :return: Email attribute
        :rtype: str
        """
        return self.get("emailAttribute")

    def get_enable_groups(self):
        """
        Get whether groups are enabled in SAML.

        :return: True if groups are enabled, False otherwise
        :rtype: bool
        """
        return self.get("enableGroups")

    def get_groups_attribute(self):
        """
        Get the groups attribute in SAML.

        :return: Groups attribute
        :rtype: str
        """
        return self.get("groupsAttribute")


class SPNEGOMode(Enum):
    PREAUTH_KEYTAB = "PREAUTH_KEYTAB"
    CUSTOM_LOGIN_CONF = "CUSTOM_LOGIN_CONF"


class SSOSettings:
    def __init__(self, client, path, sso_settings):
        """
        A class holding SSO settings information
        Do not create this directly.

        :param client: The client associated with the SSO settings
        :type client: Client
        :param path: The endpoints path prefix
        :param dict sso_settings: The initial SSO settings
        """
        self.client = client
        self.path = path
        self.sso_settings = sso_settings
        self.openid_params_instance = OpenIDParams(self.sso_settings.get("openIDParams", {}))
        self.saml_sp_params_instance = SAMLSPParams(self.sso_settings.get("samlSPParams", {}))

    def save(self):
        """
        Saves back the settings to the project
        """
        self.sso_settings["openIDParams"] = dict(self.openid_params_instance)
        self.sso_settings["samlSPParams"] = dict(self.saml_sp_params_instance)
        self.client._perform_empty(
            "PUT", self.path + "/iam/sso-settings", body=self.sso_settings
        )

    def set_protocol(self, protocol):
        """
        Set the SSO protocol.

        :param SSOProtocol protocol: SSO protocol
        :return: self
        :rtype: SSOSettings
        """
        if not isinstance(protocol, SSOProtocol):
            raise ValueError("Invalid value for protocol. Must be one of: SAML, SPNEGO, OPENID")
        
        self.sso_settings["protocol"] = protocol.value
        return self

    def get_protocol(self):
        """
        Get the SSO protocol.

        :return: SSO protocol
        :rtype: SSOProtocol
        """
        return SSOProtocol(self.sso_settings["protocol"])

    def set_remapping_rules(self, remapping_rules):
        """
        Set the remapping rules.

        :param list remapping_rules: List of UserRemappingRule instances
        :return: self
        :rtype: SSOSettings
        """
        # Convert UserRemappingRule instances to dictionaries
        remapping_rules_data = [{"ruleFrom": rule.rule_from, "ruleTo": rule.rule_to} for rule in remapping_rules]
        self.sso_settings["remappingRules"] = remapping_rules_data
        return self

    def get_remapping_rules(self):
        """
        Get the remapping rules.

        :return: List of UserRemappingRule instances
        :rtype: list
        """
        return [UserRemappingRule(rule["ruleFrom"], rule["ruleTo"]) for rule in self.sso_settings.get("remappingRules", [])]

    def set_saml_sp_params(self, saml_sp_params):
        """
        Set the SAML Service Provider parameters.

        :param saml_sp_params: Instance of SAMLSPParams
        :type saml_sp_params: SAMLSPParams
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["samlSPParams"] = saml_sp_params
        self.saml_sp_params_instance = SAMLSPParams(self.sso_settings.get("samlSPParams", {}))
        return self

    def get_saml_sp_params(self):
        """
        Get the SAML Service Provider parameters.

        :return: Instance of SAMLSPParams
        :rtype: SAMLSPParams
        """
        return self.saml_sp_params_instance

    def set_openid_params(self, openid_params):
        """
        Set the OpenID parameters.

        :param openid_params: Instance of OpenIDParams
        :type openid_params: OpenIDParams
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["openIDParams"] = openid_params
        self.openid_params_instance = OpenIDParams(self.sso_settings.get("openIDParams", {}))
        return self

    def get_openid_params(self):
        """
        Get the OpenID parameters.

        :return: Instance of OpenIDParams
        :rtype: OpenIDParams
        """
        return self.openid_params_instance

    def set_spnego_mode(self, spnego_mode):
        """
        Set the SPNEGO mode.

        :param SPNEGOMode spnego_mode: SPNEGO mode
        :return: self
        :rtype: SSOSettings
        """
        if not isinstance(spnego_mode, SPNEGOMode):
            raise ValueError("Invalid value for spnego_mode. Must be one of: PREAUTH_KEYTAB, CUSTOM_LOGIN_CONF")
        
        self.sso_settings["spnegoMode"] = spnego_mode.value
        return self

    def get_spnego_mode(self):
        """
        Get the SPNEGO mode.

        :return: SPNEGO mode
        :rtype: SPNEGOMode
        """
        return SPNEGOMode(self.sso_settings["spnegoMode"])

    def set_sso_enabled(self, enabled):
        """
        Set whether SSO is enabled.

        :param bool enabled: True if SSO is enabled, False otherwise
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["enabled"] = enabled
        return self

    def get_sso_enabled(self):
        """
        Get whether SSO is enabled.

        :return: True if SSO is enabled, False otherwise
        :rtype: bool
        """
        return self.sso_settings.get("enabled", False)

    def set_auto_provision_users_at_login_time(self, auto_provision):
        """
        Set whether auto-provisioning of users is enabled at login time.

        :param bool auto_provision: True to enable auto-provisioning, False otherwise
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["autoProvisionUsersAtLoginTime"] = auto_provision
        return self

    def get_auto_provision_users_at_login_time(self):
        """
        Get whether auto-provisioning of users is enabled at login time.

        :return: True if auto-provisioning is enabled, False otherwise
        :rtype: bool
        """
        return self.sso_settings.get("autoProvisionUsersAtLoginTime", False)

    def set_auto_sync_users_at_login_time(self, auto_sync):
        """
        Set whether auto-syncing of users is enabled at login time.

        :param bool auto_sync: True to enable auto-syncing, False otherwise
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["autoSyncUsersAtLoginTime"] = auto_sync
        return self

    def get_auto_sync_users_at_login_time(self):
        """
        Get whether auto-syncing of users is enabled at login time.

        :return: True if auto-syncing is enabled, False otherwise
        :rtype: bool
        """
        return self.sso_settings.get("autoSyncUsersAtLoginTime", False)

    def set_default_user_profile(self, default_profile):
        """
        Set the default user profile.

        :param str default_profile: Default user profile
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["defaultUserProfile"] = default_profile
        return self

    def get_default_user_profile(self):
        """
        Get the default user profile.

        :return: Default user profile
        :rtype: str
        """
        return self.sso_settings.get("defaultUserProfile", "")

    def set_group_profiles(self, group_profiles):
        """
        Set the group profiles.

        :param list group_profiles: List of group profiles
        :return: self
        :rtype: SSOSettings
        """
        self.sso_settings["groupProfiles"] = group_profiles
        return self

    def get_group_profiles(self):
        """
        Get the group profiles.

        :return: List of group profiles
        :rtype: list
        """
        return self.sso_settings.get("groupProfiles", [])

    def set_authorized_groups(self, authorized_groups):
        """
        Set the authorized groups.

        :param list[str] authorized_groups: Authorized groups
        :return: self
        :rtype: SSOSettings
        """
        # for retro-compatibility when authorized_group was a comma-separated list in a str
        if isinstance(authorized_groups, str):
            authorized_groups = authorized_groups.split(',')

        self.sso_settings["authorizedGroups"] = authorized_groups
        return self

    def get_authorized_groups(self):
        """
        Get the authorized groups.

        :return: Authorized groups
        :rtype: list[str]
        """
        return self.sso_settings.get("authorizedGroups", [])


class LDAPSettings:
    def __init__(self, client, path, ldap_settings):
        """
        A class holding LDAP settings information
        Do not create this directly.

        :param client: The client associated with the LDAP settings
        :type client: Client
        :param path: The endpoints path prefix
        :param dict ldap_settings: The initial LDAP settings
        """
        self.client = client
        self.path = path
        self.ldap_settings = ldap_settings

    def save(self):
        """
        Saves back the settings
        """
        self.client._perform_empty(
            "PUT", self.path + "/iam/ldap-settings", body=self.ldap_settings
        )

    def set_url(self, url):
        """
        Set the LDAP server URL.

        :param str url: The LDAP server URL
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["url"] = url
        return self

    def get_url(self):
        """
        Get the LDAP server URL.

        :return: The LDAP server URL
        :rtype: str
        """
        return self.ldap_settings.get("url", "")

    def set_use_tls(self, use_tls):
        """
        Set whether to use TLS in LDAP.

        :param bool use_tls: True to use TLS, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["useTls"] = use_tls
        return self

    def get_use_tls(self):
        """
        Get whether to use TLS in LDAP.

        :return: True if using TLS, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("useTls", False)

    def set_bind_dn(self, bind_dn):
        """
        Set the LDAP bind DN.

        :param str bind_dn: The LDAP bind DN
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["bindDN"] = bind_dn
        return self

    def get_bind_dn(self):
        """
        Get the LDAP bind DN.

        :return: The LDAP bind DN
        :rtype: str
        """
        return self.ldap_settings.get("bindDN", "")

    def set_bind_password(self, bind_password):
        """
        Set the LDAP bind password.

        :param str bind_password: The LDAP bind password
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["bindPassword"] = bind_password
        return self

    def get_bind_password(self):
        """
        Get the LDAP bind password.

        :return: The LDAP bind password
        :rtype: str
        """
        return self.ldap_settings.get("bindPassword", "")

    def set_user_filter(self, user_filter):
        """
        Set the LDAP user filter.

        :param str user_filter: LDAP user filter
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["userFilter"] = user_filter
        return self

    def get_user_filter(self):
        """
        Get the LDAP user filter.

        :return: LDAP user filter
        :rtype: str
        """
        return self.ldap_settings.get("userFilter", "")

    def set_display_name_attribute(self, display_name_attribute):
        """
        Set the LDAP display name attribute.

        :param str display_name_attribute: The LDAP display name attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["displayNameAttribute"] = display_name_attribute
        return self

    def get_display_name_attribute(self):
        """
        Get the LDAP display name attribute.

        :return: The LDAP display name attribute
        :rtype: str
        """
        return self.ldap_settings.get("displayNameAttribute", "")

    def set_email_attribute(self, email_attribute):
        """
        Set the LDAP email attribute.

        :param str email_attribute: The LDAP email attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["emailAttribute"] = email_attribute
        return self

    def get_email_attribute(self):
        """
        Get the LDAP email attribute.

        :return: The LDAP email attribute
        :rtype: str
        """
        return self.ldap_settings.get("emailAttribute", "")

    def set_enable_groups(self, enable_groups):
        """
        Set whether to enable groups in LDAP.

        :param bool enable_groups: True to enable groups, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["enableGroups"] = enable_groups
        return self

    def get_enable_groups(self):
        """
        Get whether groups are enabled in LDAP.

        :return: True if groups are enabled, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("enableGroups", False)

    def set_group_filter(self, group_filter):
        """
        Set the LDAP group filter.

        :param str group_filter: LDAP group filter
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["groupFilter"] = group_filter
        return self

    def get_group_filter(self):
        """
        Get the LDAP group filter.

        :return: LDAP group filter
        :rtype: str
        """
        return self.ldap_settings.get("groupFilter", "")

    def set_group_name_attribute(self, group_name_attribute):
        """
        Set the LDAP group name attribute.

        :param str group_name_attribute: The LDAP group name attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["groupNameAttribute"] = group_name_attribute
        return self

    def get_group_name_attribute(self):
        """
        Get the LDAP group name attribute.

        :return: The LDAP group name attribute
        :rtype: str
        """
        return self.ldap_settings.get("groupNameAttribute", "")

    def set_authorized_groups(self, authorized_groups):
        """
        Set the authorized groups in LDAP.

        :param list[str] authorized_groups: Authorized groups
        :return: self
        :rtype: LDAPSettings
        """
        # for retro-compatibility when authorized_group was a comma-separated list in a str
        if isinstance(authorized_groups, str):
            authorized_groups = authorized_groups.split(',')

        self.ldap_settings["authorizedGroups"] = authorized_groups
        return self

    def get_authorized_groups(self):
        """
        Get the authorized groups in LDAP.

        :return: Authorized groups
        :rtype: list[str]
        """
        return self.ldap_settings.get("authorizedGroups", [])

    def set_enabled(self, enabled):
        """
        Set whether LDAP is enabled.

        :param bool enabled: True if LDAP is enabled, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["enabled"] = enabled
        return self

    def get_enabled(self):
        """
        Get whether LDAP is enabled.

        :return: True if LDAP is enabled, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("enabled", False)

    def set_auto_import_users(self, auto_import_users):
        """
        Set whether to auto-import users in LDAP.

        :param bool auto_import_users: True to auto-import users, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["autoImportUsers"] = auto_import_users
        return self

    def get_auto_import_users(self):
        """
        Get whether auto-importing users is enabled in LDAP.

        :return: True if auto-importing is enabled, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("autoImportUsers", False)

    def set_auto_sync_users_at_login_time(self, auto_sync_users_at_login_time):
        """
        Set whether auto-syncing of users is enabled at login time in LDAP.

        :param bool auto_sync_users_at_login_time: True to enable auto-syncing, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["autoSyncUsersAtLoginTime"] = auto_sync_users_at_login_time
        return self

    def get_auto_sync_users_at_login_time(self):
        """
        Get whether auto-syncing of users is enabled at login time in LDAP.

        :return: True if auto-syncing is enabled, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("autoSyncUsersAtLoginTime", False)

    def set_allow_on_demand_users_sync(self, allow_on_demand_users_sync):
        """
        Set whether to allow on-demand users syncing in LDAP.

        :param bool allow_on_demand_users_sync: True to allow syncing, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["allowOnDemandUsersSync"] = allow_on_demand_users_sync
        return self

    def get_allow_on_demand_users_sync(self):
        """
        Get whether on-demand users syncing is allowed in LDAP.

        :return: True if syncing is allowed, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("allowOnDemandUsersSync", False)

    def set_default_user_profile(self, default_user_profile):
        """
        Set the default user profile in LDAP.

        :param str default_user_profile: Default user profile
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["defaultUserProfile"] = default_user_profile
        return self

    def get_default_user_profile(self):
        """
        Get the default user profile in LDAP.

        :return: Default user profile
        :rtype: str
        """
        return self.ldap_settings.get("defaultUserProfile", "")

    def set_group_profiles(self, group_profiles):
        """
        Set the group profiles in LDAP.

        :param list group_profiles: List of group profiles
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["groupProfiles"] = group_profiles
        return self

    def get_group_profiles(self):
        """
        Get the group profiles in LDAP.

        :return: List of group profiles
        :rtype: list
        """
        return self.ldap_settings.get("groupProfiles", [])

    def set_authentication_enabled(self, authentication_enabled):
        """
        Set whether authentication is enabled in LDAP.

        :param bool authentication_enabled: True if authentication is enabled, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["authenticationEnabled"] = authentication_enabled
        return self

    def get_authentication_enabled(self):
        """
        Get whether authentication is enabled in LDAP.

        :return: True if authentication is enabled, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("authenticationEnabled", False)

    def set_all_groups_filter(self, all_groups_filter):
        """
        Set the LDAP filter for retrieving all groups.

        :param str all_groups_filter: The LDAP filter for all groups
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["allGroupsFilter"] = all_groups_filter
        return self

    def get_all_groups_filter(self):
        """
        Get the LDAP filter for retrieving all groups.

        :return: The LDAP filter for all groups
        :rtype: str
        """
        return self.ldap_settings.get("allGroupsFilter", "")

    def set_all_users_filter(self, all_users_filter):
        """
        Set the LDAP filter for retrieving all users.

        :param str all_users_filter: The LDAP filter for all users
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["allUsersFilter"] = all_users_filter
        return self

    def get_all_users_filter(self):
        """
        Get the LDAP filter for retrieving all users.

        :return: The LDAP filter for all users
        :rtype: str
        """
        return self.ldap_settings.get("allUsersFilter", "")

    def set_username_attribute(self, username_attribute):
        """
        Set the LDAP username attribute.

        :param str username_attribute: The LDAP username attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["usernameAttribute"] = username_attribute
        return self

    def get_username_attribute(self):
        """
        Get the LDAP username attribute.

        :return: The LDAP username attribute
        :rtype: str
        """
        return self.ldap_settings.get("usernameAttribute", "")

    def set_group_membership_attribute(self, group_membership_attribute):
        """
        Set the LDAP group membership attribute.

        :param str group_membership_attribute: The LDAP group membership attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["groupMembershipAttribute"] = group_membership_attribute
        return self

    def get_group_membership_attribute(self):
        """
        Get the LDAP group membership attribute.

        :return: The LDAP group membership attribute
        :rtype: str
        """
        return self.ldap_settings.get("groupMembershipAttribute", "")

    def set_allow_on_demand_users_provisioning(self, allow_on_demand_users_provisioning):
        """
        Set whether on-demand users provisioning is allowed in LDAP.

        :param bool allow_on_demand_users_provisioning: True to allow provisioning, False otherwise
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["allowOnDemandUsersProvisioning"] = allow_on_demand_users_provisioning
        return self

    def get_allow_on_demand_users_provisioning(self):
        """
        Get whether on-demand users provisioning is allowed in LDAP.

        :return: True if provisioning is allowed, False otherwise
        :rtype: bool
        """
        return self.ldap_settings.get("allowOnDemandUsersProvisioning", False)

    def set_group_membership_user_attribute(self, group_membership_user_attribute):
        """
        Set the LDAP group membership user attribute.

        :param str group_membership_user_attribute: The LDAP group membership user attribute
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["groupMembershipUserAttribute"] = group_membership_user_attribute
        return self

    def get_group_membership_user_attribute(self):
        """
        Get the LDAP group membership user attribute.

        :return: The LDAP group membership user attribute
        :rtype: str
        """
        return self.ldap_settings.get("groupMembershipUserAttribute", "")

    def set_remapping_rules(self, remapping_rules):
        """
        Set the remapping rules in LDAP.

        :param list remapping_rules: List of remapping rules
        :return: self
        :rtype: LDAPSettings
        """
        self.ldap_settings["remappingRules"] = remapping_rules
        return self

    def get_remapping_rules(self):
        """
        Get the remapping rules in LDAP.

        :return: List of remapping rules
        :rtype: list
        """
        return self.ldap_settings.get("remappingRules", [])


class AzureADSettings:
    def __init__(self, client, path, azuread_settings):
        """
        A class holding Azure AD settings information
        Do not create this directly.

        :param client: The client associated with the Azure AD settings
        :type client: Client
        :param path: The endpoints path prefix
        :param dict azuread_settings: The initial Azure AD settings
        """
        self.client = client
        self.path = path
        self.azuread_settings = azuread_settings

    def save(self):
        """
        Saves back the settings
        """
        self.client._perform_empty(
            "PUT", self.path + "/iam/azure-ad-settings", body=self.azuread_settings
        )

    def set_use_global_proxy(self, use_global_proxy):
        """
        Set whether to use a global proxy for Azure AD.

        :param bool use_global_proxy: True to use a global proxy, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["useGlobalProxy"] = use_global_proxy
        return self

    def get_use_global_proxy(self):
        """
        Get whether to use a global proxy for Azure AD.

        :return: True if using a global proxy, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("useGlobalProxy", False)

    def set_credential_method(self, credential_method):
        """
        Set the credential method for Azure AD.

        :param str credential_method: The credential method (possible values: "OAUTH2_SECRET" or "OAUTH2_CERT")
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["credentialMethod"] = credential_method
        return self

    def get_credential_method(self):
        """
        Get the credential method for Azure AD.

        :return: The credential method
        :rtype: str
        """
        return self.azuread_settings.get("credentialMethod", "")

    def set_credentials_client_id(self, credentials_client_id):
        """
        Set the client ID for Azure AD credentials.

        :param str credentials_client_id: The client ID
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["credentialsClientId"] = credentials_client_id
        return self

    def get_credentials_client_id(self):
        """
        Get the client ID for Azure AD credentials.

        :return: The client ID
        :rtype: str
        """
        return self.azuread_settings.get("credentialsClientId", "")

    def set_credentials_client_secret(self, credentials_client_secret):
        """
        Set the client secret for Azure AD credentials.

        :param str credentials_client_secret: The client secret
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["credentialsClientSecret"] = credentials_client_secret
        return self

    def get_credentials_client_secret(self):
        """
        Get the client secret for Azure AD credentials.

        :return: The client secret
        :rtype: str
        """
        return self.azuread_settings.get("credentialsClientSecret", "")

    def set_credentials_tenant_id(self, credentials_tenant_id):
        """
        Set the tenant ID for Azure AD credentials.

        :param str credentials_tenant_id: The tenant ID
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["credentialsTenantId"] = credentials_tenant_id
        return self

    def get_credentials_tenant_id(self):
        """
        Get the tenant ID for Azure AD credentials.

        :return: The tenant ID
        :rtype: str
        """
        return self.azuread_settings.get("credentialsTenantId", "")

    def set_user_query_filter(self, user_query_filter):
        """
        Set the user query filter for Azure AD.

        :param str user_query_filter: The user query filter
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["userQueryFilter"] = user_query_filter
        return self

    def get_user_query_filter(self):
        """
        Get the user query filter for Azure AD.

        :return: The user query filter
        :rtype: str
        """
        return self.azuread_settings.get("userQueryFilter", "")

    def set_group_query_filter(self, group_query_filter):
        """
        Set the group query filter for Azure AD.

        :param str group_query_filter: The group query filter
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["groupQueryFilter"] = group_query_filter
        return self

    def get_group_query_filter(self):
        """
        Get the group query filter for Azure AD.

        :return: The group query filter
        :rtype: str
        """
        return self.azuread_settings.get("groupQueryFilter", "")

    def set_groups_limit(self, groups_limit):
        """
        Set the limit for the number of groups in Azure AD.

        :param int groups_limit: The groups limit
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["groupsLimit"] = groups_limit
        return self

    def get_groups_limit(self):
        """
        Get the limit for the number of groups in Azure AD.

        :return: The groups limit
        :rtype: int
        """
        return self.azuread_settings.get("groupsLimit", 0)

    def set_enabled(self, enabled):
        """
        Set whether Azure AD integration is enabled.

        :param bool enabled: True if Azure AD integration is enabled, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["enabled"] = enabled
        return self

    def get_enabled(self):
        """
        Get whether Azure AD integration is enabled.

        :return: True if Azure AD integration is enabled, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("enabled", False)

    def set_auto_provision_users_at_login_time(self, auto_provision_users_at_login_time):
        """
        Set whether auto-provisioning of users is enabled at login time in Azure AD.

        :param bool auto_provision_users_at_login_time: True to enable auto-provisioning, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["autoProvisionUsersAtLoginTime"] = auto_provision_users_at_login_time
        return self

    def get_auto_provision_users_at_login_time(self):
        """
        Get whether auto-provisioning of users is enabled at login time in Azure AD.

        :return: True if auto-provisioning is enabled, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("autoProvisionUsersAtLoginTime", False)

    def set_auto_sync_users_at_login_time(self, auto_sync_users_at_login_time):
        """
        Set whether auto-syncing of users is enabled at login time in Azure AD.

        :param bool auto_sync_users_at_login_time: True to enable auto-syncing, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["autoSyncUsersAtLoginTime"] = auto_sync_users_at_login_time
        return self

    def get_auto_sync_users_at_login_time(self):
        """
        Get whether auto-syncing of users is enabled at login time in Azure AD.

        :return: True if auto-syncing is enabled, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("autoSyncUsersAtLoginTime", False)

    def set_allow_on_demand_users_sync(self, allow_on_demand_users_sync):
        """
        Set whether to allow on-demand users syncing in Azure AD.

        :param bool allow_on_demand_users_sync: True to allow syncing, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["allowOnDemandUsersSync"] = allow_on_demand_users_sync
        return self

    def get_allow_on_demand_users_sync(self):
        """
        Get whether on-demand users syncing is allowed in Azure AD.

        :return: True if syncing is allowed, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("allowOnDemandUsersSync", False)

    def set_default_user_profile(self, default_user_profile):
        """
        Set the default user profile in Azure AD.

        :param str default_user_profile: Default user profile
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["defaultUserProfile"] = default_user_profile
        return self

    def get_default_user_profile(self):
        """
        Get the default user profile in Azure AD.

        :return: Default user profile
        :rtype: str
        """
        return self.azuread_settings.get("defaultUserProfile", "")

    def set_group_profiles(self, group_profiles):
        """
        Set the group profiles in Azure AD.

        :param list group_profiles: List of group profiles
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["groupProfiles"] = group_profiles
        return self

    def get_group_profiles(self):
        """
        Get the group profiles in Azure AD.

        :return: List of group profiles
        :rtype: list
        """
        return self.azuread_settings.get("groupProfiles", [])

    def set_authorized_groups(self, authorized_groups):
        """
        Set the authorized groups in Azure AD.

        :param list[str] authorized_groups: Authorized groups
        :return: self
        :rtype: AzureADSettings
        """
        # for retro-compatibility when authorized_group was a comma-separated list in a str
        if isinstance(authorized_groups, str):
            authorized_groups = authorized_groups.split(',')

        self.azuread_settings["authorizedGroups"] = authorized_groups
        return self

    def get_authorized_groups(self):
        """
        Get the authorized groups in Azure AD.

        :return: Authorized groups
        :rtype: list[str]
        """
        return self.azuread_settings.get("authorizedGroups", [])

    def set_allow_on_demand_users_provisioning(self, allow_on_demand_users_provisioning):
        """
        Set whether to allow on-demand users provisioning in Azure AD.

        :param bool allow_on_demand_users_provisioning: True to allow provisioning, False otherwise
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["allowOnDemandUsersProvisioning"] = allow_on_demand_users_provisioning
        return self

    def get_allow_on_demand_users_provisioning(self):
        """
        Get whether on-demand users provisioning is allowed in Azure AD.

        :return: True if provisioning is allowed, False otherwise
        :rtype: bool
        """
        return self.azuread_settings.get("allowOnDemandUsersProvisioning", False)

    def set_login_attribute_ref(self, login_attribute_ref):
        """
        Set the login attribute reference in Azure AD.

        :param str login_attribute_ref: The login attribute reference
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["loginAttributeRef"] = login_attribute_ref
        return self

    def get_login_attribute_ref(self):
        """
        Get the login attribute reference in Azure AD.

        :return: The login attribute reference
        :rtype: str
        """
        return self.azuread_settings.get("loginAttributeRef", "")

    def set_remapping_rules(self, remapping_rules):
        """
        Set the remapping rules in Azure AD.

        :param list remapping_rules: List of remapping rules
        :return: self
        :rtype: AzureADSettings
        """
        self.azuread_settings["remappingRules"] = remapping_rules
        return self

    def get_remapping_rules(self):
        """
        Get the remapping rules in Azure AD.

        :return: List of remapping rules
        :rtype: list
        """
        return self.azuread_settings.get("remappingRules", [])


class FMSSOSettings(SSOSettings):
    def __init__(self, client, sso_settings):
        """
        A class holding FM SSO settings information, inheriting from SSOSettings
        Do not create this directly.

        :param client: The client associated with the FM SSO settings
        :type client: Client
        :param dict sso_settings: The initial FM SSO settings
        """
        # Call the constructor of the parent class (SSOSettings)
        path = "/tenants/%s" % str(client.get_tenant_id())
        super().__init__(client, path, sso_settings)


class DSSSSOSettings(SSOSettings):
    def __init__(self, client, sso_settings):
        """
        A class holding DSS SSO settings information, inheriting from SSOSettings
        Do not create this directly.

        :param client: The client associated with the DSS SSO settings
        :type client: Client
        :param dict sso_settings: The initial DSS SSO settings
        """
        # Call the constructor of the parent class (SSOSettings)
        super().__init__(client, "/admin/", sso_settings)


class FMLDAPSettings(LDAPSettings):
    def __init__(self, client, ldap_settings):
        """
        A class holding FM LDAP settings information, inheriting from LDAPSettings
        Do not create this directly.

        :param client: The client associated with the FM LDAP settings
        :type client: Client
        :param dict ldap_settings: The initial FM LDAP settings
        """
        # Call the constructor of the parent class (LDAPSettings)
        path = "/tenants/%s" % str(client.get_tenant_id())
        super().__init__(client, path, ldap_settings)


class DSSLDAPSettings(LDAPSettings):
    def __init__(self, client, ldap_settings):
        """
        A class holding DSS LDAP settings information, inheriting from LDAPSettings
        Do not create this directly.

        :param client: The client associated with the DSS LDAP settings
        :type client: Client
        :param dict ldap_settings: The initial DSS LDAP settings
        """
        # Call the constructor of the parent class (LDAPSettings)
        super().__init__(client, "/admin/", ldap_settings)


class FMAzureADSettings(AzureADSettings):
    def __init__(self, client, azure_ad_settings):
        """
        A class holding FM Azure AD settings information, inheriting from AzureADSettings
        Do not create this directly.

        :param client: The client associated with the FM Azure AD settings
        :type client: Client
        :param dict azure_ad_settings: The initial FM Azure AD settings
        """
        # Call the constructor of the parent class (AzureADSettings)
        path = "/tenants/%s" % str(client.get_tenant_id())
        super().__init__(client, path, azure_ad_settings)


class DSSAzureADSettings(AzureADSettings):
    def __init__(self, client, azure_ad_settings):
        """
        A class holding DSS Azure AD settings information, inheriting from AzureADSettings
        Do not create this directly.

        :param client: The client associated with the DSS Azure AD settings
        :type client: Client
        :param dict azure_ad_settings: The initial DSS Azure AD settings
        """
        # Call the constructor of the parent class (AzureADSettings)
        super().__init__(client, "/admin/", azure_ad_settings)