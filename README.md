# twitch-observer

> Easy to use

[![License: GPL v3](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![Python 2](https://img.shields.io/badge/python-2-blue.svg)]() [![Python 3](https://img.shields.io/badge/python-3-blue.svg)]()

## Examples

#### Polling for Events

```python
import time
from twitchobserver import TwitchChatObserver

with TwitchChatObserver('BotNick', 'oauth:abcdefghijklmnopqrstuvwxyz0123', '#channel') as observer:
    while True:
        try:
            for event in observer.get_events():
                if event.command == 'PRIVMSG':
                    print(event.message)
                    
            time.sleep(1)

        except KeyboardInterrupt:
            break
```

#### Subscribing to Events

Allow viewers to cast ```!yes``` or ```!no``` votes and tally the result.

```python
import time
from twitchobserver import TwitchChatObserver

votes = {}

def handle_event(event):
    if event.command != 'PRIVMSG' or event.message[0] != '!':
        return
        
    if event.message == '!yes':
        votes[event.nickname] = 1
        
    elif event.message == '!no':
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