
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
    
        