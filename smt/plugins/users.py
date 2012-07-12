# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - users plugin.

Classes:
    UsersPlugin     --- Plugin monitoring number of logins and users on the machine.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from smt.core import Plugin, call


__all__ = ["UsersPlugin"]


class UsersPlugin(Plugin):
    """
    Plugin monitoring number of logins and users on the machine.

    Class properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Class methods:
        configure   --- Automatically configure the plugin.

    Methods:
        read_data   --- Read the data from sensors.

    """

    name = "users"
    update_interval = 120

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        """
        return UsersPlugin()

    def __init__(self):
        Plugin.__init__(self)
        self.add_datasource("logins", "GAUGE", min_=0, title="Logins", description="Number of logged in users.")
        self.add_datasource("users", "GAUGE", min_=0, title="Users", description="Number of unique logged in users.")

    def read_data(self):
        """
        Read the data from sensors.

        """
        values = {}
        result = call("who", "-q").split("\n")[0].split(" ")
        if len(result[0]) == 0:
            result = []
        values["logins"] = len(result)
        values["users"] = len(set(result))
        return values
