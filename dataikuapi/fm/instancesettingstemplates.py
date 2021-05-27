class FMInstanceSettingsTemplate(object):
    def __init__(self, client, ist_data):
        self.client  = client
        self.id = ist_data['id']
        self.ist_data = ist_data

