#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html
import time
from urllib.parse import urlparse, quote

import isodate
import lxml.etree as xml

from evernote.api.client import EvernoteClient
from evernote.edam.error.ttypes import EDAMUserException
from evernote.edam.limits.constants import EDAM_USER_NOTES_MAX
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note, Notebook

import logging
logger = logging.getLogger(__name__)

__author__ = 'Denis Kovalev (aikikode)'

DEV_TOKEN = ''


class Evernote(EvernoteClient):
    def __init__(self, token):
        super(Evernote, self).__init__(dev_token=token)
        self.token = token
        try:
            self.note_store = self.get_note_store()
        except EDAMUserException as ex:
            logger.error('ERROR: Authorization failed. Make sure you have correct token.')
            raise ex

    def find_note(self, note_title):
        notes_retrieve_count = EDAM_USER_NOTES_MAX
        start_index = 0
        remaining = notes_retrieve_count
        notes = []
        while remaining > 0:
            notes_data_list = self.note_store.findNotesMetadata(NoteFilter(words='intitle:"{}"'.format(note_title)),
                                                                start_index, notes_retrieve_count,
                                                                NotesMetadataResultSpec())
            retrieved_notes = [self.note_store.getNote(note_data.guid, True, False, False, False)
                               for note_data in notes_data_list.notes]
            for n in retrieved_notes:
                if n.title == note_title:
                    return n
            notes += retrieved_notes

            total = notes_data_list.totalNotes
            retrieved = len(notes)
            start_index += retrieved
            remaining = total - start_index
        else:
            return None

    def create_or_update_note(self, new_note):
        """ Create new note or update existing one if there's any with provided tile
        Arguments:
        new_note  -- new note dictionary with the following items:
          'title'    -- note title, should be unique, this field is used to search for existing note
          'content'  -- note data in ENML markup. See https://dev.evernote.com/doc/articles/enml.php
          'notebook' -- name of the notebook to create note in (ignored on 'update')
          'created'  -- note creation time in milliseconds from epoch
          'updated'  -- note last updated time in milliseconds from epoch
        """
        note_title = new_note.get('title')
        note_contents = new_note.get('content')
        notebook_name = new_note.get('notebook')
        note_created = new_note.get('created')
        note_updated = new_note.get('updated')
        note = self.find_note(note_title)
        if note:
            note.content = note_contents
            note.created = note_created
            note.updated = note_updated
            self.note_store.updateNote(note)
        else:
            note = Note()
            note.title, note.content = note_title, note_contents
            note.created, note.updated = note_created, note_updated
            for notebook in self.note_store.listNotebooks():
                if notebook.name == notebook_name:
                    note.notebookGuid = notebook.guid
                    break
            else:
                if notebook_name:
                    # Notebook not found, create new one
                    notebook = Notebook()
                    notebook.name = notebook_name
                    notebook = self.note_store.createNotebook(notebook)
                    note.notebookGuid = notebook.guid
            self.note_store.createNote(note)

    def cat_note(self, note_title):
        note = self.find_note(note_title)
        if note:
            print(note.content)


def convert_tomboy_to_evernote(note_path):
    def el(name, parent=''):
        return '{{http://beatniksoftware.com/tomboy{}}}{}'.format(parent, name)

    tags_convertion = {el('bold'): 'strong',
                       el('underline'): ['span style="text-decoration: underline;"', 'span'],
                       el('monospace'): ['span style="font-family: \'courier new\', courier, monospace;"', 'span'],
                       el('list'): 'ul',
                       el('list-item'): 'li',
                       el('small', '/size'): ['span style="font-size: 8pt;"', 'span'],
                       el('large', '/size'): ['span style="font-size: 14pt;"', 'span'],
                       el('huge', '/size'): ['span style="font-size: 18pt;"', 'span'],
                       }

    def innertext(tag):
        """Convert Tomboy XML to Markdown"""
        text = html.escape(tag.text or '')
        tail_text = html.escape('{}'.format(tag.tail or ''))
        try:
            if tag.tag == el('url', '/link') and not text.startswith('/'):
                text = quote(text, safe="/;%[]=:$&())+,!?*@'~")
                if not urlparse(text).scheme:
                    text = 'http://{}'.format(text)
                ev_tag = ('a shape="rect" href="{}"'.format(text), 'a')
                text = '<{}>{}</{}>'.format(ev_tag[0], text, ev_tag[1])
            else:
                ev_tag = tags_convertion[tag.tag]
                if isinstance(ev_tag, list):
                    start_tag, end_tag = ev_tag
                else:
                    start_tag = end_tag = ev_tag
                text = '<{}>{}'.format(start_tag, text.replace(' ', '&nbsp;'))
                tail_text = '</{}>{}'.format(end_tag, tail_text)
        except KeyError:
            # Unsupported tag - leave as plain text
            pass
        return '{}{}{}'.format(text, ''.join(innertext(e) for e in tag), tail_text)

    TOMBOY_CAT_PREFIX = 'system:notebook:'
    root = xml.parse(note_path).getroot()

    tags = []
    notebook = None

    tagsEl = root.find(el('tags'))
    if tagsEl is not None:
        for tagEl in tagsEl:
            tag = tagEl.text
            if tag.startswith(TOMBOY_CAT_PREFIX):
                notebook = tag.replace(TOMBOY_CAT_PREFIX, '')
            else:
                tags.append(tag)
    if 'system:template' in tags:
        return None

    note = {}

    title = root.find(el('title')).text
    # Empty title should be replaced with note creation date
    created = '{}'.format(isodate.parse_datetime(root.find(el('create-date')).text))
    if not title:  # title is empty
        title = created
    title = title.lstrip()
    if not title:  # it consisted only of spaces, which is illegal
        title = created

    # Parse and convert contents to evernote format
    EVERNOTE_HEADER = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                       "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n")
    content_tag = root.find(el('text')).find(el('note-content'))
    content = innertext(content_tag).replace(title, '', 1).lstrip()
    content = '{}<en-note>{}</en-note>'.format(EVERNOTE_HEADER, ''.join(['{}<br clear="none"/>'.format(line.strip())
                                                                         if not line.strip().endswith('</ul>')
                                                                         else '{}'.format(line.strip())
                                                                         for line in content.split('\n')]))

    for tag, key in [('create-date', 'created'), ('last-change-date', 'updated')]:
        # store time as milliseconds (https://dev.evernote.com/doc/reference/Types.html#Typedef_Timestamp)
        note[key] = int(time.mktime(isodate.parse_datetime(root.find(el(tag)).text).timetuple())) * 1000

    note['title'] = title
    note['content'] = content
    note['tags'] = tags
    note['notebook'] = notebook
    return note
