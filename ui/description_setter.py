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
"""This file contains procedures making multilanguage bot descriptions at empty chat."""

import asyncio
import logging

from telegram.ext import Application

from config import Cfg
from services.logger import logger
from services.message_service import i34g

logger = logging.getLogger("A.des")
logger.setLevel(logging.DEBUG)

CFG = Cfg()


def set_description(application: Application) -> None:
    """
    Procedure to setup multilanguage bot descriptions that you see at empty chat.
    Args:
        application: application with bot to add description to
    """
    if not CFG.NEED_DESCRIPTION:
        logger.debug('Descriptions setup skipped')
        return None

    problem = False
    for locale in CFG.LOCALES_ISO:
        desc = asyncio.get_event_loop().run_until_complete(
            i34g(f'description.{locale}', locale=locale)
        )
        changed = asyncio.get_event_loop().run_until_complete(
            application.bot.set_my_description(description=desc, language_code=locale)
        )
        if not changed:
            problem = True
            logger.warning(f'Descriptions tried to be set but some problem happens')
    if not problem:
        logger.info(f'Desriptions set for languages: {CFG.LOCALES_ISO}')
    return None
