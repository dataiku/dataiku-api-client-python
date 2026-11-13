#
# Vendored from requests-toolbelt.
# Source: https://github.com/requests/toolbelt/tree/1.0.0
# License: Apache-2.0
# Modified from upstream by Dataiku.
#
"""Private module full of compatibility hacks.

Primarily this is for downstream redistributions of requests that unvendor
urllib3 without providing a shim.

.. warning::

    This module is private. If you use it, and something breaks, you were
    warned
"""

# Not used:
# import requests

try:
    from requests.packages.urllib3 import fields
except ImportError:
    from urllib3 import fields

# Not used:
# try:
#     from requests.packages.urllib3.connection import HTTPConnection
#     from requests.packages.urllib3 import connection
# except ImportError:
#     try:
#         from urllib3.connection import HTTPConnection
#         from urllib3 import connection
#     except ImportError:
#         HTTPConnection = None
#         connection = None

# Not used:
# if requests.__build__ < 0x020300:
#     timeout = None
# else:
#     try:
#         from requests.packages.urllib3.util import timeout
#     except ImportError:
#         from urllib3.util import timeout

# Not used:
# import sys
# PY3 = sys.version_info > (3, 0)

# Not used:
# if PY3:
#     from collections.abc import Mapping, MutableMapping
#     import queue
#     from urllib.parse import urlencode, urljoin
# else:
#     from collections import Mapping, MutableMapping
#     import Queue as queue
#     from urllib import urlencode
#     from urlparse import urljoin

# Not used:
# try:
#     basestring = basestring
# except NameError:
#     basestring = (str, bytes)
