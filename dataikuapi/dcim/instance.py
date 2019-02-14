import sys
import os.path as osp
from dataikuapi.dss.future import DSSFuture
from dataikuapi.utils import DataikuException

class DCIMLogicalInstanceSettings(object):
    def __init__(self, client, li_id, settings):
        self.client = client
        self.li_id = li_id
        self.settings = settings

    def get_raw(self):
        return self.settings

    def save(self):
        self.client._perform_json("POST", "/instances/%s", body = self.settings)

class DCIMPhysicalInstanceStatus(object):
    def __init__(self, client, li_id, status):
        self.client = client
        self.li_id = li_id
        self.status = status

    def get_raw(self):
        return self.status

class DCIMLogicalInstance(object):
    """
    """
    def __init__(self, client, li_id):
       self.client = client
       self.li_id = li_id

    def get_settings(self):
        settings = self.client._perform_empty("GET", "/instances/%s" % self.li_id)
        return DCIMLogicalInstanceSettings(self.client, self.li_id, settings)

    def start_reprovision(self):
        fr = self.client._perform_empty("POST", "/instances/%s/actions/reprovision" % self.li_id)
        return self.client.get_future(fr["jobId"])

    def get_status(self):
        status = self.client._perform_empty("GET", "/instances/%s/status" % self.li_id)
        return DCIMPhysicalInstanceStatus(self.client, self.li_id, settings)
