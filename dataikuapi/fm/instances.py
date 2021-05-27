from enum import Enum

class FMInstance(object):
    def __init__(self, client):
        self.client  = client

class FMInstanceEncryptionMode(Enum):
    NONE = "NONE"
    DEFAULT_KEY = "DEFAULT_KEY"
    TENANT = "TENANT"
    CUSTOM = "CUSTOM"
