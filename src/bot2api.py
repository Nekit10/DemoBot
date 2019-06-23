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
        pass

    def add_command_listener(self, command: str, listener, timeout_seconds: int = 300) -> None:
        pass

    def add_inline_listener(self, msg_id: int, listener, timeout_seconds: int = 1) -> None:
        pass

    def start_poll(self, chat_id: int, question: str, answers: str) -> dict:
        pass

    def send_message(self, chat_id: int, message: str) -> dict:
        pass

    def kick_chat_member(self, chat_id: int, user_id: int) -> dict:
        pass

    def _load_config(self, filename: str) -> None:
        pass

    def _request_prepare(self, request: str) -> None:
        pass

    def _command_listener_def(self, update: dict, chat_id: int, from_user: int, command: str) -> None:
        pass

    def _inline_listener_def(self, update: dict, chat_id: int, data: str, msg_id: int) -> None:
        pass

    def _respond_prepare(self) -> dict:
        pass

    def _run_request(self) -> requests.Response:
        pass

    class _UpdaterLoopThread(Thread):
        def __init__(self, cmd_queue: Queue):
            Thread.__init__(self)

        def run(self):
            pass
