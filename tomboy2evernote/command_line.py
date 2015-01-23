#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from datetime import timedelta, date
import glob
import os
import sys

import pyinotify

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
    parser.add_argument('-d', '--daemon', action='store_true', help='Run as daemon', required=False)
    args = parser.parse_args()

    try:
        evernote = Evernote(token=get_token())
    except EDAMUserException as ex:
        sys.exit(ex.errorCode)

    if args.daemon:
        run_as_daemon(evernote)
    else:
        convert_all_tomboy_notes(evernote, args.t)


def convert_all_tomboy_notes(evernote, modified_time=None):
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
    failed_notes = []
    notes_hash = dict()
    for idx, tomboy_note in enumerate(notes_files):
        print('[{}/{}]:'.format(idx + 1, total_notes), end=' ')
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        if ev_note:
            print('Converted \'{}\'. Uploading...'.format(ev_note['title']), end=' ')
            try:
                evernote.create_or_update_note(ev_note)
            except:
                failed_notes.append(ev_note['title'])
                print('FAILED')
            else:
                print('OK')
            notes_hash[tomboy_note] = ev_note['title']
        else:
            print('Skipped template note')
    if failed_notes:
        print('The following notes failed to upload:')
        for idx, note_title in enumerate(failed_notes):
            print('[{}]: \'{}\''.format(idx + 1, note_title))
    return notes_hash


def run_as_daemon(evernote_client):
    # First we need to get all current notes and their titles to correctly handle note deletion
    notes = convert_all_tomboy_notes(evernote_client)

    # Configure daemon
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY | \
           pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM

    class EventHandler(pyinotify.ProcessEvent):
        def my_init(self, evernote, notes_hash):
            self.evernote = evernote
            self.notes_hash = notes_hash

        def process_IN_CREATE(self, event):
            self.process_IN_MOVED_TO(event)

        def process_IN_DELETE(self, event):
            self.process_IN_MOVED_FROM(event)

        def process_IN_MODIFY(self, event):
            self.process_IN_MOVED_TO(event)

        def process_IN_MOVED_TO(self, event):
            # New note / Modify note
            tomboy_note = event.pathname
            if os.path.isfile(tomboy_note) and os.path.splitext(tomboy_note)[1] == '.note':
                ev_note = convert_tomboy_to_evernote(tomboy_note)
                if ev_note:
                    try:
                        self.evernote.create_or_update_note(ev_note)
                        self.notes_hash[tomboy_note] = ev_note['title']
                        logger.info('Updated \'{}\''.format(ev_note['title']))
                    except:
                        logger.error('ERROR: Failed to upload \'{}\' note'.format(ev_note['title']))

        def process_IN_MOVED_FROM(self, event):
            # Delete note
            tomboy_note = event.pathname
            note_title = self.notes_hash.get(tomboy_note)
            if note_title:
                try:
                    self.evernote.remove_note(note_title)
                    logger.info('Deleted \'{}\''.format(note_title))
                    self.notes_hash.pop(tomboy_note, None)
                except:
                    logger.error('ERROR: Failed to delete "{}" note'.format(note_title))

    handler = EventHandler(evernote=evernote_client, notes_hash=notes)
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(TOMBOY_DIR, mask, rec=False)
    try:
        notifier.loop(daemonize=True, pid_file='/tmp/t2ev.pid', stdout='/tmp/t2ev.log')
    except pyinotify.NotifierError as ex:
        logger.exception('ERROR: notifier exception: {}'.format(ex))


if __name__ == "__main__":
    ()
