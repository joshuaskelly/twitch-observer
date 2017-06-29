import os
import re
import socket
import sys
import threading
import time
import warnings


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
        command_to_type = {
            'JOIN': 'TWITCHCHATJOIN',
            'PART': 'TWITCHCHATLEAVE',
            'PRIVMSG': 'TWITCHCHATMESSAGE',
            'MODE': 'TWITCHCHATMODE',
            'CLEARCHAT': 'TWITCHCHATCLEARCHAT',
            'HOSTTARGET': 'TWITCHCHATHOSTTARGET',
            'NOTICE': 'TWITCHCHATNOTICE',
            'RECONNECT': 'TWITCHCHATRECONNECT',
            'ROOMSTATE': 'TWITCHCHATROOMSTATE',
            'USERNOTICE': 'TWITCHCHATUSERNOTICE',
            'USERSTATE': 'TWITCHCHATUSERSTATE',
            'WHISPER': 'TWITCHCHATWHISPER'
        }

        if command in command_to_type:
            self.type = command_to_type[command]

        else:
            self.type = 'TWITCHCHATCOMMAND'

        self.channel = channel
        self._command = command

        if message:
            self.message = message

    def dumps(self):
        message = getattr(self, 'message', '')

        if message:
            message = ' :' + message

        return '{} #{}{}\r\n'.format(self._command, self.channel, message)


# Server messages. Groups: (nickname_or_servername, command, parameters)
_sever_message_re = re.compile('(?:@(\S*)\s+)?:(\w*|tmi.twitch.tv)(?:!\w*)?(?:@\w*.tmi.twitch.tv)?\s+([A-Z]*|\d{3})\s+([^\r\n]*)')

# PRIVMSG Parameters. Groups: (channel, message)
_privmsg_params_re = re.compile('#(\w+) :([\s\S]*)')

# WHISPER parameters. Groups: (recipient, message)
_whisper_params_re = re.compile('(\w+)\s+:([\s\S]*)')

# MODE parameters. Groups: (channel, mode, nickname)
_mode_params_re = re.compile('#(\w+)\s+([+-]o)\s+(\w+)')


