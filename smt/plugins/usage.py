# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - usage plugin.

Classes:
    UsagePlugin     --- Plugin monitoring the usage of the machine.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.core import ArchiveGroup, Plugin


__all__ = ["UsagePlugin"]


class UsagePlugin(Plugin):
    """
    Plugin monitoring the usage of the machine.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "usage"
    update_interval = 120

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return UsagePlugin()

    def __init__(self):
        Plugin.__init__(self)
        self.add_datasource("uptime", "GAUGE", min_=0, max_=1, unknown=0, archives=[ArchiveGroup(cfs=("AVERAGE",))], title="Uptime", description="Uptime ratio.")

    def read_data(self):
        """
        Read the data from sensors.

        """
        return {"uptime": 1}
