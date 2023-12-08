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
"""This file, like other in /commands, contains callback funcs for same name command."""

import logging

from telegram import Update
from telegram.ext import CallbackContext

from db.db_service import Db
from services.logger import logger
from services.message_service import reply, up_full
from ui.news_builders import prepare_details_text

db = Db()

logger = logging.getLogger('A.det')
logger.setLevel(logging.DEBUG)


async def details(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends detailed info about events of the artist, chosen by user
    with command /xx, where xx called shorthand.
    Args:
        update, context: standart PTB callback signature
    """
    user_id, _, command, _ = up_full(update)
    shorthand = int(command[1:])
    text = await prepare_details_text(user_id, shorthand)
    await reply(update, text, disable_web_page_preview=True)
    logger.info(f'Details was sent to {user_id}')
    return None
