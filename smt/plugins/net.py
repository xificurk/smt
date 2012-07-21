# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - nettraffic plugin.

Classes:
    NetTrafficPlugin    --- Plugin monitoring network traffic.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import Plugin


__all__ = ["NetTrafficPlugin"]


class NetTrafficPlugin(Plugin):
    """
    Plugin monitoring network traffic.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "net_traffic"
    update_interval = 120

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        interfaces = set(cls._get_data().keys())
        interfaces.discard("lo")
        return NetTrafficPlugin(interfaces)

    @classmethod
    def _get_data(cls):
        values = {}
        with open("/proc/net/dev") as fp:
            fp.readline()
            fp.readline()
            for line in fp:
                line = re.split(":?\s+", line.strip())
                name = line[0]
                values[name] = (int(line[1]), int(line[9]))
        return values

    def __init__(self, interfaces):
        """
        Arguments:
            interfaces  --- Names of interfaces to monitor.

        """
        Plugin.__init__(self)
        for interface in interfaces:
            name = "{}:in".format(interface)
            title = "{} in".format(interface)
            description = "Incoming traffic on interface {}.".format(interface)
            self.add_datasource(name, "COUNTER", title=title, description=description, min_=0, unknown=0)
            name = "{}:out".format(interface)
            title = "{} out".format(interface)
            description = "Outgoing traffic on interface {}.".format(interface)
            self.add_datasource(name, "COUNTER", title=title, description=description, min_=0, unknown=0)

    def read_data(self):
        """
        Read the data from sensors.

        """
        interfaces = set((name.split(":", 1)[0] for name in self.datasource_names))
        values = {}
        for name, value in self._get_data().items():
            if name not in interfaces:
                continue
            values[name + ":in"] = value[0]
            values[name + ":out"] = value[1]
        return values
