# -*- coding: utf-8 -*-
"""
setup
~~~~~
Treblle Flask setup
"""

from setuptools import setup
from os.path import join, dirname

with open(join(dirname(__file__), 'requirements.txt'), 'r') as f:
    install_requires = f.read().split("\n")

setup(
    name='Treblle-Flask',
    url='https://github.com/Treblle/treblle-flask',
    license='MIT',
    description="A Flask extension for Treblle",
    packages=['treblle_flask'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=install_requires,
    classifiers=[
        'Environment :: Web Environment', 'Intended Audience :: Developers',
        'Operating System :: OS Independent', 'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ])
