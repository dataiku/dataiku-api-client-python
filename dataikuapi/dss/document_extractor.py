import base64
import copy
import json
import warnings

from dataikuapi.dss.llm_utils import get_json_schema_and_parser
from dataikuapi.dss.recipe import DSSRecipe
from dataikuapi.utils import _write_response_content_to_file


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
                    "inlineImages": [ir.as_dict() for ir in images]
                }
            }
        elif all(isinstance(ir, ManagedFolderImageRef) for ir in images):
            extractor_request["inputs"] = {
                "imagesRef": {
                    "type": images[0].type,
                    "managedFolderRef": images[0].managed_folder_ref,
                    "imagesPaths": [ir.image_path for ir in images]
                }
            }
        else:
            raise ValueError("Unsupported mix of image types: %s" % set([ir.type for ir in images]))

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/vlm" % self.project_key,
                                        body=extractor_request)
        return VlmExtractorResponse(ret)


    def vlm_extract_fields(self, images, schema=None, llm_id=None, llm_prompt=None, from_recipe=None, strict=None, compatible=None):
        """
        Extract specific fields (structured data) from images (typically screenshots of a document's pages) using a vision LLM.
        Describe expected fields in ``extraction_schema``, or specify an Extract Fields recipe to use its settings.

        :param images: screenshots of the document's pages from which to extract the fields
        :type images: iterable(:class:`InlineImageRef`) | iterable(:class:`ManagedFolderImageRef`)
        :param schema: a JSON schema or a Pydantic model class describing the fields to extract.
                       JSON schema definitions or Pydantic models referencing other models are unsupported.
        :type schema: str | dict | pydantic.BaseModel class or Python type hint.
        :param llm_id: Identifier of a vision LLM
        :type llm_id: str
        :param llm_prompt: Custom prompt to extract fields from the images
        :type llm_prompt: str
        :param from_recipe: Name of a recipe from which to read the other arguments.
                            Arguments provided explicitly take precedence.
        :type from_recipe: str
        :param strict: Whether to strictly enforce the schema. Support varies across models/providers.
        :type strict: bool
        :param compatible: Allow DSS to modify the schema in order to increase compatibility, depending on known limitations of the model/provider. Defaults to automatic.
        :type compatible: bool

        :returns: Extracted fields from images
        :rtype: :class:`FieldsVlmExtractorResponse`
        """
        if from_recipe is not None and (schema is None or llm_id is None or llm_prompt is None or strict is None or compatible is None):
            recipe_settings = DSSRecipe(self.client, self.project_key, from_recipe).get_settings()
            recipe_params = recipe_settings.raw_params

            if schema is None:
                schema = recipe_params.get("extractionSchema")
            if llm_id is None:
                llm_id = recipe_params.get("vlmId")
            if llm_prompt is None:
                llm_prompt = recipe_params.get("extractionPrompt")
            if strict is None:
                strict = recipe_params.get("valueErrorHandling") == "BLANK_VALUE"
            if compatible is None:
                compatible = True
                dku_properties = recipe_settings.get_recipe_raw_definition().get("dkuProperties") or []
                for prop in dku_properties:
                    if isinstance(prop, dict) and prop.get("name") == "dku.extractFields.schemaCompatibilityEnhancer" and isinstance(prop.get("value"), bool):
                        compatible = prop.get("value")
                        break

        json_schema, parser_method = get_json_schema_and_parser(schema)

        extractor_request = {
            "settings": {
                "llmId": llm_id,
                "llmPrompt": llm_prompt,
                "extractionSchema" : json.loads(json_schema),
                "strictSchemaAdherence": strict,
                "schemaCompatibilityEnhancer": compatible
            }
        }

        images = list(images)
        if not images:
            raise ValueError("No images provided")
        if all(isinstance(ir, InlineImageRef) for ir in images):
            extractor_request["inputs"] = {
                "imagesRef": {
                    "type": images[0].type,
                    "inlineImages": [ir.as_dict() for ir in images]
                }
            }
        elif all(isinstance(ir, ManagedFolderImageRef) for ir in images):
            extractor_request["inputs"] = {
                "imagesRef": {
                    "type": images[0].type,
                    "managedFolderRef": images[0].managed_folder_ref,
                    "imagesPaths": [ir.image_path for ir in images]
                }
            }
        else:
            raise ValueError("Unsupported mix of image types: %s" % set([ir.type for ir in images]))

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/fields/vlm" % self.project_key,
                                        body=extractor_request)
        return FieldsVlmExtractorResponse(ret, parser_method)

    def structured_extract(self, document, max_section_depth=6, image_handling_mode='IGNORE', ocr_engine='AUTO', languages="en", llm_id=None, llm_prompt=None,
                           output_managed_folder=None, image_validation=True):
        """
        Splits a document (txt, md, pdf, docx, pptx, html, png, jpg, jpeg) into a structured hierarchy of sections and texts

        :param document: document to split
        :type document: :class:`DocumentRef`
        :param max_section_depth: Maximum depth of sections to extract - consider deeper sections as plain text.
                                  If set to 0, extract the whole document as one single section.
        :type max_section_depth: int
        :param image_handling_mode: How to handle images in the document. Can be one of: 'IGNORE', 'OCR', 'VLM_ANNOTATE'.
        :type image_handling_mode: str
        :param ocr_engine: Engine to perform the OCR, either 'AUTO', 'EASYOCR' or 'TESSERACT'. Auto uses tesseract if available, otherwise easyOCR.
        :type ocr_engine: str
        :param languages: OCR languages to use for recognition. List (either a comma-separated string, or list of strings) of ISO639 languages codes.
        :type languages: str | list
        :param llm_id: ID of the (vision-capable) LLM to use for annotating images when image_handling_mode is 'VLM_ANNOTATE'
        :type llm_id: str
        :param llm_prompt: Custom prompt to extract text from the images
        :type llm_prompt: str
        :param output_managed_folder: id of a managed folder to store the image in the document.
                              When unspecified, return inline images in the response.
        :type output_managed_folder: str
        :param image_validation: Whether to validate images before processing. If True, images classified as barcodes, icons, logos, QR codes, signatures, or stamps are skipped.
        :type image_validation: boolean
        :returns: Structured content of the document
        :rtype: :class:`StructuredExtractorResponse`
        """
        if image_handling_mode not in ["IGNORE", "OCR", "VLM_ANNOTATE"]:
            raise ValueError("Invalid image_handling_mode, it must be set to 'IGNORE', 'OCR' or 'VLM_ANNOTATE'")

        extractor_request = {
            "inputs": {
                "document": document.as_dict()
            },
            "settings": {
                "maxSectionDepth": max_section_depth,
                "imageValidation": image_validation,
                "outputManagedFolderRef": output_managed_folder,
            }
        }
        if image_handling_mode == "IGNORE":
            extractor_request["settings"]["imageHandlingMode"] = "IGNORE"
        elif image_handling_mode == "OCR":
            if ocr_engine not in ["TESSERACT", "EASYOCR", "AUTO"]:
                raise ValueError("Invalid ocr_engine, it must be set to 'TESSERACT', 'EASYOCR' or 'AUTO'")
            extractor_request["settings"]["imageHandlingMode"] = "OCR"
            if type(languages) is list:
                languages = ",".join(languages)
            extractor_request["settings"]["ocrSettings"] = {
                "ocrEngine": ocr_engine,
                "ocrLanguages": languages
            }
        elif image_handling_mode == "VLM_ANNOTATE":
            extractor_request["settings"]["imageHandlingMode"] = "VLM_ANNOTATE"
            extractor_request["settings"]["vlmAnnotationSettings"] = {
                "llmId": llm_id,
                "llm_prompt": llm_prompt,
            }
        else:
            raise ValueError("Invalid image_handling_mode, it must be set to 'IGNORE', 'OCR' or 'VLM_ANNOTATE'")

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/structured" % self.project_key,
                                        raw_body={"extractionRequest": json.dumps(extractor_request)},
                                        files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)

        return StructuredExtractorResponse(ret)

    def text_extract(self, document, image_handling_mode='IGNORE', ocr_engine='AUTO', languages="en"):
        """
        Extract raw text from a document (txt, md, pdf, docx, pptx, html, png, jpg, jpeg).

        Some documents like PDF or PowerPoint have an inherent structure (page, bookmarks or slides); for those documents, the returned results contain this structure.
        Otherwise, the document's structure is not inferred, resulting in one or more text item(s).

        PDF files are converted to images and processed using OCR if `image_handling_mode` is set to 'OCR', recommended for scanned PDFs.
        Otherwise, their text content is extracted.

        :param document: document to split
        :type document: :class:`DocumentRef`
        :param image_handling_mode: How to handle images in the document, either 'IGNORE' or 'OCR'.
        :type image_handling_mode: str
        :param ocr_engine: Engine to perform the OCR, either 'AUTO', 'EASYOCR' or 'TESSERACT'. Auto uses tesseract if available, otherwise easyOCR.
        :type ocr_engine: str
        :param languages: OCR languages to use for recognition. List (either a comma-separated string, or list of strings) of ISO639 languages codes.
        :type languages: str | list

        :returns: Text content of the document
        :rtype: :class:`TextExtractorResponse`
        """
        if image_handling_mode not in ["IGNORE", "OCR"]:
            raise ValueError("Invalid image_handling_mode, it must be set to 'IGNORE' or 'OCR'")

        extractor_request = {
            "inputs": {
                "document": document.as_dict()
            },
            "settings": {
            }
        }
        if image_handling_mode == "IGNORE":
            extractor_request["settings"]["imageHandlingMode"] = "IGNORE"
        elif image_handling_mode == "OCR":
            if ocr_engine not in ["TESSERACT", "EASYOCR", "AUTO"]:
                raise ValueError("Invalid ocr_engine, it must be set to 'TESSERACT', 'EASYOCR' or 'AUTO'")
            extractor_request["settings"]["imageHandlingMode"] = "OCR"
            if type(languages) is list:
                languages = ",".join(languages)
            extractor_request["settings"]["ocrSettings"] = {
                "ocrEngine": ocr_engine,
                "ocrLanguages": languages
            }
        else:
            raise ValueError("Invalid image_handling_mode, it must be set to 'IGNORE' or 'OCR'")

        ret = self.client._perform_json("POST", "/projects/%s/document-extractors/text" % self.project_key,
                                        raw_body={"extractionRequest": json.dumps(extractor_request)},
                                        files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)

        return TextExtractorResponse(ret)

    def generate_pages_screenshots(self, document, output_managed_folder=None, offset=0, fetch_size=10, keep_fetched=True,
                                   page_dpi=None, max_memory_per_document=None):
        """
        Generate per-page screenshots of a document, returning an iterable over the screenshots.

        Usage example:

        .. code-block:: python

            doc_extractor = DocumentExtractor(client, "project_key")
            document_ref = ManagedFolderDocumentRef('path_in_folder/document.pdf', folder_id)

            fetch_size = 10
            response = doc_extractor.generate_pages_screenshots(document_ref, fetch_size=fetch_size)
            # The first 10 screenshots (fetch_size) are computed & retrieved immediately within the response.

            first_screenshot = response.fetch_screenshot(0)  # InlineImageRef or ManagedFolderImageRef

            # Iterating through the first 10 items is instantaneous as they are already fetched.
            # Iterating from the 11th item triggers new backend requests (processing pages 11-20, fetch screenshots).
            for idx, screenshot in enumerate(response):
                if (idx % fetch_size == 0) and idx != 0:
                    print(f"Computing the next {fetch_size} screenshots")
                print(f"Screenshot #{idx}: {screenshot.as_dict()}")

            # Alternatively, response being an iterable, you can compute & fetch all screenshots at once:
            response = doc_extractor.generate_pages_screenshots(document_ref)
            screenshots = list(response)  # list of InlineImageRef or ManagedFolderImageRef objects


        :param document: input document (txt | pdf | docx | doc | odt | pptx | ppt | odp | xlsx | xls | xlsm | xlsb | ods | png | jpg | jpeg).
        :type document: :class:`DocumentRef`
        :param output_managed_folder: id of a managed folder to store the generated screenshots as png.
                                      When unspecified, return inline images in the response.
        :type output_managed_folder: str
        :param int offset: start extraction from `offset` screenshots.
        :type offset: int
        :param fetch_size: number of screenshots to fetch in each request, iterating on the next result automatically sends a new request for another
                           `fetch_size` screenshots
        :type fetch_size: int
        :param keep_fetched: whether to keep previous screenshots requests within this response object when fetching next ones.
        :type keep_fetched: boolean
        :param page_dpi: DPI used to render pages if memory allows.
        :type page_dpi: int
        :param max_memory_per_document: maximum memory budget in MB used while rendering a document.
            The effective DPI may be reduced to fit this limit depending on page dimensions.
        :type max_memory_per_document: int

        :returns: An iterable over the result screenshots
        :rtype: :class:`ScreenshotterResponse`
        """

        screenshotter_request = ScreenshotterRequest(
            document,
            output_managed_folder,
            offset,
            fetch_size,
            page_dpi,
            max_memory_per_document
        )
        return ScreenshotterResponse(self.client, self.project_key, screenshotter_request, keep_fetched)


    def convert_to_pdf(self, document, output_managed_folder=None, path_in_output_folder=None):
        """
        Convert a document to PDF format.

        :param document: input document (docx | doc | odt | pptx | ppt | odp | xlsx | xls | xlsm | xlsb | ods | png | jpg | jpeg).
        :type document: :class:`DocumentRef`
        :param output_managed_folder: id of an optional managed folder to store the generated PDF document.
            If unspecified, the document is not stored and should be downloaded from the returned :class:`PDFConversionResponse`
        :type output_managed_folder: str
        :param path_in_output_folder: optional path of the generated PDF document in the output managed folder.
            If unspecified and the input document is in a managed folder, defaults to the input document path (with a .pdf extension).
        :type path_in_output_folder: str

        :returns: A :class:`PDFConversionResponse`, to reference & download the resulting PDF.
        :rtype: :class:`PDFConversionResponse`
        """
        if path_in_output_folder is not None and output_managed_folder is None:
            raise ValueError("The output_managed_folder must be specified when path_in_output_folder is specified.")

        return PDFConversionResponse(self.client, self.project_key, document, output_managed_folder, path_in_output_folder)


