# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - smart plugin.

Classes:
    SmartPlugin     --- Plugin monitoring some raw values of S.M.A.R.T. data.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import call, ArchiveGroup, Plugin


__all__ = ["SmartPlugin"]


class SmartPlugin(Plugin):
    """
    Plugin monitoring some raw values of S.M.A.R.T. data.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Methods:
        read_data   --- Read the data from sensors.

    """

    # Known S.M.A.R.T. column names
    _columns = ("Start_Stop_Count", "Reallocated_Sector_Ct", "Power_On_Hours", "Power_Cycle_Count")

    name = "smart"
    update_interval = 1800

    def __init__(self, drive, columns):
        """
        Arguments:
            drive       --- Name of the drive to monitor (e.g. sda).
            columns     --- Iterable with column names to monitor.

        """
        if re.match("^[a-z0-9]+$", drive, re.I) is None:
            raise ValueError("Invalid drive name {!r}.".format(drive))
        self._drive = "/dev/{}".format(drive)
        self.name = "smart_{}".format(drive)
        Plugin.__init__(self)
        conf = {"min_": 0, "heartbeat": 3*24*3600, "step": 1800, "archives": [ArchiveGroup(cfs=("AVERAGE",), templates=("week", "month", "year"))]}
        description = "{{}} S.M.A.R.T. value for drive {}.".format(drive)
        title = "{} {{}}".format(drive)
        for name in columns:
            if name not in self._columns:
                raise ValueError("Unknown column name {!r}.".format(column))
            column = name.replace("_", " ")
            self.add_datasource(name, "GAUGE", title=title.format(column), description=description.format(drive), **conf)

    def read_data(self):
        """
        Read the data from sensors.

        """
        columns = list(self.datasource_names)
        values = {}
        for row in call("smartctl", "-A", self._drive).split("\n"):
            match = re.match("\s*[0-9]+\s+(\S+)\s*\S+\s*\S+\s*\S+\s*\S+\s*\S+\s*\S+\s*\S+\s*([0-9]+)", row)
            if match is None:
                continue
            name = match.group(1)
            if name not in columns:
                continue
            values[name] = int(match.group(2))
        return values
