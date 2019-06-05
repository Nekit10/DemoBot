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

from botapi import TelegramBotAPI

polls: dict = {}
token: str
api: TelegramBotAPI


def init_bot():
    pass


def load_token() -> str:
    pass


def check_return_poll_candidates() -> list:
    pass


def start_poll(chat_id: int, name: str, user_id: int) -> str:
    pass


def main_loop() -> None:
    pass
