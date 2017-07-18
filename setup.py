from setuptools import setup
from twitchobserver import __version__

setup(name='twitchobserver',
      version=__version__,
      description='Turn Twitch chatter into Python events.',
      long_description="""twitch-observer
===============

twitchobserver makes interacting with Twitch chat super easy. It is
built and tuned for realtime applications. You can make chatbots chat.
You can build *Twitch Plays* video games.

Features
--------

-  *Pure Python:* No extra dependencies. Just plain and simple Python.
-  *Small API:* With a few classes and a handful of methods, you can
   learn it over a coffee break.
-  *Event Based:* Makes writing apps easy and straightforward.
-  *Context Manager:* Further simplifies working with observers.

Installation
------------

``$ pip install twitchobserver``

Usage
-----

.. code:: python

    from twitchobserver import Observer

    observer = Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123')
    observer.start()
    observer.join_channel('channel')
    observer.send_message('Hello and goodbye', 'channel')
    observer.leave_channel('channel')

Documentation
-------------

API documentation can be found over on `ReadtheDocs.org`_.

Tests
-----

``$ python -m unittest discover -s tests``

Examples
--------

Echo bot
^^^^^^^^

Whenever a message is sent, echo it back. The ``Observer`` is created as
a `context manager object`_ which will implicitly handle calling
``start()`` and ``stop()``.

.. code:: python

    import time
    from twitchobserver import Observer

    with Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123') as observer:
        observer.join_channel('channel')

        while True:
            try:
                for event in observer.get_events():
                    if event.type == 'TWITCHCHATMESSAGE':
                        observer.send_message(event.message, event.channel)

                time.sleep(1)

            except KeyboardInterrupt:
                observer.leave_channel('channel')
                break

More examples can be found in the `Cookbook`_.

License
-------

MIT

.. _ReadtheDocs.org: http://twitch-observer.readthedocs.io/en/latest
.. _context manager object: https://docs.python.org/3/reference/datamodel.html#context-managers
.. _Cookbook: https://github.com/JoshuaSkelly/twitch-observer/wiki/Cookbook""",
      url='https://github.com/JoshuaSkelly/twitch-observer',
      author='Joshua Skelton',
      author_email='joshua.skelton@gmail.com',
      license='MIT',
      packages=['twitchobserver'], 
      keywords=['twitch.tv', 'twitch', 'video games', 'chatbot'],
      classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development :: Libraries :: Python Modules'
      ])