class TwitchChatObserver(object):
    """Class for watching a Twitch channel. Creates events for various chat
    messages.
    
    Args:
        nickname: The user nickname to connect to the channel as.

        password: The OAuth token to authenticate with.

        channel: Optional. The name of the initial channel to connect to. This
            is typically the user's nickname.
    """

    def __init__(self, nickname, password):
        self._nickname = nickname
        self._password = password
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

    def unsubscribe(self, callback):
        """Unsubscribe a callback from the observer."""

        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def _notify_subscribers(self, *args, **kwargs):
        for callback in self._subscribers:
            try:
                callback(*args, **kwargs)

            except:
                error_type, error_value, error_traceback = sys.exc_info()

                # Extract the backtrace if present
                if error_traceback.tb_next:
                    error_traceback = error_traceback.tb_next

                filename = os.path.normpath(error_traceback.tb_frame.f_code.co_filename)
                warnings.warn(RuntimeWarning("Callback '{}' raised an error:\n{}:{}: {}: {}".format(callback.__name__, filename, error_traceback.tb_lineno, error_type.__name__, error_value)))

    def get_events(self):
        """Returns a sequence of events since the last time called.
        
        Returns: A sequence of TwitchChatEvents
        """

        with self._inbound_lock:
            result = self._inbound_event_queue[:]
            self._inbound_event_queue = []

        return result

    def _send_events(self, *events):
        """Queues up the given events for sending."""

        with self._outbound_lock:
            for event in events:
                if not isinstance(event, TwitchChatEvent):
                    raise BadTwitchChatEvent('Invalid event type: {}'.format(type(event)))

                self._outbound_event_queue.append(event)

    def send_message(self, message, channel, use_color=False):
        """Sends a message to a channel."""

        self._send_events(TwitchChatEvent(channel, 'PRIVMSG', "/me {}".format(message) if use_color else message))

    def join_channel(self, channel):
        """Joins a channel."""

        self._send_events(TwitchChatEvent(channel, 'JOIN'))

    def leave_channel(self, channel):
        """Leaves a channel."""
        
        self._send_events(TwitchChatEvent(channel, 'PART'))

    def send_whisper(self, user, message):
        """Sends a whisper (private message) to a user."""

        self.send_message("/w {} {}".format(user, message), None)

    def list_moderators(self, channel):
        """Lists all moderators of a given channel."""

        self.send_message("/mods", channel)

    def ban_user(self, user, channel):
        """Bans a user from a channel."""

        self.send_message("/ban {}".format(user), channel)

    def unban_user(self, user, channel):
        """Unbans a user from a channel."""

        self.send_message("/unban {}".format(user), channel)

    def clear_chat_history(self, channel):
        """Clears the chat history of a channel."""

        self.send_message("/clear", channel)

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

        # Request Twitch-Specific Capabilities
        self._socket.send('CAP REQ :twitch.tv/membership\r\n'.encode('utf-8'))
        self._socket.send('CAP REQ :twitch.tv/commands\r\n'.encode('utf-8'))
        self._socket.send('CAP REQ :twitch.tv/tags\r\n'.encode('utf-8'))

        response = self._socket.recv(1024).decode('utf-8')
        self._socket.settimeout(0.25)

        # Handle the initial sequence of responses on main thread to raise if
        # authentication fails
        self._process_server_messages(response)

        def inbound_worker():
            """Worker thread function that handles the incoming messages from
            Twitch IRC.
            """

            truncated_response = ''

            # Handle socket responses
            while self._is_running:
                try:
                    with self._socket_lock:
                        response = truncated_response + self._socket.recv(1024).decode('utf-8')

                        if '\r\n' in response:
                            response, truncated_response = response.rsplit('\r\n', 1)

                        else:
                            response, truncated_response = '', response

                    self._process_server_messages(response)
                    time.sleep(self._inbound_poll_interval)

                except OSError:
                    # Forcing the socket to shutdown will result in this
                    # exception
                    pass

                except StopIteration:
                    # Raised by test mock under Python 2
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
            with self._socket_lock:
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

    def _process_server_messages(self, response):
        for message in [m for m in response.split('\r\n') if m]:
            # Confirm that we are still listening
            if message == 'PING :tmi.twitch.tv':
                with self._socket_lock:
                    self._socket.send('PONG :tmi.twitch.tv\r\n'.encode('utf-8'))

            # Raise if authentication fails
            elif message == ':tmi.twitch.tv NOTICE * :Login authentication failed':
                self.stop(force_stop=True)
                raise RuntimeError('Login authentication failed')

            # Handle sever messages
            match = _sever_message_re.match(message)
            if match:
                tags, nick, cmd, params = match.groups()
                event = TwitchChatEvent(command=cmd)
                event.nickname = nick
                event._command = cmd
                event._params = params

                if tags:
                    event.tags = {}

                    for tag_pair in tags.split(';'):
                        key, value = tag_pair.split('=')
                        event.tags[key] = value

                if cmd in ('JOIN', 'PART', 'USERSTATE', 'ROOMSTATE'):
                    event.channel = params[1:]

                elif cmd in ('PRIVMSG', 'HOSTTARGET', 'NOTICE', 'USERNOTICE'):
                    params_match = _privmsg_params_re.match(params)

                    if params_match:
                        channel, message = _privmsg_params_re.match(params).groups()
                        event.channel = channel
                        event.message = message

                    else:
                        warnings.warn(RuntimeWarning('Failed to process {} message: {}'.format(cmd, message)))

                elif cmd == "WHISPER":
                    params_match = _whisper_params_re.match(params)

                    if params_match:
                        _, message = _whisper_params_re.match(params).groups()
                        event.message = message

                    else:
                        warnings.warn(RuntimeWarning('Failed to process {} message: {}'.format(cmd, message)))

                elif cmd == 'MODE':
                    params_match = _mode_params_re.match(params)

                    if params_match:
                        channel, mode, nick = _mode_params_re.match(params).groups()
                        event.channel = channel
                        event.mode = mode
                        event.nickname = nick

                    else:
                        warnings.warn(RuntimeWarning('Failed to process {} message: {}'.format(cmd, message)))

                self._notify_subscribers(event)

                with self._inbound_lock:
                    self._inbound_event_queue.append(event)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
