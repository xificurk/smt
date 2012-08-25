# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - nvidia plugin.

Classes:
    NvidiaTempPlugin   --- Plugin monitoring temperatures from nvidia-smi tool.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import os
import re
from smt.core import call, Plugin


__all__ = ["NvidiaTempPlugin"]


os.environ["PATH"] = "{}:/opt/bin".format(os.environ["PATH"])


class NvidiaTempPlugin(Plugin):
    """
    Plugin monitoring temperatures from nvidia-smi tool.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "nvidia"
    update_interval = 120

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        temperatures = list(cls._get_temps().keys())
        return NvidiaTempPlugin(temperatures)

    @classmethod
    def _get_temps(cls):
        values = {}
        command = ["nvidia-smi", "-q", "-d", "TEMPERATURE"]
        result = call(*command).split("\n")
        # Find temperature section
        for i in range(len(result)):
            if re.match("\s*Temperature\s*", result[i]) is not None:
                break
        for j in range(i+1, len(result)):
            match = re.match("\s*([^:]+?)\s*:\s*([0-9]+) C", result[j], re.I)
            if match is None:
                break
            name = match.group(1)
            values[name] = float(match.group(2))
        return values

    def __init__(self, temperatures):
        """
        Arguments:
            temperatures    --- List of temperature nvidia sensors to monitor.

        """
        Plugin.__init__(self)
        for sensor in temperatures:
            self.add_datasource(sensor, "GAUGE", description="Temperature of nvidia sensor {}.".format(sensor))

    def read_data(self):
        """
        Read the data from sensors.

        """
        temperatures = self.datasource_names
        values = {}
        for name, value in self._get_temps().items():
            if name not in temperatures:
                continue
            values[name] = value
        return values