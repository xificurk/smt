# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - basic set of plugins.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.plugins.cpu import CPUPlugin
from smt.plugins.df import DfPlugin
from smt.plugins.hddtemp import HDDTempPlugin
from smt.plugins.loadavg import LoadAvgPlugin
from smt.plugins.net import NetTrafficPlugin
from smt.plugins.nvidia import NvidiaTempPlugin
from smt.plugins.sensors import SensorsPlugin
from smt.plugins.smart import SmartPlugin
from smt.plugins.users import UsersPlugin
from smt.plugins.usage import UsagePlugin


__all__ = ["CPUPlugin",
           "DfPlugin",
           "HDDTempPlugin",
           "LoadAvgPlugin",
           "NetTrafficPlugin",
           "NvidiaTempPlugin",
           "SensorsPlugin",
           "SmartPlugin",
           "UsersPlugin",
           "UsagePlugin",
          ]