# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - auth plugin.

Classes:
    AuthFailPlugin      --- Plugin monitoring authentication failures.

"""

__author__ = "Petr Morávek (petr@pada.cz)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


import re
from smt.core import Plugin, ArchiveGroup


__all__ = ["AuthFailPlugin"]


class AuthFailPlugin(Plugin):
    """
    Plugin monitoring authentication failures.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.
        log_file    --- Path to log file.
        encoding    --- Encoding of the log file.
        warning     --- Warning limit for total rate of authentication failures.
        critical    --- Critical limit for total rate of authentication failures.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "auth_fail"
    update_interval = 300

    # Path to log file.
    log_file = "/var/log/auth.log"
    # Encoding of the log file.
    encoding = "utf-8"

    # Warning limit for total rate of authentication failures.
    warning = "0.02"

    # Critical limit for total rate of authentication failures.
    critical = "0.1"

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return AuthFailPlugin()

    def __init__(self, methods=("su", "login", "sshd")):
        """
        Arguments:
            methods     --- Authentication methods to monitor, the rest goes to 'other'.

        """
        Plugin.__init__(self)
        conf = {"min_": 0, "unknown": 0, "archives": [ArchiveGroup(cfs=("AVERAGE",))]}
        for name in methods:
            description = "Authentication failures using {}.".format(name)
            self.add_datasource(name, "DERIVE", description=description, **conf)
        if len(methods) > 0:
            self.add_datasource("other", "DERIVE", description="Other authentication failures.", **conf)
        self.add_datasource("total", "DERIVE", description="Total authentication failures.", warning=self.warning, critical=self.critical, **conf)

    def read_data(self):
        """
        Read the data from log.

        """
        values = {}
        for name in self.datasource_names:
            values[name] = 0
        with open(self.log_file, encoding=self.encoding) as fp:
            for line in fp:
                match = re.search("pam_unix\(([^:]+):auth\): authentication failure;", line)
                if match is not None:
                    values["total"] += 1
                    if match.group(1) in values:
                        values[match.group(1)] += 1
                    elif "other" in values:
                        values["other"] += 1
        return values
