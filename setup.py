#!/usr/bin/env python

import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='canvas-eos-import',
    version='1.0',
    packages=['eos'],
    include_package_data=True,
    install_requires = [
        'setuptools',
        'django',
        'lxml==2.3.5'
    ],
    dependency_links = [
        'http://github.com/uw-it-aca/uw-restclients#egg=RestClients'
    ],
    license='Apache License, Version 2.0',  # example license
    description='Imports EOS courses to UW Canvas',
    long_description=README,
    url='https://github.com/uw-it-aca/canvas-eos-import',
    author = "UW-IT ACA",
    author_email = "aca-it@uw.edu",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
