from os import path as osp

class APINodeService(object):
    """
    A handle to interact with the settings of an API node service
    """
    def __init__(self, client, service_id):
       self.client = client
       self.service_id = service_id

    def delete(self):
        """Deletes the API node service"""
        self.client._perform_empty("DELETE",
                "services/%s" % self.service_id)

    ########################################################
    # On-disk generations management
    ########################################################

    def list_generations(self):
        return self.client._perform_json("GET",
            "services/%s/generations" % self.service_id)["generations"]

    def import_generation_from_archive(self, file_path):
        self.client._perform_empty("POST",
            "services/%s/generations/actions/importFromArchive" % (self.service_id),
            params = { "filePath" : osp.abspath(file_path) })

    def preload_generation(self, generation):
        self.client._perform_empty("POST",
            "services/%s/generations/%s/preload" % (self.service_id, generation))

    ########################################################
    # Switch / mapping management
    ########################################################

    def disable(self):
        """Disable the service."""
        self.client._perform_empty("POST",
            "services/%s/actions/disable" % self.service_id)

    def enable(self):
        self.client._perform_empty("POST",
            "services/%s/actions/enable" % self.service_id)

    def set_generations_mapping(self, mapping):
        """Setting a generations mapping automatically enables
        the service"""
        self.client._perform_empty("POST",
            "services/%s/actions/setMapping" % self.service_id, body = mapping)

    def switch_to_newest(self):
        return self.client._perform_json("POST",
            "services/%s/actions/switchToNewest" % self.service_id)

    def switch_to_single_generation(self, generation):
        self.client._perform_empty("POST",
            "services/%s/actions/switchTo/%s" % (self.service_id, generation))
