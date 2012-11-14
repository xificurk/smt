# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - basic set of plugins.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.plugins.auth import AuthFailPlugin
from smt.plugins.cpu import CPUPlugin
from smt.plugins.df import DfPlugin
from smt.plugins.hddtemp import HDDTempPlugin
from smt.plugins.loadavg import LoadAvgPlugin
from smt.plugins.memory import MemoryPlugin
from smt.plugins.net import NetTrafficPlugin
from smt.plugins.nvidia import NvidiaTempPlugin
from smt.plugins.sensors import SensorsPlugin
from smt.plugins.smart import SmartPlugin
from smt.plugins.users import UsersPlugin
from smt.plugins.usage import UsagePlugin


__all__ = ["AuthFailPlugin",
           "CPUPlugin",
           "DfPlugin",
           "HDDTempPlugin",
           "LoadAvgPlugin",
           "MemoryPlugin",
           "NetTrafficPlugin",
           "NvidiaTempPlugin",
           "SensorsPlugin",
           "SmartPlugin",
           "UsersPlugin",
           "UsagePlugin",
          ]