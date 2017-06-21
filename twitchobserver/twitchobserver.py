import re
import socket
import threading
import time


class BadTwitchChatEvent(Exception):
    pass


class TwitchChatEvent(object):
    """A class for representing Twitch chat events.
    
    Attributes:
        type: Type of the event. Always will be 'TWITCHCHATEVENT'.
        
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

        channel: Optional. The name of the initial channel to connect to. This
            is typically the user's nickname.
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
        self._inbound_poll_interval = 30 / 40
        self._outbound_send_interval = 30 / 20
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

    def _notify_subscribers(self, *args, **kwargs):
        for callback in self._subscribers:
            callback(*args, **kwargs)

    def get_events(self):
        """Returns a sequence of events since the last time called.
        
        Returns: A sequence of TwitchChatEvents
        """

        with self._inbound_lock:
            result = self._inbound_event_queue[:]
            self._inbound_event_queue = []

        return result

    def _send_events(self, *events):
        """Queues up the given events for sending.
        """

        with self._outbound_lock:
            for event in events:
                if not isinstance(event, TwitchChatEvent):
                    raise BadTwitchChatEvent('Invalid event type: {}'.format(type(event)))

                self._outbound_event_queue.append(event)

    def send_message(self, message, channel):
        """Sends a message to a channel.
        """

        self._send_events(TwitchChatEvent(channel, "PRIVMSG", message))

    def join_channel(self, channel):
        """Joins a channel.
        """

        self._send_events(TwitchChatEvent(channel, "JOIN"))

    def leave_channel(self, channel):
        """Leaves a channel.
        """
        
        self._send_events(TwitchChatEvent(channel, "PART"))

    def start(self):
        """Starts the observer.

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
            self.join_channel(self._channel)

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
                            event.channel = args[1:]

                        elif cmd == 'PRIVMSG':
                            channel, message = message_pattern.match(args).groups()
                            event.channel = channel[1:]
                            event.message = message

                        self._notify_subscribers(event)

                        with self._inbound_lock:
                            self._inbound_event_queue.append(event)

                    time.sleep(self._inbound_poll_interval)

                except OSError:
                    # Forcing the socket to shutdown will result in this
                    # exception
                    pass

                except socket.timeout as e:
                    if e.message != 'timed out':
                        raise socket.error

        def outbound_worker():
            """Worker thread function that handles the outgoing messages to
            Twitch IRC.
            
            Warning:
                Exceeding the Twitch message limit will result in a soft ban.
            """

            while self._is_running:
                try:
                    if self._outbound_event_queue and time.time() - self._last_time_sent > self._outbound_send_interval:
                        with self._outbound_lock:
                            event = self._outbound_event_queue.pop(0)

                        with self._socket_lock:
                            self._socket.send(event.dumps().encode('utf-8'))

                        self._last_time_sent = time.time()

                    time.sleep(self._outbound_send_interval / 2)

                except OSError:
                    pass

        self._inbound_worker_thread = threading.Thread(target=inbound_worker)
        self._inbound_worker_thread.start()

        self._outbound_worker_thread = threading.Thread(target=outbound_worker)
        self._outbound_worker_thread.start()

    def stop(self, force_stop=False):
        """Stops the observer.

        Stop watching the channel, shutdown the socket, and stop the worker
        threads once all of the outbound events have been sent.

        Args:
            force_stop: Immediately stop and do not wait for remaining outbound
                events to be sent.
        """

        # Wait until all outbound events are sent
        while self._outbound_event_queue and not force_stop:
            time.sleep(self._outbound_send_interval)

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
