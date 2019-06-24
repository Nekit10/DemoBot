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

import platform
import json
import sys
import os

from src import demobot, logger
from src.bot2api import Bot2API
from src.sysbugs.bugtrackerapi import report_exception
from src.syslang.langapi import load_chat_langs, msg_version_info

VERSION = '1.0.0-alpha.2'
DEBUG_MODE = True

logger.init()
load_chat_langs()


def log_server_info():
    logger.logger.info('\nPC Specs: ' +
                 '\nMachine: ' + platform.machine() +
                 '\nOS Version: ' + platform.version() +
                 '\nPlatform: ' + platform.platform() +
                 '\nUname: ' + ' '.join(platform.uname()) +
                 '\nSystem: ' + platform.system() +
                 '\nCPU: ' + platform.processor() +
                 '\nPython version: ' + platform.python_version())


def load_chats():
    logger.logger.info('Loading chats in main.py')

    path = os.path.join(os.path.dirname(__file__), 'chats.json')

    logger.logger.debug('Full path to file with chats: ' + path)

    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.loads(f.read())
    else:
        logger.logger.debug('Chats file doest not exist, returning empty list')
        return []


if __name__ == '__main__':
    logger.logger.info('Starting bot, version: ' + VERSION)

    log_server_info()
    logger.logger.debug('Debug mode is ' + ('on' if DEBUG_MODE else 'off'))
    demobot.init_bot(DEBUG_MODE)

    logger.logger.debug('Full run command (argc = ' + str(len(sys.argv)) + ') : ' + ' '.join(sys.argv))
    if len(sys.argv) > 1 and sys.argv[1] == '--version-notify':
        logger.logger.info('Running version notify variant of program')

        api = Bot2API(DEBUG_MODE)

        chats = load_chats()
        logger.logger.debug('Loaded ' + str(len(chats)) + ' chats')

        for chat in chats:
            logger.logger.debug('Sending version notify message to chat #' + str(chat))
            api.send_message(chat, msg_version_info(chat))
        logger.logger.info('Ended sending notify messages')
        sys.exit(0)

    while True:
        try:
            logger.logger.debug('Running main loop from beginning')
            demobot.main_loop()
        except Exception as e:
            logger.logger.warning('Exception (Ignored)! ' + str(e))
            if not DEBUG_MODE:
                report_exception(e)
            else:
                raise e
