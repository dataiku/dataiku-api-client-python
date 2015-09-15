
class DSSConnection(object):

    def __init__(self, client, name):
        self.client = client
        self.name = name
    
    ########################################################
    # User deletion
    ########################################################
    
    def delete(self):
        """
        Delete the user
        """
        return self.client._perform_empty(
            "DELETE", "/admin/connections/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get infos on the user
        """
        return self.client._perform_json(
            "GET", "/admin/connections/%s" % self.name)
    
    def set_definition(self, description):
        """
        Set infos on the user
        """
        return self.client._perform_json(
            "PUT", "/admin/connections/%s" % self.name,
            body = description)
    
        