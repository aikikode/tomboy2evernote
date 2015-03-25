#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile

import pytest

from evernote.edam.error.ttypes import EDAMUserException

from tomboy2evernote.tomboy2evernote import Evernote, convert_tomboy_to_evernote

__author__ = 'Denis Kovalev (aikikode)'

TOMBOY_HEADER = (
    "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
    "<note version=\"0.3\" xmlns:link=\"http://beatniksoftware.com/tomboy/link\" "
    "xmlns:size=\"http://beatniksoftware.com/tomboy/size\" xmlns=\"http://beatniksoftware.com/tomboy\">"
)


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

    def base_content_test(self, note, tomboy_xml, evernote_xml):
        with open(note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write(tomboy_xml)
        ev_note = convert_tomboy_to_evernote(note)
        assert ev_note['content'] == evernote_xml

    def test_empty_title_error(self, tomboy_note):
        """ Empty title should be replaced with note creation date """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write(
                """<title></title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>"""
            )
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == '2014-08-04 17:59:08.929727+04:00'

    def test_space_title(self, tomboy_note):
        """ Empty title should be replaced with note creation date """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write(
                """<title>    </title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>"""
            )
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == '2014-08-04 17:59:08.929727+04:00'

    def test_title_with_spaces(self, tomboy_note):
        """ Title should strip spaces only from the left """
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write(
                """<title>  Hello World  </title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>"""
            )
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == 'Hello World  '

    def test_simple_empty_note(self, tomboy_note):
        with open(tomboy_note, 'w') as f:
            f.write(TOMBOY_HEADER)
            f.write(
                """<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>"""
            )
        ev_note = convert_tomboy_to_evernote(tomboy_note)
        assert ev_note['title'] == 'Hello'
        assert ev_note['content'] == '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><br clear="none"/></en-note>'''
        assert 'notebook' not in ev_note
        assert ev_note['tags'] == []

    def test_plain_text_note(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            """<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"></note-content>This is plain text note.\nNew paragraph\n\nTest Test.</text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>""",
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>This is plain text note.<br clear="none"/>New paragraph<br clear="none"/><br clear="none"/>Test Test.<br clear="none"/></en-note>'''
        )

    def test_list(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">list:
<list><list-item dir="ltr">first element
</list-item><list-item dir="ltr">second element
<list><list-item dir="ltr">deep elem
</list-item></list></list-item><list-item dir="ltr">third element</list-item></list>
New paragraph</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>list:<br clear="none"/><ul><li>first&nbsp;element<br clear="none"/></li><li>second&nbsp;element<br clear="none"/><ul><li>deep&nbsp;elem<br clear="none"/></li></ul></li><li>third&nbsp;element</li></ul>New paragraph<br clear="none"/></en-note>'''
        )

    def test_url(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">element with link: <link:url>http://google.com</link:url> after the link</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>element with link: <a shape="rect" href="http://google.com">http://google.com</a> after the link<br clear="none"/></en-note>'''
        )

    def test_bold(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">elem in <bold>bold</bold> and normal</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>elem in <strong>bold</strong> and normal<br clear="none"/></en-note>'''
        )

    def test_underline(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">elem in <strong>bold</strong> and normal</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>elem in bold and normal<br clear="none"/></en-note>'''
        )

    def test_bold_underline(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">this is <bold>und start, <underline>both bold and underline</underline></bold> and back to normal</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>this is <strong>und&nbsp;start,&nbsp;<span style="text-decoration: underline;">both&nbsp;bold&nbsp;and&nbsp;underline</span></strong> and back to normal<br clear="none"/></en-note>'''
        )

    def test_underline_bold(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">this is <underline>bold start, <bold>both bold and underline</bold> underline again</underline> and back to normal</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>this is <span style="text-decoration: underline;">bold&nbsp;start,&nbsp;<strong>both&nbsp;bold&nbsp;and&nbsp;underline</strong> underline again</span> and back to normal<br clear="none"/></en-note>'''
        )

    def test_fixed_width_font(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"><monospace>Fixed width font</monospace>
<monospace>And this too</monospace> back to normal font</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><span style="font-family: \'courier new\', courier, monospace;">Fixed&nbsp;width&nbsp;font</span><br clear="none"/><span style="font-family: \'courier new\', courier, monospace;">And&nbsp;this&nbsp;too</span> back to normal font<br clear="none"/></en-note>'''
        )

    def test_font_sizes(self, tomboy_note):
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1"><size:small>small font</size:small>
normal font
<size:large>large font</size:large>
<size:huge>very large font</size:huge></note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><span style="font-size: 8pt;">small&nbsp;font</span><br clear="none"/>normal font<br clear="none"/><span style="font-size: 14pt;">large&nbsp;font</span><br clear="none"/><span style="font-size: 18pt;">very&nbsp;large&nbsp;font</span><br clear="none"/></en-note>'''
        )

    def test_unsupported_tags(self, tomboy_note):
        """ All text with unsupported tags should be treated as plain text """
        self.base_content_test(
            tomboy_note,
            '''<title>Hello</title>
<text xml:space="preserve"><note-content version="0.1">Normal text with <unknown_tag>bla-bla</unknown_tag>. That's it.</note-content></text>
<last-change-date>2014-08-08T18:02:02.0980690+04:00</last-change-date>
<last-metadata-change-date>2014-08-08T18:02:02.0980690+04:00</last-metadata-change-date>
<create-date>2014-08-04T17:59:08.9297270+04:00</create-date></note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>Normal text with bla-bla. That&#x27;s it.<br clear="none"/></en-note>'''
        )

    def test_html(self, tomboy_note):
        """ """
        self.base_content_test(
            tomboy_note,
            '''<title>test html</title>
<text xml:space="preserve"><note-content version="0.1">test html
&lt;!DOCTYPE html&gt;
&lt;html lang="en"&gt;
&lt;head&gt;
    &lt;title&gt;Tomboy&lt;/title&gt;
&lt;/head&gt;
&lt;body&gt;
    body content
    &lt;link rel="shortcut icon" href="/favicon.ico"&gt;
    &lt;link rel="search" type="application/opensearchdescription+xml" href="/odd.jsp" title="sript_name"/&gt;
    &lt;!--[if IE]&gt;&lt;![endif]--&gt;
    &lt;script type="text/javascript"&gt;var contextPath = '';&lt;/script&gt;
    &lt;script type="text/javascript"&gt;
        window.comment = null;
        RTW.$(GA.LOAD.init);
    &lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;
</note-content></text>
  <last-change-date>2015-03-25T15:36:04.5560300+03:00</last-change-date>
  <last-metadata-change-date>2015-03-25T15:36:04.5574680+03:00</last-metadata-change-date>
  <create-date>2015-03-25T15:26:47.5981400+03:00</create-date>
</note>''',
            '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note>&lt;!DOCTYPE html&gt;<br clear="none"/>&lt;html lang=&quot;en&quot;&gt;<br clear="none"/>&lt;head&gt;<br clear="none"/>&lt;title&gt;Tomboy&lt;/title&gt;<br clear="none"/>&lt;/head&gt;<br clear="none"/>&lt;body&gt;<br clear="none"/>body content<br clear="none"/>&lt;link rel=&quot;shortcut icon&quot; href=&quot;/favicon.ico&quot;&gt;<br clear="none"/>&lt;link rel=&quot;search&quot; type=&quot;application/opensearchdescription+xml&quot; href=&quot;/odd.jsp&quot; title=&quot;sript_name&quot;/&gt;<br clear="none"/>&lt;!--[if IE]&gt;&lt;![endif]--&gt;<br clear="none"/>&lt;script type=&quot;text/javascript&quot;&gt;var contextPath = &#x27;&#x27;;&lt;/script&gt;<br clear="none"/>&lt;script type=&quot;text/javascript&quot;&gt;<br clear="none"/>window.comment = null;<br clear="none"/>RTW.$(GA.LOAD.init);<br clear="none"/>&lt;/script&gt;<br clear="none"/>&lt;/body&gt;<br clear="none"/>&lt;/html&gt;<br clear="none"/><br clear="none"/></en-note>'''
        )
