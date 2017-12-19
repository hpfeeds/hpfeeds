#!/usr/bin/env python

from distutils.core import setup

setup(
    name='hpfeeds3',
    version='1.0',
    description='hpfeeds module',
    author='John Carr',
    author_email='john.carr@unrouted.co.uk',
    url='https://github.com/Jc2k/hpfeeds',
    license='GPL',
    package_dir = {'': 'lib'},
    py_modules = ['hpfeeds'],
    scripts=['cli/hpfeeds-client']
)
