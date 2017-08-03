.. twitch-observer documentation master file, created by
   sphinx-quickstart on Thu Jun 29 21:01:11 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

twitch-observer Documentation
=============================

.. image:: ../.media/header.png
   :target: https://github.com/JoshuaSkelly/twitch-observer
   :align: center
   :alt: Header Image

Turn Twitch chatter into Python events.

**twitchobserver** makes interacting with Twitch chat super easy. It is built and tuned for realtime applications. You can make chatbots chat. You can build Twitch Plays video games.

Features
========

- *Pure Python:* No extra dependencies. Just plain and simple Python.
- *Small API:* With a few classes and a handful of methods, you can learn it over a coffee break.
- *Event Based:* Makes writing apps easy and straightforward.
- *Context Manager:* Further simplifies working with observers.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. module:: twitchobserver.twitchobserver

TwitchChatObserver
==================

.. autoclass:: TwitchChatObserver
   :members:

TwitchChatEvent
===============

.. autoclass:: TwitchChatEvent
   :members:

BadTwitchChatEvent
==================

.. autoclass:: BadTwitchChatEvent
   :members:

TwitchChatEventType
===================

.. autoclass:: TwitchChatEventType
   :members:
   :undoc-members:

TwitchChatColor
===============

.. autoclass:: TwitchChatColor
   :members:
   :undoc-members:

Aliases
=======

There exist the following aliases:

.. module:: twitchobserver

.. autoclass:: Observer
.. autoclass:: ChatEvent
.. autoclass:: ChatEventType
.. autoclass:: ChatColor
