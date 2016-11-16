#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Version statuses:
# - 0.1: developing
# - 0.9: testing
# - 0.9.4: pre-releasing
# - 1.0: product
__version__ = '0.1.0'

from setuptools import setup


with open('requirements.txt', 'r') as f:
    requirements = [l for l in f.readlines() if not l.startswith("-")]

setup(
    #license='License :: OSI Approved :: MIT License',
    name='loki',
    version=__version__,
    author='sre-team',
    author_email='sre-team@nosa.me',
    description='Automated Operation System',
    #long_description=open('README.md').read(),
    #scripts=[],
    packages=[
        'loki',
    ],
    install_requires=requirements
    #package_data={}
    #entry_points={}
)
