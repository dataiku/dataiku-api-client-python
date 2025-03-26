import copy
import json


class DocumentExtractor(object):
    """
    A handle to interact with a DSS-managed Document Extractor.

    """

    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def vlm_extract(self, images, llm_id, llm_prompt=None, window_size=1, window_overlap=0):
        """
        Extract text content from images using a vision LLM: for each group of 'window_size' consecutive images,
        prompt the given vision LLM to summarize in plain text.

        :param images: iterable over the images to be described by the vision LLM
        :type images: iterable(:class:`InlineImageRef`) | iterable(:class:`ManagedFolderImageRef`)
        :param llm_id: the identifier of a vision LLM
        :type llm_id: str
        :param llm_prompt: Custom prompt to extract text from the images
        :type llm_prompt: str
        :param window_size: Number of consecutive images to represent in a single output. Use -1 for all images.
        :type window_size: int
        :param int window_overlap: Number of overlapping images between two windows of images. Must be less than window_size.
        :type window_overlap: int

        :returns: Extracted text content per group of images
        :rtype: :class:`VlmExtractorResponse`
        """

        extractor_request = {
            "settings": {
                "windowSize": window_size,
                "windowOverlap": window_overlap,
                "llmId": llm_id,
                "llmPrompt": llm_prompt
            }
        }

        images = list(images)
        if not images:
            raise ValueError("No images provided")
        if all(isinstance(ir, InlineImageRef) for ir in images):
            extractor_request["inputs"] = {
                "imagesRef": {
                    "type": images[0].type,
                    "inlineImages": [ir.as_json() for ir in images]
                }
            }
        elif all(isinstance(ir, ManagedFolderImageRef) for ir in images):
            extractor_request["inputs"] = {
                "imagesRef": {
                    "type": images[0].type,
                    "managedFolderId": images[0].managed_folder_id,
                    "imagesPaths": [ir.image_path for ir in images]
                }
            }
        else:
            raise ValueError("Unsupported mix of image types: %s" % set([ir.type for ir in images]))

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/vlm" % self.project_key,
                                        body=extractor_request)
        return VlmExtractorResponse(ret)

    def structured_extract(self, document, max_section_depth=6):
        """
        Splits a document (txt/md) into a structured hierarchy of sections and texts

        :param document: document to split
        :type document: :class:`DocumentRef`
        :param max_section_depth: Maximum depth of sections to extract - consider deeper sections as plain text.
                                  If set to 0, extract the whole document as one single section.
        :type max_section_depth: int

        :returns: Structured content of the document
        :rtype: :class:`StructuredExtractorResponse`
        """
        extractor_request = {
            "inputs": {
                "document": document.as_json()
            },
            "settings": {
                "maxSectionDepth": max_section_depth
            }
        }

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/structured" % self.project_key,
                                        raw_body={"json": json.dumps(extractor_request)},
                                        files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)

        return StructuredExtractorResponse(ret)

    def generate_pages_screenshots(self, document, output_managed_folder=None, offset=0, fetch_size=10, keep_fetched=True):
        """
        Generate per-page screenshots of a document, returning an iterable over the screenshots.
        In most cases, a screenshot corresponds to a single page of a document.

        Usage example:

        .. code-block:: python

            doc_extractor = DocumentExtractor(client, "project_key")
            document_ref = ManagedFolderDocumentRef('path_in_folder/document.pdf', folder_id)

            for image in doc_extractor.generate_pages_screenshots(document_ref):
                print(image.get_raw())

        :param document: input document (txt | md | docx | pdf).
        :type document: :class:`DocumentRef`
        :param output_managed_folder: id of a managed folder to store the generated screenshots as png.
                                      When unspecified, return inline images in the response.
        :type output_managed_folder: str
        :param int offset: start extraction from `offset` screenshots.
        :type offset: int
        :param fetch_size: number of screenshots to fetch in each request, iterating on the next result automatically sends a new request for another `fetch_size` screenshots
        :type fetch_size: int
        :param keep_fetched: whether to keep previous screenshots requests within this response object when fetching next ones.
        :type keep_fetched: boolean

        :returns: An iterable over the result screenshots
        :rtype: :class:`ScreenshotterResponse`
        """

        screenshotter_request = ScreenshotterRequest(document, output_managed_folder, offset, fetch_size)
        return ScreenshotterResponse(self.client, self.project_key, screenshotter_request, keep_fetched)

