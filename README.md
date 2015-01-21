tomboy2evernote
===============
[Tomboy](https://wiki.gnome.org/Apps/Tomboy) to [Evernote](https://evernote.com) export tool  


Installation
============
1. Install Evernote SDK for Python 3  
  [Download it](https://github.com/evernote/evernote-sdk-python3), extract and run  
  ``python ./setup.py install``  
2. Install Tomboy2Evernote  
  Download sources and run  
  ``python ./setup.py install``  

Usage
=====
* Upload all Tomboy notes to your Evernote account modified during the last day:  
``t2ev -t day``  
* Upload all Tomboy notes:  
``t2ev -t all``  
* Get all options:  
``t2ev --help``  

Other
=====
See [Tomboy notes format](https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat).
