
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
    
        