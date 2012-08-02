# -*- coding: utf-8 -*-
"""
Simple Monitoring Tool library - core SMT functionality.

Functions:
    call        --- Call command and read output.

Classes:
    rrdtool     --- API for the rrdtool commands (incomplete).
    ArchiveGroup --- Generator of RRA definitions from list of CFs and template names.
    Sensor      --- Class managing the creation and updates of RRD and metadata files.
    Plugin      --- Base plugin class.
    Limits      --- Checking for a datasource values outside allowed range.

"""

__author__ = "Petr Morávek (xificurk@gmail.com)"
__copyright__ = "Copyright (C) 2012 Petr Morávek"
__license__ = "LGPL 3.0"


from abc import ABCMeta, abstractproperty, abstractmethod
import json
import logging
from math import ceil, isnan
import os, os.path
import re
import subprocess
import threading
import time


__all__ = ["call",
           "rrdtool",
           "ArchiveGroup",
           "Datasource",
           "Plugin",
           "Limits",
          ]


# To prevent unexpected encoding of command output.
os.environ["LC_ALL"] = "C"

def call(*command):
    """
    Call command and read output.
    Raises RuntimeError when the command terminates with non-zero exit code.

    """
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retcode = proc.wait()
    if retcode != 0:
        e = RuntimeError("{} terminated with non-zero exit code.".format(command[0]))
        e.output = proc.stdout.read().decode("utf-8")
        raise e
    return proc.stdout.read().decode("utf-8")


class rrdtool(object):
    """
    API for the rrdtool commands (incomplete).

    Class methods:
        call        --- Call general rrdtool command.
        create      --- Create RRD file.
        update      --- Update RRD file.
        fetch       --- Fetch data from RRD file.

    """

    def __new__(cls, *p, **k):
        raise TypeError("This class cannot be instantionalized.")

    log = logging.getLogger("rrdtool")

    @classmethod
    def call(cls, command, *args):
        """
        Call general rrdtool command.

        Arguments:
            command     --- Command name.
            *args       --- Options/arguments to rrdtool create command.

        """
        cls.log.debug("Calling rrdtool {} {}".format(command, " ".join(args)))
        try:
            return call("rrdtool", command, *args)
        except RuntimeError as e:
            cls.log.error("RRDtool returned non-zero exit code with output:\n{}".format(e.output))
            raise e

    @classmethod
    def create(cls, filename, *args):
        """
        Create RRD file.

        Arguments:
            filename    --- Path to the RRD file.
            *args       --- Options/arguments to rrdtool create command.

        """
        return cls.call("create", filename, *args)

    @classmethod
    def update(cls, filename, *args):
        """
        Update RRD file.

        Arguments:
            filename    --- Path to the RRD file.
            *args       --- Options/arguments to rrdtool create command.

        """
        return cls.call("update", filename, *args)

    @classmethod
    def fetch(cls, filename, cf="AVERAGE", *args):
        """
        Fetch data from RRD file.

        Arguments:
            filename    --- Path to RRD file.
            cf          --- CF to use when fetching data from the file, default 'AVERAGE'.
            *args       --- Options/arguments to rrdtool create command.

        """
        data = {}
        for row in cls.call("fetch", filename, cf, *args).split("\n")[2:]:
            row = row.strip().split(" ")
            if len(row) < 2:
                break
            timestamp = int(row.pop(0)[:-1])
            values = tuple(float(v) for v in row)
            data[timestamp] = values
        return data



