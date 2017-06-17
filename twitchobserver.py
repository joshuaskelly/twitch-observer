import re
import socket
import threading
import time


class TwitchChatEvent(object):
    """A class for representing Twitch chat events.
    
    Attributes:
        type: Type of the event. Always will be 'TWITCHCHATEVENT'
        
        nickname: The nickname of the user.
        
        channel: The name of the channel.
        
        command: The command sent. Will be one of the following:
            - JOIN
            - PART
            - PRIVMSG
            
        message: Optional. The message sent by the user. Only set with the 
            'PRIVMSG' command, so check the command attribute before checking.
    """

    def __init__(self):
        self.type = 'TWITCHCHATEVENT'
        self.nickname = None
        self.channel = None
        self.command = None


class TwitchChatObserver(object):
    """Class for watching a Twitch channel. Creates events for various chat
    messages.
    
    Args:
        nickname: The user nickname to connect to the channel as.

        password: The OAuth token to authenticate with.

        channel: The name of the channel to connect to. This is typically
            the user's nickname.
    """

    def __init__(self, nickname, password, channel):
        self._nickname = nickname
        self._password = password
        self._channel = channel
        self._subscribers = []
        self._worker_thread = None
        self._is_running = True
        self._polling_rate = 20 / 30
        self._socket = None
        self._event_queue = []

    def subscribe(self, callback):
        """Receive events from watched channel.
        
        Args:
            callback: A function that takes a single TwitchChatEvent argument.
        """

        self._subscribers.append(callback)

    def _notify(self, *args, **kwargs):
        for callback in self._subscribers:
            callback(*args, **kwargs)

    def get_events(self):
        with threading.Lock():
            result = self._event_queue[:]
            self._event_queue = []

        return result

    def start(self):
        """Start watching the channel.

        Attempt to connect to the Twitch channel with the given nickname and
        password. If successful a worker thread will be started to handle
        socket communication.

        Raises:
            RuntimeError: If authentication fails
        """

        # Connect to Twitch via IRC
        self._socket = socket.socket()
        self._socket.connect(('irc.twitch.tv', 6667))
        self._socket.send('PASS {}\r\n'.format(self._password).encode('utf-8'))
        self._socket.send('NICK {}\r\n'.format(self._nickname).encode('utf-8'))
        self._socket.send('JOIN {}\r\n'.format(self._channel).encode('utf-8'))

        # Check to see if authentication failed
        response = self._socket.recv(1024).decode('utf-8')
        if response == ':tmi.twitch.tv NOTICE * :Login authentication failed\r\n':
            self.stop()
            raise RuntimeError('Login authentication failed')

        def worker():
            response_pattern = re.compile(':(\w*)!\w*@\w*.tmi.twitch.tv ([A-Z]*) ([\s\S]*)')
            message_pattern = re.compile('(#[\w]+) :([\s\S]*)')

            # Handle socket responses
            while self._is_running:
                try:
                    response = self._socket.recv(1024).decode('utf-8')

                    # Confirm that we are still listening
                    if response == 'PING :tmi.twitch.tv\r\n':
                        self._socket.send('PONG :tmi.twitch.tv\r\n'.encode('utf-8'))

                    for nick, cmd, args in [response_pattern.match(m).groups() for m in response.split('\r\n') if response_pattern.match(m)]:
                        event = TwitchChatEvent()
                        event.nickname = nick
                        event.command = cmd

                        if cmd == 'JOIN' or cmd == 'PART':
                            event.channel = args

                        elif cmd == 'PRIVMSG':
                            channel, message = message_pattern.match(args).groups()
                            event.channel = channel
                            event.message = message

                        self._notify(event)

                        with threading.Lock():
                            self._event_queue.append(event)

                    time.sleep(self._polling_rate)

                except OSError:
                    # Forcing the socket to shutdown will result in this
                    # exception
                    pass

        self._worker_thread = threading.Thread(target=worker)
        self._worker_thread.start()

    def stop(self):
        """Stops watching the channel.

        The socket to Twitch will be shutdown and the worker thread will be
        stopped.
        """

        self._is_running = False

        if self._socket:
            sock = self._socket
            self._socket = None

            sock.shutdown(socket.SHUT_RDWR)
            sock.close()

        if self._worker_thread:
            worker = self._worker_thread
            self._worker_thread = None
            worker.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
