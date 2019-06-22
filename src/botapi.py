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
import os

import requests

from src import logger


class TelegramBotException(Exception):
    pass


def import_config(debug: bool = False):
    config_filename = 'config.json' if not debug else 'devconfig.json'
    logger.logger.debug('Using ' + config_filename + ' as config file')
    with open(config_filename, 'r') as f:
        return json.loads(f.read())


class TelegramBotAPI:
    """A set if function that communicate with official Telegram bot api"""
    token: str
    url: str
    offset: int = 0

    command_listeners = {}
    callback_query_listeners = {}

    chats = []

    polls: dict
    _POLLS_FILENAME: str = 'polls.json'
    _CHATS_FILENAME: str = 'chats.json'

    def __init__(self, token: str, debug: bool):
        """
        Create instance of TelegramBotAPI

        Params:
        token: str - your's bot token. You can get it from @BotFather in Telegram
        """
        logger.logger.debug('Running __init__ of TelegramBotAPI, token="' + token + '"')

        self.config = import_config(debug)

        self.token = token
        self.url = 'https://api.telegram.org/bot' + token
        self.polls = self._load_polls()
        self.chats = self._load_chats()

    def start_poll(self, chat_id: int, question: str, answers: list) -> dict:
        logger.logger.info('Starting poll (' + question + ') -> [' + ', '.join(answers) + ']; in chat #' + str(chat_id))
        response = requests.get('{}/sendPoll?chat_id={}&question={}&options={}'.format(
            self.url,
            str(chat_id),
            question,
            '["' + '","'.join(answers) + '"]'))

        logger.logger.debug('Got poll creation response. Status code: ' + str(response.status_code))

        response = response.json()

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        poll_id = int(response['result']['poll']['id'])
        logger.logger.debug('Successfully created poll with id: ' + str(poll_id))
        empty_poll_options = response['result']['poll']['options']
        self.polls[poll_id] = empty_poll_options

        return response

    def send_message(self, chat_id: int, msg: str) -> dict:
        logger.logger.debug('Sending message "' + msg + '" to chat #' + str(chat_id))
        response = requests.get('{}/sendMessage?chat_id={}&text={}'.format(self.url, str(chat_id), msg))

        logger.logger.debug('Got sending message response. Status code: ' + str(response.status_code))

        response = response.json()

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        logger.logger.debug('Successfully sent message')

        return response

    def get_new_updates(self) -> dict:
        logger.logger.trace('Getting new updates!')
        response = requests.get('{}/getUpdates?offset={}'.format(self.url, str(self.offset)))

        logger.logger.trace('Got updates response. Status code: ' + str(response.status_code))

        response = response.json()

        if len(response['result']) > 0:
            self.offset = response['result'][-1]['update_id'] + 1
            logger.logger.trace('Updated offset to ' + str(self.offset))

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        self._update_polls(response['result'])
        self._check_for_commands(response['result'])
        self._check_for_inline(response['result'])
        self._check_for_new_chats(response['result'])

        return response

    def kick_chat_member(self, chat_id: int, user_id: int, until_date: int = 0) -> dict:
        logger.logger.info('Kicking user with id ' + str(user_id) + ' until ' + str(until_date) + ' (in seconds), chat #' + str(chat_id))
        response = requests.get('{}/kickChatMember?chat_id={}&user_id={}&until_date={}'.format(
            self.url,
            str(chat_id),
            str(user_id),
            str(until_date)))

        logger.logger.debug('Got kicking response. Status code: ' + str(response.status_code))

        response = response.json()

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        return response

    def _get_new_updates_without_offset(self) -> dict:
        logger.logger.trace('Getting new updates w/o offset!')
        response = requests.get('{}/getUpdates'.format(self.url))

        logger.logger.trace('Got updates response. Status code: ' + str(response.status_code))

        response = response.json()

        self._check_for_commands(response['result'])
        self._check_for_inline(response['result'])

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        return response

    def send_error_message(self, chat_id: int, e: Exception) -> dict:
        logger.logger.warning('Sending error message to chat #' + str(chat_id) + ' for Exception: ' + str(e))
        return self.send_message(chat_id, 'Error: ' + str(e))

    def add_command_listener(self, command: str, listener):
        if not callable(listener):
            raise TypeError('Listener must be callable')

        self.command_listeners[command] = listener

        logger.logger.info('Successfully added listener for command /' + command)

    def send_inline_question(self, chat_id: int, msg: str, options: list, listener) -> None:
        if not callable(listener):
            raise TypeError('Listener must be callable')

        logger.logger.info('Sending message with inline reply markup to chat #' + str(chat_id) + ', msg = "' + msg)

        url_ = '{}/sendMessage?chat_id={}&text={}&reply_markup={}"inline_keyboard":[['.format(self.url, str(chat_id), msg, '{')

        for option in options:
            url_ = url_ + '{' + '"text": "{}", "callback_data": "{}"'.format(option[0], option[1]) + '}, '

        url_ = url_[:-2] + ']]}'

        response = requests.get(url_)

        logger.logger.info('Got sendMessage with inline reply markup response. Status code: ' + str(response.status_code))

        response = response.json()

        if not response['ok']:
            logger.logger.error('Got error from api! ' + response['description'])
            raise TelegramBotException(response['description'])

        msg_id = response['result']['message_id']

        self.callback_query_listeners[msg_id] = listener

    @staticmethod
    def _load_polls() -> dict:
        """Load information about all polls from file"""

        logger.logger.info('Loading polls from ' + TelegramBotAPI._POLLS_FILENAME)

        if os.path.exists(TelegramBotAPI._POLLS_FILENAME):
            with open(TelegramBotAPI._POLLS_FILENAME, 'r') as f:
                return json.loads(f.read())
        else:
            logger.logger.info('Polls file does not exist. Returning empty dict')
            return dict()

    def save_polls(self) -> None:
        """Saves information about polls to file"""

        logger.logger.trace('Saving polls to file')

        with open(TelegramBotAPI._POLLS_FILENAME, 'w') as f:
            f.write(json.dumps(self.polls))

    def get_poll_result(self, poll_id: int) -> dict:
        logger.logger.trace('Getting results of poll with id ' + str(poll_id))
        self._update_polls(self._get_new_updates_without_offset()['result'])

        logger.logger.trace('Done getting results')
        return self.polls[poll_id]

    def _update_polls(self, updates: list) -> None:
        """Update options of every poll that was updated"""

        logger.logger.trace('Updating polls')

        for update in updates:
            if 'poll' in update.keys():
                poll_id = int(update['poll']['id'])
                poll_options = update['poll']['options']
                self.polls[poll_id] = poll_options
                logger.logger.trace('Updated poll with id ' + str(poll_id))

    def _check_for_commands(self, updates: list) -> None:
        """Checking if messages contain message with command. If yes will launch command listener"""

        logger.logger.trace('Checking for commands')

        for update in updates:
            try:
                if update['message']['text'].startswith('/') and (self.config['bot_username'] in update['message']['text'] or update['message']['chat']['type'] == 'private'):
                    command = update['message']['text'].replace('@', ' ').split()[0][1:]

                    if command in self.command_listeners.keys():
                        self.command_listeners[command](update['message']['chat']['id'], update['message']['from']['id'])
            except (NameError, IndexError, KeyError) as e:
                logger.logger.trace('Ignored name exception in checking report command: ' + str(e))

    def _check_for_inline(self, updates: list):
        """Checking updates for callback_query"""

        logger.logger.trace('Checking for callback_query')

        for update in updates:
            try:
                if 'callback_query' in update.keys():
                    msg_id = update['callback_query']['message']['message_id']
                    if msg_id in self.callback_query_listeners.keys():
                        self.callback_query_listeners[msg_id](update['callback_query']['message']['chat']['id'], update['callback_query']['data'])
            except (NameError, IndexError, KeyError) as e:
                logger.logger.trace('Ignored name exception in checking callback_query command: ' + str(e))

    def _load_chats(self) -> list:
        chats_full_path = os.path.join(os.path.dirname(__file__), '../' + self._CHATS_FILENAME)

        if os.path.isfile(chats_full_path):
            with open(chats_full_path, 'r') as f:
                return json.loads(f.read())

    def _save_chats(self):
        chats_full_path = os.path.join(os.path.dirname(__file__), '../' + self._CHATS_FILENAME)

        with open(chats_full_path, 'w') as f:
            f.write(json.dumps(self.chats))

    def _check_for_new_chats(self, updates: list):
        for update in updates:
            try:
                chat_id = update['message']['chat']['id']
                if chat_id not in self.chats:
                    self.chats += [chat_id]
            except (NameError, IndexError, KeyError) as e:
                logger.logger.trace('Ignored name exception in for new chats: ' + str(e))
        self._save_chats()