class ArchiveGroup(object):
    """
    Generator of RRA definitions from list of CFs and template names.

    Class properties:
        xff         --- Default value for xff.
        template_defs --- Predefined RRA templates.

    Properties:
        cfs         --- List of CFs for generation of RRA definitions.
        templates   --- List of template names for generation of RRA definitions.

    Methods:
        generate    --- Generate list of RRA definitions.

    """

    # Allowed CF names
    _cfs = ("AVERAGE", "MIN", "MAX", "LAST")

    # Default value for xff
    xff = 0.999999

    # Predefined RRA templates
    template_defs = {}
    template_defs["day"] = "RRA:{CF}:{xff}:#steps:300#:576"
    template_defs["week"] = "RRA:{CF}:{xff}:#steps:1800#:672"
    template_defs["month"] = "RRA:{CF}:{xff}:#steps:7200#:720"
    template_defs["year"] = "RRA:{CF}:{xff}:#steps:86400#:730"

    def __init__(self, cfs=("AVERAGE", "MIN", "MAX"), templates=("day", "week", "month", "year")):
        """
        Keyworded arguments:
            cfs         --- List of CFs for generation of RRA definitions.
            templates   --- List of template names for generation of RRA definitions.

        """
        for cf in cfs:
            if cf not in self._cfs:
                raise ValueError("Invalid CF {!r}.".format(cf))
        self.cfs = cfs
        for template in templates:
            if template not in self.template_defs:
                raise ValueError("Unknown template name {!r}.".format(template))
        self.templates = templates

    def generate(self, step):
        """
        Generate list of RRA definitions.

        Arguments:
            step        --- Step time for the PDP.

        """
        get_steps = lambda match: "{:.0f}".format(int(match.group(1)) / step)
        rras = []
        for cf in self.cfs:
            for template in self.templates:
                # RRDtool seems to be really picky about the xff format :/
                xff = "{:.0f}e-07".format(self.xff*1e07)
                rra = self.template_defs[template].format(CF=cf, xff=xff)
                rra = re.sub("#steps:([0-9]+)#", get_steps, rra)
                rras.append(rra)
        return rras



