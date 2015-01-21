tomboy2evernote
===============

[Tomboy](https://wiki.gnome.org/Apps/Tomboy) to [Evernote](https://evernote.com) export tool  

See [Tomboy notes format](https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat).

Installation
============

``python ./setup.py install``  

Usage
=====
* Upload all Tomboy notes to your Evernote account modified during the last day:  
``t2ev -t day``  
* Upload all Tomboy notes:  
``t2ev -t all``  
* Get all options:  
``t2ev --help``  

Packaging
=========

Run ``python setup.py sdist``, ``python setup.py bdist`` or
``python setup.py bdist_wheel`` to build a source, binary or wheel
distribution.
