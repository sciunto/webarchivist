#!/usr/bin/env python

from distutils.core import setup
from libwa import info

setup(
    name         = 'webarchivist',
    version      = info.VERSION,
    url          = info.URL,
    author       = "Francois Boulogne",
    license      = info.LICENSE,
    author_email = info.EMAIL,
    description  = info.SHORT_DESCRIPTION,
    packages     = ['libwa'],
    scripts      = ['wa'],
    requires     = [],
)
