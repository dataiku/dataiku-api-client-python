import copy
import json

class DocumentExtractor(object):
    """
    A handle to interact with a DSS-managed Extractor.

    """

    def __init__(self, client, project_key):
        self.client = client
        self.project_key = project_key

    def vlm_extract(self, images, llm_id, llm_prompt=None, window_size=1, window_overlap=0):
        """
        Extract text content from images using a vision LLM :
        - for each group of 'window_size' consecutive images, use the provided vision LLM prompted to extract a
        comprehensive content in a plain text format

        :param ImagesRef images: images used to extract text content
        :param str llm_id: the identifier of a vision LLM
        :param str llm_prompt: Custom prompt to extract text from the images. (Optional: a default prompt will be
                               used by default)
        :param int window_size: Number of consecutive images to represent in a single output. Default to 1, -1 for all images.
        :param int window_overlap: Number of overlapping images between two windows of images. Default to 0.
                    Must be less than window_size.
        :return: Extracted text content per group of images
        :rtype: DocumentExtractorResponse.
        """

        extractor_request = {
            "inputs": {
                "imagesRef": images.as_json()
            },
            "settings": {
                "windowSize": window_size,
                "windowOverlap": window_overlap,
                "llmId": llm_id,
                "llmPrompt:": llm_prompt
            }
        }
        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/vlm" % self.project_key,
                                        body=extractor_request)
        return VlmExtractorResponse(ret)

    def structured_extract(self, document, max_section_depth=6):
        """
        Splits a document (txt/md) into a structured hierarchy of sections and texts

        :param DocumentRef document: document to split
        :param int max_section_depth: (optional): Maximum depth of sections to extract - deeper sections will be considered as plain text. If set to 0, the
            whole document will be extracted as one section.

        :return: Structured content of the document
        :rtype: StructuredExtractorResponse.
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

    def generate_pages_screenshots(self, document, output_managed_folder=None, pagination_offset=0, pagination_size=10):
        """
        Generate per-page screenshots of a document, returns an iterator over the screenshots

        :param DocumentRef document: input document (txt/md/docx/pdf).
        :param str output_managed_folder: id of a managed folder to store the generated screenshots as jpg.
                 (optional) default to 'None' which return inline images (note that this mode can greatly increase response size)
        :param int pagination_offset: pagination offset if the screenshots. The extraction will start from offset_pagination screenshots.
                 (optional) default to 0
        :param int pagination_size: size of the pagination, each iteration should return at most pagination_size screenshots
                (optional) default to 100
        :return: An iterator over the generated screenshots
        :rtype: Iterator[:class:`ScreenshotterResponse`]
        """

        screenshotter_request = ScreenshotterRequest(document, output_managed_folder, pagination_offset, pagination_size)

        res = self.client._perform_json("POST", "/projects/%s/document-extractors/screenshotter" % self.project_key,
                                        raw_body={"json": json.dumps(screenshotter_request.as_json())},
                                        files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)

        response = ScreenshotterResponse(res)

        yield response
        while response.has_next_results:
            screenshotter_request.pagination_offset = int(response.last_image_index) + 1
            screenshotter_request.document = response.document
            res = self.client._perform_json("POST", "/projects/%s/document-extractors/screenshotter" % self.project_key,
                                            raw_body={"json": json.dumps(screenshotter_request.as_json())})
            response = ScreenshotterResponse(res)
            yield response

class ScreenshotterRequest(object):
    """
    A screenshotter request to based on pagination and query settings

    """
    def __init__(self, document, output_managed_folder, pagination_offset, pagination_size):
        self.document = document
        self.output_managed_folder = output_managed_folder
        self.pagination_offset = pagination_offset
        self.pagination_size = pagination_size

    def as_json(self):
        return {
            "inputs": {
                "document": self.document.as_json(),
            },
            "settings": {
                "outputManagedFolderId": self.output_managed_folder,
                "paginationOffset": self.pagination_offset,
                "paginationSize": self.pagination_size,
            }
        }

class ScreenshotterResponse(object):
    """
    A handle to interact with a document extractor result.

    .. important:
        Do not create this class directly, use :meth:`dataikuapi.dss.document_extractor.generate_page_screenshots` instead.
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :return: The outcome of the extractor request.
        :rtype: bool
        """
        return self._data.get("ok")

    @property
    def has_next_results(self):
        """
        :return: Whether there are still screenshots to extract
        :rtype: bool
        """
        return self._data.get("hasNextResults")

    @property
    def last_image_index(self):
        """
        :return: Index of the last image of the response
        :rtype: bool
        """
        return self._data.get("lastImageIndex")

    @property
    def images(self):
        """
        Per-page screenshots of the original document

        :returns:
        :rtype: ImagesRef
        """
        self._fail_unless_success()
        if self._data["type"] == "inline":
            res = InlineImagesRef()
            res.add_images(inline["content"] for inline in self._data["imagesRefs"]["inlineImages"])
        else:
            res = ManagedFolderImagesRef(self._data["imagesRefs"]["managedFolderId"])
            res.add_images(self._data["imagesRefs"]["imagesPaths"])
        return res

    @property
    def document(self):
        """
        :return: The outcome of the extractor request.
        :rtype: DocumentRef
        """
        doc_type = self._data.get("documentRef").get("type")
        if doc_type == "managed_folder":
            return ManagedFolderDocumentRef(self._data.get("documentRef").get("filePath"), self._data.get("documentRef").get("managedFolderId"))
        if doc_type == "tmp_file":
            return _TmpDocumentRef(self._data.get("documentRef").get("tmpFileName"), self._data.get("documentRef").get("originalFileName"))
        else:
            raise Exception("Output document is not valid")

    def _fail_unless_success(self):
        if not self.success:
            error_message = "Document failed to be extracted - request failed: {}".format(
                self._data.get("errorMessage", "An unknown error occurred")
            )
            raise Exception(error_message)

class StructuredExtractorResponse(object):
    """
    A handle to interact with a document structured extractor result.

    .. important::
        Do not create this class directly, use :meth:`dataikuapi.dss.document_extractor.structured_extract` instead.
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :return: The outcome of the structured extractor request.
        :rtype: bool
        """
        return self._data.get("ok")

    @property
    def content(self):
        """
        :return: The structure of the document as a dictionary
        :rtype: dict
        """
        return self._data["content"]

    @property
    def text_chunks(self):
        """
        :return: A flattened text-only view of the documents, along with their outline.
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
        Do not create this class directly, use :meth:`dataikuapi.dss.document_extractor.vlm_extract`
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :return: The outcome of the extractor request.
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
    def __init__(self):
        self.type = None

    def as_json(self):
        raise NotImplementedError

