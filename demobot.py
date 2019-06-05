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
import time

from botapi import TelegramBotAPI

polls: dict = {}
token: str
api: TelegramBotAPI


def init_bot():
    global token, api

    token = load_token()
    api = TelegramBotAPI(token)


def load_token() -> str:
    with open('config.json', 'r') as f:
        return json.loads(f.read())['token']


def check_return_poll_candidates() -> list:
    global api

    updates = api.get_new_updates()['result']
    candidates = []

    for update in updates:
        try:
            if '@chatdemocratic_bot' in update['message']['text'] and 'reply_to_message' in update['message'].keys():
                result = dict()
                result['chat_id'] = update['message']['reply_to_message']['chat']['id']
                result['name'] = update['message']['reply_to_message']['from']['first_name'] + ' ' + update['message']['reply_to_message']['from']['last_name']
                result['user_id'] = update['message']['reply_to_message']['from']['id']

                candidates += [result]
        except (NameError, IndexError, KeyError):
            pass

    return candidates


def start_poll(chat_id: int, name: str, user_id: int) -> None:
    global polls, api

    response = api.start_poll(chat_id, 'Кикнуть ' + name + '?', ['Да', 'Нет'])

    poll_id = int(response['result']['poll']['id'])

    poll_info = dict()
    poll_info['chat_id'] = chat_id
    poll_info['date'] = response['result']['date']
    poll_info['user_id'] = user_id
    poll_info['name'] = name

    polls[poll_id] = poll_info


def main_loop() -> None:
    global polls, api

    while True:
        candidates = check_return_poll_candidates()
        for candidate in candidates:
            start_poll(candidate['chat_id'], candidate['name'], candidate['user_id'])

        remove = []
        for poll_id in polls.keys():
            poll_options = api.get_poll_result(poll_id)
            if (time.time() - polls[poll_id]['date']) >= 12*3600 and poll_options[0]['voter_count'] > poll_options[1]['voter_count']:
                api.send_message(polls[poll_id]['chat_id'], 'Выгоняем ' + polls[poll_id]['name'] + ' по результатам опроса!')
                api.kick_chat_member(polls[poll_id]['chat_id'], polls[poll_id]['user_id'])
                remove += [poll_id]
            elif (time.time() - polls[poll_id]['date']) >= 24*3600:
                remove += [poll_id]

        for i in remove:
            del polls[i]

        api.save_polls()
