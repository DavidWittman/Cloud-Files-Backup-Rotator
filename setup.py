#!/usr/bin/env python

from setuptools import setup, find_packages

__author__ = "David Wittman <david@wittman.com>"
NAME = "cfrotate"
DESC = "A backup rotator for use with Rackspace Cloud Files"
VERSION = "0.2"
REQS = [ 'python-cloudfiles', 'argparse' ]

setup(name = NAME,
      description = DESC,
      version = VERSION,  
      author = "David Wittman",
      author_email = "david@wittman.com",
      license = "BSD",
      install_requires = REQS,
      package_dir = {'': 'lib'},
      packages = ['cfrotate'],
      scripts = ['bin/cfrotate']
     )