class ScreenshotterRequest(object):
    """
    A screenshotter request based on pagination and query settings

    """
    def __init__(self, document, output_managed_folder, offset, fetch_size):
        self.document = document
        self.output_managed_folder = output_managed_folder
        self.offset = offset
        self.fetch_size = fetch_size

    def as_json(self):
        return {
            "inputs": {
                "document": self.document.as_json(),
            },
            "settings": {
                "outputManagedFolderId": self.output_managed_folder,
                "paginationOffset": self.offset,
                "paginationSize": self.fetch_size,
            }
        }


class ScreenshotterResponse(object):
    """
    A handle to interact with a screenshotter result. Iterable over the :class:`ImageRef` screenshots.

    .. important::
        Do not create this class directly, use :meth:`generate_page_screenshots` instead.
    """
    def __init__(self, client, project_key, screenshotter_request, keep_fetched):
        self.client = client
        self.project_key = project_key
        self.screenshotter_request = screenshotter_request
        self._current_data = self.client._perform_json("POST", "/projects/%s/document-extractors/screenshotter" % self.project_key,
                                                       raw_body={"json": json.dumps(screenshotter_request.as_json())},
                                                       files={"file": screenshotter_request.document.file} if isinstance(screenshotter_request.document, LocalFileDocumentRef) else None)
        self._fail_unless_success()
        self._screenshots = [None] * self.total_count
        self.initial_offset = screenshotter_request.offset
        self.keep_fetched = keep_fetched
        self._update_screenshot_list_at_index(screenshotter_request.offset)

    def get_raw(self):
        return self._current_data

    def __iter__(self):
        return ScreenshotIterator(self)

    def fetch_screenshot(self, screenshot_index):
        if screenshot_index >= self.total_count:
            raise StopIteration("Reached end of document")
        if self._screenshots[screenshot_index] is not None:
            return self._screenshots[screenshot_index]
        else:
            self.screenshotter_request.offset = screenshot_index
            self.screenshotter_request.document = self.document
            self._current_data = self.client._perform_json("POST", "/projects/%s/document-extractors/screenshotter" % self.project_key,
                                                           raw_body={"json": json.dumps(self.screenshotter_request.as_json())},
                                                           files={"file": self.document.file} if isinstance(self.document, LocalFileDocumentRef) else None)
            self._fail_unless_success()
            self._update_screenshot_list_at_index(screenshot_index)
            return self._screenshots[screenshot_index]

    def _update_screenshot_list_at_index(self, index):
        if self._current_data["imagesRefs"]["type"] == "inline":
            res =  [InlineImageRef(image["content"], image["mimeType"] if "mimeType" in image else None) for image in self._current_data["imagesRefs"]["inlineImages"]]
        elif self._current_data["imagesRefs"]["type"] == "managed_folder":
            res = [ManagedFolderImageRef(self._current_data["imagesRefs"]["managedFolderId"], path) for path in self._current_data["imagesRefs"]["imagesPaths"]]
        else:
            raise ValueError("Did not return valid images ref")
        if not self.keep_fetched:
            for idx in range(len(self._screenshots)):
                if idx < index or idx >= len(res):
                    self._screenshots[idx] = None
        self._screenshots[index:len(res) + index] = res

    @property
    def success(self):
        """
        :returns: The outcome of the extractor request / latest fetch.
        :rtype: bool
        """
        return self._current_data.get("ok")

    @property
    def has_next(self):
        """
        :returns: Whether there are more screenshots to extract after this response
        :rtype: bool
        """
        return self._current_data.get("hasMoreResults")

    @property
    def total_count(self):
        """
        :returns: Total number of screenshots that can be extracted from the document. In most cases corresponds to the number of pages of the document.
        :rtype: int
        """
        return self._current_data.get("totalResults")

    @property
    def document(self):
        """
        :returns: The reference to the screenshotted document.
        :rtype: :class:`DocumentRef`
        """
        doc_type = self._current_data.get("documentRef").get("type")
        if doc_type == "managed_folder":
            return ManagedFolderDocumentRef(self._current_data.get("documentRef").get("filePath"), self._current_data.get("documentRef").get("managedFolderId"))
        if doc_type == "tmp_file":
            return _TmpDocumentRef(self._current_data.get("documentRef").get("tmpFileName"), self._current_data.get("documentRef").get("originalFileName"))
        else:
            raise Exception("Output document is not valid")

    def _fail_unless_success(self):
        if not self.success:
            error_message = "Document failed to be extracted - request failed: {}".format(
                self._current_data.get("errorMessage", "An unknown error occurred")
            )
            raise Exception(error_message)


