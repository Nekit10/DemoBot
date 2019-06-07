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

import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

TRACE_LOGLEVEL = 5


class AppLogger(logging.getLoggerClass()):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)

        logging.addLevelName(TRACE_LOGLEVEL, 'TRACE')

    def trace(self, message, *args, **kws):
        if self.isEnabledFor(TRACE_LOGLEVEL):
            self._log(TRACE_LOGLEVEL, message, args, **kws)


logger: AppLogger


def clean_old_logs():
    log_dir = 'logs\\'
    files = [f for f in os.listdir(log_dir) if os.path.isfile(os.path.join(log_dir, f)) and f.endswith('.log') and not f.startswith('latest')]
    if len(files) > 4:
        for log_file in files[4:]:
            os.remove(os.path.join(log_dir, log_file))


def init():
    global logger

    clean_old_logs()

    logger = AppLogger(__name__)
    logger.setLevel(TRACE_LOGLEVEL)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

    # Logging to console
    std_handler = logging.StreamHandler()
    std_handler.setLevel(TRACE_LOGLEVEL)
    std_handler.setFormatter(formatter)

    # Latest debug log
    latest_handler = RotatingFileHandler('logs\\latest.log', mode='a', maxBytes=20 * 1024 * 2014, backupCount=0,
                                         encoding=None, delay=0)
    latest_handler.setLevel(logging.DEBUG)
    latest_handler.setFormatter(formatter)

    # Old info log
    old_handler = RotatingFileHandler(datetime.datetime.now().strftime("logs\\%Y.%m.%d_%H-%M-%S") + '.log', mode='w',
                                      maxBytes=5 * 1024 * 2014, backupCount=5, encoding=None, delay=0)
    old_handler.setLevel(logging.INFO)
    old_handler.setFormatter(formatter)

    logger.addHandler(std_handler)
    logger.addHandler(latest_handler)
    logger.addHandler(old_handler)
