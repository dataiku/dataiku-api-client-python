from dataikuapi.dss.dataset import DSSDataset


class DSSFeatureGroupListItem(object):
    def __init__(self, client, project_key, name):
        self.client = client
        self.project_key = project_key
        self.name = name

    @property
    def id(self):
        return self.project_key + "." + self.name

    def get_as_dataset(self):
        """
        :return: a handle on the dataset
        :rtype: :class:`dataikuapi.dss.dataset.DSSDataset`
        """
        return DSSDataset(self.client, self.project_key, self.name)


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
        :rtype: list of :class:`dataikuapi.feature_store.DSSFeatureGroupListItem`
        """
        items = self.client._perform_json("GET", "/feature-store/feature-groups")
        return [DSSFeatureGroupListItem(self.client, item["projectKey"], item["name"]) for item in items]