class ScreenshotterRequest(object):
    """
    A screenshotter request based on pagination and query settings

    """

    def __init__(self, document, output_managed_folder, offset, fetch_size, page_dpi=None, max_memory_per_document=None):
        self.document = document
        self.output_managed_folder = output_managed_folder
        self.offset = offset
        self.fetch_size = fetch_size
        self.page_dpi = page_dpi
        self.max_memory_per_document = max_memory_per_document # MB

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

            Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("ScreenshotterRequest.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        """
        Get a dictionary representation.

        :rtype: dict
        """
        return {
            "inputs": {
                "document": self.document.as_dict(),
            },
            "settings": {
                "outputManagedFolderRef": self.output_managed_folder,
                "paginationOffset": self.offset,
                "paginationSize": self.fetch_size,
                "pageDPI": self.page_dpi,
                "maxMemoryPerDocMB": self.max_memory_per_document,
            }
        }


class ScreenshotterResponse(object):
    """
    A handle to interact with a screenshotter result. Iterable over the :class:`ImageRef` screenshots.

    .. important::
        Do not create this class directly, use :meth:`~DocumentExtractor.generate_pages_screenshots` instead.
    """

    def __init__(self, client, project_key, screenshotter_request, keep_fetched):
        self.client = client
        self.project_key = project_key
        self.screenshotter_request = screenshotter_request
        self._current_data = self.client._perform_json("POST", "/projects/%s/document-extractors/screenshotter" % self.project_key,
                                                       raw_body={"screenshotRequest": json.dumps(screenshotter_request.as_dict())},
                                                       files={"file": screenshotter_request.document.file} if isinstance(screenshotter_request.document,
                                                                                                                         LocalFileDocumentRef) else None)
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
                                                           raw_body={"screenshotRequest": json.dumps(self.screenshotter_request.as_dict())},
                                                           files={"file": self.document.file} if isinstance(self.document, LocalFileDocumentRef) else None)
            self._fail_unless_success()
            self._update_screenshot_list_at_index(screenshot_index)
            return self._screenshots[screenshot_index]

    def _update_screenshot_list_at_index(self, index):
        if self._current_data["imagesRefs"]["type"] == "inline":
            res = [InlineImageRef(image["content"], image["mimeType"] if "mimeType" in image else None) for image in
                   self._current_data["imagesRefs"]["inlineImages"]]
        elif self._current_data["imagesRefs"]["type"] == "managed_folder":
            res = [ManagedFolderImageRef(self._current_data["imagesRefs"]["managedFolderRef"], path) for path in self._current_data["imagesRefs"]["imagesPaths"]]
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
            document_ref = self._current_data.get("documentRef")
            managed_folder_ref = document_ref.get("managedFolderRef") or document_ref.get("managedFolderId")
            return ManagedFolderDocumentRef(document_ref.get("filePath"), managed_folder_ref)
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
        Do not create this class directly, use `:meth:`~DocumentExtractor.generate_pages_screenshots` instead.
    """

    def __init__(self, screenshotter_response):
        self.screenshotter_response = screenshotter_response
        self.current_index = screenshotter_response.initial_offset

    def __next__(self):
        res = self.screenshotter_response.fetch_screenshot(self.current_index)
        self.current_index += 1
        return res


class TextExtractorResponse(object):
    """
    A handle to interact with a document text extractor result.

    .. important::
        Do not create this class directly, use :meth:`~DocumentExtractor.text_extract` instead.
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :returns: The outcome of the text extraction request.
        :rtype: bool
        """
        return self._data.get("ok")

    @property
    def content(self):
        """
        The content of the document as extracted by :meth:`text_extract` can contain some structure inherent to the document. For instance, PDF documents are
        extracted page by page, and PowerPoint documents slide by slide.
        Some PDF documents contain bookmarks that can be used to separate them into sections.
        For other documents, a single section with one or more text item(s).

        This property returns a dict that represents this structure.

        :returns: The structure of the document as a dictionary
        :rtype: dict
        """
        return self._data["content"]

    @property
    def text_content(self):
        """
        :returns: The textual content of the document as a string.
        :rtype: str
        """
        if "content" in self.content:
            return "\n".join([TextExtractorResponse._text(item) for item in self.content["content"]])

        return ""


    @staticmethod
    def _text(structured):
        if "text" in structured.keys():
            return structured["text"]
        elif "description" in structured.keys():
            return structured["description"]
        return ""



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
        Do not create this class directly, use :meth:`~DocumentExtractor.structured_extract` instead.
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
            if not node or "type" not in node:
                return []
            elif node["type"] == "text" or node["type"] == "table":
                if "text" not in node or not node["text"]:
                    return []
                return [{"text": node["text"], "outline": current_outline}]
            elif node["type"] == "image":
                if "description" not in node or not node["description"]:
                    return []
                return [{"text": node["description"], "outline": current_outline}]
            elif node["type"] not in ["document", "section", "slide"]:
                raise ValueError("Unsupported structured content type: " + node["type"])
            if "content" not in node:
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

class PDFConversionResponse(object):
    """
    A handle to interact with a document PDF conversion result.

    .. important::
        Do not create this class directly, use :meth:`~DocumentExtractor.convert_to_pdf` instead.
    """

    def __init__(self, client, project_key, document, output_managed_folder, path_in_output_folder=None):
        self.client = client
        self.project_key = project_key
        self.output_managed_folder = output_managed_folder
        self.path_in_output_folder = path_in_output_folder
        pdf_convert_request = {
            "inputs": {
                "document": document.as_dict()
            }
        }
        if output_managed_folder is not None:
            pdf_convert_request["outputManagedFolderRef"] = output_managed_folder
            if path_in_output_folder is not None:
                pdf_convert_request["outputFilePath"] = path_in_output_folder
            self._data = self.client._perform_json("POST", "/projects/%s/document-extractors/convert/to-pdf" % self.project_key,
                                                   raw_body={"conversionRequest": json.dumps(pdf_convert_request)},
                                                   files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)
        else:
            self._data = self.client._perform_raw("POST", "/projects/%s/document-extractors/convert/to-pdf/download" % self.project_key,
                                            raw_body={"conversionRequest": json.dumps(pdf_convert_request)},
                                            files={"file": document.file} if isinstance(document, LocalFileDocumentRef) else None)

    def get_raw(self):
        return self._data

    def stream(self):
        """
        Download the converted PDF as a binary stream.

        :returns: The converted PDF file as a binary stream.
        :rtype: :class:`requests.Response`
        """
        self._fail_unless_success()
        if self.output_managed_folder is not None:
            project = self.client.get_project(self.project_key)
            folder = project.get_managed_folder(self.output_managed_folder)
            return folder.get_file(self.document.file_path)
        else:
            return self._data

    def download_to_file(self, path):
        """
        Download the converted PDF to a local file.

        :param path: the path where to download the PDF file
        :type path: str
        :returns: None
        """
        self._fail_unless_success()
        if self.output_managed_folder is not None:
            project = self.client.get_project(self.project_key)
            folder = project.get_managed_folder(self.output_managed_folder)
            file = folder.get_file(self.document.file_path)
            _write_response_content_to_file(file, path)
        else:
            _write_response_content_to_file(self._data, path)

    @property
    def document(self):
        """
        :returns: The reference to the stored PDF if applicable, otherwise None
        :rtype: :class:`ManagedFolderDocumentRef`
        """
        self._fail_unless_success()
        if self.output_managed_folder is None:
            return None
        else:
            document_ref = self._data.get("documentRef")
            managed_folder_ref = document_ref.get("managedFolderRef") or document_ref.get("managedFolderId")
            return ManagedFolderDocumentRef(document_ref.get("filePath"), managed_folder_ref)

    @property
    def success(self):
        """
        :returns: The outcome of the PDF conversion request.
        :rtype: bool
        """
        if self.output_managed_folder:
            return self._data.get("ok")
        else:
            return self._data.ok

    def _fail_unless_success(self):
        if not self.success:
            if self.output_managed_folder:
                error_message = "Document failed to be converted - request failed: {}".format(
                    self._data.get("errorMessage", "An unknown error occurred")
                )
                raise Exception(error_message)
            else:
                self._data.raise_for_status()


class VlmExtractorResponse(object):
    """
    A handle to interact with a VLM extractor result.

    .. important::
        Do not create this class directly, use :meth:`~DocumentExtractor.vlm_extract`
    """

    def __init__(self, data):
        self._data = data

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
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

class FieldsVlmExtractorResponse(object):
    """
    A handle to interact with a VLM fields extraction result.

    .. important::
        Do not create this class directly; use :meth:`~DocumentExtractor.vlm_extract_fields`
    """

    def __init__(self, data, response_parser=None):
        self._data = data
        self._response_parser = response_parser
        self._parsed_fields = None

    def get_raw(self):
        return self._data

    @property
    def success(self):
        """
        :rtype: bool
        """
        return self._data.get("status", "nok") != "nok"

    @property
    def fields(self):
        """
        Fields extracted from the original document.
        Follows the structure of the extraction schema, has only the fields that abide by it.

        :returns: extracted fields.
        :rtype: dict
        """
        self._fail_unless_success()
        return self._data["curatedFields"]

    @property
    def parsed_fields(self):
        """
        Fields extracted from the original document.
        Follows the structure of the extraction schema, has only the fields that abide by it.
        Only available for extraction schema given as a Pydantic model or using Python type hint.

        :returns: extracted fields deserialized into a Pydantic model instance.
        :rtype: pydantic.BaseModel
        """
        self._fail_unless_success()
        if self._parsed_fields is None and self._data["curatedFields"] is not None:
            if not self._response_parser:
                raise Exception("Require extraction schema to be given as a Pydantic model or using Python type hint.")
            else:
                self._parsed_fields = self._response_parser(json.dumps(self._data["curatedFields"]))
        return self._parsed_fields

    @property
    def invalid_fields(self):
        """
        Fields in the extraction schema that the Vision LLM could not extract.
        Follows the structure/hierarchy of the extraction schema, but has only the incorrect or missing fields.

        :rtype: dict
        """
        self._fail_unless_success()
        return self._data["invalidFields"]

    def _fail_unless_success(self):
        if not self.success:
            error_message = "Document failed to be extracted - request failed: {}".format(
                self._data.get("errorMessage", "An unknown error occurred")
            )
            raise Exception(error_message)


class InputRef(object):
    def as_dict(self):
        raise NotImplementedError


class DocumentRef(InputRef):
    """
    A reference to a document file.

    .. important::
        Do not create this class directly, use one of its implementations:
            * :class:`LocalFileDocumentRef` for a local file to be uploaded
            * :class:`ManagedFolderDocumentRef` for a file inside a DSS-managed folder
    """

    def __init__(self, mime_type=None):
        self.type = None
        self.mime_type = mime_type

    def as_dict(self):
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

    def __init__(self, fp, mime_type=None):
        """
         :param fp: File-like object or stream
         :param str mime_type: MIME type of the file, optional
        """
        super(LocalFileDocumentRef, self).__init__(mime_type)
        self.type = "local_file"
        self.file = fp

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

           Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("LocalFileDocumentRef.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        return {
            "type": self.type,
            "mimeType": self.mime_type,
        }


class _TmpDocumentRef(DocumentRef):
    """
    A reference to interact with a document in the tmp/docextraction folder.

    .. important::
        Do not create this class directly, use :meth:`~DocumentExtractor.generate_pages_screenshots` instead.
    """

    def __init__(self, tmp_file_name, original_file_name, mime_type=None):
        """
         :param str tmp_file_name: File name that is returned when the file is uploaded
         :param str original_file_name: File name before upload
         :param str mime_type: MIME type of the file, optional
        """
        super(_TmpDocumentRef, self).__init__(mime_type)
        self.type = "tmp_file"
        self.tmp_file_name = tmp_file_name
        self.original_file_name = original_file_name

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

           Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("_TmpDocumentRef.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        return {
            "type": self.type,
            "tmpFileName": self.tmp_file_name,
            "originalFileName": self.original_file_name,
            "mimeType": self.mime_type,
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

    def __init__(self, file_path, managed_folder_id, mime_type=None):
        """
        :param str file_path: path to the document file inside the managed folder
        :param str managed_folder_id: identifier of the folder containing the file
        :param str mime_type: MIME type of the file, optional
        """
        super(ManagedFolderDocumentRef, self).__init__(mime_type)
        self.type = "managed_folder"
        self.file_path = file_path
        self.managed_folder_ref = managed_folder_id

    @property
    def managed_folder_id(self):
        warnings.warn("ManagedFolderDocumentRef.managed_folder_id is deprecated, please use managed_folder_ref", DeprecationWarning)
        return self.managed_folder_ref

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

           Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("ManagedFolderDocumentRef.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        """
        Get a dictionary representation.

        :rtype: dict
        """
        return {
            "type": self.type,
            "filePath": self.file_path,
            "managedFolderRef": self.managed_folder_ref,
            "mimeType": self.mime_type,
        }


class InlineDocumentRef(DocumentRef):
    CONTENT_TYPE_PLAIN_TEXT = "PLAIN_TEXT"
    CONTENT_TYPE_BASE64_BYTES = "BASE64_BYTES"

    """ A document with content stored in memory.
    """
    def __init__(self, content, content_type, mime_type=None):
        """
        :param str content: contents of the document as text or base64 string
        :param str content_type: either PLAIN_TEXT or BASE64_BYTES
        :param str mime_type: MIME type of the document, optional
        """
        super(InlineDocumentRef, self).__init__(mime_type)
        self.type = "inline_document"
        self.content = content
        self.content_type = content_type

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

            Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        return self.as_dict()

    def as_dict(self):
        """
        Get a dictionary representation.

        :rtype: dict
        """
        return {
            "type": self.type,
            "content": self.content,
            "contentType": self.content_type,
            "mimeType": self.mime_type,
        }

    def is_base64(self):
        return self.content_type == self.CONTENT_TYPE_BASE64_BYTES

    def as_bytes(self):
        assert self.is_base64(), "as_bytes requires the document to be base64-encoded"
        return base64.b64decode(self.content)

    def is_text(self):
        return self.content_type == self.CONTENT_TYPE_PLAIN_TEXT

    def as_string(self):
        assert self.is_text(), "as_string requires the document to be plain text"
        return self.content


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

    def as_dict(self):
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
        """
        Get a dictionary representation.

        .. caution::

            Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("InlineImageRef.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        """
        Get a dictionary representation.

        :rtype: dict
        """
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

        managed_img = ManagedFolderImageRef('managed_folder_ref', 'path_in_folder/image.png')

        # Extract a text summary from the image using a vision LLM:
        resp = doc_ex.vlm_extract([managed_img], 'llm_id')
    """

    def __init__(self, managed_folder_ref, image_path):
        """
        :param str managed_folder_ref: identifier of the folder containing the image
        :param str image_path: path to the image file inside the managed folder
        """
        super(ManagedFolderImageRef, self).__init__()
        self.type = "managed_folder"
        self.managed_folder_ref = managed_folder_ref
        self.image_path = image_path

    @property
    def managed_folder_id(self):
        warnings.warn("ManagedFolderImageRef.managed_folder_id is deprecated, please use managed_folder_ref", DeprecationWarning)
        return self.managed_folder_ref

    def as_json(self):
        """
        Get a dictionary representation.

        .. caution::

            Deprecated, use :meth:`as_dict` instead

        :rtype: dict
        """
        warnings.warn("ManagedFolderImageRef.as_json is deprecated, please use as_dict", DeprecationWarning)
        return self.as_dict()

    def as_dict(self):
        """
        Get a dictionary representation.

        :rtype: dict
        """
        return {
            "type": self.type,
            "managedFolderRef": self.managed_folder_ref,
            "imagePath": self.image_path
        }
