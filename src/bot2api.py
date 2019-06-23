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

import os
import json
import ctypes
import re
import threading
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
        This methods adds `listener` as listener for inline callback.
        UpdaterLoopThread will call listener(chat_id: int, data: str) for every new command.
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

    def send_inline_message(self, chat_id: int, message: str, options: list, listener, timeout_seconds: int):
        inline_keyboard_items = []

        for option in options:
            inline_keyboard_items += [{
                'text': option[0],
                'callback_data': option[1]
            }]

        resp = self._respond_prepare(self._request_prepare('sendMessage', {
            'chat_id': chat_id,
            'text': message,
            'reply_markup': {
                'inline_keyboard': [inline_keyboard_items]
            }
        }))

        self.add_inline_listener(resp['message_id'], resp['chat']['id'], listener, timeout_seconds)

        return resp

    def kick_chat_member(self, chat_id: int, user_id: int, until_date: int = 0) -> dict:
        return self._respond_prepare(self._request_prepare('kickChatMember', {
            'chat_id': chat_id,
            'user_id': user_id,
            'until_date': until_date
        }))

    def _load_config(self, filename: str) -> None:
        path = os.path.join(os.path.dirname(__file__), os.path.join('../', filename))

        with open(path, 'r') as f:
            self._config = json.loads(f.read())

    def _request_prepare(self, command_name: str, args: dict) -> requests.Response:
        url_ = self._url + '/' + command_name

        if args:
            url_ += '?'

            for arg_name, value in args.items():
                val_ = str(value) if type(value) != dict and type(value) != list else json.dumps(value)
                url_ += '{}={}&'.format(arg_name, val_)

            url_ = url_[:-1]

        return self._run_request(url_)

    def _command_listener_def(self, update: dict, command: str, timeout_seconds: int = 300) -> None:
        try:
            text = update['message']['text']
            if text.startswith('/' + command) and re.search(r'[^a-zA-Z]', text[1:]) and self._config['bot_username'] in text:
                thread = self._MethodRunningThread(self._command_listeners[command], update['chat']['id'], update['from']['id'])
        except (NameError, KeyError, IndexError):
            pass

    def _inline_listener_def(self, update: dict,  msg_id: int, chat_id: int, timeout_seconds: int = 300) -> None:
        pass

    def _respond_prepare(self, response: requests.Response) -> dict:
        pass

    def _run_request(self, url: str) -> requests.Response:
        pass

    class _UpdaterLoopThread(Thread):
        def __init__(self, cmd_queue: Queue):
            Thread.__init__(self)

        def run(self) -> None:
            pass

    class _MethodRunningThread(Thread):
        def __init__(self, method, *args, **kwargs):
            if not callable(method):
                raise TypeError('Method must be callable')

            self.method = method
            self.args = args
            self.kwargs = kwargs

        def run(self) -> None:
            try:
                self.method(*self.args, **self.kwargs)
            finally:
                pass  # end function here bro

        def get_id(self):
            if hasattr(self, '_thread_id'):
                return self._thread_id
            for id, thread in threading._active.items():
                if thread is self:
                    return id

            raise NotImplementedError('Hmm I don\'t know what happening')

        def exit(self):
            thread_id = self.get_id()
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                             ctypes.py_object(SystemExit))
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                raise NotImplementedError('I still don\'t know what happening')
