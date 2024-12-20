import langchain
import pydantic


def must_use_deprecated_pydantic_config():
    # Pydantic 2 models are supported starting with Pydantic 2 and Langchain 0.3
    return pydantic.__version__[0] < '2' or langchain.__version__[0] == '0' and langchain.__version__[2] < '3'
