#! /usr/bin/make -f
# :vim: filetype=make : -*- makefile; coding: utf-8; -*-

# Makefile
# Part of Bugs Everywhere, a distributed bug tracking system.
#
# Copyright (C) 2008-2010 Anton Batenev <abbat@abbat>
#                         Ben Finney <benf@cybersource.com.au>
#                         Eric Kow <eric.kow@gmail.com>
#                         Gianluca Montecchi <gian@grys.it>
#                         W. Trevor King <wking@drexel.edu>
#
# This file is part of Bugs Everywhere.
#
# Bugs Everywhere is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 2 of the License, or (at your
# option) any later version.
#
# Bugs Everywhere is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bugs Everywhere.  If not, see <http://www.gnu.org/licenses/>.

SHELL = /bin/bash
RM = /bin/rm
DB2MAN = http://docbook.sourceforge.net/release/xsl-ns/current/manpages/docbook.xsl
DB2HTML = http://docbook.sourceforge.net/release/xsl-ns/current/html/docbook.xsl
XP = /usr/bin/xsltproc --nonet --param man.charmap.use.subset "0" \
	--param make.year.ranges "1" --param make.single.year.ranges "1"

#PATH = /usr/bin:/bin  # must include sphinx-build for 'sphinx' target.

#PREFIX = /usr/local
PREFIX = ${HOME}
INSTALL_OPTIONS = "--prefix=${PREFIX}"

# Select the documentation you wish to build
DOC = sphinx man

# Directories with semantic meaning
DOC_DIR := doc
MAN_DIR := ${DOC_DIR}/man

MANPAGES = be.1
LIBBE_VERSION := libbe/_version.py
GENERATED_FILES := build $(LIBBE_VERSION)

MANPAGE_FILES = $(patsubst %,${MAN_DIR}/%,${MANPAGES})
GENERATED_FILES += ${MANPAGE_FILES}


.PHONY: all
all: build


.PHONY: build
build: $(LIBBE_VERSION)
	python setup.py build

.PHONY: doc
doc: $(DOC)

.PHONY: install
install: build doc
	python setup.py install ${INSTALL_OPTIONS}

test: build
	python test.py

.PHONY: clean
clean:
	$(RM) -rf ${GENERATED_FILES}
	$(MAKE) -C ${DOC_DIR} clean


.PHONY: libbe/_version.py
libbe/_version.py:
	git log -1 --date=short --pretty='format:"Autogenerated by make libbe/_version.py"%nversion_info = {%n    "date":"%cd",%n    "revision":"%H",%n    "committer":"%cn"}%n' > $@

.PHONY: man
man: ${MANPAGE_FILES}

%.1: %.1.xml
	$(XP) -o $@ $(DB2MAN) $<
%.1.html: %.1.xml
	$(XP) -o $@ $(DB2HTML) $<

.PHONY: sphinx
sphinx:
	$(MAKE) -C ${DOC_DIR} html
