# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - loadavg plugin.

Classes:
    LoadAvgPlugin   --- Plugin monitoring system load.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.core import Plugin


__all__ = ["LoadAvgPlugin"]


class LoadAvgPlugin(Plugin):
    """
    Plugin monitoring system load.

    By default monitors only 5min load average. If you want to monitor 1min load
    average, consider changing update_interval.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    # Available load average intervals.
    _intervals = ("1min", "5min", "15min")

    name = "loadavg"
    update_interval = 300

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return LoadAvgPlugin()

    def __init__(self, intervals=("5min",)):
        """
        Keyworded arguments:
            intervals       --- Load average intervals to monitor (1min, 5min, 15min).

        """
        Plugin.__init__(self)
        for interval in intervals:
            if interval not in self._intervals:
                raise ValueError("Invalid load average interval {!r}.".format(interval))
            self.add_datasource(interval, "GAUGE", min_=0, title="{} load".format(interval), description="{} system load average.".format(interval))

    def read_data(self):
        """
        Read the data from sensors.

        """
        with open("/proc/loadavg", "r") as fp:
            data = fp.read()
        data = data.split("\n")[0].split(" ")[0:3]
        return {"1min": data[0], "5min": data[1], "15min": data[2]}
