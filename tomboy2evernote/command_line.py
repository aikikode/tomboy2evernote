#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from datetime import timedelta, date
import glob
import os
import sys

from evernote.edam.error.ttypes import EDAMUserException

from tomboy2evernote.tomboy2evernote import Evernote, convert_tomboy_to_evernote

__author__ = 'Denis Kovalev (aikikode)'

TOMBOY_DIR = os.path.join(os.environ['HOME'], ".local", "share", "tomboy")
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 't2ev')
if not os.path.isdir(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)
if CONFIG_DIR not in sys.path:
    sys.path.append(CONFIG_DIR)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.py')

import logging
logger = logging.getLogger(__name__)


def get_token():
    try:
        from settings import DEV_TOKEN
    except ImportError:
        DEV_TOKEN = ''
        with open(CONFIG_FILE, 'w') as config_file:
            config_file.write("DEV_TOKEN = ''")
    if not DEV_TOKEN:
        logger.error(
            'Please, get new Evernote development token from the site and put it into the\n'
            '{} file. E.g.: DEV_TOKEN = "12345"'.format(CONFIG_FILE)
        )
    return DEV_TOKEN


def main():
    parser = argparse.ArgumentParser(
        description='Tomboy2Evernote notes converter. Upload Tomboy notes to your Evernote account')
    parser.add_argument('-t', action='store', choices=['day', 'week', 'month', 'all'], default='day',
                        help='Upload only notes modified during this period. Default: day', required=False)
    args = parser.parse_args()
    convert_all_tomboy_notes(args.t)


def convert_all_tomboy_notes(modified_time):
    delta = timedelta.max
    if modified_time == 'day':
        delta = timedelta(days=1)
    elif modified_time == 'week':
        delta = timedelta(weeks=1)
    elif modified_time == 'month':
        delta = timedelta(weeks=4)
    today = date.today()
    notes_files = list(filter(lambda f: delta > today - date.fromtimestamp(os.path.getmtime(f)),
                              glob.glob(os.path.join(TOMBOY_DIR, "*.note"))))
    total_notes = len(notes_files)
    try:
        evernote = Evernote(token=get_token())
    except EDAMUserException as ex:
        sys.exit(ex.errorCode)
    failed_notes = []
    for idx, tomboy_note in enumerate(notes_files):
        print("[{}/{}]:".format(idx + 1, total_notes), end=" ")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        if ev_note:
            print("Converted '{}'. Uploading...".format(ev_note['title']), end=" ")
            try:
                evernote.create_or_update_note(ev_note)
            except:
                failed_notes.append(ev_note['title'])
                print("FAILED")
            else:
                print("OK")
        else:
            print("Skipped template note")
    if failed_notes:
        print("The following notes failed to upload:")
        for idx, note_title in enumerate(failed_notes):
            print("[{}]: '{}'".format(idx + 1, note_title))


if __name__ == "__main__":
    main()
