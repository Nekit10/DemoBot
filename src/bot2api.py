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

from threading import Thread
from multiprocessing import Queue

import requests

import src.logger


class Bot2API:
    """
    This class works with Telegram Bot API using HTTP-requests ans `requests` python library
    This class is multithreading-safe
    """

    _config: dict
    _token: str
    _url: str

    _message_listeners: list
    _command_listeners: dict
    _inline_listeners: dict

    _updater_loop: Thread
    _updater_command_queue: Queue

    def __init__(self, debug_mode: bool):
        config_filename = 'config.json' if not debug_mode else 'devconfig.json'
        self._load_config(config_filename)

        self._token = self._config['token']
        self._url = 'https://api.telegram.org/bot' + self._token

        self._updater_command_queue = Queue()
        self._updater_loop = self._UpdaterLoopThread(self._updater_command_queue)
        self._updater_loop.setDaemon(True)
        self._updater_loop.start()

    def add_message_listener(self, listener, *args, **kwargs) -> None:
        """
        This methods adds `listener` as listener for new updates.
        UpdaterLoopThread will call listener(update: dict, *args, **kwargs) for every new update
        """

        if not callable(listener):
            raise TypeError('Message listener must be callable')

        self._message_listeners += [[listener, args, kwargs]]

    def add_command_listener(self, command: str, listener, timeout_seconds: int = 300) -> None:
        """
        This methods adds `listener` as listener for running /`command`@BotName.
        UpdaterLoopThread will call listener(chat_id: int, from_id: int) for every new command.
        Listener will be killed after timeout_seconds
        """

        if not callable(listener):
            raise TypeError('Command listener must be callable')

        if timeout_seconds > 600:
            raise OverflowError('Timeout must be smaller than 10 minutes')

        self._command_listeners[command] = listener
        self.add_message_listener(self._command_listener_def, command, timeout_seconds)

    def add_inline_listener(self, msg_id: int, chat_id: int, listener, timeout_seconds: int = 1) -> None:
        """
        This methods adds `listener` as listener for running /`command`@BotName.
        UpdaterLoopThread will call listener(chat_id: int, from_id: int) for every new command.
        Listener will be killed after timeout_seconds
        """

        if not callable(listener):
            raise TypeError('Command listener must be callable')

        if timeout_seconds > 60:
            raise OverflowError('Timeout must be smaller than 1 minute')

        self._inline_listeners[str(msg_id) + '_' + str(chat_id)] = listener
        self.add_message_listener(self._inline_listener_def, msg_id, chat_id, timeout_seconds)

    def start_poll(self, chat_id: int, question: str, answers: list) -> dict:
        return self._respond_prepare(self._request_prepare('sendPoll', {
            'chat_id': chat_id,
            'question': question,
            'options': answers
        }))

    def send_message(self, chat_id: int, message: str) -> dict:
        return self._respond_prepare(self._request_prepare('sendMessage', {'chat_id': chat_id, 'text': message}))

    def kick_chat_member(self, chat_id: int, user_id: int) -> dict:
        pass

    def _load_config(self, filename: str) -> None:
        pass

    def _request_prepare(self, command_name: str, args: dict) -> requests.Response:
        pass

    def _command_listener_def(self, update: dict, command: str, timeout_seconds: int = 300) -> None:
        pass

    def _inline_listener_def(self, update: dict,  msg_id: int, chat_id: int, timeout_seconds: int = 300) -> None:
        pass

    def _respond_prepare(self, response: requests.Response) -> dict:
        pass

    def _run_request(self) -> requests.Response:
        pass

    class _UpdaterLoopThread(Thread):
        def __init__(self, cmd_queue: Queue):
            Thread.__init__(self)

        def run(self):
            pass
