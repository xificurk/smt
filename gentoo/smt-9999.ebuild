# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI="4"

EGIT_REPO_URI="git://github.com/xificurk/smt.git"
PYTHON_COMPAT=( python3_1 python3_2 )

inherit distutils-r1 git-2 user

DESCRIPTION="Simple monitoring tool for various sensors."
HOMEPAGE="http://github.com/xificurk/smt"

LICENSE="LGPL-3"
SLOT="0"
KEYWORDS="amd64 x86"
IUSE=""

DEPEND=""
RDEPEND="net-analyzer/rrdtool"

DOCS=( README CHANGES )


pkg_setup() {
	enewgroup smt
	enewuser smt -1 -1 /var/lib/smt smt
}

python_install() {
	distutils-r1_python_install

	# install scripts
	local python_scriptroot=/usr/sbin
	python_doscript bin/smtd
	fowners smt:smt "${python_scriptroot}/smtd-${EPYTHON}"
	fperms 750 "${python_scriptroot}/smtd-${EPYTHON}"
	python_doscript bin/smt-limits
	fowners smt:smt "${python_scriptroot}/smt-limits-${EPYTHON}"
	fperms 750 "${python_scriptroot}/smt-limits-${EPYTHON}"
}

src_install() {
	distutils-r1_src_install

	# install example plugins configuration
	keepdir /etc/smt/plugins
	insinto /etc/smt/plugins
	newins config/plugins.py __init__.py

	# install init script and its configuration
	newinitd gentoo/smt-init smt
	newconfd gentoo/smt-conf smt

	# install logrotate file
	insinto /etc/logrotate.d
	newins gentoo/smt-logrotate smt

	# create data dir
	local dirs
	dirs="/var/lib/smt/data /var/lib/smt/state"
	keepdir $dirs
	fowners smt:smt $dirs
	fperms 775 $dirs
}
