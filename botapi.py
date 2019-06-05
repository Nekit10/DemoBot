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

import json

import requests


class TelegramBotException(Exception):
    pass


class TelegramBotAPI:
    """A set if function that communicate with official Telegram bot api"""
    token: str
    url: str
    offset: int = 934596997

    def __init__(self, token: str):
        """
        Create instance of TelegramBotAPI

        Params:
        token: str - your's bot token. You can get it from @BotFather in Telegram
        """

        self.token = token
        self.url = 'https://api.telegram.org/bot' + token

    def start_poll(self, chat_id: int, question: str, answers: list) -> dict:
        response = json.loads(requests.get('{}/sendPoll?chat_id={}&question={}%options={}'.format(
            self.url,
            str(chat_id),
            question,
            '[' + ','.join(answers) + ']')).json())

        if not response['ok']:
            raise TelegramBotException(response['description'])

        return response

    def send_message(self, chat_id: int, msg: str) -> dict:
        response = json.loads(requests.get('{}/sendMessage?chat_id={}&text={}'.format(
            self.url,
            str(chat_id),
            msg)))

        if not response['ok']:
            raise TelegramBotException(response['description'])

        return response

    def get_new_updates(self) -> dict:
        response = json.loads(requests.get('{}/getUpdates?offset='.format(self.url, str(self.offset))))

        self.offset = response['result'][-1]['update_id'] + 1

        if not response['ok']:
            raise TelegramBotException(response['description'])

        return response

    def send_error_message(self, chat_id: int, e: Exception) -> dict:
        pass
