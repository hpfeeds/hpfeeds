AUTOMAKE_OPTIONS = foreign

AM_CFLAGS = -I../include -Werror -Wall -g

lib_LTLIBRARIES = libhpfeeds.la

libhpfeeds_la_SOURCES = hpfeeds.c sha1.c

libhpfeeds_la_LDFLAGS = -no-undefined -version-info @libhpfeeds_soname@ -export-symbols-regex "^hpf_"
