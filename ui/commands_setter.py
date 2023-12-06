# Green Grass Bot — Ties the music you're listening to with the concert it's playing at.
# Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com>

# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <https://www.gnu.org/licenses/>.
"""This file contains procedures making multilanguage bot commands at Menu button."""

import asyncio
import logging

from telegram import BotCommand
from telegram.ext import Application

from config import Cfg
from services.logger import logger
from services.message_service import i34g

logger = logging.getLogger("A.com")
logger.setLevel(logging.DEBUG)

CFG = Cfg()


def set_commands(application: Application) -> None:
    """
    Procedure to setup multilanguage bot commands at Menu button.
    Args:
        application: application with bot to add commands to
    """
    if not CFG.NEED_COMMANDS:
        logger.debug('Commands setup skipped')
        return None

    problem = False
    bot_commands = []

    for locale in CFG.LOCALES_ISO:
        for com_group in CFG.COMMANDS_ALL.values():
            for command in com_group:
                if command in CFG.COMMANDS_UNDISPLAYED:
                    continue
                description = asyncio.get_event_loop().run_until_complete(
                    i34g(f'commands.{command}_shor', locale=locale)
                )
                bot_commands.append(
                    BotCommand(command=command, description=description)
                )
                changed = asyncio.get_event_loop().run_until_complete(
                    application.bot.set_my_commands(bot_commands, language_code=locale)
                )
                if not changed:
                    problem = True
                    logger.warning(f'Commands tried to be set but some problem happens')
    if not problem:
        logger.info(f'Commands set for languages: {CFG.LOCALES_ISO}')
    return None
