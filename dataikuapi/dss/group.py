
class DSSGroup(object):

    def __init__(self, client, name):
        self.client = client
        self.name = name
    
    ########################################################
    # Group deletion
    ########################################################
    
    def delete(self):
        """
        Delete the group
        """
        return self.client._perform_empty(
            "DELETE", "/admin/groups/%s" % self.name)
    
        
    ########################################################
    # User description
    ########################################################
    
    def get(self):
        """
        Get infos on the group
        """
        return self.client._perform_json(
            "GET", "/admin/groups/%s" % self.name)
    
    def set(self, description):
        """
        Set infos on the group
        """
        return self.client._perform_json(
            "PUT", "/admin/groups/%s" % self.name,
            body = description)
    
        