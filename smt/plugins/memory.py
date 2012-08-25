# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - memory plugin.

Classes:
    MemoryPlugin    --- Plugin monitoring memory usage.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import ArchiveGroup, Plugin


__all__ = ["MemoryPlugin"]


class MemoryPlugin(Plugin):
    """
    Plugin monitoring memory usage.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "memory"
    update_interval = 300

    # Descriptions for /proc/stat columns
    _descriptions = {}
    _descriptions["page_tables"] = "Memory used to map between virtual and physical memory addresses."
    _descriptions["swap_cache"] = "Memory that once was swapped out, is swapped back in but still also is in the swapfile."
    _descriptions["slab_cache"] = "Memory used by the kernel (major users are caches like inode, dentry, etc)."
    _descriptions["cache"] = "In-memory cache for files read from the disk (the pagecache)."
    _descriptions["buffers"] = "Relatively temporary storage for raw disk blocks."
    _descriptions["free"] = "Wasted memory. Memory that is not used for anything at all."
    _descriptions["apps"] = "Memory used by user-space applications."
    _descriptions["swap"] = "Memory which has been evicted from RAM, and is temporarily on the disk."

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return MemoryPlugin()

    def __init__(self):
        Plugin.__init__(self)
        for name, description in self._descriptions.items():
            self.add_datasource(name, "GAUGE", description=description, min_=0, archives=[ArchiveGroup(cfs=("AVERAGE",))])

    def _get_meminfo(self):
        data = {}
        with open("/proc/meminfo") as fp:
            for line in fp:
                line = re.split(":?\s+", line)
                data[line[0]] = int(line[1])
        return data

    def read_data(self):
        """
        Read the data from sensors.

        """
        data = self._get_meminfo()
        values = {}
        values["page_tables"] = 1024 * data["PageTables"]
        values["swap_cache"] = 1024 * data["SwapCached"]
        values["slab_cache"] = 1024 * data["Slab"]
        values["cache"] = 1024 * data["Cached"]
        values["buffers"] = 1024 * data["Buffers"]
        values["free"] = data["MemFree"] * 1024
        values["apps"] = 1024 * data["MemTotal"] - values["page_tables"]  - values["swap_cache"] - values["slab_cache"] - values["cache"] - values["buffers"] - values["free"]
        values["swap"] = (data["SwapTotal"] - data["SwapFree"]) * 1024
        return values
