# -*- coding: utf-8 -*-

# This file contains examples of SMT plugins configuration.
# WARNING: If you make changes that require re-creation of RRD or metadata
#          files, you MUST delete the affected files manually.

# Setup logging
import logging
log = logging.getLogger("config")

# Let's import the module with the basic set of plugins.
import smt.plugins

# This the heart of the configuration - every plugin you want to start from the
# daemon should be added to this list and is expected to be an instance of class
# that inherits from smt.core.Plugin.
plugins = []

# The easiest way to configure SMT plugins is to use automatic configuration.
# NOTE: Not all plugins support this.
# OK, let's go through all basic plugins and try to configure them automatically.
for plugin_name in smt.plugins.__all__:
    plugin_cls = getattr(smt.plugins, plugin_name)
    try:
        plugins.append(plugin_cls.configure())
    except NotImplementedError:
        # The automatic configuration failed, because the plugins does not support it.
        pass
    except Exception as e:
        # Some other exception was raised, let's log it.
        log.exception(e)

# You can configure the plugins by hand as well.
"""
# First initialize the plugin
loadavg = smt.plugins.loadavg.LoadAvgPlugin()
# Adjust the settings as you wish, e.g. set warning bound:
loadavg.get_datasource("5min").warning = ":5"
# And finally append it to plugins list
plugins.append(loadavg)
"""

# Some plugins require manual configuration, see examples below.
"""
plugins.append(smt.plugins.hddtemp.HDDTempPlugin(("/dev/sda",)))
plugins.append(smt.plugins.sensors.SensorsPlugin(("CPU Temp",)))
plugins.append(smt.plugins.smart.SmartPlugin("sda", ("Start_Stop_Count", "Reallocated_Sector_Ct")))
"""

# NOTE: In this file you can define your own plugin classes and use them.