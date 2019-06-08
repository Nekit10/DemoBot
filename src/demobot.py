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

from src import logger
from src.syslang import langapi
from src.botapi import TelegramBotAPI
from src.sysbugs.bugtrackerapi import report_custom_message

polls: dict = {}
config: dict = {}
api: TelegramBotAPI


def init_bot(debug: bool = False):
    global api, config
    logger.logger.info('Begging init of bot')

    logger.logger.debug('Loading config file (debug = ' + 'True)' if debug else 'False)')
    config = load_config(debug)
    logger.logger.debug('Crating instance of TelegramBotAPI in bot init')
    api = TelegramBotAPI(config['token'], debug)
    api.add_command_listener('report', report_command_processor)
    api.add_command_listener('lang', send_lang_inline)


def load_config(debug: bool = False) -> dict:
    config_filename = 'config.json' if not debug else 'devconfig.json'
    logger.logger.debug('Using ' + config_filename + ' as config file')
    with open(config_filename, 'r') as f:
        return json.loads(f.read())


def check_return_poll_candidates() -> list:
    global api

    logger.logger.trace('Checking poll candidates')

    updates = api.get_new_updates()['result']
    candidates = []

    logger.logger.trace('Got ' + str(len(updates)) + ' updates')

    for update in updates:
        try:
            logger.logger.trace('Checking new update! (is mention? ' + str(
                config['bot_username'] in update['message']['text']) + '; is reply? ' + str(
                'reply_to_message' in update['message'].keys()) + ')\n' + str(update))
            if config['bot_username'] in update['message']['text'] and 'reply_to_message' in update['message'].keys():
                result = dict()
                result['chat_id'] = update['message']['reply_to_message']['chat']['id']
                result['name'] = update['message']['reply_to_message']['from']['first_name'] + ' ' + update['message']['reply_to_message']['from']['last_name']
                result['user_id'] = update['message']['reply_to_message']['from']['id']

                logger.logger.info('Found kick candidate in chat #' + str(result['chat_id']) + ', with name ' + result['name'] + '(' + str(result['user_id']) + ')')

                candidates += [result]
        except (NameError, IndexError, KeyError) as e:
            logger.logger.trace('Ignored name exception in checking poll candidates: ' + str(e))

    logger.logger.trace('Returning ' + str(len(candidates)) + ' kick candidates')

    return candidates


def start_poll(chat_id: int, name: str, user_id: int) -> None:
    global polls, api

    response = api.start_poll(chat_id, langapi.msg_kick(chat_id).replace('%NAME%', name), [langapi.msg_kick_yes(chat_id), langapi.msg_kick_no(chat_id)])

    poll_id = int(response['result']['poll']['id'])

    poll_info = dict()
    poll_info['chat_id'] = chat_id
    poll_info['date'] = response['result']['date']
    poll_info['user_id'] = user_id
    poll_info['name'] = name

    polls[poll_id] = poll_info


def check_kick_candidates():
    candidates = check_return_poll_candidates()
    for candidate in candidates:
        start_poll(candidate['chat_id'], candidate['name'], candidate['user_id'])


def kick_candidate(poll_id: int):
    global polls

    logger.logger.info('Kicking ' + polls[poll_id]['name'] + '(' + str(polls[poll_id]['user_id']) + ') in chat #' + str(polls[poll_id]['chat_id']))

    api.send_message(polls[poll_id]['chat_id'],
                     langapi.msg_kick_res(polls[poll_id]['chat_id']).replace('%NAME%', polls[poll_id]['name']))
    logger.logger.debug('Kick message already sent')
    api.kick_chat_member(polls[poll_id]['chat_id'], polls[poll_id]['user_id'])


def check_old_polls():
    global polls
    remove = []

    for poll_id in polls.keys():
        logger.logger.trace('Checking poll with id ' + str(poll_id))
        poll_options = api.get_poll_result(poll_id)
        if (time.time() - polls[poll_id]['date']) >= 12 * 3600 and poll_options[0]['voter_count'] > poll_options[1]['voter_count']:
            kick_candidate(poll_id)
            remove += [poll_id]
        elif (time.time() - polls[poll_id]['date']) >= 24 * 3600:
            logger.logger.info('Closing poll with id ' + str(poll_id) + ' after 24 hours')
            remove += [poll_id]

    for i in remove:
        del polls[i]


def report_command_processor(chat_id: int, from_id: int):
    api.get_new_updates()
    api.send_message(chat_id, langapi.msg_descrb_problem(chat_id))

    bug_report_msg = ''

    while bug_report_msg == '':
        updates_ = api.get_new_updates()['result']
        for update_ in updates_:
            try:
                if update_['message']['chat']['id'] == chat_id and update_['message']['from']['id'] == from_id:
                    bug_report_msg = update_['message']['text']
                    break
            except (NameError, IndexError, KeyError) as e:
                logger.logger.trace('Ignored name exception in checking report command: ' + str(e))

    api.get_new_updates()
    api.send_message(chat_id, langapi.msg_give_contact_info(chat_id))

    from_msg = ''

    while from_msg == '':
        updates_ = api.get_new_updates()['result']
        for update_ in updates_:
            try:
                if update_['message']['chat']['id'] == chat_id and update_['message']['from']['id'] == from_id:
                    from_msg = update_['message']['text']
                    break
            except (NameError, IndexError, KeyError) as e:
                logger.logger.trace('Ignored name exception in checking report command: ' + str(e))

    report_custom_message(bug_report_msg, from_msg)
    api.send_message(chat_id, langapi.msg_bug_report_send(chat_id))


def change_lang_in_chat(chat_id: int, lang: str):
    langapi.set_lang_for_chat(chat_id, lang)


def send_lang_inline(chat_id: int, from_id: int):
    api.send_inline_question(chat_id, langapi.msg_lang_choose(chat_id), langapi.get_all_langs(), change_lang_in_chat)


def main_loop() -> None:
    global polls
    logger.logger.info('Started main loop')

    while True:
        check_kick_candidates()
        check_old_polls()
        api.save_polls()
