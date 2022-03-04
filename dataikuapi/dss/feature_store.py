class DSSFeatureStore(object):
    def __init__(self, client):
        """
        A handle on the Feature Store.
        Do not create this class directly, use :meth:`DSSClient.get_feature_store`
        """
        self.client = client

    def list_feature_groups(self):
        """
        Get a list of names of datasets on which the user has right permissions
        and that are defined as feature groups in the DSS instance

        :return: list of dataset names
        :rtype: list of str
        """
        return self.client._perform_json("GET", "/feature-store/feature-groups/list")
