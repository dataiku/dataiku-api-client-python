
class APINodeAuth(object):
    """
    A handle to interact with authentication settings on API node
    """
    def __init__(self, client):
       self.client = client

    def list_keys(self):
        """Lists the Admin API keys"""
        return self.client._perform_json("GET", "keys")

    def add_key(self, label=None, description=None, created_by=None):
        """Add an Admin API key. Returns the key details"""
        key = {
            "label" : label,
            "description" : description,
            "createdBy" : created_by
        }
        return self.client._perform_json("POST", "keys", body=key)

    def delete_key(self, key):
        self.client._perform_empty("DELETE", "keys/%s" % key)