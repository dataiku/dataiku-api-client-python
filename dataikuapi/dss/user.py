
class DSSUser(object):

    def __init__(self, client, login):
        self.client = client
        self.login = login
    
    ########################################################
    # User deletion
    ########################################################
    
    def delete(self):
        """
        Delete the user
        """
        return self.client._perform_empty(
            "DELETE", "/admin/users/%s" % self.login)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get_definition(self):
        """
        Get infos on the user
        """
        return self.client._perform_json(
            "GET", "/admin/users/%s" % self.login)
    
    def set_definition(self, description):
        """
        Set infos on the user
        """
        return self.client._perform_json(
            "PUT", "/admin/users/%s" % self.login,
            body = description)
    
        