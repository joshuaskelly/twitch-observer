# [![twitch-observer](.media/header.png)](https://github.com/JoshuaSkelly/twitch-observer)

# twitch-observer

[![License: GPL v3](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Python 2](https://img.shields.io/badge/python-2-blue.svg)](https://www.python.org/) [![Python 3](https://img.shields.io/badge/python-3-blue.svg)](https://www.python.org/) [![Build Status](https://travis-ci.org/JoshuaSkelly/twitch-observer.svg?branch=master)](https://travis-ci.org/JoshuaSkelly/twitch-observer) [![Documentation Status](https://readthedocs.org/projects/twitch-observer/badge/?version=latest)](http://twitch-observer.readthedocs.io/en/latest/?badge=latest)

Turn Twitch chatter into Python events.

## Features

- *Pure Python:* No extra dependencies. Just plain and simple Python.
- *Small API:* With three classes and twelve methods, you can learn it over a coffee break.
- *Event Based:* Makes writing apps easy and straightforward.
- *Context Manager:* Further simplifies working with observers.

## Usage

### 1. Installation

To install twitch-observer clone from the [repo](https://github.com/JoshuaSkelly/twitch-observer) and run:

```
$ pip install .
```

Directly installing from PyPI will be supported in the future.

### 2. Create an Observer

To get Twitch chat events, you create an Observer that monitors a given channel. You will need to provide a username, OAuth token, and a Twitch channel name.

*Note:* To get an OAuth token visit: http://twitchapps.com/tmi/

```python
from twitchobserver import Observer

observer = Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123')
```

### 3. Get Events

The Observer class has methods to handle events both synchronously and asynchronously.

#### a. Synchronous

The ```Observer.get_events()``` method returns a sequence of ```ChatEvents``` for processing.

```python
observer.start()
observer.join_channel('channel')

while True:
    try:
        for event in observer.get_events():
            """ Do something with the event """
            
    except KeyboardInterrupt:
        break

observer.leave_channel('channel')
observer.stop()
```

#### b. Asynchronous

The ```Observer.subscribe(callback)``` method takes a callback that is invoked when Twitch chat messages are recieved. 

```python
 def event_handler(event):
     """ Do something with the event """
     
 observer.subscribe(event_handler)
 observer.start()
 observer.join_channel('channel')

 # Wait a while

 observer.leave_channel('channel')
 observer.stop()
```

### 4. Send Events

```Observer``` provides several methods to make talking to Twitch super easy.

#### a. Basic Events

#### Sending Messages

```python
observer.send_message('message', 'channel')
```

#### Joining a Channel

```python
observer.join_channel('channel')
```

#### Leaving a Channel

```python
observer.leave_channel('channel')
```

#### b. Advanced Events

#### Sending a Whisper

```python
observer.send_whisper('user', message')
```

#### Listing All Moderators of a Channel

```python
observer.list_moderators('channel')
```

#### Baning a User From a Channel

```python
observer.ban_user('user', 'channel')
```

#### Unbaning a User From a Channel

```python
observer.unban_user('user', 'channel')
```

#### Clearing a Channels History

```python
observer.clear_chat_history('channel')
```

## Tests

```$ python -m unittest discover -s tests```

## Build the Docs

Navigate to `docs` and run either

```$ make html```

or

```$ make latexpdf```

## Examples

#### Polling for Events

Whenever a viewer joins chat, print out a greeting. The ```Observer``` is created as a [context manager object](https://docs.python.org/3/reference/datamodel.html#context-managers) which will implicitly handle calling ```start()``` and ```stop()```.

```python
import time
from twitchobserver import Observer

with Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123') as observer:
    observer.join_channel('channel')

    while True:
        try:
            for event in observer.get_events():
                if event.type == 'TWITCHCHATJOIN':
                    observer.send_message('Greetings {}!'.format(event.nickname), 'channel')

            time.sleep(1)

        except KeyboardInterrupt:
            observer.leave_channel('channel')
            break
```

#### Subscribing to Events

Allow viewers to cast either a ```!yes``` or ```!no``` vote and tally the result.

```python
import time
from twitchobserver import Observer

votes = {}

def handle_event(event):
    if event.type != 'TWITCHCHATPRIVMSG':
        return
        
    if event.message[0:2].upper() == '!Y':
        votes[event.nickname] = 1
        
    elif event.message[0:2].upper() == '!N':
        votes[event.nickname] = -1
        

observer = Observer('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123')
observer.subscribe(handle_event)

observer.send_message('Voting has started!', 'channel')

observer.start()
observer.join_channel('channel')
time.sleep(60)
observer.unsubscribe(handle_event)

observer.send_message('Voting is over!', 'channel')

time.sleep(2)
tally = sum(votes.values())

if tally > 0:
    observer.send_message('The yeas have it!', 'channel')

elif tally < 0:
    observer.send_message('The nays have it!', 'channel')

else:
    observer.send_message('Its a draw!', 'channel')

observer.leave_channel('channel')
observer.stop()
```

## Contributors

[![Joshua Skelton](https://avatars.githubusercontent.com/u/372642?s=130)](http://github.com/joshuaskelly) | [![Felix Siebeneicker](https://avatars0.githubusercontent.com/u/13063023?s=130)](https://github.com/pythooonuser)
---|---
[Joshua Skelton](http://github.com/joshuaskelly) | [Felix Siebeneicker](https://github.com/pythooonuser)

## License
MIT

See the [license](./LICENSE) document for the full text.
