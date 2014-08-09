import os
import tempfile
import datetime
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
    @pytest.fixture
    def tomboy_note(self, request):
        _, tmp = tempfile.mkstemp()

        def fin():
            os.remove(tmp)

        request.addfinalizer(fin)
        return tmp

    def test_empty_title_error(self, tomboy_note):
        """ Empty title should be replaced with note creation date """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title></title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        datetime.datetime.strptime(ev_note['title'][:-6], '%Y-%m-%d %H:%M:%S.%f')

    def test_space_title(self, tomboy_note):
        """ Empty title should be replaced with note creation date """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title>    </title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        datetime.datetime.strptime(ev_note['title'][:-6], '%Y-%m-%d %H:%M:%S.%f')

    def test_title_with_spaces(self, tomboy_note):
        """ Title should strip spaces only from the left """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title>  Hello World  </title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == 'Hello World  '

    def test_simple_empty_note(self, tomboy_note):
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == 'Hello'
        assert ev_note['content'] == '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><br clear="none"/></en-note>'''
        assert ev_note['notebook'] is None
        assert ev_note['tags'] == []

    def test_plain_text_note(self, tomboy_note):
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write("""<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"></note-content>This is plain text note.\nNew paragraph\n\nTest Test.</text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""")
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['content'] == '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>This is plain text note.<br clear="none"/>New paragraph<br clear="none"/><br clear="none"/>Test Test.<br clear="none"/></en-note>'''