class LocalFileDocumentRef(DocumentRef):

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
    A handle to interact with a document in the tmp/docextraction folder.

    .. important:
        Do not create this class directly, use :meth:`dataikuapi.dss.document_extractor.generate_pages_screenshots` instead.
    """

    def __init__(self, tmp_file_name, original_file_name):
        """
         :param str tmp_file_name: File name that is returned when the file is uploaded
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
    def __init__(self, file_path, managed_folder_id):
        """
         :param file_path: path to the document file inside the managed folder
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

class ImagesRef(InputRef):
    def __init__(self):
        super(ImagesRef, self).__init__()
        self.type = None

    def as_json(self):
        raise NotImplementedError

class InlineImagesRef(ImagesRef):
    def __init__(self):
        super(InlineImagesRef, self).__init__()
        self.type = "inline"
        self.inline_images = []

    def add_images(self, images):
        """
        :param List[str | bytes] images: Image content as bytes or str (base64)
        """
        for image in images:
            if isinstance(image, str):
                self.inline_images.append({"content": image})
            elif isinstance(image, bytes):
                import base64
                self.inline_images.append({"content": base64.b64encode(image).decode("utf8")})
            else:
                raise Exception("Unsupported image format, expected image content as bytes or string (base64)")
        return self

    def as_json(self):
        return {
            "type": self.type,
            "inlineImages": self.inline_images
        }

class ManagedFolderImagesRef(ImagesRef):
    def __init__(self, managed_folder_id):
        """
        :param str managed_folder_id:
        """
        super(ManagedFolderImagesRef, self).__init__()
        self.type = "managed_folder"
        self.managed_folder_id = managed_folder_id
        self.images_paths = []

    def add_images(self, images):
        """
        :param images: :param List[str] images: paths to the image files inside the managed folder
        """
        self.images_paths.extend(images)

    def as_json(self):
        return {
            "type": self.type,
            "managedFolderId": self.managed_folder_id,
            "imagesPaths": self.images_paths
        }
