import logging
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional, Callable, Literal, Type, Any, Dict
from pydantic import BaseModel
from dataiku.langchain.dku_tracer import dku_span_builder_for_callbacks
class DKUStructuredTool(StructuredTool):
    
    @property
    def tool_call_schema(self):
        return self.get_input_schema()

    @classmethod
    def dku_from_function(
        cls,
        func: Optional[Callable] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        return_direct: bool = False,
        args_schema: Optional[Type[BaseModel]] = None,
        infer_schema: bool = True,
        *,
        response_format: Literal["content", "content_and_artifact"] = "content",
        parse_docstring: bool = False,
        error_on_invalid_docstring: bool = False,
        **kwargs: Any,
    ) -> StructuredTool:
        """Create tool from a given function.

        A classmethod that helps to create a tool from a function.

        Args:
            func: The function from which to create a tool.
            coroutine: The async function from which to create a tool.
            name: The name of the tool. Defaults to the function name.
            description: The description of the tool.
                Defaults to the function docstring.
            return_direct: Whether to return the result directly or as a callback.
                Defaults to False.
            args_schema: The schema of the tool's input arguments. Defaults to None.
            infer_schema: Whether to infer the schema from the function's signature.
                Defaults to True.
            response_format: The tool response format. If "content" then the output of
                the tool is interpreted as the contents of a ToolMessage. If
                "content_and_artifact" then the output is expected to be a two-tuple
                corresponding to the (content, artifact) of a ToolMessage.
                Defaults to "content".
            parse_docstring: if ``infer_schema`` and ``parse_docstring``, will attempt
                to parse parameter descriptions from Google Style function docstrings.
                Defaults to False.
            error_on_invalid_docstring: if ``parse_docstring`` is provided, configure
                whether to raise ValueError on invalid Google Style docstrings.
                Defaults to False.
            kwargs: Additional arguments to pass to the tool

        Returns:
            The tool.

        Raises:
            ValueError: If the function is not provided.

        Examples:

            .. code-block:: python

                def add(a: int, b: int) -> int:
                    \"\"\"Add two numbers\"\"\"
                    return a + b
                tool = StructuredTool.from_function(add)
                tool.run(1, 2) # 3
        """

        if func is not None:
            source_function = func
        elif coroutine is not None:
            source_function = coroutine
        else:
            raise ValueError("Function and/or coroutine must be provided")
        name = name or source_function.__name__
        if args_schema is None and infer_schema:
            # schema name is appended within function
            args_schema = create_schema_from_function(
                name,
                source_function,
                parse_docstring=parse_docstring,
                error_on_invalid_docstring=error_on_invalid_docstring,
                filter_args=_filter_schema_args(source_function),
            )
        description_ = description
        if description is None and not parse_docstring:
            description_ = source_function.__doc__ or None
        if description_ is None and args_schema:
            description_ = args_schema.__doc__ or None
        if description_ is None:
            raise ValueError(
                "Function must have a docstring if description not provided."
            )
        if description is None:
            # Only apply if using the function's docstring
            description_ = textwrap.dedent(description_).strip()

        # Description example:
        # search_api(query: str) - Searches the API for the query.
        description_ = f"{description_.strip()}"
        return cls(
            name=name,
            func=func,
            #coroutine=coroutine,
            args_schema=args_schema,  # type: ignore[arg-type]
            description=description_,
            return_direct=return_direct,
            response_format=response_format,
            **kwargs,
        )

def convert_to_langchain_structured_tool(dku_tool, context = None):
    from langchain.tools import BaseTool, StructuredTool, tool
    from dataikuapi.dss.langchain.tool import DKUStructuredTool

    desc = dku_tool.get_descriptor()

    tool_context = context

    def run_tool_func(callbacks = None, *args, **kwargs):
        #logging.debug("run_tool_func args=%s" % (args,))
        #logging.debug("run_tool_func kwargs=%s" % (kwargs,))
        #logging.debug("run_tool_func callbacks=%s" % (callbacks))

        with dku_span_builder_for_callbacks(callbacks, ignore_missing=True).subspan("DKUStructuredTool") as s:
            tool_output =  dku_tool.run(input=kwargs, context=tool_context)

            # Split into output for LLM and artifact

            if "trace" in tool_output:
                s.append_trace(tool_output["trace"])

            ret = (tool_output["output"], {
                #"trace": tool_output.get("trace", None),
                "sources": tool_output.get("sources", None)
            })

            return ret

    # LangChain does not have the concept of dynamically defining a tool schema without Pydantic
    # And Pydantic does not have a concept of dynamically defining a model from a JSON schema
    # so we must fake everything
    from pydantic import BaseModel
    class FakeModel(BaseModel):
        dku_dict: Dict = None

        #def __init__(self, obj):
        #    self._dict = obj

        # Pydantic < 2 -> LangChain uses parse_obj + dict
        @classmethod
        def parse_obj(cls, obj):
            ret = FakeModel()
            setattr(ret, "dku_dict", obj)# = obj
            return ret
        def dict(self):
            return self.dku_dict

        # Pydantic >= 2 -> Langchain uses model_validate + model_dump
        @classmethod
        def model_validate(cls, obj):
            ret = FakeModel()
            setattr(ret, "dku_dict", obj)# = obj
            return ret
        def model_dump(self):
            return self.dku_dict

        def __getattr__(self, attr):
            return self.dku_dict[attr]

        def schema():
            return desc["inputSchema"]

        def model_json_schema():
            return desc["inputSchema"]                

    tool = DKUStructuredTool.dku_from_function(func = run_tool_func,
                name = desc["name"],
                description = desc["description"],
                args_schema = FakeModel,
                response_format="content_and_artifact"
                    )

    return tool