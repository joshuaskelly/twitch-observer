import sys
import time
import unittest

if sys.version_info[0] == 3:
    import unittest.mock as mock

else:
    import mock

from twitchobserver import Observer, ChatEventType

SUCCESSFUL_LOGIN_MESSAGE = """:tmi.twitch.tv 001 nickname :Welcome, GLHF!\r
:tmi.twitch.tv 002 nickname :Your host is tmi.twitch.tv\r
:tmi.twitch.tv 003 nickname :This server is rather new\r
:tmi.twitch.tv 004 nickname :-\r
:tmi.twitch.tv 375 nickname :-\r
:tmi.twitch.tv 372 nickname :You are in a maze of twisty passages, all alike.\r
:tmi.twitch.tv 376 nickname :>\r
""".encode('utf-8')

UNSUCCESSFUL_LOGIN_MESSAGE = """:tmi.twitch.tv NOTICE * :Login authentication failed\r\n""".encode('utf-8')

SERVER_PING_MESSAGE = """PING :tmi.twitch.tv\r\n""".encode('utf-8')
CLIENT_PONG_MESSAGE = """PONG :tmi.twitch.tv\r\n""".encode('utf-8')

SERVER_PRIVMSG_MESSAGE = ':nickname!nickname@nickname.tmi.twitch.tv PRIVMSG #channel :message\r\n'.encode('utf-8')
CLIENT_PRIVMSG_MESSAGE = 'PRIVMSG #channel :message\r\n'.encode('utf-8')

SERVER_JOIN_MESSAGE = ':nickname!nickname@nickname.tmi.twitch.tv JOIN #channel\r\n'.encode('utf-8')
CLIENT_JOIN_MESSAGE = 'JOIN #channel\r\n'.encode('utf-8')

SERVER_PART_MESSAGE = ':nickname!nickname@nickname.tmi.twitch.tv PART #channel\r\n'.encode('utf-8')
CLIENT_PART_MESSAGE = 'PART #channel\r\n'.encode('utf-8')

SERVER_WHISPER_MESSAGE = ':nickname!nickname@nickname.tmi.twitch.tv WHISPER nickname :message\r\n'.encode('utf-8')
CLIENT_WHISPER_MESSAGE = 'PRIVMSG #None :/w nickname message\r\n'.encode('utf-8')

SERVER_USERSTATE_TAGS_MESSAGE = '@badges=moderator/1;color=;display-name=nickname;emote-sets=0;mod=1;subscriber=0;user-type=mod :tmi.twitch.tv USERSTATE #channel'.encode('utf-8')

