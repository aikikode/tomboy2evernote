===============
tomboy2evernote
===============

[Tomboy](https://wiki.gnome.org/Apps/Tomboy) to [Evernote](https://evernote.com) synchronization tool  

See [Tomboy notes format](https://wiki.gnome.org/Apps/Tomboy/NoteXmlFormat).

Packaging
=========

Run ``python setup.py sdist``, ``python setup.py bdist`` or
``python setup.py bdist_wheel`` to build a source, binary or wheel
distribution.


Documentation
=============

Build the documentation with ``python setup.py docs`` and run doctests with
``python setup.py doctest``.


Unittest & Coverage
===================

Run ``python setup.py test`` to run all unittests defined in the subfolder
``tests`` with the help of `py.test <http://pytest.org/>`_. The py.test plugin
`pytest-cov <https://github.com/schlamar/pytest-cov>`_ is used to automatically
generate a coverage report.
