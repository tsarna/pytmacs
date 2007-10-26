#!/usr/bin/env python
"""Distutils setup file"""

from ez_setup import use_setuptools
use_setuptools()
    
import sys, os
from setuptools import setup, Extension, Feature, find_packages

# Metadata
PACKAGE_NAME = "TMACS"
PACKAGE_VERSION = "2.0dev5"

extensions = [
    Extension("tmacs.termioscap._tclayer",
        ["tmacs/termioscap/_tclayer.c"],
#        define_macros=[('XML_STATIC',1),('HAVE_MEMMOVE',1)]   # XXX
        libraries=['termcap'],
    ),
    Extension("tmacs.edit.ubuf",
        ["tmacs/edit/ubuf.c", "tmacs/edit/marker.c"]
    ),
]

setup(
    name=PACKAGE_NAME,
    version=PACKAGE_VERSION,

    description="TMACS text editor",
    author="Ty Sarna",
    author_email="tsarna@sarna.org",
#    url="http://www.sarna.org/",
    license="BSD",

    test_suite = 'test_tmacs',
    packages  = find_packages(),
    ext_modules = extensions
)
