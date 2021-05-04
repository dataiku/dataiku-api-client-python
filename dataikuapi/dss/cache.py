class DSSCache(object):
    def __init__(self, client, project):
        self.client = client
        self.project = project

    def get_entry(self, key):
        """
        Gets the cache entry if it exists
        Returns the value or raises an exception if entry does not exists
        """
        resp = self.client._perform_raw("GET", "/projects/%s/cache/%s" % (self.project.project_key, key))
        if resp.status_code == 200:
            # cache hit
            return resp.json()
        elif resp.status_code == 204:
            # cache miss
            return None
        raise Exception("WTF")

    def set_entry(self, key, value, ttl=0):
        """
        Sets the cache entry with an optional ttl (defaults to infinite)
        """
        if ttl > 0:
            self.client._perform_raw("POST", "/projects/%s/cache/%s?ttl=%s" % (self.project.project_key, key, ttl),
                                      body={value})
        else:
            self.client._perform_raw("POST", "/projects/%s/cache/%s" % (self.project.project_key, key),
                                      body={value})

    def delete_entry(self, key):
        """
        Deletes the entry
        """
        self.client._perform_raw("DELETE", "/projects/%s/cache/%s" % (self.project.project_key, key))
