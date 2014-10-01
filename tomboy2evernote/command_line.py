#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import glob
import os
from tomboy2evernote.tomboy2evernote import Evernote, DEV_TOKEN, convert_tomboy_to_evernote
from datetime import timedelta, date

__author__ = 'Denis Kovalev (aikikode)'

TOMBOY_DIR = os.path.join(os.environ['HOME'], ".local", "share", "tomboy")


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
    evernote = Evernote(token=DEV_TOKEN)
    for idx, tomboy_note in enumerate(notes_files):
        print("[{}/{}]:".format(idx + 1, total_notes), end=" ")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        if ev_note:
            print("Converted '{}'. Uploading...".format(ev_note['title']), end=" ")
            evernote.create_or_update_note(ev_note)
            print("OK")
        else:
            print("Skipped template note")


if __name__ == "__main__":
    main()