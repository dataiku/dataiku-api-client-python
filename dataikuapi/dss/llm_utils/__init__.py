import copy
import json

from six import string_types

from ...utils import DataikuException

_footer_attributes = [
    # usage metadata
    "promptTokens",
    "cacheReadInputTokens",
    "cacheWriteInputTokens",
    "completionTokens",
    "reasoningTokens",
    "totalTokens",
    "totalUsage",
    "tokenCountsAreEstimated",
    "estimatedCost",
    # specific to SimpleCompletionResponse
    "finishReason",
    "additionalInformation",
    "trace",
    "contextUpsert",
]

def get_json_schema_and_parser(schema):
    """
    Build JSON schema + parser from str, dict, Pydantic model or Python type hint.
    str/dict input must be a valid json schema, returned parser is then None.
    
    :rtype: Tuple[str, Optional[Callable[[str], Any]]]
    """
    if isinstance(schema, string_types) and schema:  # schema given directly as string
        return schema, None
    elif isinstance(schema, dict):
        return json.dumps(schema), None
    else:  # schema might be given as a pydantic model :
        json_schema, parser_method = _get_json_schema_and_parser_from_pydantic_model(schema)
        return json.dumps(json_schema), parser_method

def _get_json_schema_and_parser_from_pydantic_model(model_type):
    """
    Build JSON schema and response parser from a Pydantic model or Python type hint.

    :param model_type: Pydantic BaseModel class or Python type hint.
    :rtype: Tuple[dict, Callable[[str], Any]]
    """
    if hasattr(model_type, "model_json_schema") and hasattr(model_type, "model_validate_json"):
        # Pydantic 2 BaseModel
        return model_type.model_json_schema(), model_type.model_validate_json
    elif hasattr(model_type, "schema") and hasattr(model_type, "parse_raw"):
        # Pydantic 1 BaseModel
        return model_type.schema(), model_type.parse_raw
    else:
        # 'model_type' is not a Pydantic BaseModel. Derive schema from Python type hints.
        try:
            import pydantic
        except ImportError:
            raise Exception("Pydantic is required to use Python's type hints with structured output")

        if hasattr(pydantic, "TypeAdapter"):
            # Pydantic 2 provides a TypeAdapter to work with regular Python classes / type hints
            from pydantic import TypeAdapter
            adapter = TypeAdapter(model_type)
            return adapter.json_schema(), adapter.validate_json
        elif hasattr(pydantic, "schema_of") and hasattr(pydantic, "parse_obj_as"):
            # Pydantic 1 had similar functionality via 'schema_of' and 'parse_obj_as'
            schema = pydantic.schema_of(model_type)

            def response_parser(json_response):
                parsed_json = json.loads(json_response)
                return pydantic.parse_obj_as(model_type, parsed_json)

            return schema, response_parser
        else:
            # Unsupported Pydantic version
            raise Exception("Incompatible Pydantic version")


class LLMException(DataikuException):
    def __init__(self, error_message, error_code=None, error_type=None, error_source=None):
        error_message = "%s" % (error_message or "An unknown error occurred")
        super(LLMException, self).__init__(error_message)
        self.error_message = error_message
        self.error_code = error_code
        self.error_type = error_type
        self.error_source = error_source


def _stream_from_single_response(response):
    chunk = {}
    for key in ["text", "logProbs", "toolCalls", "toolValidationRequests", "memoryFragment"]:
        if key in response and response[key]:
            chunk[key] = response[key]
    if chunk:
        chunk["type"] = "content"
        yield {"chunk": chunk}

    if "artifacts" in response and response["artifacts"]:
        yield {"chunk" : {"type": "content", "artifacts": response["artifacts"]} }

    footer = {}
    for key in _footer_attributes:
        if key in response and response[key]:
            footer[key] = response[key]
    if footer:
        footer["type"] = "footer"
        yield {"footer": footer}