class Datasource(object):
    """
    Class managing the creation and updates of datasource files.

    Class properties:
        data_dir    --- Directory where the RRD files should be stored.

    Properties:
        plugin      --- Plugin instance that owns this datasource.
        name        --- Name of the datasource.
        safe_name   --- Safe name ([A-Za-z0-9_-]+) to use for filenames.
        type_       --- Type of the datasource.
        step        --- Step time for the PDP.
        heartbeat   --- Heartbeat of the datasource.
        min_        --- Min value of the datasource.
        max_        --- Max value of the datasource.
        unknown     --- Unknown value of the datasource. If not 'U', then RRD
                        file will contain additional clean datasource with
                        unknown values replaced by this one.
        archives    --- List of RRA archive definitions.
        title       --- Name of the datasource suitable for presenting to humans.
        description --- Human readable description of the datasource.
        warning     --- If the value goes outside of this interval, switch to warning state.
        critical    --- If the value goes outside of this interval, switch to critical state.
        filename    --- Safe filename where the datasource stores data.
        rrd_file    --- Path to rrd file.
        metadata_file --- Path to metadata file.

    Methods:
        update      --- Update the datasource with new value.
        check_files --- Check if RRD and metadata file exists, if not, create them.
        create_rrd  --- Create RRD file for this datasource.
        create_metadata  --- Create RRD file for this datasource.

    """

    # Available types of datasources
    _types = ("GAUGE", "COUNTER", "DERIVE", "ABSOLUTE")

    # Directory where the RRD files should be stored.
    data_dir = "/var/lib/smt/data"

    @property
    def filename(self):
        """
        Safe filename where the datasource stores data.

        """
        return "{}.{}".format(self.plugin.name, self.safe_name)

    @property
    def rrd_file(self):
        """
        Path to rrd file.

        """
        return os.path.join(self.data_dir, "{}.rrd".format(self.filename))

    @property
    def metadata_file(self):
        """
        Path to metadata file.

        """
        return os.path.join(self.data_dir, "{}.json".format(self.filename))

    def __init__(self, plugin, name, type_, **kwargs):
        """
        Arguments:
            plugin      --- Plugin instance that owns this datasource.
            name        --- Name of the datasource.
            type_       --- Type of the datasource.

        Keyworded arguments:
            safe_name   --- Safe name ([A-Za-z0-9_-]+) to use for filenames, default re.sub("[^A-Za-z0-9_-]", "_", name).
            step        --- Step time for the PDP, default round(300/ceil(300/plugin.update_interval)).
            heartbeat   --- Heartbeat of the datasource, default 2.5*plugin.update_interval.
            min_        --- Min value of the datasource, default 'U'.
            max_        --- Max value of the datasource, default 'U'.
            unknown     --- Unknown value of the datasource, default 'U'. If not 'U',
                            then RRD file will contain additional clean datasource
                            with unknown values replaced by this one.
            archives    --- List of RRA archive definitions. The definition is
                            either a string or instance of ArchiveGroup, default [ArchiveGroup()].
            title       --- Name of the datasource suitable for presenting to humans, default name.
            description --- Human readable description of the datasource, default ''.
            warning     --- If the value goes outside of this interval, switch to warning state, default ''.
                            The interval may have the form of 'min:max', 'min:', ':max', 'max', ''.
            critical    --- If the value goes outside of this interval, switch to critical state, default ''.
                            The interval may have the form of 'min:max', 'min:', ':max', 'max', ''.

        """
        if not isinstance(plugin, Plugin):
            raise ValueError("{} is not an instance of smt.core.Plugin.".format(plugin))
        self.plugin = plugin
        if type_ not in self._types:
            raise ValueError("Invalid datasource type {!r}.".format(type_))
        self.type_ = type_
        self.name = name
        self.safe_name = re.sub("[^A-Za-z0-9_-]", "_", kwargs.get("safe_name", name))
        if self.name in plugin.datasource_names:
            raise Value("Datasource with name {!r} already exists in this plugin.".format(self.name))
        if self.safe_name in plugin.datasource_safe_names:
            raise ValueError("Datasource with safe_name {!r} already exists in this plugin.".format(self.safe_name))
        plugin._datasources.append(self)
        self.step = int(kwargs.get("step", round(300/ceil(300/plugin.update_interval))))
        self.heartbeat = int(kwargs.get("heartbeat", plugin.update_interval*2.5))
        self.min_ = kwargs.get("min_", "U")
        self.max_ = kwargs.get("max_", "U")
        self.unknown = kwargs.get("unknown", "U")
        self.archives = []
        for archive in kwargs.get("archives", [ArchiveGroup()]):
            if isinstance(archive, ArchiveGroup):
                self.archives += archive.generate(self.step)
            else:
                self.archives.append(archive)
        self.title = kwargs.get("title", self.name)
        self.description = kwargs.get("description", "")
        self.warning = kwargs.get("warning", "")
        self.critical = kwargs.get("critical", "")

    def check_files(self):
        """
        Check if RRD and metadata file exists, if not, create them.

        """
        self.plugin.log.debug("Checking files for datasource {}.".format(self.name))
        if not os.path.isfile(self.rrd_file):
            self.create_rrd()
        if not os.path.isfile(self.metadata_file):
            self.create_metadata()

    def create_rrd(self):
        """
        Create RRD file for this datasource.

        """
        self.plugin.log.info("Creating RRD file for datasource {}.".format(self.name))
        datasources = []
        datasources.append("DS:raw:{}:{:d}:{}:{}".format(self.type_, self.heartbeat, self.min_, self.max_))
        if self.unknown != "U":
            datasources.append("DS:clean:COMPUTE:raw,UN,{},raw,IF".format(float(self.unknown)))
        cmd = [self.rrd_file, "--no-overwrite", "--step", str(int(self.step))]
        cmd += datasources
        cmd += self.archives
        rrdtool.create(*cmd)

    def _parse_interval(self, interval):
        """ Parses 'min:max', 'min:', ':max', 'max', '' into dictionary """
        if interval.count(":") > 1:
            raise ValueError("Invalid interval value {!r}.".format(interval))
        if interval.startswith(":"):
            interval = interval[1:]
        if len(interval) == 0:
            return {}
        elif ":" not in interval:
            return {"max": float(interval)}
        elif interval.endswith(":"):
            return {"min": float(interval[:-1])}
        else:
            min_, max_ = interval.split(":")
            return {"min": float(min_), "max": float(max_)}

    def create_metadata(self):
        """
        Create metadata file for this datasource.

        """
        self.plugin.log.info("Creating metadata file datasource {}.".format(self.name))
        metadata = {}
        metadata["update_interval"] = self.plugin.update_interval
        metadata["title"] = str(self.title)
        metadata["description"] = str(self.description)
        metadata["limits"] = {}
        for limit in ("warning", "critical"):
            metadata["limits"][limit] = self._parse_interval(getattr(self, limit))
        with open(self.metadata_file, "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)

    def update(self, value):
        """
        Update the datasource with new value.

        Arguments:
            value       --- Value of the sensor.

        """
        self.plugin.log.debug("Updating datasource {} = {}.".format(self.name, value))
        self.check_files()
        rrdtool.update(self.rrd_file, "N:{}".format(value))



class Plugin(threading.Thread, metaclass=ABCMeta):
    """
    Base plugin class.
    Every SMT plugin should be a subclass of smt.core.Plugin.

    Abstract properties:
        name        --- Name of the plugin.
        update_interval --- Interval in seconds in which the sensors should be read.

    Abstract methods:
        read_data   --- Read the data from sensors.

    Class properties:
        stop        --- Event to signal the plugin to stop.

    Class methods:
        configure   --- Automatically configure the plugin.

    Properties:
        datasources --- Tuple with all attached datasources.
        datasource_names --- Names of datasources attached to this plugin.
        datasource_safe_names --- Safe names of datasources attached to this plugin.
        last_update --- Time of the last update.

    Methods:
        add_datasource --- Adds datasource of given name and parameters.
        remove_datasource --- Removes datasource of given name (if it exists).
        get_datasource --- Get the instance of attached datasource or raise KeyError.
        run         --- Main plugin thread method.
        update      --- Fetch new data and update the datasource.

    """

    @abstractproperty
    def name(self):
        """
        Name of the plugin.

        """
        raise NotImplementedError

    @abstractproperty
    def update_interval(self):
        """
        Interval in seconds in which the sensors should be read.

        """
        raise NotImplementedError

    @abstractmethod
    def read_data(self):
        """
        Read the data from sensors.

        """
        raise NotImplementedError

    # Event to signal the plugin to stop.
    stop = threading.Event()

    @classmethod
    def configure(cls):
        """
        Automatically configure the plugin.

        Raises NotImplementedError, override this method in the subclass.

        The implementation should return a new instance of the plugin configured
        with all available datasources, or raise an Exception.

        """
        raise NotImplementedError

    @property
    def datasources(self):
        """
        Tuple with all attached datasources.

        """
        return tuple(self._datasources)

    @property
    def datasource_names(self):
        """
        Names of datasources attached to this plugin.

        """
        return tuple(datasource.name for datasource in self._datasources)

    @property
    def datasource_safe_names(self):
        """
        Safe names of datasources attached to this plugin.

        """
        return tuple(datasource.safe_name for datasource in self._datasources)

    def __init__(self):
        threading.Thread.__init__(self)
        self.log = logging.getLogger("smt.plugin.{}".format(self.name))
        self._datasources = []

    def add_datasource(self, name, type_, **kwargs):
        """
        Adds datasource of given name and parameters.

        Arguments:
            name        --- Name of the datasource.
            type_       --- Type of the datasource.

        Keyworded arguments:
            safe_name   --- Safe name ([A-Za-z0-9_-]+) to use for filenames.
            step        --- Step time for the PDP.
            heartbeat   --- Heartbeat of the datasource.
            min_        --- Min value of the datasource.
            max_        --- Max value of the datasource.
            unknown     --- Unknown value of the datasource. If not 'U', then RRD
                            file will contain additional clean datasource with
                            unknown values replaced by this one.
            archives    --- List of RRA archive definitions. The definition is
                            either a string or instance of ArchiveGroup.
            title       --- Name of the datasource suitable for presenting to humans.
            description --- Human readable description of the datasource.
            warning     --- If the value goes outside of this interval, switch to warning state.
            critical    --- If the value goes outside of this interval, switch to critical state.

        """
        self.log.debug("Adding datasource {}.".format(name))
        Datasource(self, name, type_, **kwargs)

    def remove_datasource(self, name):
        """
        Removes datasource of given name (if it exists).

        Arguments:
            name        --- Name of the datasource.

        """
        self.log.debug("Removing datasource {}.".format(name))
        for datasource in list(self._datasources):
            if datasource.name == name:
                self._datasources.remove(datasource)
                break

    def get_datasource(self, name):
        """
        Get the instance of attached datasource or raise KeyError.

        """
        for datasource in self._datasources:
            if datasource.name == name:
                return datasource
        raise KeyError("Could not find datasource {!r}.".format(name))

    def update(self):
        """
        Fetch new data and update the datasource.

        """
        self.log.debug("Reading data from sensors.")
        data = self.read_data()
        for datasource in self._datasources:
            try:
                datasource.update(data[datasource.name])
            except KeyError as e:
                self.log.error("Provided data do not contain value for datasource {!r}.".format(datasource.name))

    def run(self):
        """
        Main plugin thread method.

        """
        self.log.info("Plugin {} starting.".format(self.name))
        wait_time = 5
        while not self.stop.wait(wait_time):
            try:
                self.last_update = time.time()
                self.update()
                wait_time = max(1, self.update_interval - (time.time() - self.last_update))
            except Exception as e:
                self.log.exception(e)
                self.log.error("Ignoring the exception and reseting the timer.")
                wait_time = self.update_interval
        self.log.info("Plugin {} exiting.".format(self.name))



class Limits(object):
    """
    Checking for a datasource values outside allowed range.

    Properties:
        data_dir    --- Path to directory where RRD and metadata files are stored.
        state_dir   --- Path to directory where to store the state of datasources.
        unknown_skip --- Number of allowed unknown values at the end of dataset.

    Methods:
        get_limits  --- Load the limits of specified datasource from metadata file.
        get_value   --- Get the last value of specified datasource (ignoring unknown_skip last NaN values).
        check       --- Check the specified datasource for state change.
        check_all   --- Check all datasources and return dictionary with all datasources that have changed the state.

    """

    def __init__(self, data_dir, state_dir, unknown_skip=3):
        """
        Arguments:
            data_dir    --- Path to directory where RRD and metadata files are stored.
            state_dir   --- Path to directory where to store the state of datasources.

        Keyworded arguments:
            unknown_skip --- Number of allowed unknown values at the end of dataset.

        """
        self.log = logging.getLogger("smt.limits")
        self.data_dir = data_dir
        self.state_dir = state_dir
        self.unknown_skip = unknown_skip

    def get_limits(self, path):
        """
        Load the limits of specified datasource from metadata file.

        Arguments:
            path        --- Path to the metadata file.

        """
        with open(path, "r", encoding="utf-8") as fp:
            metadata = json.load(fp)
        limits = dict(filter(lambda x: len(x[1]) > 0, metadata["limits"].items()))
        return limits

    def get_value(self, path):
        """
        Get the last value of specified datasource (ignoring unknown_skip last NaN values).

        Arguments:
            path        --- Path to the RRD file.

        """
        data = rrdtool.fetch(path)
        value = float('nan')
        skipped = 0
        for timestamp in reversed(sorted(data.keys())):
            value = data[timestamp][-1]
            if not (isnan(value) and skipped < self.unknown_skip):
                break
            skipped += 1
        return value

    def check(self, name):
        """
        Check the specified datasource for state change.

        Arguments:
            name        --- Name of the datasource.

        """
        limits = self.get_limits(os.path.join(self.data_dir, "{}.json".format(name)))
        if len(limits) == 0:
            raise ValueError("Could not find any limits for datasource {!r}.".format(name))
        value = self.get_value(os.path.join(self.data_dir, "{}.rrd".format(name)))

        state_file = os.path.join(self.state_dir, "{}.txt".format(name))
        if os.path.isfile(state_file):
            with open(state_file) as fp:
                old_state = fp.read()
            if old_state not in ("NORM", "WARN", "CRIT", "UNKN"):
                # Corrupted state file
                self.log.warn("{} state file contained corrupted state value {!r}.".format(state_file, old_state))
                old_state = "UNKN"
        else:
            old_state = "NORM"

        if isnan(value):
            state = "UNKN"
        elif "warning" in limits and (("min" in limits["warning"] and value < limits["warning"]["min"]) or ("max" in limits["warning"] and value > limits["warning"]["max"])):
            state = "WARN"
        elif "critical" in limits and (("min" in limits["critical"] and value < limits["critical"]["min"]) or ("max" in limits["critical"] and value > limits["critical"]["max"])):
            state = "CRIT"
        else:
            state = "NORM"

        if state != old_state:
            with open(state_file, "w") as fp:
                fp.write(state)

        return (old_state, state, value)

    def check_all(self):
        """
        Check all datasources and return dictionary with all datasources that have changed the state.

        """
        result = {}
        for filename in os.listdir(self.data_dir):
            if not filename.endswith(".json"):
                continue
            name = filename[:-5]
            try:
                old_state, state, value = self.check(name)
                if old_state != state:
                    result[name] = (old_state, state, value)
            except ValueError:
                pass
            except Exception as e:
                self.log.exception(e)
                self.log.error("Could not check the limits of datasource {!r}.".format(name))
        return result