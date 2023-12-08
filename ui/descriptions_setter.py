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
import time

from telegram.ext import Application

import config as cfg
from services.logger import logger
from services.message_service import i34g

logger = logging.getLogger("A.des")
logger.setLevel(logging.DEBUG)


def set_descriptions(application: Application) -> None:
    """
    Procedure to setup multilanguage bot descriptions: that you see at empty chat (512
    char max) AND description shown on the bot's profile page, also sent together with
    the link when users share the bot (120 char max). Better turn off in cfg after once.
    Args:
        application: application with bot to add description to
    """
    if not cfg.NEED_DESCRIPTION:
        logger.debug('Descriptions setup skipped')
        return None

    #  Add empty string as lang to set descriptions to users without dedicated language.
    language_codes = cfg.LOCALES_ISO
    language_codes.append('')

    problem = False
    for locale in language_codes:
        #  Lines below prepare descriptions. get_event_loop() to awoid awaitable func
        i34g_locale = cfg.LOCALE_DEFAULT if locale == '' else locale
        desc_prof_share_120 = asyncio.get_event_loop().run_until_complete(
            i34g(f'description.prof_share_120', locale=i34g_locale)
        )
        desc_empty_chat_512 = asyncio.get_event_loop().run_until_complete(
            i34g(f'description.empty_chat_512', locale=i34g_locale)
        )

        #  Lines below change descriptions.
        changed_120 = asyncio.get_event_loop().run_until_complete(
            application.bot.set_my_short_description(
                short_description=desc_prof_share_120, language_code=locale
            )
        )
        changed_512 = asyncio.get_event_loop().run_until_complete(
            application.bot.set_my_description(
                description=desc_empty_chat_512, language_code=locale
            )
        )
        if (not changed_512) or (not changed_120):
            problem = True
            logger.warning('Descriptions tried to be set but some problem happens')
        time.sleep(1)

    if not problem:
        logger.info('Desriptions set for languages: {cfg.LOCALES_ISO}')
    return None
