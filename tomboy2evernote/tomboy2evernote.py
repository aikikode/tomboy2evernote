#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import os
import re
from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note, Notebook
import lxml.etree as ET

__author__ = 'aikikode'

EVERNOTE_HEADER = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                   "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n")
EV_DATE_FORMAT = '%Y%m%dT%H%M%SZ'
TOMBOY_DIR = os.path.join(os.environ['HOME'], ".local", "share", "tomboy")

class Evernote(EvernoteClient):
    def __init__(self, token):
        super(Evernote, self).__init__(dev_token=token)
        self.token = token
        self.note_store = self.get_note_store()

    def create_or_update_note(self, note_title, note_contents, notebook_name=None):
        """ Create new note or update existing one if there's any with provided tile
        Arguments:
        note_title    -- note title, should be unique, this field is used to search for existing note
        note_contents -- note data in ENML markup without <en-note> tags. See https://dev.evernote.com/doc/articles/enml.php
        notebook_name -- name of the notebook to create note in (ignored on 'update')
        """
        notes_data_list = self.note_store.findNotesMetadata(NoteFilter(words="intitle:\"{}\"".format(note_title)), 0,
                                                            100, NotesMetadataResultSpec())
        notes = (self.note_store.getNote(note_data.guid, True, False, False, False)
                 for note_data in notes_data_list.notes)
        note_contents = "{}<en-note>\n{}\n</en-note>".format(EVERNOTE_HEADER, note_contents)
        for note in notes:
            if note.title == note_title:
                note.content = note_contents
                self.note_store.updateNote(note)
                break
        else:
            note = Note()
            note.title, note.content = note_title, note_contents
            for notebook in self.note_store.listNotebooks():
                if notebook.name == notebook_name:
                    notebook_guid = notebook.guid
                    note.notebookGuid = notebook_guid
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
        notes_data_list = self.note_store.findNotesMetadata(NoteFilter(words="intitle:\"{}\"".format(note_title)), 0,
                                                            100, NotesMetadataResultSpec())
        notes = (self.note_store.getNote(note_data.guid, True, False, False, False)
                 for note_data in notes_data_list.notes)
        for note in notes:
            if note.title == note_title:
                print note.content
                break


def convert_tomboy_to_evernote(note_path):
    def el(name, parent=''):
        return "{{http://beatniksoftware.com/tomboy{}}}{}".format(parent, name)

    def innertext(tag):
        """Convert Tomboy XML to Markdown"""
        text = tag.text or ''
        tail_text = ''
        tags_convertion = {el('bold'): 'strong',
                           el('underline'): ['span style="text-decoration: underline;"', 'span'],
                           el('monospace'): ['span style="font-family: \'courier new\', courier, monospace;"', 'span'],
                           el('url', '/link'): ['a href="{}"', 'a'],
                           el('list'): 'ul',
                           el('list-item'): 'li',
                           }
        try:
            ev_tag = tags_convertion[tag.tag]
            if isinstance(ev_tag, list):
                text = '<{}>{}</{}>'.format(ev_tag[0].format(text), text, ev_tag[1])
                tail_text = '{}'.format(tag.tail or '')
            else:
                text = '<{}>{}'.format(ev_tag, text)
                if ev_tag == 'ul':
                    tail_text = '</{}>{}'.format(ev_tag, tag.tail or '')
                else:
                    tail_text = '{}</{}>'.format(tag.tail or '', ev_tag)
        except KeyError:
            pass
        return "{}{}{}".format(text, ''.join(innertext(e) for e in tag), tail_text)
    TOMBOY_CAT_PREFIX = 'system:notebook:'
    root = ET.parse(note_path).getroot()

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

    # Parse contents
    contentTag = root.find(el('text')).find(el('note-content'))
    content = innertext(contentTag)
    content = content.replace(title, '', 1).lstrip()
    content = ''.join(['{}<br clear="none"/>'.format(line.strip()) if re.match('<.*>', line.strip()) else '<div>{}<br clear="none"/></div>'.format(line.strip()) for line in content.split('\n')])

    note['title'] = title
    note['content'] = content
    note['tags'] = tags
    note['notebook'] = notebook

    return note


if __name__ == "__main__":
    dev_token = ""
    evernote = Evernote(token=dev_token)
    for tomboy_note in glob.glob(os.path.join(TOMBOY_DIR, "*.note")):
        note = convert_tomboy_to_evernote(tomboy_note)
        evernote.create_or_update_note(note['title'], note['content'], note['notebook'])
