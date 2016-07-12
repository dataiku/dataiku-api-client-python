
class DSSConnection(object):
    """
    A connection on the DSS instance
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name
    
    ########################################################
    # User deletion
    ########################################################
    
    def delete(self):
        """
        Delete the connection

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/connections/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get the connection's definition (type, name, params, usage restrictions)

        Note: this call requires an API key with admin rights
        
        Returns:
            the connection definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/admin/connections/%s" % self.name)
    
    def set_definition(self, description):
        """
        Set the connection's definition.
        
        Note: this call requires an API key with admin rights
        
        Args:
            definition: the definition for the connection, as a JSON object.            
        """
        return self.client._perform_json(
            "PUT", "/admin/connections/%s" % self.name,
            body = description)
    
        
class DSSUser(object):
    """
    A handle for a user on the DSS instance
    """
    def __init__(self, client, login):
        self.client = client
        self.login = login

    ########################################################
    # User deletion
    ########################################################

    def delete(self):
        """
        Deletes the user

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)

    ########################################################
    # User description
    ########################################################

    def get_definition(self):
        """
        Get the user's definition (login, type, display name, permissions, ...)

        Note: this call requires an API key with admin rights

        :return: the user's definition, as a dict
        """
        return self.client._perform_json(
            "GET", "/admin/users/%s" % self.login)

    def set_definition(self, definition):
        """
        Set the user's definition.

        Note: this call requires an API key with admin rights

        :param dict definition: the definition for the user, as a dict. You should
            obtain the definition using get_definition, not create one.
            The fields that can be changed are:
                * email
                * displayName
                * groups
                * userProfile
                * password
        """
        return self.client._perform_json(
            "PUT", "/admin/users/%s" % self.login,
            body = definition)
class DSSGroup(object):
    """
    A group on the DSS instance
    """
    def __init__(self, client, name):
        self.client = client
        self.name = name
    
    ########################################################
    # Group deletion
    ########################################################
    
    def delete(self):
        """
        Delete the group

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/groups/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get the group's definition (name, description, admin abilities, type, ldap name mapping)

        Note: this call requires an API key with admin rights
        
        Returns:
            the group definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)
    
    def set_definition(self, definition):
        """
        Set the group's definition.
        
        Note: this call requires an API key with admin rights
        
        Args:
            definition: the definition for the group, as a JSON object.                        
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body = definition)
    
        