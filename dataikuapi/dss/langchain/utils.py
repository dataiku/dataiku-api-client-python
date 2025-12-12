def must_use_deprecated_pydantic_config():
    # Pydantic 2 models are supported starting with Pydantic 2 and Langchain 0.3
    try:
        import langchain_core
        import pydantic
        return str(pydantic.__version__[0]) < '2' or not hasattr(langchain_core, "__version__") or str(langchain_core.__version__[0]) == '0' and str(langchain_core.__version__[2]) < '3'
    except ModuleNotFoundError:
        return False
