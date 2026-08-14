from .future import DSSFuture

ENTERPRISE_ASSET_LIBRARY_PROMPTS_URI_FORMAT = "/enterprise-asset-library/collections/%s/prompts"
ENTERPRISE_ASSET_LIBRARY_PROMPT_URI_FORMAT = ENTERPRISE_ASSET_LIBRARY_PROMPTS_URI_FORMAT + "/%s"

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

    def get_collection(self, collection_id):
        """
        Get a handle to interact with a specific Enterprise Asset Collection

        :param str collection_id: the id of the Enterprise Asset Collection to fetch
        :rtype: :class:`dataikuapi.dss.enterprise_asset_library.DSSEnterpriseAssetCollection`
        """
        return DSSEnterpriseAssetCollection(self.client, collection_id)

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

    def get_export_stream(self):
        """
        Export the Enterprise Asset Library collections that the caller can export.

        .. warning::

            You are responsible for closing the returned stream.

        :returns: a stream of the export archive
        :rtype: file-like object
        """
        return self.client._perform_raw("POST", "/enterprise-asset-library/export").raw

    def export_collections_to_file(self, path):
        """
        Export the Enterprise Asset Library collections to a file.

        :param str path: the path of the file in which the exported archive should be saved
        """
        with open(path, 'wb') as f:
            with self.client._perform_raw("POST", "/enterprise-asset-library/export") as export_stream:
                for chunk in export_stream.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
                f.flush()

    def import_collections(self, fp, conflict_resolution_strategy="MERGE"):
        """
        Import Enterprise Asset Library collections from an archive.

        :param object fp: A file-like object pointing to an Enterprise Asset Library archive zip
        :param str conflict_resolution_strategy: how to handle existing conflicting collection ids.
            A conflict occurs when the archive contains a collection whose id already exists on the
            target DSS instance:

            - ``ABORT``: if a conflict is found, the import is cancelled.
            - ``MERGE``: when a collection conflicts, new assets are added and existing assets with
              the same id are overwritten in the target collection.
            - ``OVERWRITE``: conflicting collections are overwritten.

              .. warning::

                 With ``OVERWRITE``, assets present in the target collection but absent from the
                 imported archive are removed.

            - ``SKIP``: conflicting collections are skipped.

            Defaults to ``MERGE`` if not provided.
        :return: a future representing the import process
        :rtype: :class:`dataikuapi.dss.future.DSSFuture`
        """
        resp = self.client._perform_json("POST", "/enterprise-asset-library/import",
                                         params={"conflictResolutionStrategy": conflict_resolution_strategy},
                                         files={"file": fp})
        return DSSFuture.from_resp(self.client, resp["future"])


class DSSEnterpriseAssetCollection:
    """
    A handle to interact with an Enterprise Asset Collection on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.dss.enterprise_asset_library.DSSEnterpriseAssetLibrary.get_collection`
    """

    def __init__(self, client, collection_id):
        self.client = client
        self.id = collection_id

    def get_prompt(self, prompt_id):
        """
        Get a prompt from the Enterprise Asset Collection.

        :param prompt_id: id of the Enterprise Prompt
        :type prompt_id: str

        :return: the Enterprise Prompt
        :rtype: :class:`dataikuapi.dss.enterprise_asset_library.EnterpriseAssetLibraryPrompt`
        """
        return EnterpriseAssetLibraryPrompt(self, self.client._perform_json("GET", ENTERPRISE_ASSET_LIBRARY_PROMPT_URI_FORMAT % (self.id, prompt_id)))

    def create_prompt(self, name=None, description=None, content=None, tags=None, prompt=None):
        """
        Add a prompt to this Enterprise Asset Collection.
        This call requires at least contributor rights on the Enterprise Asset Collection.

        :param str name: name of the prompt to create
        :param str description: description of the prompt to create
        :param str content: content of the prompt to create
        :param list[string] tags: tags of the prompt to create
        :param prompt: prompt to add to the Enterprise Asset Collection.
                       If not provided, a prompt is built from ``name``, ``description``,
                       ``content`` and ``tags`` parameters. If both are provided, keyword arguments
                       override values from ``prompt``.
        :type prompt: :class:`dict`

        :return: the newly created Enterprise Prompt
        :rtype: :class:`dataikuapi.dss.enterprise_asset_library.EnterpriseAssetLibraryPrompt`
        """
        if prompt is None:
            prompt = {}
        if name is not None:
            prompt["name"] = name
        if description is not None:
            prompt["description"] = description
        if content is not None:
            prompt["content"] = content
        if tags is not None:
            prompt["tags"] = tags

        if "name" not in prompt:
            raise ValueError("name is required to create a prompt")
        if "content" not in prompt:
            raise ValueError("content is required to create a prompt")

        prompt_id = self.client._perform_json("POST", ENTERPRISE_ASSET_LIBRARY_PROMPTS_URI_FORMAT % self.id, body=prompt)["id"]
        return self.get_prompt(prompt_id)


class EnterpriseAssetLibraryPrompt(object):
    """
    A handle to interact with an Enterprise Prompt on the DSS instance.

    Do not create this class directly, instead use :meth:`dataikuapi.dss.enterprise_asset_library.DSSEnterpriseAssetCollection.create_prompt` or
    :meth:`dataikuapi.dss.enterprise_asset_library.DSSEnterpriseAssetCollection.get_prompt`
    """
    def __init__(self, collection, prompt):
        self.collection = collection
        self.prompt = prompt

    def get_raw(self):
        """
        Get the raw prompt. This returns a reference to the raw prompt, not a copy,
        so changes made to the returned object will be reflected when saving.

        :return: the raw Enterprise Prompt
        :rtype: :class:`dict`
        """
        return self.prompt

    @property
    def id(self):
        """
        The Enterprise Asset Collection id (read-only)

        :rtype: str
        """
        return self.prompt['id']

    @property
    def name(self):
        """
        Get or set the name of the Enterprise Asset Collection

        :rtype: str
        """
        return self.prompt['name']

    @name.setter
    def name(self, value):
        self.prompt['name'] = value

    @property
    def description(self):
        """
        Get or set the description of the Enterprise Asset Collection

        :rtype: str
        """
        return self.prompt['description']

    @description.setter
    def description(self, value):
        self.prompt['description'] = value

    @property
    def tags(self):
        """
        Get or set the tags of the Enterprise Asset Collection

        :rtype: list[string]
        """
        return self.prompt['tags']

    @tags.setter
    def tags(self, value):
        self.prompt['tags'] = value

    @property
    def content(self):
        """
        Get or set the content of the Enterprise Asset Collection

        :rtype: string
        """
        return self.prompt['content']

    @content.setter
    def content(self, value):
        self.prompt['content'] = value

    def save(self):
        """
        Save the changes made on the prompt

        This call requires at least contributor rights on the Enterprise Asset Collection.
        """
        self.collection.client._perform_empty("PUT", ENTERPRISE_ASSET_LIBRARY_PROMPT_URI_FORMAT % (self.collection.id, self.prompt["id"]), body=self.prompt)

    def delete(self):
        """
        Delete this Enterprise Prompt

        This call requires at least contributor rights on the Enterprise Asset Collection.
        """
        return self.collection.client._perform_empty("DELETE", ENTERPRISE_ASSET_LIBRARY_PROMPT_URI_FORMAT % (self.collection.id, self.prompt["id"]))
