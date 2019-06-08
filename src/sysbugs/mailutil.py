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
import os
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from src import logger


def _parse_mail_info():
    logger.logger.debug('Reading data from emailinfo.json')

    with open(os.path.join(os.path.dirname(__file__), 'mailinfo.json'), 'r') as f:
        return json.loads(f.read())


def send_email(to: str, re: str, msg_: str, files: list):
    mail_info = _parse_mail_info()

    logger.logger.info('Sending email to ' + to)

    s = SMTP(host='smtp.gmail.com', port=587)
    s.starttls()
    s.login(mail_info['sender']['email'], mail_info['sender']['password'])

    msg = MIMEMultipart()
    msg['From'] = mail_info['sender']['email']
    msg['To'] = to
    msg['Subject'] = re

    msg.attach(MIMEText(msg_, 'plain'))

    for file_lst in files:
        filename = file_lst[0]
        attachment = open(file_lst[1], 'rb')

        logger.logger.debug('Attaching ' + filename + ' to email')

        p = MIMEBase('application', 'octet-stream')

        p.set_payload(attachment.read())

        encoders.encode_base64(p)

        p.add_header('Content-Disposition', "attachment; filename= {}".format(filename))

        msg.attach(p)

    s.send_message(msg)

    logger.logger.info('Email successfullly sent')

    del msg