def _process_tool_call_chunk(tool_call_chunk, tool_calls_map, tool_calls_list):
    if "index" not in tool_call_chunk or tool_call_chunk["index"] is None:
        # tool call does not have an index, we won't be able to aggregate chunks, so assume it's full
        tool_calls_list.append(tool_call_chunk)

    else:
        index = tool_call_chunk["index"]

        if index not in tool_calls_map:
            # tool call not yet in map: insert it
            tool_calls_map[index] = tool_call_chunk

        else:
            # tool call already in map: update it
            tool_call = tool_calls_map[index]
            if ("type" not in tool_call or not tool_call["type"]) and ("type" in tool_call_chunk and tool_call_chunk["type"]):
                tool_call["type"] = tool_call_chunk["type"]
            if ("id" not in tool_call or tool_call["id"] is None) and ("id" in tool_call_chunk and tool_call_chunk["id"] is not None):
                tool_call["id"] = tool_call_chunk["id"]

            if "function" in tool_call_chunk and tool_call_chunk["function"]:
                chunk_function_info = tool_call_chunk["function"]
                if "function" not in tool_call or not tool_call["function"]:
                    # function info not already listed: insert it
                    tool_call["function"] = chunk_function_info
                else:
                    # function info already listed: update it
                    function_info = tool_call["function"]
                    if ("name" not in function_info or not function_info["name"]) and ("name" in chunk_function_info and chunk_function_info["name"]):
                        function_info["name"] = chunk_function_info["name"]

                    if "arguments" in chunk_function_info and chunk_function_info["arguments"]:
                        if "arguments" not in function_info or function_info["arguments"] is None:
                            function_info["arguments"] = ""
                        function_info["arguments"] += chunk_function_info["arguments"]


def _process_artifact_chunk(
        incoming_artifact,
        artifacts_map,
        artifacts_list
):
    """
    Processes a single artifact chunk, aggregating it into the
    artifacts_map (for streamable artifacts) or artifacts_list
    (for non-streamable artifacts).
    This method should be kept in sync with StreamingConsumer.java, method updateCompleteArtifacts
    """
    artifact_id = incoming_artifact.get("id")

    # If artifact has no ID, it's not streamable.
    if not artifact_id:
        artifacts_list.append(incoming_artifact)
        return

    # Artifact is streamable (has an ID).
    if artifact_id not in artifacts_map:
        # First time seeing this artifact, add it to the map.
        artifacts_map[artifact_id] = incoming_artifact
        return

    # --- Artifact already exists, merge the new chunk ---
    existing_artifact = artifacts_map[artifact_id]

    # 1. Update top-level metadata
    if incoming_artifact.get("name") is not None:
        existing_artifact["name"] = incoming_artifact["name"]
    if incoming_artifact.get("description") is not None:
        existing_artifact["description"] = incoming_artifact["description"]
    if incoming_artifact.get("type") is not None:
        existing_artifact["type"] = incoming_artifact["type"]

    # 2. Process and merge parts
    if not incoming_artifact.get("parts"):
        return

    if "parts" not in existing_artifact:
        existing_artifact["parts"] = []

    for incoming_part in incoming_artifact["parts"]:
        part_index = incoming_part.get("index")

        if part_index is None:
            existing_artifact["parts"].append(incoming_part)
            continue

        existing_part = None
        for part in existing_artifact["parts"]:
            if part.get("index") == part_index:
                existing_part = part
                break  # Found the part

        if not existing_part:
            existing_artifact["parts"].append(incoming_part)
        else:
            if incoming_part.get("type") == "TEXT":
                if incoming_part.get("text"):
                    existing_part["text"] = existing_part.get("text", "") + incoming_part["text"]
            else:
                existing_artifact["parts"].append(incoming_part)
                existing_artifact["parts"].remove(existing_part)


