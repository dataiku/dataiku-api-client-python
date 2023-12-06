from dataikuapi.dss.dataset import DSSDataset


class DSSFeatureGroupListItem(object):
    """
    An item in a list of feature groups.

    .. important::
        Do not instantiate this class, use :meth:'dataikuapi.dss.feature_store.DSSFeatureStore.list_feature_groups'
    """
    def __init__(self, client, project_key, name):
        self.client = client
        self.project_key = project_key
        self.name = name

    @property
    def id(self):
        """
        Get the identifier of the feature group.

        :rtype: string
        """
        return self.project_key + "." + self.name

    def get_as_dataset(self):
        """
        Get the feature group as a dataset.

        :returns: a handle on the dataset
        :rtype: :class:`dataikuapi.dss.dataset.DSSDataset`
        """
        return DSSDataset(self.client, self.project_key, self.name)


class DSSFeatureStore(object):
    """
    A handle on the Feature Store.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.DSSClient.get_feature_store`
    """

    def __init__(self, client):
        self.client = client

    def list_feature_groups(self):
        """
        List the feature groups on which the user has at least read permissions.

        :returns: the list of feature groups, each one as a :class:`dataikuapi.dss.feature_store.DSSFeatureGroupListItem`
        :rtype: list of :class:`dataikuapi.dss.feature_store.DSSFeatureGroupListItem`
        """
        items = self.client._perform_json("GET", "/feature-store/feature-groups")
        return [DSSFeatureGroupListItem(self.client, item["projectKey"], item["name"]) for item in items]
