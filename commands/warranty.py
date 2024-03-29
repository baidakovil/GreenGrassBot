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

from services.message_service import i34g, reply, up


async def warranty(update: Update, _context: CallbackContext) -> None:
    """
    Callback function. Sends appropriate parts of the General Public License to message
    «This program comes with ABSOLUTELY NO WARRANTY at starting screen.
    Args:
        update, context: standart PTB callback signature
    """
    user_id = up(update)
    await reply(
        update,
        await i34g('warranty.message', user_id=user_id),
    )
    return None
