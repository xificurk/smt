# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - df plugin.

Classes:
    DfPlugin        --- Plugin monitoring free/used space on partitions.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import call, ArchiveGroup, Plugin


__all__ = ["DfPlugin"]


class DfPlugin(Plugin):
    """
    Plugin monitoring free/used space on partitions.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.
        exclude     --- Partition types to exclude when autoconfiguring.
        warning     --- Lower warning limit as portion of total capacity for autoconfiguration.
        critical    --- Lower critical limit as portion of total capacity for autoconfiguration.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "df"
    update_interval = 900

    # Partition types to exclude when autoconfiguring.
    exclude = set(("none", "unknown", "iso9660", "squashfs", "udf", "romfs", "ramfs", "tmpfs", "devtmpfs", "rootfs"))

    # Lower warning limit as portion of total capacity for autoconfiguration.
    warning = 0.1

    # Lower critical limit as portion of total capacity for autoconfiguration.
    critical = 0.05

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        data = cls._get_data()
        partitions = list(data.keys())
        plugin = DfPlugin(partitions)
        for name, value in data.items():
            capacity = value[0]
            datasource = plugin.get_datasource(name)
            datasource.warning = "{:.0f}:".format(capacity * cls.warning)
            datasource.critical = "{:.0f}:".format(capacity * cls.critical)
            datasource.max_ = capacity

    @classmethod
    def _get_data(cls, partitions=None):
        values = {}
        command = ["df", "-l", "-B1"]
        if partitions is None:
            for part in cls.exclude:
                command.append("-x")
                command.append(part)
        else:
            command += list(partitions)
        for row in call(*command).split("\n")[1:]:
            row = re.split("\s+", row)
            if len(row) != 6 or row[5].startswith("/media/"):
                continue
            values[row[5]] = (row[1], row[2], row[3])
        return values

    def __init__(self, partitions, used_space=False, percentage=False):
        """
        Arguments:
            partitions      --- Dictionary with partitions to monitor and their datasource config.

        Keyworded arguments:
            used_space      --- Report used space rather than free space.
            percentage      --- Report values as percentage of total capacity.

        """
        self._used_space = used_space
        self._percentage = percentage
        conf = {"min_": 0, "heartbeat": 3*24*3600, "step": 900, "archives": [ArchiveGroup(templates=("week", "month", "year"))]}
        description = "{{}} of {} space on {{{{}}}}."
        if used_space:
            self.name += "_used"
            description = description.format("used")
        else:
            self.name += "_free"
            description = description.format("free")
        if percentage:
            self.name += "_percent"
            description = description.format("Percentage")
            conf["max_"] = 100
        else:
            self.name += "_absolute"
            description = description.format("Amount")
        Plugin.__init__(self)
        for partition in partitions:
            self.add_datasource(partition, "GAUGE", description=description.format(partition), **conf)

    def read_data(self):
        """
        Read the data from sensors.

        """
        partitions = self.datasource_names
        values = {}
        for name, value in self._get_data(partitions).items():
            if name not in partitions:
                continue
            if self._used_space:
                values[name] = value[1]
            else:
                values[name] = value[2]
            if self._percentage:
                values[name] = values[name] / value[0] * 100
        return values
