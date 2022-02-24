class DSSFeatureStore(object):
    def __init__(self, client):
        """
        A handle on the Feature Store. Do not call this methid directly, call """
        self.client = client

    def list_feature_groups(self):
        """
        Get a list of names of datasets defined as feature groups on the DSS instance.

        :return: list of names of datasets defined as feature groups
        :rtype: list of str
        """
        return self.client._perform_json("GET", "/feature-store/feature-groups/list")
