import sys
import unittest

if sys.version_info[0] == 3:
    import unittest.mock as mock

else:
    import mock

from twitchobserver import Observer

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


class B(unittest.TestCase):
    def test_connect(self):
        with mock.patch('socket.socket') as mock_socket:
            mock_socket.return_value.recv.return_value = SUCCESSFUL_LOGIN_MESSAGE

            observer = Observer('nickname', 'password123', 'channel')
            observer.start()

            self.assertEqual(observer._nickname, 'nickname', 'Nickname should be set')
            self.assertEqual(observer._password, 'password123', 'Password should be set')
            self.assertEqual(observer._channel, 'channel', 'Channel should be set')
            self.assertIsNotNone(observer._inbound_worker_thread, 'Inbound worker thread should be running')
            self.assertIsNotNone(observer._outbound_worker_thread, 'Outbound worker thread should be running')
            self.assertTrue(observer._is_running, 'The observer should be running')

            observer.stop(force_stop=True)

            self.assertIsNone(observer._inbound_worker_thread, 'Inbound worker thread should not be running')
            self.assertIsNone(observer._outbound_worker_thread, 'Outbound worker thread should not be running')
            self.assertFalse(observer._is_running, 'The observer should be stopped')

    def test_failed_connect(self):
        with mock.patch('socket.socket') as mock_socket:
            mock_socket.return_value.recv.return_value = UNSUCCESSFUL_LOGIN_MESSAGE

            with self.assertRaises(RuntimeError):
                observer = Observer('nickname', 'password123', 'channel')
                observer.start()
                observer.stop(force_stop=True)

    def test_server_ping(self):
        with mock.patch('socket.socket') as mock_socket:
            mock_socket.return_value.recv.side_effect = [SUCCESSFUL_LOGIN_MESSAGE, SERVER_PING_MESSAGE]

            observer = Observer('nickname', 'password123', 'channel')
            observer.start()
            self.assertEqual(mock_socket.return_value.send.call_args[0][0], CLIENT_PONG_MESSAGE, 'Client should respond with PONG response')
            observer.stop(force_stop=True)


if __name__ == '__main__':
    unittest.main()
