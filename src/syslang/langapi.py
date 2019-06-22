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

from src import logger

lang_by_chat = {}

CHAT_LANG_FILE = 'chat_langs.json'


def set_lang_for_chat(chat_id: int, lang: str) -> None:
    global lang_by_chat

    logger.logger.info('Changing lang for chat #' + str(chat_id) + ' to ' + lang)

    lang_by_chat[chat_id] = lang
    save_chat_langs()


def get_lang_name_by_code(code: str) -> str:
    lang_file = os.path.join(os.path.dirname(__file__), '..\\..\\langs\\' + code + '.json')
    with open(lang_file, 'r', encoding='utf-8') as f:
        return json.loads(f.read())['name']


def get_all_langs() -> list:
    langs_path = os.path.join(os.path.dirname(__file__), '..\\..\\langs\\')
    return [[get_lang_name_by_code(f[:-5]), f[:-5]] for f in os.listdir(langs_path) if f.endswith('.json') and os.path.isfile(os.path.join(langs_path, f))]


def _get_trans_str(chat_id: int, name: str) -> str:
    code = 'en-US' if chat_id not in lang_by_chat.keys() else lang_by_chat[chat_id]

    lang_file = os.path.join(os.path.dirname(__file__), '..\\..\\langs\\' + code + '.json')
    with open(lang_file, 'r', encoding='utf-8') as f:
        langs = json.loads(f.read())

    return langs['translation'][name]


def load_chat_langs():
    global lang_by_chat

    logger.logger.info('Reading chat\'s langs')

    lang_by_chat_ = {}

    file_full_path = os.path.join(os.path.dirname(__file__), '..\\..\\' + CHAT_LANG_FILE)
    if os.path.exists(file_full_path):
        with open(file_full_path, 'r') as f:
            lang_by_chat_ = json.loads(f.read())

    for k, v in lang_by_chat_.items():
        lang_by_chat[int(k)] = v


def save_chat_langs():
    logger.logger.info('Saving chat\'s langs')

    file_full_path = os.path.join(os.path.dirname(__file__), '..\\..\\' + CHAT_LANG_FILE)
    with open(file_full_path, 'w') as f:
        f.write(json.dumps(lang_by_chat))


def msg_kick(chat_id) -> str:
    return _get_trans_str(chat_id, 'kick')


def msg_kick_yes(chat_id) -> str:
    return _get_trans_str(chat_id, 'kick_yes')


def msg_kick_no(chat_id) -> str:
    return _get_trans_str(chat_id, 'kick_no')


def msg_kick_res(chat_id) -> str:
    return _get_trans_str(chat_id, 'kick_res')


def msg_descrb_problem(chat_id) -> str:
    return _get_trans_str(chat_id, 'descrb_problem')


def msg_give_contact_info(chat_id) -> str:
    return _get_trans_str(chat_id, 'give_contact_info')


def msg_bug_report_send(chat_id) -> str:
    return _get_trans_str(chat_id, 'bug_report_send')


def msg_lang_choose(chat_id) -> str:
    return _get_trans_str(chat_id, 'lang_choose')


def msg_lang_notify(chat_id) -> str:
    return _get_trans_str(chat_id, 'lang_notify')


def msg_version_info(chat_id) -> str:
    return _get_trans_str(chat_id, 'version_info')
