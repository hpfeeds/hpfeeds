#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='hpfeeds3',
    version='0.9',
    description='Python implementation of the honeypot feeds broker',
    author='John Carr',
    author_email='john.carr@unrouted.co.uk',
    url='https://github.com/Jc2k/hpfeeds',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    entry_points='''
        [console_scripts]
        hpfeeds = hpfeeds.scripts.cli:main
        hpfeeds-broker = hpfeeds.scripts.broker:main
    ''',
    extra_require = {
        'test': [
            'flake8',
            'flake8-isort',
            'pytest',
            'pytest-cov',
            'codecov',
        ],
        'broker': [
            'aiorun',
            'aiohttp',
            'prometheus_client',
        ],
    },
)
