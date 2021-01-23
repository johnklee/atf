#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages

# what `purifier` minimally needs to run correctly (runtime)
requires = [
    'certifi==2019.9.11',
    'chardet==3.0.4',
    'docker==4.1.0',
    'idna==2.8',
    'pexpect==4.7.0',
    'ptyprocess==0.6.0',
    'requests==2.22.0',
    'six==1.12.0',
    'urllib3==1.24.3',
    'websocket-client==0.56.0',
    'coloredlogs==10.0'
]

# test / dev requirements
test_requirements = [
    'pytest>=4.3.0'
]

setup(
    name='atf-docker',
    version='0.0.2',
    author='johnklee',
    author_email='kueiching.a.lee@rakuten.com',
    description='ATF for docker',
    url='https://github.com/jkclee/atf',
    python_requires='~=3.6',
    packages=find_packages(exclude=('tests', 'docs', 'env', 'tools')),
    setup_requires=['pytest-runner'],
    install_requires=requires,
    tests_require=test_requirements,
)
