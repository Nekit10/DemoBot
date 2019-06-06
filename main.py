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

import logging
import datetime
from logging.handlers import RotatingFileHandler

import demobot

VERSION = '1.0.0-alpha.1'
DEBUG_MODE = True

logger = logging.getLogger('dembot_logger')
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')

# Logging to console
std_handler = logging.StreamHandler()
std_handler.setLevel(logging.DEBUG)
std_handler.setFormatter(formatter)

# Latest debug log
latest_handler = RotatingFileHandler('latest.log', mode='a', maxBytes=20*1024*2014, backupCount=0, encoding=None, delay=0)
latest_handler.setLevel(logging.DEBUG)
latest_handler.setFormatter(formatter)

# Old info log
old_handler = RotatingFileHandler(datetime.datetime.now().strftime("%Y.%m.%d_%H-%M-%S") + '.log', mode='w', maxBytes=5*1024*2014, backupCount=5, encoding=None, delay=0)
old_handler.setLevel(logging.INFO)
old_handler.setFormatter(formatter)


def log_server_info():
    pass


if __name__ == '__main__':
    logging.info('Starting bot')
    log_server_info()
    demobot.init_bot(DEBUG_MODE)
    while True:
        try:
            logger.debug('Running main loop from beginning')
            demobot.main_loop()
        except Exception as e:
            logger.error('Exception (Ignored)! ' + str(e))
            print(str(e))
