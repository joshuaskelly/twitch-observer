# [![twitch-observer](.media/header.png)](https://github.com/JoshuaSkelly/twitch-observer)

# twitch-observer

[![License: GPL v3](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Python 2](https://img.shields.io/badge/python-2-blue.svg)](https://www.python.org/) [![Python 3](https://img.shields.io/badge/python-3-blue.svg)](https://www.python.org/) [![Build Status](https://travis-ci.org/JoshuaSkelly/twitch-observer.svg?branch=master)](https://travis-ci.org/JoshuaSkelly/twitch-observer) [![Documentation Status](https://readthedocs.org/projects/twitch-observer/badge/?version=latest)](http://twitch-observer.readthedocs.io/en/latest/?badge=latest)

Turn Twitch chatter into Python events.

## Features

- *Pure Python:* No extra dependencies. Just plain and simple Python.
- *Small API:* With a few classes and a handful of methods, you can learn it over a coffee break.
- *Event Based:* Makes writing apps easy and straightforward.
- *Context Manager:* Further simplifies working with observers.

## Installation

```$ pip install twitchobserver```

## Usage

```python
from twitchobserver import Observer

observer = Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123')
observer.start()
observer.join_channel('channel')
observer.send_message('Hello and goodbye', 'channel')
observer.leave_channel('channel')
```

## Documentation

API documentation can be found over on [ReadtheDocs.org](http://twitch-observer.readthedocs.io/en/latest).

## Tests

```$ python -m unittest discover -s tests```

## Examples

#### Echo bot

Whenever a message is sent, echo it back. The ```Observer``` is created as a [context manager object](https://docs.python.org/3/reference/datamodel.html#context-managers) which will implicitly handle calling ```start()``` and ```stop()```.

```python
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
```

More examples can be found in the [Cookbook](https://github.com/JoshuaSkelly/twitch-observer/wiki/Cookbook).

## Contributors

[![Joshua Skelton](https://avatars.githubusercontent.com/u/372642?s=130)](http://github.com/joshuaskelly) | [![Felix Siebeneicker](https://avatars0.githubusercontent.com/u/13063023?s=130)](https://github.com/pythooonuser)
---|---
[Joshua Skelton](http://github.com/joshuaskelly) | [Felix Siebeneicker](https://github.com/pythooonuser)

## License
MIT

See the [license](./LICENSE) document for the full text.
