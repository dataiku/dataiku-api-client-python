class FMVirtualNetwork(object):
    def __init__(self, client, virtual_network_settings):
        self.client  = client
        self.settings = virtual_network_settings
        self.id = self.settings['id']
