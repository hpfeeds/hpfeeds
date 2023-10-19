#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='hpfeeds',
    version='3.1.0',
    description='Python implementation of the hpfeeds client and broker',
    url='https://github.com/hpfeeds/hpfeeds',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,
    entry_points='''
        [console_scripts]
        hpfeeds = hpfeeds.scripts.cli:main
        hpfeeds-broker = hpfeeds.scripts.broker:main
    ''',
    project_urls={
        'Documentation': 'https://hpfeeds.readthedocs.org/',
        'Code': 'https://github.com/hpfeeds/hpfeeds',
        'Issue tracker': 'https://github.com/hpfeeds/hpfeeds/issues',
    },
    extras_require = {
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
            'wrapt',
        ],
        'broker-auth-json': [
            'aionotify',
        ],
        'broker-auth-mongo': [
            'motor',
        ],
        'broker-auth-database': [
            'databases',
        ]
    },
)
