tomboy2evernote
===============
[Tomboy](https://wiki.gnome.org/Apps/Tomboy) to [Evernote](https://evernote.com) export and synchronization tool.  

I love Tomboy notes: they are clean, easy to use, multiplatform notes with no unnecessary functionality.
I've been using them for a long time both for work and for personal notes.  

Sometimes I need to review some notes, but I'm away from my PC.
Unfortunately there's no Tomboy phone application since it's not client/server app and all your notes are stored locally.  
Luckily, there's another notes service which is client/server and provides the corresponding application - Evernote.
But is has its own drawbacks: no offline notes editing (it exists, but only for premium accounts), desktop application is overwhelmed with functionality, etc.  

So I wanted the zen simplicity of Tomboy combined with the power of Evernote phone app.

Here comes tomboy2evernote
==========================
* It provides the ability to upload all (or only some) your Tomboy notes and notebooks to your Evernote account (yes, you'll have to have one). 
  So you'll be able to use Evernote phone app to read them.
* And more than that - it can continuously monitor your Tomboy notes and upload all the changes to Evernote.  
* It is also for those who want to switch from Tomboy to Evernote: just upload all your notes to Evernote once (see usage below).

Important
=========
* Synchronization is one-way only  
  As the name states - it loads only Tomboy notes to Evernote and not vise a versa
* Tomboy notes are more important than Evernote  
  If you have two notes that have same title in Tomboy and Evernote and run this app, Evernote note will be overwritten with Tomboy one. 
* Evernote notes are "read-only"  
  It comes from the previous point. Of course you can modify your Evernote notes, but they will be overwritten with the corresponding Tomboy notes after the next tool run.  
* Use it at your own risk  
  This tool does not modify/create/delete your Tomboy notes. BUT. **It does modify/create/delete your Evernote notes.** 
  Although it can mess up only notes that have same titles, use it at your own risk.

Installation
============
1. Install Evernote SDK for Python 3  
  [Download it](https://github.com/evernote/evernote-sdk-python3), extract and run  
  ``python3 ./setup.py install``  
2. Install Tomboy2Evernote  
  Download sources and run  
  ``python3 ./setup.py install``  

Configuration
=============
1. Request your Evernote developer token by visiting the [corresponding page](https://www.evernote.com/api/DeveloperToken.action).
2. Create the file '~/.config/t2ev/settings.py' with the following contents:  
   ``DEV_TOKEN = '12345'``  
   where 12345 is your dev token

Usage
=====
## If you want just to upload some Tomboy notes to Evernote
* Upload all Tomboy notes:  
  ``t2ev -t all``  
* Upload Tomboy notes modified during the last day to your Evernote account:  
  ``t2ev -t day``  
* Get all options:  
  ``t2ev --help``  

## If you want to continuously upload all changes you make to Tomboy notes to your Evernote account  
* Run it as a daemon:  
``t2ev --daemon``  
  First it will upload all your notes to Evernote and then will sit and wait for your actions on Tomboy notes. 
  It's very handy if this PC is online 24/7.

Other
=====
See [Tomboy notes format](https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat).
