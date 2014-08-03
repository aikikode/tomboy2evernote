#!/usr/bin/env python
import os
from evernote.api.client import EvernoteClient
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.ttypes import Note

__author__ = 'aikikode'

EVERNOTE_HEADER = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                   "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n")
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
            note.title = note_title
            note.content = note_contents
            for notebook in self.note_store.listNotebooks():
                if notebook.name == notebook_name:
                    notebook_guid = notebook.guid
                    note.notebookGuid = notebook_guid
                    break
            else:
                # TODO: create notebook
                notebook_guid = None
                self.note_store.createNote(note)


if __name__ == "__main__":
    dev_token = ""
    evernote = Evernote(token=dev_token)
    evernote.create_or_update_note("Test note 123", "12345<h1>title</h1>new line")
