#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi
import glob
import isodate
import lxml.etree as xml
import os
import urllib
import time
from evernote.api.client import EvernoteClient
from evernote.edam.limits.constants import EDAM_USER_NOTES_MAX
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note, Notebook
from urlparse import urlparse

__author__ = 'aikikode'

TOMBOY_DIR = os.path.join(os.environ['HOME'], ".local", "share", "tomboy")


class Evernote(EvernoteClient):
    def __init__(self, token):
        super(Evernote, self).__init__(dev_token=token)
        self.token = token
        self.note_store = self.get_note_store()

    def find_note(self, note_title):
        NOTES_RETRIEVE_COUNT = EDAM_USER_NOTES_MAX
        start_index = 0
        remaining = NOTES_RETRIEVE_COUNT
        notes = []
        while remaining >= 0:
            notes_data_list = self.note_store.findNotesMetadata(NoteFilter(words="intitle:\"{}\"".format(note_title)),
                                                                start_index, NOTES_RETRIEVE_COUNT,
                                                                NotesMetadataResultSpec())
            notes += [self.note_store.getNote(note_data.guid, True, False, False, False)
                      for note_data in notes_data_list.notes]

            total = notes_data_list.totalNotes
            retrieved = len(notes)
            start_index += retrieved
            remaining = total - start_index
        for note in notes:
            if note.title == note_title:
                print "Found the note"
                return note
        else:
            print "Didn't find the note"
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
        note_title = new_note['title']
        note_contents = new_note['content']
        notebook_name = new_note['notebook']
        note_created = new_note['created']
        note_updated = new_note['updated']
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
        print note.content


def convert_tomboy_to_evernote(note_path):
    def el(name, parent=''):
        return u"{{http://beatniksoftware.com/tomboy{}}}{}".format(parent, name)

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
        text = cgi.escape(tag.text or '')
        tail_text = cgi.escape(u'{}'.format(tag.tail or ''))
        try:
            if tag.tag == el('url', '/link') and not text.startswith('/'):
                text = urllib.quote(text.encode('utf-8'), safe="/;%[]=:$&())+,!?*@'~")
                if not urlparse(text).scheme:
                    text = "http://{}".format(text)
                ev_tag = (u'a shape="rect" href="{}"'.format(text), 'a')
                text = u'<{}>{}</{}>'.format(ev_tag[0], text, ev_tag[1])
            else:
                ev_tag = tags_convertion[tag.tag]
                text = text.replace(' ', '&nbsp;')
                if isinstance(ev_tag, list):
                    text = u'<{}>{}</{}>'.format(ev_tag[0], text, ev_tag[1])
                else:
                    text = u'<{}>{}'.format(ev_tag, text)
                    if ev_tag in ['ul', 'strong']:
                        tail_text = u'</{}>{}'.format(ev_tag, tail_text)
                    else:
                        tail_text = u'{}</{}>'.format(tail_text, ev_tag)
        except KeyError:
            # Unsupported tag - leave as plain text
            pass
        return u"{}{}{}".format(text, ''.join(innertext(e) for e in tag), tail_text)

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
    created = "{}".format(isodate.parse_datetime(root.find(el('create-date')).text))
    if not title:  # title is empty
        title = created
    title = title.lstrip()
    if not title:  # it consisted only of spaces, which is illegal
        title = created
    title = title.encode('utf-8')

    # Parse and convert contents to evernote format
    EVERNOTE_HEADER = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                       "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n")
    content_tag = root.find(el('text')).find(el('note-content'))
    content = innertext(content_tag).encode('utf-8').replace(title, '', 1).lstrip()
    content = "{}<en-note>{}</en-note>".format(EVERNOTE_HEADER, ''.join(['{}<br clear="none"/>'.format(line.strip())
                                                                         if not line.strip().endswith("</ul>")
                                                                         else "{}".format(line.strip())
                                                                         for line in content.split('\n')]))

    for tag, key in [('create-date', 'created'), ('last-change-date', 'updated')]:
        # store time as milliseconds (https://dev.evernote.com/doc/reference/Types.html#Typedef_Timestamp)
        note[key] = int(time.mktime(isodate.parse_datetime(root.find(el(tag)).text).timetuple())) * 1000

    note['title'] = title
    note['content'] = content
    note['tags'] = tags
    note['notebook'] = notebook
    return note


if __name__ == "__main__":
    dev_token = "S=s1:U=8f228:E=14eee252a16:C=1479673faa8:P=1cd:A=en-devtoken:V=2:H=d748d05b5f513e363d6f9327dd3e47ce"
    evernote = Evernote(token=dev_token)
    if True:
        tomboy_note = "/home/aikikode/.local/share/tomboy/b553a080-8c7e-4e5f-9346-07ee22660a6e.note"
    # for tomboy_note in glob.glob(os.path.join(TOMBOY_DIR, "*.note")):
        note = convert_tomboy_to_evernote(tomboy_note)
        if note:
            evernote.create_or_update_note(note)
