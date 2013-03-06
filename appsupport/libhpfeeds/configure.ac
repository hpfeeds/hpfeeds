# -*- mode: m4; -*-
# -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.
# $Id$

AC_PREREQ(2.59)
AC_INIT([libhpfeeds], [0.1.0], [tillmann.werner@gmx.de])
AM_INIT_AUTOMAKE([libhpfeeds], [0.1.0])
AC_REVISION([$Id$])

AC_PREFIX_DEFAULT(/)
AC_CONFIG_SRCDIR([include/hpfeeds.h])
AM_CONFIG_HEADER([config.h])
# AM_MAINTAINER_MODE

AC_CANONICAL_HOST
AC_C_CONST
AC_C_BIGENDIAN

# Checks for programs.
AC_PROG_CC
AC_PROG_MAKE_SET
AC_PROG_LIBTOOL

AC_CHECK_HEADERS([arpa/inet.h sys/types.h])

AC_TYPE_SIZE_T

# library soname
# check http://sources.redhat.com/autobook/autobook/autobook_91.html#SEC91
libhpfeeds=0
libhpfeeds_current=1
libhpfeeds_revision=0
libhpfeeds_age=0
libhpfeeds_soname=$libhpfeeds_current:$libhpfeeds_revision:$libhpfeeds_age
AC_SUBST(libhpfeeds_soname)

AC_CONFIG_FILES([Makefile
		src/Makefile
		include/Makefile
		tools/Makefile
		])

AC_OUTPUT