class ScreenshotIterator(object):
    """
    Iterator over the :class:`ImageRef` screenshots.

    .. important::
        Do not create this class directly, use `:meth:`generate_page_screenshots` instead.
    """
    def __init__(self, screenshotter_response):
        self.screenshotter_response = screenshotter_response
        self.current_index = screenshotter_response.initial_offset

    def __next__(self):
        res = self.screenshotter_response.fetch_screenshot(self.current_index)
        self.current_index += 1
        return res


class StructuredExtractorResponse(object):
    """
    A handle to interact with a document structured extractor result.

    .. important::
        Do not create this class directly, use :meth:`structured_extract` instead.
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :returns: The outcome of the structured extractor request.
        :rtype: bool
        """
        return self._data.get("ok")

    @property
    def content(self):
        """
        :returns: The structure of the document as a dictionary
        :rtype: dict
        """
        return self._data["content"]

    @property
    def text_chunks(self):
        """
        :returns: A flattened text-only view of the documents, along with their outline.
        :rtype: list[dict]
        """

        def _flatten_using_dfs(node, current_outline):
            if not node or not "type" in node:
                return []
            elif node["type"] == "text":
                return [{"text": node["text"], "outline": current_outline}]
            elif node["type"] not in ["document", "section"]:
                raise ValueError("Unsupported structured content type: " + node["type"])
            if not "content" in node:
                return []
            deeper_outline = copy.deepcopy(current_outline)
            if node["type"] == "section":
                deeper_outline.append(node["title"])
            chunks = []
            for child in node["content"]:
                chunks.extend(_flatten_using_dfs(child, deeper_outline))
            return chunks

        return _flatten_using_dfs(self._data["content"], [])

    def _fail_unless_success(self):
        if not self.success:
            error_message = "Document failed to be extracted - request failed: {}".format(
                self._data.get("errorMessage", "An unknown error occurred")
            )
            raise Exception(error_message)


class VlmExtractorResponse(object):
    """
    A handle to interact with a VLM extractor result.

    .. important::
        Do not create this class directly, use :meth:`vlm_extract`
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :returns: The outcome of the extractor request.
        :rtype: bool
        """
        return self._data.get("ok")

    @property
    def chunks(self):
        """
        Content extracted from the original document, split into chunks

        :returns: extracted text content per chunk.
        :rtype: list[str]
        """
        self._fail_unless_success()
        return self._data["chunks"]

    def _fail_unless_success(self):
        if not self.success:
            error_message = "Document failed to be extracted - request failed: {}".format(
                self._data.get("errorMessage", "An unknown error occurred")
            )
            raise Exception(error_message)


class InputRef(object):
    def as_json(self):
        raise NotImplementedError


class DocumentRef(InputRef):
    """
    A reference to a document file.

    .. important::
        Do not create this class directly, use one of its implementations:
            * :class:`LocalFileDocumentRef` for a local file to be uploaded
            * :class:`ManagedFolderDocumentRef` for a file inside a DSS-managed folder
    """
    def __init__(self):
        self.type = None

    def as_json(self):
        raise NotImplementedError


class LocalFileDocumentRef(DocumentRef):
    """
        A reference to a client-local file.

        Usage example:

        .. code-block:: python

            with open("/Users/mdupont/document.pdf", "rb") as f:
                file_ref = LocalFileDocumentRef(f)

                # upload the document & generate images of the document's pages:
                images = list(doc_ex.generate_pages_screenshots(file_ref))
    """
    def __init__(self, fp):
        """
         :param fp: File-like object or stream
        """
        super(LocalFileDocumentRef, self).__init__()
        self.type = "local_file"
        self.file = fp

    def as_json(self):
        return {
            "type": self.type,
        }


