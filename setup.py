#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

from smt import __version__ as version

setup(
    name = "smt",
    version = version,
    description = "Simple Monitoring Tool",
    author = "Petr Morávek",
    author_email = "xificurk@gmail.com",
    license = "LGL-3",
    url = "http://github.com/xificurk/smt",
    packages = ["smt", "smt.plugins"],
    long_description = """
SMT is library for monitoring of various sensor data.
Gathered data are stored in the form of RRD files.
    """,
)
