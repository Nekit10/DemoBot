#    This file is part of DemocraticBot.
#    https://github.com/Nekit10/DemoBot
#
#    DemocraticBot is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    DemocraticBot is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with DemocraticBot.  If not, see <https://www.gnu.org/licenses/>.
#
#    Copyright (c) 2019 Nikita Serba

import unittest
import json

from botapi import TelegramBotAPI, TelegramBotException


class TelegramBotAPITests(unittest.TestCase):
    chat_id: int = -1001346306199

    @classmethod
    def setUpClass(cls):
        with open('../devconfig.json', 'r') as f:
            token = json.loads(f.read())['token']
        TelegramBotAPI._POLLS_FILENAME = '../polls.json'
        cls.botapi = TelegramBotAPI(token)
        try:
            cls.botapi.get_new_updates()
            cls.botapi.send_message(TelegramBotAPITests.chat_id,
                                     'Starting testing DemoBot. Please, do NOT DO ANYTHING HERE UNTIL ALL TESTS END. '
                                     'Thx')
        except Exception:
            pass

    def tearDown(self) -> None:
        try:
            self.botapi.get_new_updates()
        except Exception:
            pass

    def test_astart_poll(self):
        response = self.botapi.start_poll(self.chat_id, 'Testing Poll...', ['Yes', 'No'])
        with open('pollid.tmp', 'w') as f:
            f.write(response['result']['poll']['id'])

    def test_get_poll_options(self):
        with open('pollid.tmp', 'r') as f:
            poll_id = int(f.read())
        options = self.botapi.get_poll_result(poll_id)
        self.assertEqual(0, options[0]['voter_count'])
        self.assertEqual(0, options[1]['voter_count'])

    def test_get_new_updates(self):
        self.botapi.get_new_updates()

    @unittest.skip('This test does not support running automatically')
    def test_get_poll_options_second(self):
        print('Answer NO in this poll. Press enter after voting')
        input()

        with open('pollid.tmp', 'r') as f:
            poll_id = int(f.read())

        options = self.botapi.get_poll_result(poll_id)
        self.assertEqual(0, options[0]['voter_count'])
        self.assertEqual(1, options[1]['voter_count'])

    def test_send_message_to_wrong_chat(self):
        self.assertRaises(TelegramBotException, self.botapi.send_message, -1, "Test")
        self.assertRaises(TelegramBotException, self.botapi.send_error_message, -1, Exception())
        self.assertRaises(TelegramBotException, self.botapi.start_poll, -1, "Test", ["Yes", "No"])

    def test_poll_no_answers(self):
        self.assertRaises(TelegramBotException, self.botapi.start_poll, self.chat_id, "Test", [])

    def test_send_error_message(self):
        self.botapi.send_error_message(self.chat_id, TelegramBotException('Test error'))

    def test_save_poll(self):
        self.botapi.save_polls()

    def test_send_message_second(self):
        self.botapi.send_message(self.chat_id, 'Testing ended. Thx')


if __name__ == '__main__':
    unittest.main()