class TestBasicFunctionality(unittest.TestCase):
    def setUp(self):
        self.observer = Observer('nickname', 'password123')
        self.observer._inbound_poll_interval = 0
        self.observer._outbound_send_interval = 0

        self._patcher = mock.patch('socket.socket', spec=True)
        self.mock_socket = self._patcher.start()
        self.mock_socket.return_value.connect.return_value = None
        self.mock_socket.return_value.recv.side_effect = [''.encode('utf-8')]

    def tearDown(self):
        if self.observer:
            self.observer.stop(force_stop=True)
            self.observer = None

        self._patcher.stop()

    def test_connect(self):
        self.mock_socket.return_value.recv.side_effect = [SUCCESSFUL_LOGIN_MESSAGE]

        self.observer.start()

        self.assertEqual(self.observer._nickname, 'nickname', 'Nickname should be set')
        self.assertEqual(self.observer._password, 'password123', 'Password should be set')
        self.assertIsNotNone(self.observer._inbound_worker_thread, 'Inbound worker thread should be running')
        self.assertIsNotNone(self.observer._outbound_worker_thread, 'Outbound worker thread should be running')
        self.assertTrue(self.observer._is_running, 'The observer should be running')

        self.observer.stop(force_stop=True)

        self.assertIsNone(self.observer._inbound_worker_thread, 'Inbound worker thread should not be running')
        self.assertIsNone(self.observer._outbound_worker_thread, 'Outbound worker thread should not be running')
        self.assertFalse(self.observer._is_running, 'The observer should be stopped')

    def test_failed_connect(self):
        self.mock_socket.return_value.recv.side_effect = [UNSUCCESSFUL_LOGIN_MESSAGE]

        with self.assertRaises(RuntimeError):
            self.observer.start()

    def test_server_ping(self):
        self.mock_socket.return_value.recv.side_effect = [SUCCESSFUL_LOGIN_MESSAGE, SERVER_PING_MESSAGE]
        self.observer.start()
        self.assertEqual(self.mock_socket.return_value.send.call_args[0][0], CLIENT_PONG_MESSAGE, 'Observer should respond with PONG response')

    def test_subscribe_unsubscribe(self):
        def handler(event):
            pass

        self.assertEqual(len(self.observer._subscribers), 0, 'There should be no subscribers')
        self.observer.subscribe(handler)
        self.assertEqual(len(self.observer._subscribers), 1, 'There should be a single subscriber')
        self.observer.unsubscribe(handler)
        self.assertEqual(len(self.observer._subscribers), 0, 'The subscriber should be removed')

    def test_receive_privmsg(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_PRIVMSG_MESSAGE]
        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True
            self.assertEqual(event.type, 'TWITCHCHATMESSAGE', "Type should be 'TWITCHCHATMESSAGE'")
            self.assertEqual(event.nickname, 'nickname', "Nickname should be 'nickname'")
            self.assertEqual(event.message, 'message', "Message should be 'message'")
            self.assertEqual(event.channel, 'channel', "Channel should be 'channel'")

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_send_privmsg(self):
        self.observer.start()
        self.observer.send_message('message', 'channel')
        self.observer.stop()
        self.assertEqual(self.mock_socket.return_value.send.call_args[0][0], CLIENT_PRIVMSG_MESSAGE, 'Observer should respond with PRIVMSG response')

    def test_receive_join(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_JOIN_MESSAGE]
        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True

            self.assertEqual(event.type, 'TWITCHCHATJOIN', "Type should be 'TWITCHCHATJOIN'")
            self.assertEqual(event.nickname, 'nickname', "Nickname should be 'nickname'")
            self.assertEqual(event.channel, 'channel', "Channel should be 'channel'")

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_send_join(self):
        self.observer.start()
        self.observer.join_channel('channel')
        self.observer.stop()
        self.assertEqual(self.mock_socket.return_value.send.call_args[0][0], CLIENT_JOIN_MESSAGE, 'Observer should respond with JOIN response')

    def test_receive_part(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_PART_MESSAGE]
        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True
            self.assertEqual(event.type, 'TWITCHCHATLEAVE', "Type should be 'TWITCHCHATLEAVE'")
            self.assertEqual(event.nickname, 'nickname', "Nickname should be 'nickname'")
            self.assertEqual(event.channel, 'channel', "Channel should be 'channel'")

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_send_part(self):
        self.observer.start()
        self.observer.leave_channel('channel')
        self.observer.stop()
        self.assertEqual(self.mock_socket.return_value.send.call_args[0][0], CLIENT_PART_MESSAGE, 'Observer should respond with PART response')

    def test_receive_whisper(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_WHISPER_MESSAGE]
        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True
            self.assertEqual(event.type, 'TWITCHCHATWHISPER', "Type should be 'TWITCHCHATWHISPER'")
            self.assertEqual(event.nickname, 'nickname', "Nickname should be 'nickname'")
            self.assertEqual(event.message, 'message', "Message should be 'message'")

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_send_whisper(self):
        self.observer.start()
        self.observer.send_whisper('nickname', 'message')
        self.observer.stop()
        self.assertEqual(self.mock_socket.return_value.send.call_args[0][0], CLIENT_WHISPER_MESSAGE, 'Observer should respond with PRIVMSG response')

    def test_receive_userstate_tags(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_USERSTATE_TAGS_MESSAGE]

        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True

            expected_tags = {
                'display-name': 'nickname',
                'emote-sets': '0',
                'mod': '1',
                'color': '',
                'badges': 'moderator/1',
                'user-type': 'mod',
                'subscriber': '0'
            }

            self.assertEqual(event.type, 'TWITCHCHATUSERSTATE', "Type should be 'TWITCHCHATUSERSTATE'")
            self.assertEqual(event.nickname, 'tmi.twitch.tv', "Nickname should be 'tmi.twitch.tv'")
            self.assertEqual(event.tags, expected_tags, 'Event tags should be equal')

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_truncated_messages(self):
        # Bit of a hack. Because the main thread handles consuming the first
        # server response, we need to first supply a dummy message that gets
        # ignored.
        self.mock_socket.return_value.recv.side_effect = [''.encode('utf-8'), SERVER_PRIVMSG_MESSAGE[:18], SERVER_PRIVMSG_MESSAGE[18:]]

        self.callback_invoked = False

        def verify_event(event):
            self.callback_invoked = True

            self.assertEqual(event.type, 'TWITCHCHATMESSAGE', "Type should be 'TWITCHCHATMESSAGE'")
            self.assertEqual(event.nickname, 'nickname', "Nickname should be 'nickname'")
            self.assertEqual(event.message, 'message', "Message should be 'message'")
            self.assertEqual(event.channel, 'channel', "Channel should be 'channel'")

        self.observer.subscribe(verify_event)
        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')

    def test_context_manager_force_stop(self):
        with Observer('nickname', 'password123') as observer:
            observer.stop(force_stop=True)
            self.assertTrue(len(observer._outbound_event_queue) == 0, 'Outbound event queue should be empty')
            self.assertTrue(len(observer._inbound_event_queue) == 0, 'Inbound event queue should be empty')

    def test_on_event_decorator(self):
        self.mock_socket.return_value.recv.side_effect = [SERVER_PRIVMSG_MESSAGE]
        self.callback_invoked = False

        self.assertEqual(len(self.observer._subscribers), 0, 'There should be no subscribers')

        @self.observer.on_event(ChatEventType.TWITCHCHATMESSAGE)
        def verify_event(event):
            self.callback_invoked = True
            self.assertEqual(event.type, 'TWITCHCHATMESSAGE', "Type should be 'TWITCHCHATMESSAGE'")

        self.assertEqual(len(self.observer._subscribers), 1, 'There should be a single subscriber')

        self.observer.start()
        self.assertTrue(self.callback_invoked, 'Subscriber callback should be invoked')


if __name__ == '__main__':
    unittest.main()
