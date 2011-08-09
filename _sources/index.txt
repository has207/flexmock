====================================
 Flexmock - Mocking Library
====================================

 :Author: `Herman Sheremetyev <http://github.com/has207>`_
 :Version: |version|
 :Homepage: `Flexmock Homepage`_
 :Contribute: `Flexmock on Github`_
 :Download: `http://pypi.python.org/pypi/flexmock <http://pypi.python.org/pypi/flexmock>`_
 :License: `FreeBSD-style License`_
 :Issue tracker: `Issue Tracker <http://github.com/has207/flexmock/issues>`_
 :Twitter: `Follow pyflexmock <http://twitter.com/#!/pyflexmock>`_

 .. _Flexmock on Github: http://github.com/has207/flexmock
 .. _Flexmock Homepage: http://has207.github.com/flexmock
 .. _FreeBSD-style License: http://github.com/has207/flexmock/blob/master/LICENSE

Flexmock is a mock/stub/spy library for Python.

Its API is inspired by a Ruby library of the same name.
However, it is not a goal of Python Flexmock to be a clone of the Ruby version.
Instead, the focus is on providing full support for testing Python programs
and making the creation of fake objects as unobtrusive as possible.

As a result, Python Flexmock removes a number of redandancies in
the Ruby Flexmock API, alters some defaults, and introduces a number of Python-only features.

Flexmock's design focuses on simplicity and intuitivenes. This means that the API
is as lean as possible, though a few convenient short-hand methods are provided to aid
brevity and readability.

Flexmock declarations are structured to read more like English sentences than API calls,
and it is possible to chain them together in any order to achieve high degree of
expressiveness in a single line of code.

Installation
============

::

    $ sudo easy_install flexmock

Or download the tarball, unpack it and run:

::

    $ sudo python setup.py install


Compatibility
=============

Tested to work with:

- python 2.4.4
- python 2.5
- python 2.6
- python 2.7
- python 3.1.2
- python 3.2.1rc2

Start Here
==========

.. toctree::

   start

User Guide
===================

.. toctree::

   user-guide

API
===

.. toctree::

   api

Comparison
==========

.. toctree::

   compare
