import os
import tempfile
import pytest
from evernote.edam.error.ttypes import EDAMUserException
from tomboy2evernote.tomboy2evernote import Evernote, convert_tomboy_to_evernote

__author__ = 'aikikode'

TOMBOY_HEADER = ("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
                 "<note version=\"0.3\" xmlns:link=\"http://beatniksoftware.com/tomboy/link\" "
                 "xmlns:size=\"http://beatniksoftware.com/tomboy/size\" xmlns=\"http://beatniksoftware.com/tomboy\">")


class TestEvernote(object):
    def test_init_no_params(self):
        with pytest.raises(TypeError):
            Evernote()

    def test_init_wrong_token(self):
        with pytest.raises(EDAMUserException):
            Evernote("wrong_token")


class TestT2EvConverter(object):
    def test_empty_note_error(self):
        _, tomboy_note = tempfile.mkstemp()
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title></title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text></note>""")
        try:
            with pytest.raises(AttributeError):  # Title should never be empty
                convert_tomboy_to_evernote(tomboy_note)
        except:
            raise
        finally:
            os.remove(tomboy_note)

    def test_simple_empty_note(self):
        _, tomboy_note = tempfile.mkstemp()
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text></note>""")
        try:
            ev_note = convert_tomboy_to_evernote(tomboy_note)
            assert ev_note['title'] == 'Hello'
            assert ev_note['content'] == '<br clear="none"/>'
            assert ev_note['notebook'] is None
            assert ev_note['tags'] == []
        except:
            raise
        finally:
            os.remove(tomboy_note)