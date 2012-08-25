# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - hddtemp plugin.

Classes:
    HDDTempPlugin   --- Plugin monitoring HDD temperatures.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.core import call, Plugin


__all__ = ["HDDTempPlugin"]


class HDDTempPlugin(Plugin):
    """
    Plugin monitoring HDD temperatures.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "hddtemp"
    update_interval = 300

    def __init__(self, drives):
        """
        Arguments:
            drives          --- List of drives to monitor, e.g. ("/dev/sda", "SATA:/dev/sdb").

        """
        Plugin.__init__(self)
        for drive in drives:
            drive_name = drive.split(":")[-1]
            self.add_datasource(drive, "GAUGE", title=drive_name, description="Temperature of drive {}.".format(drive_name))

    def read_data(self):
        """
        Read the data from sensors.

        """
        drives = list(sorted(self.datasource_names))
        command = ["hddtemp", "-q", "-n"] + drives
        result = call(*command).split("\n")
        values = {}
        for i in range(len(drives)):
            values[drives[i]] = float(result[i])
        return values
