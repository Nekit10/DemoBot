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

import inspect
import os
import json
import ctypes
import random
import re
import threading
from _queue import Empty
from threading import Thread
from multiprocessing import Queue, Manager
from typing import Callable, List, Iterable, Dict, Any, Mapping

import requests
import sys

from src import logger
from sysbugs import bugtrackerapi


class AutoDelete(Exception):
    pass


class Bot2API:
    """
    This class works with Telegram Bot API using HTTP-requests ans `requests` python library
    This class is multithreading-safe
    """

    _config: dict
    _token: str
    _url: str
    _url_c = threading.Condition()

    _message_listeners: list = []
    _message_listeners_c = threading.Condition()
    _command_listeners: dict = {}
    _inline_listeners: dict = {}

    _updater_loop: Thread
    _updater_command_queue: Queue
    _updater_result_dict: Dict

    def __init__(self, debug_mode: bool):

        logger.logger.info('Creating new Bot2API instance')

        config_filename = 'config.json' if not debug_mode else 'devconfig.json'
        self._load_config(config_filename)

        self._token = self._config['token']
        self._url_c.acquire()
        self._url = 'https://api.telegram.org/bot' + self._token
        self._url_c.release()

        self._updater_command_queue = Queue()
        self._updater_result_dict = Manager().dict()
        logger.logger.info('Setuping UpdaterLoop thread')
        self._updater_loop = self._UpdaterLoopThread(self._updater_command_queue, self._updater_result_dict, self)
        self._updater_loop.setDaemon(True)
        self._updater_loop.start()
        logger.logger.info('UpdaterLoop thread was successfully started')

    def add_message_listener(self, listener: Callable, *args, **kwargs) -> None:
        """
        This methods adds `listener` as listener for new updates.
        UpdaterLoopThread will call listener(update: dict, *args, **kwargs) for every new update
        """

        logger.logger.info('Adding new message listener')

        self._message_listeners_c.acquire()
        self._message_listeners += [[listener, args, kwargs]]
        self._message_listeners_c.release()

    def add_command_listener(self, command: str, listener: Callable, timeout_seconds: int = 300) -> None:
        """
        This methods adds `listener` as listener for running /`command`@BotName.
        UpdaterLoopThread will call listener(chat_id: int, from_id: int) for every new command.
        Listener will be killed after timeout_seconds
        """

        if timeout_seconds > 600:
            raise OverflowError('Timeout must be smaller than 10 minutes')

        logger.logger.info('Adding listener for command /' + command)

        self._command_listeners[command] = listener
        self.add_message_listener(self._command_listener_def, command, timeout_seconds)

    def add_inline_listener(self, msg_id: int, chat_id: int, listener: Callable, timeout_seconds: int = 1) -> None:
        """
        This methods adds `listener` as listener for inline callback.
        UpdaterLoopThread will call listener(chat_id: int, data: str) for every new command.
        Listener will be killed after timeout_seconds
        """

        if timeout_seconds > 60:
            raise OverflowError('Timeout must be smaller than 1 minute')

        logger.logger.info('Adding listener for inline query callback (msg_id = ' + str(msg_id) + ') in chat #' + str(chat_id))

        if chat_id not in self._inline_listeners.keys():
            self._inline_listeners[chat_id] = {}
        self._inline_listeners[chat_id][msg_id] = listener
        self.add_message_listener(self._inline_listener_def, msg_id, chat_id, timeout_seconds)

    def start_poll(self, chat_id: int, question: str, answers: Iterable[str]) -> Dict[str, Any]:
        logger.logger.info('Starting poll in chat #' + str(chat_id) + ' with question "' + question + '" and options [' + ', '.join(answers) + ']')
        return self._response_prepare(self._request_prepare('sendPoll', {
            'chat_id': chat_id,
            'question': question,
            'options': answers
        }))

    def send_message(self, chat_id: int, message: str) -> Dict[str, Any]:
        logger.logger.info('Sending message "' + message + '" in chat #' + str(chat_id))
        return self._response_prepare(self._request_prepare('sendMessage', {'chat_id': chat_id, 'text': message}))

    def send_inline_message(self, chat_id: int, message: str, options: list, listener: Callable, timeout_seconds: int = 1) -> Dict[str, Any]:
        inline_keyboard_items = []

        logger.logger.info('Sending inline message "' + message + '" in chat #' + str(chat_id) + '; options: ' + str(options))

        for option in options:
            inline_keyboard_items += [{
                'text': option[0],
                'callback_data': option[1]
            }]

        resp = self._response_prepare(self._request_prepare('sendMessage', {
            'chat_id': chat_id,
            'text': message,
            'reply_markup': {
                'inline_keyboard': [inline_keyboard_items]
            }
        }))

        self.add_inline_listener(resp['message_id'], resp['chat']['id'], listener, timeout_seconds)

        return resp

    def kick_chat_member(self, chat_id: int, user_id: int, until_date: int = 0) -> Dict[str, Any]:
        logger.logger.info('Kicking user with id ' + str(user_id) + ' in chat #' + str(chat_id) + ' until ' + str(until_date))

        return self._response_prepare(self._request_prepare('kickChatMember', {
            'chat_id': chat_id,
            'user_id': user_id,
            'until_date': until_date
        }))

    def _load_config(self, filename: str) -> None:
        path = os.path.join(os.path.dirname(__file__), os.path.join('../', filename))

        logger.logger.info('Loading config in api from ' + path)

        with open(path, 'r') as f:
            self._config = json.loads(f.read())
        logger.logger.info('Successfully loaded config in api')

    def _request_prepare(self, command_name: str, args: Mapping[str, Any]) -> requests.Response:
        self._url_c.acquire()
        url_ = self._url + '/' + command_name
        self._url_c.release()

        logger.logger.info('Preparing request for command ' + command_name)

        if args:
            url_ += '?'

            for arg_name, value in args.items():
                val_ = str(value) if type(value) != dict and type(value) != list else json.dumps(value)
                url_ += '{}={}&'.format(arg_name, val_)

            url_ = url_[:-1]

        return self._run_request(url_)

    def _command_listener_def(self, update: Dict[str, Any], command: str, timeout_seconds: int = 300) -> None:
        try:
            text = update['message']['text']
            logger.logger.info('Checking update for command /' + command)
            if text.startswith('/' + command) and re.search(r'[^a-zA-Z]', text[1:]) and self._config['bot_username'] in text:
                logger.logger.info('Found command /' + command)
                thread = self._MethodRunningThread(self, -1, self._command_listeners[command], update['message']['chat']['id'], update['message']['from']['id'])
                thread.setDaemon(True)
                thread.start()
                thread.join(timeout_seconds)
                thread.exit()
        except (NameError, KeyError, IndexError):
            pass

    def _inline_listener_def(self, update: Mapping[str, Any],  msg_id: int, chat_id: int, timeout_seconds: int = 300) -> None:
        try:
            logger.logger.info('Checking update for inline query callback')
            query = update['callback_query']
            thread = self._MethodRunningThread(self, -1, self._inline_listeners[chat_id][msg_id], chat_id, query['data'])
            thread.setDaemon(True)
            thread.start()
            thread.join(timeout_seconds)
            thread.exit()
        except (NameError, KeyError, IndexError):
            pass

    @staticmethod
    def _response_prepare(response: requests.Response) -> Dict[str, Any]:
        logger.logger.info('Preparing response for url: ' + response.url)

        resp_obj = response.json()

        if response.status_code != 200 or not resp_obj['ok']:
            raise ConnectionError('Error while working with Telegram Bot API (status code = ' + str(response.status_code) + '). ' + resp_obj['description'])

        return resp_obj['result']

    def _run_request(self, url: str) -> requests.Response:
        logger.logger.info('Adding request with url ' + url + ' to command queue')
        req_id_ = random.randint(0, 2 ** 16)
        while req_id_ in self._updater_result_dict.keys():
            req_id_ = random.randint(0, 2 ** 16)

        logger.logger.debug('Choosed id ' + str(req_id_))

        self._updater_command_queue.put([req_id_, url])

        while req_id_ not in self._updater_result_dict.keys():
            pass

        logger.logger.info('Got resulr for request with id ' + str(req_id_))

        result_ = self._updater_result_dict[req_id_]
        del self._updater_result_dict[req_id_]

        return result_

    class _UpdaterLoopThread(Thread):
        _offset: int = 605766741  # Why not?

        def __init__(self, cmd_queue: Queue, result_dict: Mapping[int, Dict[str, Any]], api: object):
            Thread.__init__(self)

            logger.logger.info('Creating UpdateLoop thread instance')

            self.cmd_queue = cmd_queue
            self.result_dict = result_dict
            self.api = api

        def _make_request(self, id_: int, url: str) -> None:
            logger.logger.info('Got command ' + url + ' with id ' + str(id_))
            self.result_dict[id_] = requests.get(url)

        def _update_offset(self, updates: Iterable[Mapping[str, Any]]) -> None:
            if updates:
                self._offset = updates[-1]['update_id'] + 1
                logger.logger.trace('Updated offset to ' + str(self._offset))

        def _run_update_listeners(self, update: Mapping[str, Any]) -> None:
            self.api._message_listeners_c.acquire()
            for i in range(len(self.api._message_listeners)):
                listener, args, kwargs = self.api._message_listeners[i]
                try:
                    thread = self.api._MethodRunningThread(self.api, i, listener, update, *args, **kwargs)
                    thread.setDaemon(True)
                    thread.start()
                except Exception as e:
                    logger.logger.error('Got ' + str(type(e)) + ' while running listener: ' + str(e))
            self.api._message_listeners_c.release()

        def _get_updates_to_listeners(self) -> None:
            logger.logger.trace('Sending new updates request')
            self.api._url_c.acquire()
            upd_resp = Bot2API._response_prepare(requests.get(self.api._url + '/getUpdates?offset=' + str(self._offset)))
            self.api._url_c.release()

            self._update_offset(upd_resp)

            for update in upd_resp:
                self._run_update_listeners(update)

        def run(self) -> None:
            try:
                while True:
                    try:
                        self._make_request(*self.cmd_queue.get(timeout=0.1))
                    except Empty:
                        self._get_updates_to_listeners()
            except Exception as e:
                logger.logger.fatal('Got ' + str(type(e)) + ' in UpdaterLoop thread!!! Exception: ' + str(e))
                bugtrackerapi.report_exception(e)
                raise e

    class _MethodRunningThread(Thread):
        def __init__(self, api: object, i: int, method: Callable, *args, **kwargs):
            Thread.__init__(self)

            logger.logger.info('Creating thread for running method ' + method.__name__)

            if not callable(method):
                raise TypeError('Method must be callable')

            self.method = method
            self.api = api
            self.i = i
            self.args = args
            self.kwargs = kwargs

        def run(self) -> None:
            try:
                self.method(*self.args, **self.kwargs)
            except AutoDelete:
                self.api._message_listeners_c.acquire()
                del self.api._message_listeners[self.i]
                self.api._message_listeners_c.release()
            finally:
                pass  # end function here bro

        @staticmethod
        def _async_raise(tid: int, exctype: Any) -> None:
            if not inspect.isclass(exctype):
                raise TypeError("Only types can be raised (not instances)")

            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))

            if res == 0:
                logger.logger.fatal('Can\'t exit thread')
                raise ValueError('Invalid thread id')
            elif res != 1:
                logger.logger.fatal('Can\'t exit thread')
                ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
                raise SystemError('PyThreadState_SetAsyncExc failed')

        def get_id(self) -> int:
            if not self.isAlive():
                logger.logger.fatal('Can\'t get thread\'s id')
                raise threading.ThreadError('Thread is not active')

            if hasattr(self, "_thread_id"):
                return self._thread_id
            for tid, tobj in threading._active.items():
                if tobj is self:
                    self._thread_id = tid
                    return tid

            logger.logger.fatal('Can\'t get thread\'s id')
            raise SystemError('Thread does not have id (???)')

        def exit(self) -> None:
            if self.isAlive():
                self._async_raise(self.get_id(), InterruptedError)
