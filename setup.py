##############################################################################
#
# Copyright (c) 2010 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.txt')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = ''
    CHANGES = ''

requires = [
    'setuptools',
    'Chameleon>=2.0',
    'pyramid>=1.0a10', # zcml externalized
    'pyramid_zcml',
    'formish',
    'Mako',
    ]

if sys.version_info[:2] < (2,5):
    requires.append('uuid')

setup(name='pyramid_formish',
      version='0.2a1',
      description='Formish bindings and helpers for Pyramid web framework',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        ],
      keywords='web formish formgen bfg pyramid',
      author="Chris McDonough, Agendaless Consulting",
      author_email="repoze-dev@lists.repoze.org",
      url="http://www.repoze.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      tests_require = requires,
      install_requires= requires,
      test_suite="pyramid_formish",
      entry_points = """\
        [console_scripts]
        bfgformish2pyramidformish = pyramid_formish.fix_formish_imports:main
      """
      )

