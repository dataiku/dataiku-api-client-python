
class DSSEnterpriseAssetLibrary(object):
    """
     Handle to interact with the Enterprise Asset Library on the DSS instance.

     .. important::
        Do not create this class directly, use :meth:`dataikuapi.DSSClient.get_enterprise_asset_library`
    """
    def __init__(self, client):
        self.client = client

    def list_collections(self):
        """
        Lists the collections you have read access to in the Enterprise Asset Library as dict.
        Each dict contains at least a field "id" indicating the identifier of this collection and "name"

        :returns: a list of dict
        :rtype: list[dict]
        """
        return self.client._perform_json("GET", "/enterprise-asset-library/collections")

    def list_prompts(self, restrict_collections=None):
        """
        Lists the prompts in the collections you have read access to

        :param (optional) list[string] restrict_collections: collection ids you want to get the prompts from

        :returns: the list of prompts in the collections you have access to
        :rtype: list[dict]
        """
        if restrict_collections is None:
            restrict_collections = []
        return self.client._perform_json("GET", "/enterprise-asset-library/prompts", {"restrictCollections": restrict_collections})
