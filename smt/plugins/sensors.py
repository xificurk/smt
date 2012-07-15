# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - sensors plugin.

Classes:
    SensorsPlugin   --- Plugin monitoring temperatures from sensors tool.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import call, Plugin


__all__ = ["SensorsPlugin"]


class SensorsPlugin(Plugin):
    """
    Plugin monitoring temperatures from sensors tool.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "sensors"
    update_interval = 120

    def __init__(self, temperatures):
        """
        Arguments:
            temperatures    --- List of temperature sensors to monitor.

        """
        Plugin.__init__(self)
        for sensor in temperatures:
            self.add_datasource("temp_{}".format(sensor), "GAUGE", title=sensor, description="Temperature of sensor {}.".format(sensor))

    def read_data(self):
        """
        Read the data from sensors.

        """
        temperatures = self.datasource_names
        values = {}
        for row in call("sensors", "-A").split("\n"):
            match = re.match("([^: ][^:]*):\s+\+([0-9.]+) C\s+", row)
            if match is None:
                continue
            name = "temp_{}".format(match.group(1))
            if name not in temperatures:
                continue
            values[name] = float(match.group(2))
        return values