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

from telegram import Update
from telegram.ext import CallbackContext

from db.db_service import Db
from services.message_service import i34g, reply, up

db = Db()


async def help(update: Update, context: CallbackContext) -> None:
    """
    Callback function. Sends help message.
    Args:
        update, context: standart PTB callback signature
    """
    await db.save_user(update)
    user_id = up(update)
    await reply(
        update,
        await i34g('help.message', user_id=user_id),
        disable_web_page_preview=True,
    )
    return None
