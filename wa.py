#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Francois Boulogne
# License:

from libwa import archive
import uuid

import argparse
import os, sys
from subprocess import call


import logging


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":"yes",   "y":"yes",  "ye":"yes",
             "no":"no",     "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='',
                                     epilog='')
    #parser = argparse.ArgumentParser(description=info.SHORT_DESCRIPTION,
    #                                 epilog='')
    #parser.add_argument('--version', action='version', version=info.NAME + ' ' + info.VERSION)
    parser.add_argument('url', help='URL to archive', metavar='URL')
    parser.add_argument('-o', help='Destination directory', metavar='DIR')
    parser.add_argument('-d', '--debug', action='store_true',
                        default=False, help='Run in debug mode')
    #parser.add_argument('--notimecheck', help='No timecheck', action='store_false')

    args = parser.parse_args()

    if args.debug:
        llevel = logging.DEBUG
    else:
        llevel = logging.INFO
    logger = logging.getLogger()
    logger.setLevel(llevel)

    steam_handler = logging.StreamHandler()
    steam_handler.setLevel(llevel)
    logger.addHandler(steam_handler)


    if args.o is None:
        args.o = os.path.expanduser('~/wiki/archive')
        args.o = '/tmp/dir'
    archive_root =  os.path.split(args.o)[0]

    name = uuid.uuid4()
    (title, filepath) = archive.archive_to_markdown(args.o, name, args.url)

    filepath_short = os.path.relpath(filepath, archive_root)

    if query_yes_no('Edit the mdwn file?') == 'yes':
        EDITOR = os.environ.get('EDITOR', 'nano')
        call([EDITOR, filepath])

    print('[[' + title + '|' + filepath_short + ']]')