class _TmpDocumentRef(DocumentRef):
    """
    A reference to interact with a document in the tmp/docextraction folder.

    .. important::
        Do not create this class directly, use :meth:`generate_pages_screenshots` instead.
    """

    def __init__(self, tmp_file_name, original_file_name):
        """
         :param str tmp_file_name: File name that is returned when the file is uploaded
         :param str original_file_name: File name before upload
        """
        super(_TmpDocumentRef, self).__init__()
        self.type = "tmp_file"
        self.tmp_file_name = tmp_file_name
        self.original_file_name = original_file_name

    def as_json(self):
        return {
            "type": self.type,
            "tmpFileName": self.tmp_file_name,
            "originalFileName": self.original_file_name,
        }


class ManagedFolderDocumentRef(DocumentRef):
    """
    A reference to a file in a DSS-managed folder.

    Usage example:

    .. code-block:: python

            file_ref = ManagedFolderDocumentRef('path_in_folder/document.pdf', folder_id)

            # generate images of the document's pages:
            resp = doc_ex.generate_pages_screenshots(file_ref)
    """
    def __init__(self, file_path, managed_folder_id):
        """
        :param file_path: path to the document file inside the managed folder
        :param managed_folder_id: identifier of the folder containing the file
        """
        super(ManagedFolderDocumentRef, self).__init__()
        self.type = "managed_folder"
        self.file_path = file_path
        self.managed_folder_id = managed_folder_id

    def as_json(self):
        return {
            "type": self.type,
            "filePath": self.file_path,
            "managedFolderId": self.managed_folder_id
        }


class ImageRef(InputRef):
    """
    A reference to a single image

    .. important::
        Do not create this class directly, use one of its implementations:
            * :class:`InlineImageRef` for an inline (bytes / base64 string) image
            * :class:`ManagedFolderImageRef` for an image stored in a DSS-managed folder
    """
    def __init__(self):
        super(ImageRef, self).__init__()
        self.type = None

    def as_json(self):
        raise NotImplementedError


class InlineImageRef(ImageRef):
    """
    A reference to an inline image.

    Usage example:

    .. code-block:: python

        with open("/Users/mdupont/image.jpg", "rb") as f:
            image_ref = InlineImageRef(f.read())

        # Extract a text summary from the image using a vision LLM:
        resp = doc_ex.vlm_extract([image_ref], 'llm_id')

    """
    def __init__(self, image, mime_type=None):
        """
        :param str | bytes image: image content as bytes or base64 string
        :param str mime_type: mime type of the image
        """
        super(InlineImageRef, self).__init__()
        self.type = "inline"
        if isinstance(image, str):
            self.image = image
        elif isinstance(image, bytes):
            import base64
            self.image = base64.b64encode(image).decode("utf8")
        else:
            raise Exception("Unsupported image format, expected image content as bytes or string (base64)")
        self.mime_type = mime_type

    def as_json(self):
        res = {
            "type": self.type,
            "content": self.image
        }
        if self.mime_type is not None:
            res["mimeType"] = self.mime_type
        return res


class ManagedFolderImageRef(ImageRef):
    """
    A reference to an image stored in a DSS-managed folder.

    Usage example:

    .. code-block:: python

        managed_img = ManagedFolderImageRef('managed_folder_id', 'path_in_folder/image.png')

        # Extract a text summary from the image using a vision LLM:
        resp = doc_ex.vlm_extract([managed_img], 'llm_id')
    """
    def __init__(self, managed_folder_id, image_path):
        """
        :param str managed_folder_id: identifier of the folder containing the image
        :param str image_path: path to the image file inside the managed folder
        """
        super(ManagedFolderImageRef, self).__init__()
        self.type = "managed_folder"
        self.managed_folder_id = managed_folder_id
        self.image_path = image_path

    def as_json(self):
        return {
            "type": self.type,
            "managedFolderId": self.managed_folder_id,
            "imagePath": self.image_path
        }
