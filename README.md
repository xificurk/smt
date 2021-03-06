About
============================================================================
Simple Monitoring Tool is exactly what the name says - simple tool for
monitoring various sensors and storing their data in the form of RRD files.

The package is written completely in Python, even the configuration is done
via python source file.


Contents:
    bin/ - SMT scripts
    config/ - sample SMT plugins configuration
    gentoo/ - some mostly Gentoo-specific files
        smt-9999.ebuild - live ebuild fetching the source from GitHub
          repository.
        smt-conf - configuration for the init script
        smt-init - init script for SMT daemon
        smt-logrotate - sample logrotate configuration
    smt/ - python smt package
    setup.py - distutils setup file for smt package

Homepage:
    http://github.com/xificurk/smt

Author:
    Petr Morávek [Xificurk]
    Email: petr@pada.cz
    Jabber ID: petr@pada.cz

Requirements
============================================================================
* Python 3.1 or newer
* RRDtool with python bindings
* The base set of plugins requires various *nix tools, e.g. who, df, hddtemp,
  sensors, nvidia-smi, smartctl.