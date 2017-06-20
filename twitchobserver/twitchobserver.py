import re
import socket
import threading
import time


class BadTwitchChatEvent(Exception):
    pass


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
            
        message: The message sent by the user.
    """

    def __init__(self, channel=None, command=None, message=''):
        self.type = 'TWITCHCHATEVENT'
        self.channel = channel
        self.command = command
        self.message = message

    def dumps(self):
        return '{} #{}{}\r\n'.format(self.command, self.channel, ' :' + self.message if self.message else self.message)


class TwitchChatObserver(object):
    """Class for watching a Twitch channel. Creates events for various chat
    messages.
    
    Args:
        nickname: The user nickname to connect to the channel as.

        password: The OAuth token to authenticate with.

        channel: The name of the channel to connect to. This is typically
            the user's nickname.
    """

    def __init__(self, nickname, password, channel=None):
        self._nickname = nickname
        self._password = password
        self._channel = channel
        self._subscribers = []
        self._inbound_worker_thread = None
        self._outbound_worker_thread = None
        self._is_running = True
        self._socket = None
        self._inbound_polling_rate = 30 / 40
        self._outbound_send_rate = 30 / 20
        self._inbound_event_queue = []
        self._outbound_event_queue = []
        self._inbound_lock = threading.Lock()
        self._outbound_lock = threading.Lock()
        self._socket_lock = threading.Lock()
        self._last_time_sent = time.time()

    def subscribe(self, callback):
        """Receive events from watched channel.
        
        Args:
            callback: A function that takes a single TwitchChatEvent argument.
        """

        self._subscribers.append(callback)

    def notify(self, event):
        """Sends an event
        
        Args:
            event: A TwitchChatEvent to be sent
        """

        if not isinstance(event, TwitchChatEvent):
            raise BadTwitchChatEvent('Invalid event type: {}'.format(type(event)))

        self._outbound_event_queue.insert(0, event)

    def _notify_subscribers(self, *args, **kwargs):
        for callback in self._subscribers:
            callback(*args, **kwargs)

    def get_events(self):
        """Returns a sequence of events since the last time called
        
        Returns: A sequence of TwitchChatEvents
        """

        with self._inbound_lock:
            result = self._inbound_event_queue[:]
            self._inbound_event_queue = []

        return result

    def send_events(self, *events):
        """Queues up the given events for sending"""

        with self._outbound_lock:
            for event in events:
                if not isinstance(event, TwitchChatEvent):
                    raise BadTwitchChatEvent('Invalid event type: {}'.format(type(event)))

                self._outbound_event_queue.append(event)

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

        if self._channel:
            self._socket.send('JOIN #{}\r\n'.format(self._channel).encode('utf-8'))

        # Check to see if authentication failed
        response = self._socket.recv(1024).decode('utf-8')

        self._socket.settimeout(0.25)

        if response == ':tmi.twitch.tv NOTICE * :Login authentication failed\r\n':
            self.stop()
            raise RuntimeError('Login authentication failed')

        def inbound_worker():
            """Worker thread function that handles the incoming messages from
            Twitch IRC.
            """

            response_pattern = re.compile(':(\w*)!\w*@\w*.tmi.twitch.tv ([A-Z]*) ([\s\S]*)')
            message_pattern = re.compile('(#[\w]+) :([\s\S]*)')

            # Handle socket responses
            while self._is_running:
                try:
                    with self._socket_lock:
                        response = self._socket.recv(1024).decode('utf-8')

                    # Confirm that we are still listening
                    if response == 'PING :tmi.twitch.tv\r\n':
                        with self._socket_lock:
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

                        self._notify_subscribers(event)

                        with self._inbound_lock:
                            self._inbound_event_queue.append(event)

                    time.sleep(self._inbound_polling_rate)

                except OSError:
                    # Forcing the socket to shutdown will result in this
                    # exception
                    pass

        def outbound_worker():
            """Worker thread function that handles the outgoing messages to
            Twitch IRC.
            
            Warning:
                Exceeding the Twitch message limit will result in a soft ban.
            """

            while self._is_running:
                try:
                    if time.time() - self._last_time_sent > self._outbound_send_rate and self._outbound_event_queue:
                        event = self._outbound_event_queue.pop(0)

                        with self._socket_lock:
                            self._socket.send(event.dumps().encode('utf-8'))

                        self._last_time_sent = time.time()

                except OSError:
                    pass

        self._inbound_worker_thread = threading.Thread(target=inbound_worker)
        self._inbound_worker_thread.start()

        self._outbound_worker_thread = threading.Thread(target=outbound_worker)
        self._outbound_worker_thread.start()

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

        if self._inbound_worker_thread:
            worker = self._inbound_worker_thread
            self._inbound_worker_thread = None
            worker.join()

        if self._outbound_worker_thread:
            worker = self._outbound_worker_thread
            self._outbound_worker_thread = None
            worker.join()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
