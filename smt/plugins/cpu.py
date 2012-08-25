# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - cpu plugin.

Classes:
    CPUPlugin    --- Plugin monitoring CPU activity.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import multiprocessing
import re
from smt.core import ArchiveGroup, Plugin


__all__ = ["CPUPlugin"]


class CPUPlugin(Plugin):
    """
    Plugin monitoring CPU activity.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.
        user_hz     --- USER_HZ unit for reading from /proc/stat.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "cpu"
    update_interval = 300

    # USER_HZ unit for reading from /proc/stat.
    user_hz = 100

    # /proc/stat column names
    _columns = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest")

    # Descriptions for /proc/stat columns
    _descriptions = {}
    _descriptions["user"] = "CPU time spent by normal programs and daemons."
    _descriptions["nice"] = "CPU time spent by nice(1)d programs."
    _descriptions["system"] = "CPU time spent by the kernel in system activities."
    _descriptions["idle"] = "Idle CPU time."
    _descriptions["iowait"] = "CPU time spent waiting for I/O operations to finish when there is nothing else to do."
    _descriptions["irq"] = "CPU time spent handling interrupts."
    _descriptions["softirq"] = "CPU time spent handling \"batched\" interrupts."
    _descriptions["steal"] = "CPU time that a virtual CPU had runnable tasks, but the virtual CPU itself was not running."
    _descriptions["guest"] = "CPU time spent running a virtual CPU for guest operating systems under the control of the Linux kernel."

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return CPUPlugin()

    def __init__(self):
        Plugin.__init__(self)
        max_ = multiprocessing.cpu_count()*100
        for name, description in self._descriptions.items():
            self.add_datasource(name, "COUNTER", description=description, min_=0, max_=max_, archives=[ArchiveGroup(cfs=("AVERAGE",))])

    def read_data(self):
        """
        Read the data from sensors.

        """
        values = {}
        with open("/proc/stat") as fp:
            data = fp.readline()
        data = re.split("\s+", data)
        data.pop(0)
        for i in range(len(self._columns)):
            if len(data) <= i:
                break
            values[self._columns[i]] = int(round(int(data[i]) * 100 / self.user_hz))
        return values
