#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Francois Boulogne
# License:

from libwa import archive
import uuid

import argparse
import os


import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='',
                                     epilog='')
    #parser = argparse.ArgumentParser(description=info.SHORT_DESCRIPTION,
    #                                 epilog='')
    #parser.add_argument('--version', action='version', version=info.NAME + ' ' + info.VERSION)
    parser.add_argument('url', help='URL to archive', metavar='URL')
    parser.add_argument('-d', help='Destination directory', metavar='DIR')
    #parser.add_argument('--notimecheck', help='No timecheck', action='store_false')

    args = parser.parse_args()

    if args.d is None:
        args.d = os.path.expanduser('~/wiki/archive')
        args.d = '/tmp'

    name = uuid.uuid4()
    (title, filepath) = archive.archive_to_markdown(args.d, name, args.url)

    print('[[' + title + '|' + filepath + ']]')  #FIXME : filepath : base
