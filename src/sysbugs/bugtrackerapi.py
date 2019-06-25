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
import typing

from src.sysbugs import mailutil
from src import logger


def get_log_files() -> typing.List[str]:
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '../../logs/')
    logger.logger.debug('Getting logs from ' + logs_dir)
    files = [os.path.join(logs_dir, f)
             for f in os.listdir(logs_dir) if os.path.isfile(os.path.join(logs_dir, f)) and f.endswith('.log')]

    return files


def report_custom_message(msg: str, from_email: str) -> None:
    logger.logger.info('Reporting "' + msg + '" from ' + from_email)
    mailutil.send_email(mailutil.parse_mail_info()['bug_tracker_email'], 'Bug Report', 'New bug report!\n' + msg
                        + '\nFrom: ' + from_email, get_log_files())


def report_exception(e: Exception) -> None:
    logger.logger.info('Reporting exception: ' + str(e))
    report_custom_message(str(e), 'None')
