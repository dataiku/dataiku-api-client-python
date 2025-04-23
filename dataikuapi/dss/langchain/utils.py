import langchain
import pydantic


def must_use_deprecated_pydantic_config():
    # Pydantic 2 models are supported starting with Pydantic 2 and Langchain 0.3
    return str(pydantic.__version__[0]) < '2' or not hasattr(langchain, "__version__") or str(langchain.__version__[0]) == '0' and str(langchain.__version__[2]) < '3'
