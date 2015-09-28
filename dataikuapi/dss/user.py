
class DSSUser(object):
    """
    A user on the DSS instance
    """
    def __init__(self, client, login):
        self.client = client
        self.login = login
    
    ########################################################
    # User deletion
    ########################################################
    
    def delete(self):
        """
        Delete the user

        Note: this call requires an API key with admin rights
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get the user's definition (login, type, display name, permissions)

        Note: this call requires an API key with admin rights
        
        Returns:
            the user definition, as a JSON object
        """
        return self.client._perform_json(
            "GET", "/admin/users/%s" % self.login)
    
    def set_definition(self, definition):
        """
        Set the user's definition.
        
        Note: this call requires an API key with admin rights
        
        Args:
            definition: the definition for the user, as a JSON object. The fields that can be changed are
                        'sourceType', 'email', 'displayName', 'groups', 'codeAllowed' and 'password'                        
        """
        return self.client._perform_json(
            "PUT", "/admin/users/%s" % self.login,
            body = definition)
    
        