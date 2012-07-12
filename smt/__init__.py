# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library.

Submodules:
    core    --- Core SMT functionality.
    plugins --- Basic set of plugins.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"

__version__ = "0.1.0"


import smt.core as core
import smt.plugins as plugins

import logging
logging.getLogger("").addHandler(logging.NullHandler())