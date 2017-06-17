# [![twitch-observer](.media/header.png)](#)

# twitch-observer

[![License: GPL v3](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Python 2](https://img.shields.io/badge/python-2-blue.svg)]() [![Python 3](https://img.shields.io/badge/python-3-blue.svg)]()

Turn Twitch chatter into Python events.

## Examples

#### Polling for Events

Whenever a viewer joins chat, print out a greeting.

```python
import time
from twitchobserver import TwitchChatObserver

with TwitchChatObserver('SkellyTwitchBot', 'oauth:hafb5zmpi1eezuyflsl19xn7ktmp5c', '#joshuaskelly') as observer:
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
        

observer = TwitchChatObserver('BotNick', 'oauth:abcdefghijklmnopqrstuvwxyz0123', '#channel')
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

## License
MIT

See the [license](./LICENSE) document for the full text.
