# [![twitch-observer](.media/header.png)](https://github.com/JoshuaSkelly/twitch-observer)

# twitch-observer

[![License: GPL v3](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Python 2](https://img.shields.io/badge/python-2-blue.svg)]() [![Python 3](https://img.shields.io/badge/python-3-blue.svg)]()

Turn Twitch chatter into Python events.

## Features

- *Pure Python:* No extra dependencies. Just plain and simple Python.
- *Small API:* With two classes and four methods, you can learn it over a coffee break.
- *Event Based:* Makes writing apps easy and straightforward.
- *Context Manager:* Further simplifies working with observers.

## Usage

### 1. Installation

To install twitch-observer clone from the [repo](https://github.com/JoshuaSkelly/twitch-observer) and use:

```
$ pip install .
```
Directly installing from PyPI will be supported in the future.

### 2. Create an Observer

To get Twitch chat events, you create an Observer that monitors a given channel. You will need to provide a username, OAuth token, and a Twitch channel name.

*Note:* To get an OAuth token visit: http://twitchapps.com/tmi/

```python
from twitchobserver import TwitchChatObserver

observer = TwitchChatObserver('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123', 'channel')
```

### 3. Get Events

The TwitchChatObserver class has methods to handle events both synchronously and asynchronously.

#### a. Synchronous

The ```TwitchChatObserver.get_events()``` method returns a sequence of ```TwitchChatEvents``` for processing.

```python
observer.start()

while True:
    try:
        for event in observer.get_events():
            """ Do something with the event """
            
    except KeyboardInterrupt:
        break

observer.stop()
```

#### b. Asynchronous

The ```TwitchChatObserver.subscribe(callback)``` method takes a callback that is invoked when Twitch chat messages are recieved. 

```python
def event_handler(event):
    """ Do something with the event """
    
observer.subscribe(event_handler)
observer.start()
# Wait a while
observer.stop()
```

## Examples

#### Polling for Events

Whenever a viewer joins chat, print out a greeting. The ```TwitchChatObserver``` is created as a [context manager object](https://docs.python.org/3/reference/datamodel.html#context-managers) which will implicitly handle calling ```start()``` and ```stop()```.

```python
import time
from twitchobserver import TwitchChatObserver

with TwitchChatObserver('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123', 'channel') as observer:
    while True:
        try:
            for event in observer.get_events():
                if event.command == 'JOIN':
                    print('Greetings {}!'.format(event.nickname))

            time.sleep(1)

        except KeyboardInterrupt:
            break
```

#### Subscribing to Events

Allow viewers to cast either a ```!yes``` or ```!no``` vote and tally the result.

```python
import time
from twitchobserver import TwitchChatObserver

votes = {}

def handle_event(event):
    if event.command != 'PRIVMSG':
        return
        
    if event.message[0:2].upper() == '!Y':
        votes[event.nickname] = 1
        
    elif event.message[0:2].upper() == '!N':
        votes[event.nickname] = -1
        

observer = TwitchChatObserver('Nick', 'oauth:abcdefghijklmnopqrstuvwxyz0123', 'channel')
observer.subscribe(handle_event)

print('Voting has started!')

observer.start()
time.sleep(60)
observer.stop()

print('Voting is over!')

time.sleep(2)
tally = sum(votes.values())

if tally > 0:
    print('The yeas have it!')

elif tally < 0:
    print('The nays have it!')

else:
    print('Its a draw!')
```

## Contributors

[![Joshua Skelton](https://avatars.githubusercontent.com/u/372642?s=130)](http://github.com/joshuaskelly) | [![Felix Siebeneicker](https://avatars0.githubusercontent.com/u/13063023?s=130)](https://github.com/pythooonuser)
---|---
[Joshua Skelton](http://github.com/joshuaskelly) | [Felix Siebeneicker](https://github.com/pythooonuser)

## License
MIT

See the [license](./LICENSE) document for the full text.