class _BaseChunkAggregator(object):
    def __init__(self):
        self._response = None
        self.chunk_data = {}
        self.footer_data = {}
        self.response_data = {}
        self.error_data = None

        self.text_chunks = []
        self.tool_calls_map = {}
        self.tool_calls_list = []
        self.tool_validation_requests_list = []
        self.log_probs = []
        self.artifacts_map = {}
        self.artifacts_list = []

    def _extract_data_from_chunk(self, res):
        chunk = res.get("chunk")
        footer = res.get("footer")
        response_data = res.get("responseData")
        if chunk:
            # text
            if "text" in chunk and chunk["text"]:
                self.text_chunks.append(chunk["text"])

            # artifact
            if "artifacts" in chunk and chunk["artifacts"]:
                for chunk_artifact in chunk["artifacts"]:
                    _process_artifact_chunk(chunk_artifact, self.artifacts_map, self.artifacts_list)

            # toolCalls
            if "toolCalls" in chunk and chunk["toolCalls"]:
                for tool_call_chunk in chunk["toolCalls"]:
                    _process_tool_call_chunk(tool_call_chunk, self.tool_calls_map, self.tool_calls_list)

            # toolValidationRequests
            if "toolValidationRequests" in chunk and chunk["toolValidationRequests"]:
                self.tool_validation_requests_list.extend(chunk["toolValidationRequests"])

            # logProbs
            if "logProbs" in chunk and chunk["logProbs"]:
                self.log_probs.extend(chunk["logProbs"])

            # memoryFragment
            if "memoryFragment" in chunk and chunk["memoryFragment"]:
                self.chunk_data["memoryFragment"] = chunk["memoryFragment"]

        if footer:
            for key in _footer_attributes:
                if key in footer and footer[key]:
                    self.footer_data[key] = footer[key]

        if response_data:
            self.response_data.update(response_data)

    @property
    def response(self):
        if self._response is None:
            raise Exception("The consolidated response is not available yet because the stream of chunks hasn't been entirely processed")
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def _build_response(self):
        try:
            self._response = {}
            self._response.update(self.footer_data)
            self._response.update(self.response_data)

            if self.error_data is not None:
                self._response["ok"] = False
                self._response.update(self.error_data)
                return

            self._response["ok"] = True
            self._response.update(self.chunk_data)

            if self.text_chunks:
                self._response["text"] = "".join(self.text_chunks)
            if self.tool_calls_map:
                self.tool_calls_list.extend(self.tool_calls_map.values())
            if self.tool_calls_list:
                self._response["toolCalls"] = self.tool_calls_list
            if self.tool_validation_requests_list:
                self._response["toolValidationRequests"] = self.tool_validation_requests_list
            if self.log_probs:
                self._response["logProbs"] = self.log_probs
            if self.artifacts_map:
                self.artifacts_list.extend(self.artifacts_map.values())
            if self.artifacts_list and len(self.artifacts_list) > 0:
                self._response["artifacts"] = self.artifacts_list
        except Exception as e:
            self._response = e


class _ChunkAggregator(_BaseChunkAggregator):
    def __init__(self, producer):
        super().__init__()
        self._generator = self._iter(producer)

    def _iter(self, producer):
        try:
            for res in producer:
                self._extract_data_from_chunk(res)
                yield copy.deepcopy(res)
            self._build_response()
        except LLMException as llm_exception:
            self.error_data = {}
            if llm_exception.error_message:
                self.error_data["errorMessage"] = llm_exception.error_message
            if llm_exception.error_code:
                self.error_data["errorCode"] = llm_exception.error_code
            if llm_exception.error_source:
                self.error_data["errorSource"] = llm_exception.error_source
            if llm_exception.error_type:
                self.error_data["errorType"] = llm_exception.error_type
            self._build_response()
            raise

    def __next__(self):
        return next(self._generator)

    def send(self, *args, **kwargs):
        return self._generator.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self._generator.throw(*args, **kwargs)

    def close(self):
        return self._generator.close()

    def __iter__(self):
        return self
