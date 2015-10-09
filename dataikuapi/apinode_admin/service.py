
class APINodeService(object):
    """
    A handle to interact with the settings of an API node service
    """
    def __init__(self, client, service_id):
       self.client = client
       self.service_id = service_id

    def set_generations_mapping(self, mapping):
        self.client._perform_empty("POST",
            "services/%s/actions/setMapping" % self.service_id, body = mapping)

    def switch_to_newest(self):
        self.client._perform_empty("POST",
            "services/%s/actions/switchToNewest" % self.service_id)


    def preload_generation(self, generation):
        self.client._perform_empty("POST",
            "services/%s/generations/%s/preload" % (self.service_id, generation))