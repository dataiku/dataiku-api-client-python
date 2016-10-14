#!/usr/bin/env python

from setuptools import setup

VERSION = "3.1.2"

setup(
    name = 'dataiku-api-client',
    version = VERSION,
    license = "Apache Software License",
    packages = ["dataikuapi", "dataikuapi.dss", "dataikuapi.apinode_admin"],
    description = "Python API client for Dataiku APIs",
    author = "Dataiku",
    author_email = "support@dataiku.com",
    url = "https://www.dataiku.com",
    download_url = "https://github.com/dataiku/dataiku-api-client-python/tarball/" + VERSION,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python',
        'Operating System :: OS Independent'
    ],
    install_requires = [
        "requests",
        "python-dateutil"
    ]
)
