# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from distutils.core import setup

setup(name='klupung',
      version='0.1.0',
      description='Klupu Next Generation',
      long_description="Open Ahjo -compatible RESTful HTTP API server",
      author='Koodilehto Osk',
      author_email='klupung@koodilehto.fi',
      license='AGPLv3+',
      packages=['klupung'],
      scripts=[
        "bin/klupung-ktweb-download",
        "bin/klupung-ktweb-parse",
        "bin/klupung-stupid-apiserver",
        ],
      platforms=['Linux'],
      url="http://koodilehto.fi/projects/klupung",
)
