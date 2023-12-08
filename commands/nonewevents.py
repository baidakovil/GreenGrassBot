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
from services.custom_classes import UserSettings
from services.message_service import i34g, reply, up

db = Db()


async def nonewevents(update: Update, _context: CallbackContext) -> None:
    """
    Callback function. Toggle 'nonewevents' settings on-off. This settings controls
    whether user should be notified when no events there.
    Args:
        update, context: standart PTB callback signature
    """
    user_id = up(update)
    usersettings = await db.rsql_settings(user_id)
    if usersettings is None:
        text = await i34g('nonewevents.error', user_id=user_id)
        await reply(update, text)
        return None
    assert isinstance(usersettings, UserSettings)
    new_value = int(not bool(int(usersettings.nonewevents)))
    affected = await db.wsql_settings(user_id=user_id, nonewevents=new_value)
    if affected and new_value:
        text = await i34g('nonewevents.nots_disabled', user_id=user_id)
    elif affected:
        text = await i34g('nonewevents.nots_enabled', user_id=user_id)
    else:
        text = await i34g('nonewevents.error', user_id=user_id)
    await reply(update, text)
    return None

    #  Green Grass Bot — A program to notify about concerts of artists you listened to.
    #  Copyright (C) 2021-2023 Ilia Baidakov <baidakovil@gmail.com> <please contact for paper mail>

    #  This program is free software: you can redistribute it and/or modify
    #  it under the terms of the GNU General Public License as published by
    #  the Free Software Foundation, either version 3 of the License, or
    #  (at your option) any later version.

    #  This program is distributed in the hope that it will be useful,
    #  but WITHOUT ANY WARRANTY; without even the implied warranty of
    #  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #  GNU General Public License for more details.

    #  You should have received a copy of the GNU General Public License
    #  along with this program.  If not, see <https://www.gnu.org/licenses/>.
